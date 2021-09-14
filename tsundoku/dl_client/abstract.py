from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class TorrentClient(ABC):

    @abstractmethod
    def build_api_url(self, host: str, port: int, secure: bool) -> str:
        """
        Builds the URL to make requests to the torrent client.

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

    @abstractmethod
    async def test_client(self) -> bool:
        """
        Checks whether or not the torrent client is
        able to connect.
        """

    @abstractmethod
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
        bool
            The torrent's existence status.
        """

    @abstractmethod
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
        bool
            The torrent's completion status.
        """

    @abstractmethod
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

    @abstractmethod
    async def get_torrent_fp(self, torrent_id: str) -> Optional[Path]:
        """
        Returns the torrent's path on disk.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to return information for.

        Returns
        -------
        Optional[Path]
            The torrent's downloaded file path.
        """

    @abstractmethod
    async def add_torrent(self, magnet_url: str) -> Optional[str]:
        """
        Adds a torrent with the given magnet URL.

        Parameters
        ----------
        magnet_url: str
            The magnet URL of the torrent to add.

        Returns
        -------
        Optional[str]
            The torrent ID if success, None if torrent not added.
        """

    @abstractmethod
    async def login(self) -> bool:
        """
        Authorizes with the torrent client's API.

        Returns
        -------
        bool
            Auth status.
        """