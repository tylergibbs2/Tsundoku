import base64
import hashlib
import logging
from pathlib import Path
from typing import Optional

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
        Will take a file location or an internet location for a torrent file.
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
        if location.startswith("magnet:?"):
            return location
        elif location.endswith(".torrent"):
            async with self.session.get(location) as resp:
                torrent_bytes = await resp.read()
                metadata = bencodepy.decode(torrent_bytes)
        else:
            metadata = bencodepy.decode_from_file(location)

        subject = metadata[b'info']

        hash_data = bencodepy.encode(subject)
        digest = hashlib.sha1(hash_data).digest()
        base32_hash = base64.b32encode(digest).decode()

        return "magnet:?"\
            + f"xt=urn:btih:{base32_hash}"\
            + f"&dn={metadata[b'info'][b'name'].decode()}"\
            + f"&tr={metadata[b'announce'].decode()}"


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
