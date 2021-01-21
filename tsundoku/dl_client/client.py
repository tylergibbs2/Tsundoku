import base64
import hashlib
import logging
from pathlib import Path
import re
from typing import Optional, List

import aiohttp
import bencodepy

from tsundoku.config import get_config_value
from tsundoku.dl_client.deluge import DelugeClient
from tsundoku.dl_client.qbittorrent import qBittorrentClient


logger = logging.getLogger("tsundoku")


class Manager:
    def __init__(self, session: aiohttp.ClientSession):
        client = get_config_value("TorrentClient", "client")

        host = get_config_value("TorrentClient", "host")
        port = get_config_value("TorrentClient", "port")
        secure = get_config_value("TorrentClient", "secure")

        password = get_config_value("TorrentClient", "password")

        if client == "deluge":
            self._client = DelugeClient(session, host=host, port=port, secure=secure, auth=password)
        elif client == "qbittorrent":
            username = get_config_value("TorrentClient", "username")
            auth = {
                "username": username,
                "password": password
            }
            self._client = qBittorrentClient(session, host=host, port=port, secure=secure, auth=auth)
        else:
            logger.error("Invalid TorrentClient in Configuration")

        self.session = session


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
        def b32_to_sha1(match: re.Match):
            hash_ = match.group(1)
            if len(hash_) == 40:
                return
            elif len(hash_) == 32:
                return base64.b32decode(hash_.upper()).hex()

        if location.startswith("magnet:?"):
            return re.sub(pattern, b32_to_sha1, location)
        else:
            async with self.session.get(location) as resp:
                torrent_bytes = await resp.read()
                metadata = bencodepy.decode(torrent_bytes)

        subject = metadata[b'info']

        hash_data = bencodepy.encode(subject)
        digest = hashlib.sha1(hash_data).hexdigest()

        return "magnet:?"\
            + f"xt=urn:btih:{digest}"\
            + f"&dn={metadata[b'info'][b'name'].decode()}"\
            + f"&tr={metadata[b'announce'].decode()}"


    async def get_file_structure(self, location: str) -> List[str]:
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
            metadata = bencodepy.decode(torrent_bytes)

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


    async def get_torrent_fp(self, torrent_id: str) -> Optional[Path]:
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
        return await self._client.get_torrent_fp(torrent_id)


    async def add_torrent(self, magnet_url: str) -> Optional[str]:
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
        return await self._client.add_torrent(magnet_url)
