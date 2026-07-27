from collections.abc import Iterator
import logging
from pathlib import Path
import tempfile

from pydantic import ValidationError
import pytest

from tests.mock import MockTsundokuAppState, UserType
from tsundoku.manager import PathMapping
from tsundoku.manager.path_mapping import remote_prefix_key


@pytest.fixture(name="local_dir")
def make_local_dir() -> Iterator[Path]:
    """A directory that really exists, for the save-time local prefix check.

    pytest's ``tmp_path`` is unusable alongside the ``app`` fixture: that
    fixture monkeypatches ``Path.mkdir`` for the downloader tests, which stubs
    out pytest's own tmp directory creation. ``tempfile`` goes through ``os``
    directly and is unaffected.
    """
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory)


def make_mapping(remote_prefix: str, local_prefix: str) -> PathMapping:
    """Build an unbound mapping; ``apply`` is pure and needs no app or DB."""
    return PathMapping(id_=0, remote_prefix=remote_prefix, local_prefix=local_prefix)


def test_apply_without_mappings_is_identity() -> None:
    path = Path("/downloads/Show/ep.mkv")
    assert PathMapping.apply([], path) == path


def test_apply_translates_matching_prefix() -> None:
    mappings = [make_mapping("/downloads", "/mnt/dl")]

    assert PathMapping.apply(mappings, Path("/downloads/Show/ep.mkv")) == Path("/mnt/dl/Show/ep.mkv")


def test_apply_leaves_unmatched_path_alone() -> None:
    mappings = [make_mapping("/downloads", "/mnt/dl")]
    path = Path("/elsewhere/Show/ep.mkv")

    assert PathMapping.apply(mappings, path) == path


def test_apply_matches_whole_components_only() -> None:
    """'/data/tv' must not swallow paths under '/data/tvshows'."""
    mappings = [make_mapping("/data/tv", "/mnt/tv")]
    path = Path("/data/tvshows/Show/ep.mkv")

    assert PathMapping.apply(mappings, path) == path


def test_apply_prefers_the_longest_matching_prefix() -> None:
    mappings = [
        make_mapping("/data", "/mnt/generic"),
        make_mapping("/data/torrents/complete", "/mnt/specific"),
    ]

    result = PathMapping.apply(mappings, Path("/data/torrents/complete/Show/ep.mkv"))
    assert result == Path("/mnt/specific/Show/ep.mkv")


def test_apply_falls_back_to_shorter_prefix() -> None:
    mappings = [
        make_mapping("/data", "/mnt/generic"),
        make_mapping("/data/torrents/complete", "/mnt/specific"),
    ]

    result = PathMapping.apply(mappings, Path("/data/other/ep.mkv"))
    assert result == Path("/mnt/generic/other/ep.mkv")


def test_apply_translates_path_equal_to_prefix() -> None:
    mappings = [make_mapping("/downloads", "/mnt/dl")]

    assert PathMapping.apply(mappings, Path("/downloads")) == Path("/mnt/dl")


def test_apply_translates_windows_remote_onto_posix_local() -> None:
    """A Windows seedbox reporting to a Linux Tsundoku is a real deployment."""
    mappings = [make_mapping(r"D:\torrents", "/downloaded")]

    result = PathMapping.apply(mappings, Path(r"D:\torrents\Show\ep.mkv"))
    assert result == Path("/downloaded/Show/ep.mkv")


def test_apply_windows_remote_is_case_insensitive() -> None:
    mappings = [make_mapping(r"D:\Torrents", "/downloaded")]

    result = PathMapping.apply(mappings, Path(r"d:\torrents\Show\ep.mkv"))
    assert result == Path("/downloaded/Show/ep.mkv")


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ("/downloads/", "/downloads"),
        ("/downloads//nested/", "/downloads/nested"),
    ],
)
def test_prefixes_are_normalized(stored: str, expected: str) -> None:
    assert make_mapping(stored, stored).remote_prefix == expected
    assert make_mapping(stored, stored).local_prefix == expected


def test_prefixes_are_normalized_on_assignment() -> None:
    mapping = make_mapping("/downloads", "/mnt/dl")
    mapping.remote_prefix = "/data/torrents/"

    assert mapping.remote_prefix == "/data/torrents"


@pytest.mark.parametrize("prefix", ["downloads", "downloads/nested", "./downloads"])
def test_rejects_relative_prefixes(prefix: str) -> None:
    with pytest.raises(ValidationError):
        make_mapping(prefix, "/mnt/dl")
    with pytest.raises(ValidationError):
        make_mapping("/downloads", prefix)


@pytest.mark.parametrize("prefix", ["/", "//"])
def test_rejects_filesystem_root(prefix: str) -> None:
    """A root prefix would silently remap every path on the system."""
    with pytest.raises(ValidationError):
        make_mapping(prefix, "/mnt/dl")
    with pytest.raises(ValidationError):
        make_mapping("/downloads", prefix)


def test_allows_unc_share() -> None:
    """A UNC share is its own anchor but names one export, not a whole host."""
    mapping = make_mapping(r"\\nas\share", "/mnt/nas")

    # The canonical form of a UNC anchor carries a trailing separator.
    assert mapping.remote_prefix == "\\\\nas\\share\\"
    assert PathMapping.apply([mapping], Path(r"\\nas\share\Show\x.mkv")) == Path("/mnt/nas/Show/x.mkv")


def test_remote_prefix_key_folds_windows_case() -> None:
    assert remote_prefix_key(r"D:\Torrents") == remote_prefix_key(r"d:\torrents")


def test_remote_prefix_key_preserves_posix_case() -> None:
    """POSIX is case-sensitive: '/Downloads' and '/downloads' are different."""
    assert remote_prefix_key("/Downloads") != remote_prefix_key("/downloads")


async def test_new_and_all_round_trip(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await PathMapping.new(app, "/downloads", "/mnt/dl")

    mappings = await PathMapping.all(app)
    assert [(m.remote_prefix, m.local_prefix) for m in mappings] == [("/downloads", "/mnt/dl")]


async def test_translate_reads_configured_mappings(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await PathMapping.new(app, "/downloads", "/mnt/dl")

    translated = await PathMapping.translate(app, Path("/downloads/Show/ep.mkv"))
    assert translated == Path("/mnt/dl/Show/ep.mkv")


async def test_get_torrent_fp_is_translated(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    """The manager is the chokepoint, so every client adapter inherits this."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    await PathMapping.new(app, "/downloads", "/mnt/dl")

    torrent_id = await app.dl_client.add_torrent("magnet:?xt=urn:btih:abc123")
    assert torrent_id is not None
    app.dl_client._client.torrents[torrent_id].fp = Path("/downloads/Show/ep.mkv")

    assert await app.dl_client.get_torrent_fp(torrent_id) == Path("/mnt/dl/Show/ep.mkv")


async def test_get_torrent_fp_without_mappings_is_unchanged(app: MockTsundokuAppState, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    torrent_id = await app.dl_client.add_torrent("magnet:?xt=urn:btih:abc123")
    assert torrent_id is not None
    app.dl_client._client.torrents[torrent_id].fp = Path("/downloads/Show/ep.mkv")

    assert await app.dl_client.get_torrent_fp(torrent_id) == Path("/downloads/Show/ep.mkv")


async def test_api_create_and_list(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)

    response = await client.post("/api/v1/path_mappings", json={"remote_prefix": "/downloads", "local_prefix": str(local_dir)})
    assert response.status_code == 201

    response = await client.get("/api/v1/path_mappings")
    assert response.status_code == 200
    assert len(response.json()["result"]) == 1


async def test_api_rejects_duplicate_remote_prefix(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    body = {"remote_prefix": "/downloads", "local_prefix": str(local_dir)}

    assert (await client.post("/api/v1/path_mappings", json=body)).status_code == 201
    # The trailing slash is normalized away, so this collides with the above.
    body["remote_prefix"] = "/downloads/"
    assert (await client.post("/api/v1/path_mappings", json=body)).status_code == 409


async def test_api_rejects_case_variant_windows_duplicate(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Both spellings name one directory, so storing both would make the
    winning mapping depend on insertion order."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    body = {"remote_prefix": r"D:\Torrents", "local_prefix": str(local_dir)}

    assert (await client.post("/api/v1/path_mappings", json=body)).status_code == 201
    body["remote_prefix"] = r"d:\torrents"
    assert (await client.post("/api/v1/path_mappings", json=body)).status_code == 409


async def test_api_allows_case_variant_posix_prefixes(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    """POSIX is case-sensitive, so these are genuinely different directories."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    body = {"remote_prefix": "/Downloads", "local_prefix": str(local_dir)}

    assert (await client.post("/api/v1/path_mappings", json=body)).status_code == 201
    body["remote_prefix"] = "/downloads"
    assert (await client.post("/api/v1/path_mappings", json=body)).status_code == 201


@pytest.mark.parametrize(("remote", "local"), [("", "/mnt/dl"), ("/", "/mnt/dl"), ("downloads", "/mnt/dl"), ("/downloads", "relative")])
async def test_api_rejects_malformed_prefixes(app: MockTsundokuAppState, remote: str, local: str, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)

    response = await client.post("/api/v1/path_mappings", json={"remote_prefix": remote, "local_prefix": local})
    assert response.status_code == 422


async def test_api_rejects_nonexistent_local_prefix(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    """The whole point of the feature is catching this at config time."""
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    missing = local_dir / "does-not-exist"

    response = await client.post("/api/v1/path_mappings", json={"remote_prefix": "/downloads", "local_prefix": str(missing)})
    assert response.status_code == 422
    assert "does not exist" in response.json()["error"]


async def test_api_update_revalidates_local_prefix(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    mapping = await PathMapping.new(app, "/downloads", str(local_dir))

    response = await client.put(
        f"/api/v1/path_mappings/{mapping.id_}",
        json={"remote_prefix": "/downloads", "local_prefix": str(local_dir / "does-not-exist")},
    )
    assert response.status_code == 422


async def test_api_delete(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.REGULAR)
    mapping = await PathMapping.new(app, "/downloads", str(local_dir))

    assert (await client.delete(f"/api/v1/path_mappings/{mapping.id_}")).status_code == 204
    assert await PathMapping.all(app) == []


async def test_api_readonly_user_cannot_create(app: MockTsundokuAppState, local_dir: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="tsundoku")

    client = await app.test_client(user_type=UserType.READONLY)

    response = await client.post("/api/v1/path_mappings", json={"remote_prefix": "/downloads", "local_prefix": str(local_dir)})
    assert response.status_code == 403
