import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import aiohttp

logger = logging.getLogger("tsundoku")


class DelugeClient:
    def __init__(self, session: aiohttp.ClientSession, **kwargs: Any) -> None:
        self._request_counter = 0  # counts the number of requests made to Deluge.

        self.session = session

        host: str = kwargs.pop("host")
        port: int = kwargs.pop("port")
        secure: bool = kwargs.pop("secure")

        self.password: str = kwargs.pop("auth")

        self.url = self.build_api_url(host, port, secure)

    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        """
        Builds the URL to make requests to the Deluge WebAPI.

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

        return f"{protocol}://{host}:{port}/json"

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
        ret = await self.request("webapi.get_torrents", [[torrent_id], ["state"]])

        ret_list = ret["result"].get("torrents", [])

        try:
            data = ret_list[0]
        except IndexError:
            return False

        return data["state"] == "Seeding"

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
        ret = await self.request("webapi.get_torrents", [[torrent_id], ["name", "move_completed_path"]])

        ret_list = ret["result"].get("torrents", [])

        try:
            data = ret_list[0]
        except IndexError:
            return None

        return Path(data["move_completed_path"], data["name"])

    async def add_torrent(self, magnet_url: str) -> Optional[str]:
        """
        Adds a torrent to Deluge with the given magnet URL.

        Parameters
        ----------
        magnet_url: str
            The magnet URL of the torrent to add to Deluge.

        Returns
        -------
        Optional[str]
            The torrent ID if success, None if torrent not added.
        """
        data = await self.request("webapi.add_torrent", [magnet_url])
        return data.get("result")

    async def ensure_authorization(self) -> Optional[str]:
        """
        Authorizes with the Deluge WebAPI.

        This has to use the aiohttp ClientSession itself
        due to some recursion thingys.
        """
        payload = {
            "id": self._request_counter,
            "method": "auth.check_session",
            "params": []
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            auth_status = await self.session.post(
                self.url,
                json=payload,
                headers=headers
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
                "params": [self.password]
            }
            auth_request = await self.session.post(
                self.url,
                json=payload,
                headers=headers
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
        while retries and not await self.ensure_authorization():
            await asyncio.sleep(10)
            retries -= 1
            continue

        logger.info("Deluge - Successfully Authenticated")

        payload = {
            "id": self._request_counter,
            "method": method,
            "params": data
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        resp = await self.session.post(
            self.url,
            json=payload,
            headers=headers
        )

        self._request_counter += 1

        return await resp.json(content_type=None)
