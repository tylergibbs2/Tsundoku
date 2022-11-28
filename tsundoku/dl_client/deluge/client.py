import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import aiohttp

from tsundoku.dl_client.abstract import TorrentClient

logger = logging.getLogger("tsundoku")


class DelugeClient(TorrentClient):
    def __init__(self, session: aiohttp.ClientSession, **kwargs: Any) -> None:
        self._request_counter = 0  # counts the number of requests made to Deluge.

        self.session = session

        host: str = kwargs.pop("host")
        port: int = kwargs.pop("port")
        secure: bool = kwargs.pop("secure")

        self.password: str = kwargs.pop("auth")

        self.url = self.build_api_url(host, port, secure)

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        protocol = "https" if secure else "http"

        return f"{protocol}://{host}:{port}/json"

    async def test_client(self) -> bool:
        return await self.login() is not None

    async def check_torrent_exists(self, torrent_id: str) -> bool:
        fp = await self.get_torrent_fp(torrent_id)
        return bool(fp)

    async def check_torrent_completed(self, torrent_id: str) -> bool:
        logger.debug(f"Retrieving torrent state for hash `{torrent_id}`")
        ret = await self.request("webapi.get_torrents", [[torrent_id], ["state"]])

        ret_list = ret["result"].get("torrents", [])

        try:
            data = ret_list[0]
        except IndexError:
            return False

        logger.debug(f"Torrent `{torrent_id}` is `{data['state']}`")
        return data["state"] == "Seeding"

    async def check_torrent_ratio(self, torrent_id: str) -> Optional[float]:
        ret = await self.request("webapi.get_torrents", [[torrent_id], ["ratio"]])

        ret_list = ret["result"].get("torrents", [])

        try:
            data = ret_list[0]
        except IndexError:
            return None

        if "ratio" in data:
            return data["ratio"]

        return None

    async def delete_torrent(self, torrent_id: str, with_files: bool = True) -> None:
        await self.request("webapi.remove_torrent", [torrent_id, with_files])

    async def get_torrent_fp(self, torrent_id: str) -> Optional[Path]:
        ret = await self.request(
            "webapi.get_torrents", [[torrent_id], ["name", "move_completed_path"]]
        )

        ret_list = ret["result"].get("torrents", [])

        try:
            data = ret_list[0]
        except IndexError:
            return None

        return Path(data["move_completed_path"], data["name"])

    async def add_torrent(self, magnet_url: str) -> Optional[str]:
        data = await self.request("webapi.add_torrent", [magnet_url])
        return data.get("result")

    async def login(self) -> Optional[str]:
        payload = {
            "id": self._request_counter,
            "method": "auth.check_session",
            "params": [],
        }

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        try:
            auth_status = await self.session.post(
                self.url, json=payload, headers=headers
            )
        except aiohttp.ClientConnectionError:
            logger.error("Deluge - Failed to Connect")
            resp = {}
        else:
            resp = await auth_status.json(content_type=None)

        self._request_counter += 1
        result = resp.get("result")
        if not result:
            payload = {
                "id": self._request_counter,
                "method": "auth.login",
                "params": [self.password],
            }
            auth_request = await self.session.post(
                self.url, json=payload, headers=headers
            )
            resp = await auth_request.json(content_type=None)

            self._request_counter += 1

            error = resp.get("error")
            if error or resp["result"] is False:
                logger.warn("Deluge - Failed to Authenticate")
                return None

        return result

    async def request(self, method: str, data: list = []) -> dict:
        """
        Authorizes and makes a request with the Deluge WebAPI.

        Results will be returned in the 'result' key in the response dict.
        Errors will be returned as an 'error' key in the response dict.

        Parameters
        ----------
        method: str
            The method to call within the API.
        data: list
            The parameters to send along with the method.

        Returns
        -------
        dict
            The response dict.
        """
        retries = 5
        while retries and not await self.login():
            await asyncio.sleep(10)
            retries -= 1
            continue

        logger.info("Deluge - Successfully Authenticated")

        payload = {"id": self._request_counter, "method": method, "params": data}

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        resp = await self.session.post(self.url, json=payload, headers=headers)

        self._request_counter += 1

        return await resp.json(content_type=None)
