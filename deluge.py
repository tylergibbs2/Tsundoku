import asyncio
import typing
import json

import aiohttp

from config import get_config_value
from exceptions import DelugeAuthorizationError


class DelugeClient:
    def __init__(self, session: aiohttp.ClientSession):
        self._first_auth = False  # whether or not the script has authorized before.
        self._request_counter = 0  # counts the number of requests made to Deluge.

        self.session = session
        self.url = self.build_api_url()


    def build_api_url(self) -> str:
        """
        Builds the URL to make requests to the Deluge WebAPI.

        Returns
        -------
        str
            The API's URL.
        """
        host = get_config_value("Deluge", "host")
        port = get_config_value("Deluge", "port")

        return f"http://{host}:{port}/json"


    async def get_torrents(self, torrent_ids: typing.Union[str, int]) -> typing.List:
        """
        Returns information for all specified torrents.

        Parameters
        ----------
        torrent_ids: typing.Union[str, int]
            The torrent ID or IDs to return information for.

        Returns
        -------
        list[dict]
            The information for the given torrents.
        """
        if isinstance(torrent_ids, str):
            torrent_ids = [torrent_ids]

        await self.request("webapi.get_torrents", [torrent_ids])


    async def add_torrent(self, magnet_url: str) -> bool:
        """
        Adds a torrent to Deluge with the given magnet URL.

        Parameters
        ----------
        magnet_url: str
            The magnet URL of the torrent to add to Deluge.

        Returns
        -------
        bool
            True if success, False otherwise.
        """
        await self.request("webapi.add_torrent", [magnet_url])


    async def remove_torrent(self, torrent_id: str, remove_data=False) -> bool:
        """
        Removes a torrent of specified ID from Deluge.
        
        Can also optionally remove data from disk upon deletion.

        Parameters
        ----------
        torrent_id: str
            The ID of the torrent to remove.
        remove_data: bool, optional
            Whether or not to remove data from disk on deletion.

        Returns
        -------
        bool
            True of success, False otherwise.
        """
        await self.request("webapi.remove_torrent", [torrent_id, remove_data])

    async def ensure_authorization(self):
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

        auth_status = await self.session.post(
            self.url,
            json=payload,
            headers=headers
        )
        auth_status = await auth_status.json(content_type=None)

        self._request_counter += 1

        result = auth_status.get("result")
        if not result:
            password = get_config_value("Deluge", "password")

            payload = {
                "id": self._request_counter,
                "method": "auth.login",
                "params": [password]
            }

            auth_request = await self.session.post(
                self.url,
                json=payload,
                headers=headers
            )
            auth_request = await auth_request.json(content_type=None)

            self._request_counter += 1
            
            error = auth_request.get("error")
            if error:
                raise DelugeAuthorizationError(error["message"])

        return result

    async def request(self, method: str, data: list=[]) -> dict:
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
        while not await self.ensure_authorization():
            await asyncio.sleep(10)
            continue

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
