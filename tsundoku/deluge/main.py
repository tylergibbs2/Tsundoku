import asyncio
import base64
import hashlib
import json
import logging
import sys
from typing import List, Optional

import aiohttp
import bencodepy

from tsundoku.config import get_config_value
from tsundoku.deluge.exceptions import DelugeAuthorizationError


logger = logging.getLogger("tsundoku")


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
        secure = get_config_value("Deluge", "secure")

        protocol = "https" if secure else "http"

        return f"{protocol}://{host}:{port}/json"


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


    async def get_torrents(self, torrent_ids: List[str], status_keys: Optional[List[str]]=None) -> List:
        """
        Returns information for all specified torrents.

        Parameters
        ----------
        torrent_ids: list
            The torrent IDs to return information for.
        status_keys: Optional[List[str]]
            Specific status keys to retrieve information on.

        Returns
        -------
        list[dict]
            The information for the given torrents.
        """
        result = await self.request("webapi.get_torrents", [torrent_ids, status_keys])

        return result["result"]["torrents"]


    async def get_torrent(self, torrent_id: str, status_keys: Optional[List[str]]=None) -> dict:
        """
        Returns information for a specified torrent.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to return information for.
        status_keys: Optional[List[str]]
            Specific status keys to retrieve information on.

        Returns
        -------
        dict
            The information for the given torrent.
        """
        torrent_id = [torrent_id]

        result = await self.request("webapi.get_torrents", [torrent_id, status_keys])

        return result["result"]["torrents"][0]


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
        return data["result"]


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
            True if success, False otherwise.
        """
        data = await self.request("webapi.remove_torrent", [torrent_id, remove_data])
        return data["result"]

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
                logger.warn("Deluge - Failed to Authenticate")
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
