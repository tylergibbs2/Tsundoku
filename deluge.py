import requests
import typing


def get_torrents(torrent_ids: typing.Union[str, int]) -> typing.List:
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


def add_torrent(magnet_url: str) -> bool:
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


def remove_torrent(torrent_id: str, remove_data=False) -> bool:
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