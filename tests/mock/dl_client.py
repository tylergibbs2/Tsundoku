from dataclasses import dataclass
from enum import Enum, auto
import hashlib
from pathlib import Path
import re
from typing import TYPE_CHECKING

from tsundoku.dl_client import Manager
from tsundoku.dl_client.abstract import TestClientResult, TorrentClient

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState


class TorrentStatus(Enum):
    INCOMPLETE = auto()
    COMPLETE = auto()


@dataclass
class InMemoryTorrent:
    torrent_id: str
    fp: Path | None = None
    status: TorrentStatus = TorrentStatus.INCOMPLETE
    ratio: float = 0.0

    def mark_complete(self) -> None:
        self.fp = Path(f"{self.torrent_id}.mkv")
        self.status = TorrentStatus.COMPLETE

    def is_complete(self) -> bool:
        return self.status == TorrentStatus.COMPLETE


MAGNET_RE = re.compile(r"magnet:\?.+btih:([\d\w]+)")


class UnregisteredTorrentError(BaseException):
    """Raised when app code inspects a torrent the test never described.

    Inherits from :class:`BaseException` for the same reason as
    :class:`tests.mock.session.UnstubbedRequestError`: the call sites that
    read a torrent's contents sit near broad ``except Exception`` handlers
    that would turn a missing fixture into an empty episode list, and a test
    asserting "no episodes were added" would then pass for the wrong reason.
    """


class MockDownloadManager(Manager):
    _client: "InMemoryDownloadClient"

    def __init__(self, app: "TsundokuAppState") -> None:
        # The app is needed even though the config is never read from it:
        # Manager.get_torrent_fp resolves path mappings through it, so the
        # mock exercises the same translation the real manager does. The
        # session comes along for the same reason -- Manager.fetch_torrent
        # uses it to reach the development torrent mirror.
        self.app = app
        self.session = app.session
        self._client = InMemoryDownloadClient()
        self._file_structures: dict[str, list[str]] = {}

    @property
    def torrents(self) -> list[InMemoryTorrent]:
        return list(self._client.torrents.values())

    def mark_all_torrent_complete(self) -> None:
        for torrent in self.torrents:
            torrent.mark_complete()

    async def update_config(self) -> None: ...

    async def get_magnet(self, location: str) -> str:
        if location.startswith("magnet:?"):
            return await super().get_magnet(location)

        # For a .torrent URL the real manager downloads the file and hashes
        # its info dict. There is no network here, so a deterministic hash of
        # the URL stands in: callers only need a stable magnet that maps one
        # to one with the source link.
        digest = hashlib.sha1(location.encode()).hexdigest()
        return f"magnet:?xt=urn:btih:{digest}"

    def set_file_structure(self, location: str, files: list[str]) -> None:
        """Declare the file names carried by the torrent at ``location``.

        Mirrors what the real manager derives by fetching the ``.torrent`` and
        bencode-decoding it: a single-file torrent yields one name, a folder
        torrent yields one name per contained file.
        """
        self._file_structures[location] = list(files)

    async def get_file_structure(self, location: str) -> list[str]:
        # A magnet's file name is carried in the URL itself, so the real
        # implementation reaches no network and is used as-is; stubbing it
        # would only let the mock disagree with production.
        if location.startswith("magnet:?"):
            return await super().get_file_structure(location)

        try:
            return list(self._file_structures[location])
        except KeyError:
            raise UnregisteredTorrentError(f"No file structure registered for torrent: {location}\nDeclare one with app.dl_client.set_file_structure({location!r}, [...]).") from None


class InMemoryDownloadClient(TorrentClient):
    torrents: dict[str, InMemoryTorrent]

    def __init__(self) -> None:
        self.torrents = {}

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        return "MOCK"

    async def test_client(self) -> TestClientResult:
        return TestClientResult(True)

    async def check_torrent_exists(self, torrent_id: str) -> bool:
        return torrent_id in self.torrents

    async def check_torrent_completed(self, torrent_id: str) -> bool:
        return torrent_id in self.torrents and self.torrents[torrent_id].is_complete()

    async def check_torrent_ratio(self, torrent_id: str) -> float | None:
        if torrent_id not in self.torrents:
            return None

        return self.torrents[torrent_id].ratio

    async def delete_torrent(self, torrent_id: str, with_files: bool = True) -> None:
        self.torrents.pop(torrent_id, None)

    async def get_torrent_fp(self, torrent_id: str) -> Path | None:
        return self.torrents[torrent_id].fp

    async def add_torrent(self, magnet_url: str) -> str | None:
        hash_match = re.search(MAGNET_RE, magnet_url)
        if hash_match is None:
            return None

        info_hash = hash_match.group(1).lower().strip()
        self.torrents[info_hash] = InMemoryTorrent(info_hash)
        return info_hash

    async def login(self) -> TestClientResult:
        return TestClientResult(True)
