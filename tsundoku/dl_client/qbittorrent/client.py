import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger("tsundoku")


class qBittorrentClient:
    def __init__(self, session: aiohttp.ClientSession, auth: Dict[str, str], **kwargs: Any) -> None:
        self.session = session

        host: str = kwargs.pop("host")
        port: int = kwargs.pop("port")
        secure: bool = kwargs.pop("secure")

        self.auth = auth

        self.url = self.build_api_url(host, port, secure)

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        """
        Builds the URL to make requests to the qBittorrent WebAPI.

        Parameters
        ----------
        host: str
            API host URL.
        port: int
            API port.
        secure: bool
            Use HTTPS.

        Returns
        -------
        str
            The API's URL.
        """
        protocol = "https" if secure else "http"

        return f"{protocol}://{host}:{port}"

    async def check_torrent_exists(self, torrent_id: str) -> bool:
        """
        Checks whether a torrent with the passed ID
        exists in the download client.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to check.

        Returns
        -------
        bool:
            The torrent's existence status.
        """
        fp = await self.get_torrent_fp(torrent_id)
        return bool(fp)

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
        payload = {
            "hashes": torrent_id,
            "deleteFiles": with_files
        }

        await self.request("get", "torrents", "delete", params=payload)

    async def get_torrent_fp(self, torrent_id: str) -> Optional[Path]:
        """
        Returns information for a specified torrent.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to return information for.

        Returns
        -------
        Optional[Path]:
            The torrent's downloaded file path.
        """
        payload = {
            "hashes": torrent_id
        }

        data = await self.request("get", "torrents", "info", params=payload)
        if not data:
            return None
        data = data[0]

        if data.get("hash") != torrent_id:
            return None

        return Path(data["content_path"])

    async def add_torrent(self, magnet_url: str) -> Optional[str]:
        """
        Adds a torrent to qBittorrent with the given magnet URL.

        Parameters
        ----------
        magnet_url: str
            The magnet URL of the torrent to add to qBittorrent.

        Returns
        -------
        Optional[str]
            The torrent ID if success, None if torrent not added.
        """
        payload = {
            "urls": magnet_url
        }

        await self.request("post", "torrents", "add", payload=payload)

        match = re.search(r"\burn:btih:([A-z\d]+)\b", magnet_url)
        if match is None:
            return None

        return match.group(1).lower()

    async def login(self) -> bool:
        """
        Authorizes with the qBittorrent WebUI.

        Returns
        -------
        bool
            Auth status.
        """
        headers = {
            "Referer": self.url
        }

        params = {
            "username": self.auth["username"],
            "password": self.auth["password"]
        }

        request_url = f"{self.url}/api/v2/auth/login"

        async with self.session.get(request_url, headers=headers, params=params) as resp:
            status = resp.status
            if status == 200:
                logger.info("qBittorrent - Successfully Authenticated")
            else:
                logger.warn(f"qBittorrent - Failed to Authenticate, status {status}")

        return status == 200

    async def request(self, http_method: str, location: str, method: str,
                      payload: dict = {}, params: dict = {}) -> dict:
        """
        Makes a request to qBittorrent.

        Parameters
        ----------
        http_method: str
            The request type (get, post, etc)
        location: str
            The location of the method in the API.
        method: str
            The method to call.
        payload: dict
            The data to send.

        Returns
        -------
        dict:
            The response.
        """
        # This retry code is from CuteFwan on GitHub! Thanks Cute
        # <https://github.com/CuteFwan/aqbit/blob/master/qbittorrent/connectors.py>

        request_url = f"{self.url}/api/v2/{location}/{method}"
        retries = 5

        while retries:
            async with self.session.request(http_method, request_url, data=payload, params=params) as r:
                data: Any = await r.text(encoding="utf-8")
                if r.headers.get("Content-Type") == "application/json":
                    data = json.loads(data)
                if r.status == 200:
                    return data
                elif r.status == 403:
                    retries -= 1
                    logger.warn(f"qBittorrent - Forbidden, reauthorizing {retries}")
                    await self.login()
                elif r.status == 400:
                    retries -= 1
                    logger.warn(f"qBittorrent - Bad Request, retrying {retries}")
                    await asyncio.sleep(1)
                else:
                    return {}

        return {}
