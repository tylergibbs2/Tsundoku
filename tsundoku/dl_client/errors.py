import asyncio

import aiohttp


def describe_connection_error(exc: BaseException, client_name: str, url: str) -> str:
    """
    Converts a low-level aiohttp/asyncio exception into a human-readable
    explanation of why a connection to a torrent client failed.

    Parameters
    ----------
    exc: BaseException
        The exception raised while trying to reach the client.
    client_name: str
        Display name of the torrent client, e.g. "qBittorrent".
    url: str
        The URL that was being contacted.

    Returns
    -------
    str
        A human-readable error message.
    """
    if isinstance(exc, aiohttp.ClientConnectorError):
        return f"Could not connect to {client_name} at {url}. Check that the client is running and the host/port are correct."

    if isinstance(exc, (asyncio.TimeoutError, aiohttp.ServerTimeoutError)):
        return f"Connection to {client_name} at {url} timed out."

    if isinstance(exc, aiohttp.ClientConnectionError):
        return f"Connection to {client_name} at {url} was closed unexpectedly. [{exc}]"

    if isinstance(exc, aiohttp.ClientResponseError):
        return f"{client_name} returned an unexpected response (status {exc.status})."

    if isinstance(exc, aiohttp.ClientError):
        return f"Error communicating with {client_name}: {exc}"

    return f"Unexpected error while testing {client_name}: {exc}"
