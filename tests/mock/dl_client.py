from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import re
from typing import Dict, List, Optional

from tsundoku.dl_client.abstract import TorrentClient
from tsundoku.dl_client import Manager


class TorrentStatus(Enum):
    INCOMPLETE = auto()
    COMPLETE = auto()


@dataclass
class InMemoryTorrent:
    torrent_id: str
    fp: Optional[Path] = None
    status: TorrentStatus = TorrentStatus.INCOMPLETE
    ratio: float = 0.0

    def mark_complete(self) -> None:
        self.fp = Path(f"{self.torrent_id}.mkv")
        self.status = TorrentStatus.COMPLETE

    def is_complete(self) -> bool:
        return self.status == TorrentStatus.COMPLETE


MAGNET_RE = re.compile(r"magnet:\?.+btih:([\d\w]+)")


class MockDownloadManager(Manager):
    _client: InMemoryDownloadClient

    def __init__(self) -> None:
        self._client = InMemoryDownloadClient()

    @property
    def torrents(self) -> List[InMemoryTorrent]:
        return list(self._client.torrents.values())

    def mark_all_torrent_complete(self) -> None:
        for torrent in self.torrents:
            torrent.mark_complete()

    async def update_config(self) -> None:
        ...

    async def get_magnet(self, location: str) -> str:
        if not location.startswith("magnet:?"):
            raise Exception("Can only get_manget with magnet URLs when testing")

        return await super().get_magnet(location)

    async def get_file_structure(self, location: str) -> List[str]:
        raise NotImplementedError()


class InMemoryDownloadClient(TorrentClient):
    torrents: Dict[str, InMemoryTorrent]

    def __init__(self) -> None:
        self.torrents = {}

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        return "MOCK"

    async def test_client(self) -> bool:
        return True

    async def check_torrent_exists(self, torrent_id: str) -> bool:
        return torrent_id in self.torrents

    async def check_torrent_completed(self, torrent_id: str) -> bool:
        return torrent_id in self.torrents and self.torrents[torrent_id].is_complete()

    async def check_torrent_ratio(self, torrent_id: str) -> Optional[float]:
        if torrent_id not in self.torrents:
            return

        return self.torrents[torrent_id].ratio

    async def delete_torrent(self, torrent_id: str, with_files: bool = True) -> None:
        self.torrents.pop(torrent_id, None)

    async def get_torrent_fp(self, torrent_id: str) -> Optional[Path]:
        return self.torrents[torrent_id].fp

    async def add_torrent(self, magnet_url: str) -> Optional[str]:
        hash_match = re.search(MAGNET_RE, magnet_url)
        if hash_match is None:
            return

        info_hash = hash_match.group(1).lower().strip()
        self.torrents[info_hash] = InMemoryTorrent(info_hash)
        return info_hash

    async def login(self) -> bool:
        return True
