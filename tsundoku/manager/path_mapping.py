import logging
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath
import re
from sqlite3 import Row
from typing import TYPE_CHECKING

from pydantic import ConfigDict, field_validator

from tsundoku.model import DBModel, InsertFailedError

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState

logger = logging.getLogger("tsundoku")

_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def parse_remote_path(value: str) -> PurePath:
    """Parse a download client's path in whichever flavour it reported it.

    Tsundoku and the download client do not have to run on the same OS: a
    Windows seedbox reporting ``D:\\torrents\\...`` to a Linux container is a
    normal deployment. Parsing that with the local flavour would treat the
    whole string as a single component and silently match no mapping, so the
    flavour is chosen from the shape of the path rather than from whichever
    host Tsundoku happens to be running on.
    """
    if _WINDOWS_DRIVE_RE.match(value) or "\\" in value:
        return PureWindowsPath(value)

    return PurePosixPath(value)


def is_filesystem_root(path: PurePath) -> bool:
    """Whether ``path`` is a bare filesystem root such as ``/`` or ``C:\\``.

    A UNC share (``\\\\nas\\share``) is its own anchor too, but it names one
    specific export rather than every file on the host, so it is allowed.
    """
    if isinstance(path, PureWindowsPath) and path.drive.startswith("\\\\"):
        return False

    return path.is_absolute() and len(path.parts) <= 1


def normalize_remote_prefix(value: str) -> str:
    """Validate and canonicalize a client-side prefix.

    Raises ``ValueError`` so that both the domain model and the request
    schemas can share this as a field validator; Pydantic turns it into a 422
    on the API surface.
    """
    parsed = parse_remote_path(value)

    if not parsed.is_absolute():
        raise ValueError("Remote prefix must be an absolute path.")
    if is_filesystem_root(parsed):
        raise ValueError("Remote prefix cannot be the filesystem root.")

    # Canonicalizes redundant separators and trailing slashes.
    return str(parsed)


def normalize_local_prefix(value: str) -> str:
    """Validate and canonicalize a Tsundoku-side prefix."""
    parsed = Path(value)

    if not parsed.is_absolute():
        raise ValueError("Local prefix must be an absolute path.")
    if is_filesystem_root(parsed):
        raise ValueError("Local prefix cannot be the filesystem root.")

    return str(parsed)


def remote_prefix_key(value: str) -> str:
    """A comparison key for a remote prefix, following its flavour's case rules.

    Windows paths compare case-insensitively, so ``D:\\Torrents`` and
    ``d:\\torrents`` name the same directory and must not both be storable --
    ``apply`` would treat them as equally good matches and the winner would
    come down to insertion order. POSIX paths are case-sensitive, where ``/A``
    and ``/a`` really are different directories, so those are left alone.
    """
    parsed = parse_remote_path(value)

    if isinstance(parsed, PureWindowsPath):
        return str(parsed).casefold()

    return str(parsed)


class PathMapping(DBModel):
    """A translation from a download client's filesystem namespace into ours.

    The download clients report the paths they downloaded to in their own
    namespace (qBittorrent's ``content_path``, Deluge's
    ``move_completed_path``, Transmission's ``downloadDir``), and Tsundoku
    then performs real file I/O on them. When the two do not share a mount
    layout -- separate containers, a NAS, a remote seedbox -- those paths mean
    nothing locally, and nothing in any client's API describes its own mount
    table. That translation is deployment knowledge only the operator has,
    so it is stored rather than inferred.

    Both prefixes are held as ``str`` rather than ``Path`` on purpose: a
    Windows remote prefix cannot round-trip through a POSIX ``Path``.
    """

    # Assignment is validated so the normalizers below also run when a prefix
    # is reassigned (as the update route does), not only at construction.
    model_config = ConfigDict(validate_assignment=True)

    id_: int
    remote_prefix: str
    local_prefix: str

    @field_validator("remote_prefix")
    @classmethod
    def _check_remote(cls, value: str) -> str:
        return normalize_remote_prefix(value)

    @field_validator("local_prefix")
    @classmethod
    def _check_local(cls, value: str) -> str:
        return normalize_local_prefix(value)

    @property
    def remote_prefix_key(self) -> str:
        return remote_prefix_key(self.remote_prefix)

    @classmethod
    def from_data(cls, app: "TsundokuAppState", row: Row) -> "PathMapping":
        return cls(id_=row["id"], remote_prefix=row["remote_prefix"], local_prefix=row["local_prefix"])._bind(app)

    @classmethod
    async def from_id(cls, app: "TsundokuAppState", id_: int) -> "PathMapping":
        async with app.acquire_db() as con:
            mapping = await con.fetchone(
                """
                SELECT
                    id,
                    remote_prefix,
                    local_prefix
                FROM
                    path_mapping
                WHERE
                    id=?;
                """,
                (id_,),
            )

        if mapping is None:
            raise ValueError(f"Path mapping with ID '{id_}' does not exist")

        return cls.from_data(app, mapping)

    @classmethod
    async def all(cls, app: "TsundokuAppState") -> list["PathMapping"]:
        async with app.acquire_db() as con:
            mappings = await con.fetchall(
                """
                SELECT
                    id,
                    remote_prefix,
                    local_prefix
                FROM
                    path_mapping
                ORDER BY id ASC;
                """
            )

        return [cls.from_data(app, row) for row in mappings]

    @classmethod
    async def new(cls, app: "TsundokuAppState", remote_prefix: str, local_prefix: str) -> "PathMapping":
        instance = cls(id_=0, remote_prefix=remote_prefix, local_prefix=local_prefix)

        async with app.acquire_db() as con, con.cursor() as cur:
            await cur.execute(
                """
                    INSERT INTO
                        path_mapping (
                            remote_prefix,
                            remote_prefix_key,
                            local_prefix
                        )
                    VALUES
                        (?, ?, ?);
                """,
                (instance.remote_prefix, instance.remote_prefix_key, instance.local_prefix),
            )
            id_ = cur.lastrowid
            if id_ is None:
                raise InsertFailedError("Failed to create new path mapping, lastrowid is None")

        instance.id_ = id_
        return instance._bind(app)

    async def save(self) -> None:
        async with self.app.acquire_db() as con:
            await con.execute(
                """
                UPDATE
                    path_mapping
                SET
                    remote_prefix = ?,
                    remote_prefix_key = ?,
                    local_prefix = ?
                WHERE
                    id = ?;
                """,
                (self.remote_prefix, self.remote_prefix_key, self.local_prefix, self.id_),
            )

    async def delete(self) -> None:
        async with self.app.acquire_db() as con:
            await con.execute(
                """
                    DELETE FROM
                        path_mapping
                    WHERE
                        id = ?;
                """,
                (self.id_,),
            )

    @classmethod
    async def translate(cls, app: "TsundokuAppState", path: Path) -> Path:
        """Translate a client-reported path into Tsundoku's namespace."""
        return cls.apply(await cls.all(app), path)

    @staticmethod
    def apply(mappings: list["PathMapping"], path: Path) -> Path:
        """Apply the best-matching mapping to ``path``.

        Returns ``path`` unchanged when nothing matches, which is what makes
        the shared-filesystem deployments that never configure a mapping
        behave exactly as they did before.
        """
        remote = parse_remote_path(str(path))

        # Longest prefix wins: with both '/data' and '/data/torrents' mapped,
        # a path under the latter should take the more specific translation.
        # ID breaks ties only for determinism; two distinct prefixes of equal
        # depth cannot both match the same path.
        ordered = sorted(mappings, key=lambda m: (-len(parse_remote_path(m.remote_prefix).parts), m.id_))

        for mapping in ordered:
            prefix = parse_remote_path(mapping.remote_prefix)
            # is_relative_to compares whole components, so '/data/tv' will not
            # match a path under '/data/tvshows' the way str.startswith would.
            if not remote.is_relative_to(prefix):
                continue

            # Rebuilt component-wise: the remainder may have been parsed in a
            # different flavour than the local prefix it is being joined onto.
            translated = Path(mapping.local_prefix, *remote.relative_to(prefix).parts)
            logger.debug(f"Path mapping: translated `{path}` to `{translated}`")
            return translated

        return path
