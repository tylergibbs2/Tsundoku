import asyncio
import json
import logging
from pathlib import Path
import re
from typing import Any

import aiohttp

from tsundoku.dl_client.abstract import TestClientResult, TorrentClient
from tsundoku.dl_client.errors import describe_connection_error

logger = logging.getLogger("tsundoku")


class qBittorrentClient(TorrentClient):  # noqa: N801
    auth: dict[str, str | None]
    url: str

    last_authed_user: str | None = None

    def __init__(self, session: aiohttp.ClientSession, auth: dict[str, str | None], **kwargs: Any) -> None:
        self.session = session

        host: str = kwargs.pop("host")
        port: int = kwargs.pop("port")
        secure: bool = kwargs.pop("secure")

        self.auth = auth

        self.url = self.build_api_url(host, port, secure)

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        protocol = "https" if secure else "http"

        return f"{protocol}://{host}:{port}"

    async def test_client(self) -> TestClientResult:
        return await self.login()

    async def check_torrent_exists(self, torrent_id: str) -> bool:
        fp = await self.get_torrent_fp(torrent_id)
        return bool(fp)

    async def check_torrent_completed(self, torrent_id: str) -> bool:
        payload = {"hashes": torrent_id}

        logger.debug(f"Retrieving torrent state for hash `{torrent_id}`")
        data = await self.request("get", "torrents", "info", params=payload)
        if not data or not data[0].get("state"):
            return False

        state = data[0].get("state")
        logger.debug(f"Torrent `{torrent_id}` is `{state}`")
        return state in (
            "checkingUP",
            "completed",
            "forcedUP",
            "pausedUP",
            "queuedUP",
            "stalledUP",
            "uploading",
        )

    async def check_torrent_ratio(self, torrent_id: str) -> float | None:
        payload = {"hashes": torrent_id}

        logger.debug(f"Retrieving torrent state for hash `{torrent_id}`")
        data = await self.request("get", "torrents", "info", params=payload)
        if not data or not data[0].get("state"):
            return None

        state = data[0]
        if "ratio" in state:
            return state["ratio"]

        return None

    async def delete_torrent(self, torrent_id: str, with_files: bool = True) -> None:
        payload = {
            "hashes": torrent_id,
            "deleteFiles": "true" if with_files else "false",
        }

        await self.request("get", "torrents", "delete", params=payload)

    async def get_torrent_fp(self, torrent_id: str) -> Path | None:
        payload = {"hashes": torrent_id}

        data = await self.request("get", "torrents", "info", params=payload)
        if not data:
            return None
        data = data[0]

        if data.get("hash") != torrent_id:
            return None

        return Path(data["content_path"])

    async def add_torrent(self, magnet_url: str) -> str | None:
        payload = {"urls": magnet_url}

        await self.request("post", "torrents", "add", payload=payload)

        match = re.search(r"\burn:btih:([A-z\d]+)\b", magnet_url)
        if match is None:
            return None

        return match.group(1).lower()

    async def login(self) -> TestClientResult:
        cache_key = f"{self.auth['username']}:{self.auth['password']}"
        if self.last_authed_user == cache_key:
            logger.info("qBittorrent - Authentication is already cached")
            return TestClientResult(True)

        headers = {"Referer": self.url}

        payload = {"username": self.auth["username"], "password": self.auth["password"]}

        request_url = f"{self.url}/api/v2/auth/login"

        try:
            async with self.session.post(request_url, headers=headers, data=payload) as resp:
                status = resp.status
                body = (await resp.text()).strip()
        except (TimeoutError, aiohttp.ClientError) as e:
            self.last_authed_user = None
            message = describe_connection_error(e, "qBittorrent", self.url)
            logger.warning(f"qBittorrent - {message}")
            return TestClientResult(False, message)

        # qBittorrent < 5.2.0 responds 200 with body "Ok." on a successful login.
        # 5.2.0+ instead responds 204 No Content, setting the session cookie via
        # the Set-Cookie header (picked up automatically by the shared cookie jar).
        if status == 204 or (status == 200 and body.lower() == "ok."):
            self.last_authed_user = cache_key
            logger.info("qBittorrent - Successfully Authenticated")
            return TestClientResult(True)

        self.last_authed_user = None
        if status == 403:
            message = "qBittorrent has temporarily banned this IP due to too many failed login attempts."
        elif status in (200, 401):
            message = "qBittorrent rejected the configured username or password."
        else:
            message = f"qBittorrent returned unexpected status {status} while logging in."

        logger.warning(f"qBittorrent - Failed to Authenticate, status {status}")
        return TestClientResult(False, message)

    async def request(
        self,
        http_method: str,
        location: str,
        method: str,
        payload: dict | None = None,
        params: dict | None = None,
    ) -> dict:
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
        if payload is None:
            payload = {}
        if params is None:
            params = {}

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
                if r.status == 403:
                    retries -= 1
                    logger.warning(f"qBittorrent - Forbidden, reauthorizing {retries}")
                    await self.login()
                elif r.status == 400:
                    retries -= 1
                    logger.warning(f"qBittorrent - Bad Request, retrying {retries}")
                    await asyncio.sleep(1)
                else:
                    return {}

        return {}
