import asyncio
import json
import logging
from pathlib import Path
import sys
from typing import Optional

import aiohttp
from aiohttp import ContentTypeError

from tsundoku.config import get_config_value


logger = logging.getLogger("tsundoku")


class qBittorrentClient:
    def __init__(self, session: aiohttp.ClientSession, **kwargs):
        self.session = session

        host = kwargs.pop("host")
        port = kwargs.pop("port")
        secure = kwargs.pop("secure")

        self.auth = kwargs.pop("auth")

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
            "hash": torrent_id
        }

        data = await self.request("get", "torrents", "properties", params=payload)
        if not data or not data.get("save_path"):
            return

        return Path(data["save_path"])


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

        payload = {
            "category": "tsundoku",
            "sort": "added_on",
            "limit": 1
        }

        t_list = await self.request("get", "torrents", "info", payload=payload)
        try:
            return t_list[0]["hash"]
        except (IndexError, KeyError):
            pass


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
            if resp.status == 200:
                logger.info("qBittorrent - Successfully Authenticated")
                status = resp.status
            else:
                status = resp.status

        if status != 200:
            logger.warn(f"qBittorrent - Failed to Authenticate, status {status}")

        return status == 200


    async def request(self, http_method: str, location: str, method: str, payload: dict={}, params: dict={}) -> dict:
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
                data = await r.text(encoding="utf-8")
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
