import base64
import hashlib
import logging
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

import aiohttp
import bencodepy

from tsundoku.config import TorrentConfig
from tsundoku.dl_client.abstract import TorrentClient
from tsundoku.dl_client.deluge import DelugeClient
from tsundoku.dl_client.qbittorrent import qBittorrentClient
from tsundoku.dl_client.transmission import TransmissionClient

logger = logging.getLogger("tsundoku")


class Manager:
    app: "TsundokuApp"
    session: aiohttp.ClientSession

    __last_hash: int | None

    def __init__(self, app_context: Any, session: aiohttp.ClientSession) -> None:
        self.app = app_context.app
        self.session = session
        self.__last_hash = None

        self._client: TorrentClient

    async def update_config(self) -> None:
        """
        Updates the configuration for the
        app's desired torrent client.
        """
        cfg = await TorrentConfig.retrieve(self.app)

        hash_ = hash(cfg)
        if self.__last_hash == hash_:
            return

        self.__last_hash = hash_

        host = cfg.host
        port = cfg.port
        secure = cfg.secure

        username = cfg.username
        password = cfg.password

        kwargs = {"host": host, "port": port, "secure": secure}

        if cfg.client == "deluge":
            kwargs["auth"] = password
            self._client = DelugeClient(self.session, **kwargs)
        elif cfg.client == "qbittorrent":
            kwargs["auth"] = {"username": username, "password": password}
            self._client = qBittorrentClient(self.session, **kwargs)
        elif cfg.client == "transmission":
            kwargs["auth"] = {"username": username, "password": password}
            self._client = TransmissionClient(self.session, **kwargs)

    async def get_magnet(self, location: str) -> str:
        """
        Will take an internet location for a torrent file.
        The magnet URL for that torrent is then resolved and returned.

        If the location parameter is already detected to be a magnet URL,
        it will instantly return it.

        Parameters
        ----------
        location: str
            A file location or web address.

        Returns
        -------
        str
            The magnet URL for the torrent at the given location.
        """
        pattern = re.compile(r"\burn:btih:([A-z\d]+)\b")

        def b32_to_sha1(match: re.Match) -> str:
            hash_ = match.group(1)
            if len(hash_) == 40:
                return match.group(0)
            if len(hash_) == 32:
                return "urn:btih:" + base64.b32decode(hash_.upper()).hex()

            return match.group(0)

        if location.startswith("magnet:?"):
            return re.sub(pattern, b32_to_sha1, location)
        async with self.session.get(location) as resp:
            torrent_bytes = await resp.read()
            metadata: Any = bencodepy.decode(torrent_bytes)

        subject = metadata[b"info"]

        hash_data = bencodepy.encode(subject)
        digest = hashlib.sha1(hash_data).hexdigest()

        magnet_url = f"magnet:?xt=urn:btih:{digest}&dn={metadata[b'info'][b'name'].decode()}&tr={metadata[b'announce'].decode()}"

        return re.sub(pattern, b32_to_sha1, magnet_url)

    async def get_file_structure(self, location: str) -> list[str]:
        """
        Given a URL to a .torrent file, it will then return a list
        of the file names inside.

        Parameters
        ----------
        location: str
            A URL to a .torrent file.

        Returns
        -------
        List[str]
            List of file names.
        """
        async with self.session.get(location) as resp:
            torrent_bytes = await resp.read()
            metadata: Any = bencodepy.decode(torrent_bytes)

        is_folder = b"files" in metadata[b"info"]

        file_names = []

        if is_folder:
            for item in metadata[b"info"][b"files"]:
                try:
                    file_names.append(item[b"path"][0].decode("utf-8"))
                except IndexError:
                    pass
        else:
            file_names.append(metadata[b"info"][b"name"].decode("utf-8"))

        return file_names

    async def test_client(self) -> bool:
        """
        Checks whether or not the torrent client is able
        to connect.
        """
        await self.update_config()

        try:
            return await self._client.test_client()
        except Exception as e:
            logger.error(f"Failed to test torrent client. [{e}]", exc_info=True)
            return False

    async def check_torrent_completed(self, torrent_id: str) -> bool:
        """
        Checks whether a torrent is fully completed and ready
        for file I/O operations.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to check.

        Returns
        -------
        bool:
            The torrent's completion status.
        """
        await self.update_config()

        return await self._client.check_torrent_completed(torrent_id)

    async def check_torrent_ratio(self, torrent_id: str) -> float | None:
        """
        Checks whether a torrent has a ratio of at least 1.0.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to check.

        Returns
        -------
        Optional[float]:
            The torrent's ratio.
        """
        await self.update_config()

        return await self._client.check_torrent_ratio(torrent_id)

    async def delete_torrent(self, torrent_id: str, with_files: bool = True) -> None:
        """
        Sends a request to the client to delete the torrent,
        optionally also delete the files.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to delete.
        with_files: bool
            Whether or not to delete the files downloaded.
        """
        await self.update_config()

        await self._client.delete_torrent(torrent_id, with_files=with_files)

    async def get_torrent_fp(self, torrent_id: str) -> Path | None:
        """
        Retrieves a torrent's downloaded location from a download client.

        Parameters
        ----------
        torrent_id: str
            The torrent's ID (hash)

        Returns
        -------
        Optional[Path]:
            The torrent Path object.
        """
        await self.update_config()

        return await self._client.get_torrent_fp(torrent_id)

    async def add_torrent(self, magnet_url: str) -> str | None:
        """
        Adds a torrent to a download client.

        Parameters
        ----------
        magnet_url: str
            The torrent's magnet URL.

        Returns
        -------
        Optional[str]:
            The torrent's hash.
        """
        await self.update_config()

        return await self._client.add_torrent(magnet_url)
