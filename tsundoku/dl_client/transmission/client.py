import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

from tsundoku.dl_client.abstract import TorrentClient

logger = logging.getLogger("tsundoku")


class TransmissionClient(TorrentClient):
    def __init__(self, session: aiohttp.ClientSession, **kwargs: Any) -> None:
        self.session = session

        host: str = kwargs.pop("host")
        port: int = kwargs.pop("port")
        secure: bool = kwargs.pop("secure")
        auth: Dict[str, str] = kwargs.pop("auth", {})

        self.url = self.build_api_url(host, port, secure)

        self.session_id: str = ""

        username = auth.get("username", "")
        password = auth.get("password", "")
        self.credentials = self.get_encoded_credentials(username, password)

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        protocol = "https" if secure else "http"

        return f"{protocol}://{host}:{port}"

    def get_encoded_credentials(self, username: str, password: str) -> str:
        """
        Takes a username and password and returns
        a string of them properly encoded for use
        in HTTP basic authorization.

        Parameters
        ----------
        username: str
            Auth username.
        password: str
            Auth password.

        Returns
        -------
        str
            Encoded credentials.
        """
        return base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")

    async def test_client(self) -> bool:
        try:
            resp = await self.request("session-stats")
        except ConnectionRefusedError:
            return False

        return resp.get("result") == "success"

    async def check_torrent_exists(self, torrent_id: str) -> bool:
        fp = await self.get_torrent_fp(torrent_id)
        return fp is not None

    async def check_torrent_completed(self, torrent_id: str) -> bool:
        resp = await self.request("torrent-get", {
            "ids": [torrent_id],
            "fields": ["isFinished", "status"]
        })

        if resp.get("result") != "success":
            return False

        root = resp["arguments"]["torrents"]
        if not len(root):
            return False

        torrent = root[0]

        status = torrent["status"]
        finished = torrent["isFinished"]
        return (
            (status == 0 and finished) or
            status in (5, 6)
        )

    async def delete_torrent(self, torrent_id: str, with_files: bool) -> None:
        await self.request("torrent-remove", {
            "ids": [torrent_id],
            "delete-local-data": with_files
        })

    async def get_torrent_fp(self, torrent_id: str) -> Optional[Path]:
        resp = await self.request("torrent-get", {
            "ids": [torrent_id],
            "fields": ["downloadDir", "name"]
        })

        if resp.get("result") != "success":
            return None

        root = resp["arguments"]["torrents"]
        if not len(root):
            return None

        torrent = root[0]
        return Path(torrent["downloadDir"]) / torrent["name"]

    async def add_torrent(self, magnet_url: str) -> Optional[str]:
        resp = await self.request("torrent-add", {
            "filename": magnet_url
        })

        if resp.get("result") != "success":
            return None

        return resp["arguments"]["torrent-added"]["hashString"]

    async def login(self) -> bool:
        return await super().login()

    async def request(self, method: str, arguments: dict = {}) -> dict:
        """
        Makes a request to the Transmission RPC server.

        Parameters
        ----------
        method: str
            The RPC method.
        arguments: dict
            The key-value data to send.

        Returns
        -------
        dict
            The response.
        """

        request_url = f"{self.url}/transmission/rpc"
        retries = 5

        body = {
            "method": method,
            "arguments": arguments
        }

        while retries:
            headers = {
                "X-Transmission-Session-Id": self.session_id,
                "Authorization": f"Basic {self.credentials}"
            }

            async with self.session.post(request_url, json=body, headers=headers) as resp:
                data: Any = await resp.text(encoding="utf-8")
                if resp.status == 200:
                    return json.loads(data)
                elif resp.status == 409:
                    retries -= 1
                    logger.warn(f"Transmission - Invalid session ID, retrying {retries}")
                    self.session_id = resp.headers.get("X-Transmission-Session-Id", "")
                    continue
                elif resp.status == 400:
                    retries -= 1
                    logger.warn(f"Transmission - Bad Request, retrying {retries}")
                    await asyncio.sleep(1)
                else:
                    return {}

        return {}
