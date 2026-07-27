import asyncio
import base64
import hashlib
import logging
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

if TYPE_CHECKING:
    from tsundoku.app import TsundokuAppState

import aiohttp
import bencodepy

from tsundoku.config import TorrentConfig
from tsundoku.dl_client.abstract import TestClientResult, TorrentClient
from tsundoku.dl_client.deluge import DelugeClient
from tsundoku.dl_client.errors import TorrentFetchError
from tsundoku.dl_client.qbittorrent import qBittorrentClient
from tsundoku.dl_client.transmission import TransmissionClient
from tsundoku.manager import PathMapping

logger = logging.getLogger("tsundoku")


def magnet_display_name(magnet: str) -> str | None:
    """The display name a magnet advertises, if it carries one."""
    names = parse_qs(urlparse(magnet).query).get("dn")
    return names[0] if names else None


#: Torrent hosts are unreliable enough that a single attempt is not good
#: enough: nyaa, for one, drops a large fraction of connections outright
#: rather than answering, which turned a perfectly ordinary paste into a
#: Bad Request often enough to look like a bug in Tsundoku.
TORRENT_FETCH_ATTEMPTS = 4
#: Seconds before the first retry; doubles each time after that.
TORRENT_FETCH_BACKOFF = 1.0


class Manager:
    app: "TsundokuAppState"
    session: aiohttp.ClientSession

    __last_hash: int | None

    def __init__(self, app: "TsundokuAppState", session: aiohttp.ClientSession) -> None:
        self.app = app
        self.session = session
        self.__last_hash = None

        self._client: TorrentClient

    async def update_config(self) -> None:
        """
        Updates the configuration for the
        app's desired torrent client.
        """
        cfg = await TorrentConfig.retrieve(self.app)

        hash_ = hash(cfg)
        if self.__last_hash == hash_:
            return

        self.__last_hash = hash_

        host = cfg.host
        port = cfg.port
        secure = cfg.secure

        username = cfg.username
        password = cfg.password

        kwargs = {"host": host, "port": port, "secure": secure}

        if cfg.client == "deluge":
            kwargs["auth"] = password
            self._client = DelugeClient(self.session, **kwargs)
        elif cfg.client == "qbittorrent":
            auth = {"username": username, "password": password}
            self._client = qBittorrentClient(self.session, auth, **kwargs)
        elif cfg.client == "transmission":
            kwargs["auth"] = {"username": username, "password": password}
            self._client = TransmissionClient(self.session, **kwargs)

    async def fetch_source(self, location: str) -> bytes:
        """Download the .torrent at ``location``, retrying transient failures.

        Retries connection-level failures and 5xx responses with a doubling
        backoff, and gives up immediately on a 4xx, which will not improve by
        asking again. Raises :class:`TorrentFetchError` with the reason rather
        than returning an error page's HTML for bencode to choke on.
        """
        reason = "no attempts made"

        for attempt in range(1, TORRENT_FETCH_ATTEMPTS + 1):
            try:
                async with self.session.get(location) as resp:
                    if resp.status == 200:
                        return await resp.read()

                    if resp.status < 500:
                        raise TorrentFetchError(f"The torrent host returned HTTP {resp.status} for {location}")

                    reason = f"HTTP {resp.status}"
            except (aiohttp.ClientError, TimeoutError) as e:
                reason = f"{type(e).__name__}: {e}"

            if attempt < TORRENT_FETCH_ATTEMPTS:
                delay = TORRENT_FETCH_BACKOFF * (2 ** (attempt - 1))
                logger.warning(f"Torrent fetch {attempt}/{TORRENT_FETCH_ATTEMPTS} for `{location[:96]}` failed ({reason}); retrying in {delay:.0f}s")
                await asyncio.sleep(delay)

        raise TorrentFetchError(f"Could not download the torrent from {location} after {TORRENT_FETCH_ATTEMPTS} attempts. The host may be temporarily unreachable. Last error: {reason}")

    async def fetch_torrent(self, location: str) -> bytes:
        """Return the .torrent bytes describing ``location``.

        Normally this just downloads the .torrent. When a development mirror
        is configured, the bytes are handed to it and it answers with a
        synthetic torrent carrying the same file names but locally generated
        content, so a real magnet or .torrent URL pasted into a dev instance
        downloads from a local swarm instead of the internet.

        Fetching here rather than letting the mirror fetch matters twice over:
        the mirror then needs no outbound network at all, and this session's
        cookies and auth apply, so a .torrent behind a tracker login works
        too. A magnet has nothing to fetch, so it is passed through verbatim
        for the mirror to read its display name from.
        """
        mirror = self.app.flags.TORRENT_MIRROR_URL

        if location.startswith("magnet:?"):
            if not mirror:
                raise ValueError("cannot fetch a .torrent for a magnet URL without a mirror")
            body, content_type = location.encode(), "text/plain"
        else:
            body, content_type = await self.fetch_source(location), "application/x-bittorrent"

            if not mirror:
                return body

        logger.info(f"Torrent mirror: handing `{location[:96]}` to {mirror}")
        async with self.session.post(f"{mirror.rstrip('/')}/mirror", data=body, headers={"Content-Type": content_type}) as resp:
            if resp.status != 200:
                detail = (await resp.text())[:200]
                raise RuntimeError(f"Torrent mirror returned {resp.status}: {detail}")

            return await resp.read()

    async def get_magnet(self, location: str) -> str:
        """
        Will take an internet location for a torrent file.
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
        pattern = re.compile(r"\burn:btih:([A-z\d]+)\b")

        def b32_to_sha1(match: re.Match) -> str:
            hash_ = match.group(1)
            if len(hash_) == 40:
                return match.group(0)
            if len(hash_) == 32:
                return "urn:btih:" + base64.b32decode(hash_.upper()).hex()

            return match.group(0)

        # A magnet already is the answer, unless a mirror is configured -- in
        # which case it has to be substituted like anything else, so it falls
        # through to be exchanged for the synthetic torrent.
        if location.startswith("magnet:?") and not self.app.flags.TORRENT_MIRROR_URL:
            return re.sub(pattern, b32_to_sha1, location)

        torrent_bytes = await self.fetch_torrent(location)
        metadata: Any = bencodepy.decode(torrent_bytes)

        subject = metadata[b"info"]

        hash_data = bencodepy.encode(subject)
        digest = hashlib.sha1(hash_data).hexdigest()

        magnet_url = f"magnet:?xt=urn:btih:{digest}&dn={metadata[b'info'][b'name'].decode()}&tr={metadata[b'announce'].decode()}"

        return re.sub(pattern, b32_to_sha1, magnet_url)

    async def get_file_structure(self, location: str) -> list[str]:
        """
        Given a URL to a .torrent file, it will then return a list
        of the file names inside.

        A magnet URL carries no file list -- only an info hash and an
        optional display name -- so the only thing it can describe is a
        single file, and that name is what comes back. Recovering the real
        structure of a multi-file magnet would mean fetching metadata from
        the swarm or a third-party torrent cache; Tsundoku deliberately does
        neither, and asks for the .torrent instead.

        Parameters
        ----------
        location: str
            A URL to a .torrent file, or a magnet URL.

        Returns
        -------
        List[str]
            List of file names.
        """
        if location.startswith("magnet:?"):
            name = magnet_display_name(location)
            if name is None:
                raise ValueError("This magnet URL carries no display name, so there is no file name to read from it. Use the .torrent link instead.")

            return [name]

        # Goes through the mirror too, so the names listed here match the
        # synthetic torrent that actually gets downloaded.
        metadata = bencodepy.decode(await self.fetch_torrent(location))

        is_folder = b"files" in metadata[b"info"]  # type: ignore

        file_names = []

        if is_folder:
            for item in metadata[b"info"][b"files"]:  # type: ignore
                try:
                    file_names.append(item[b"path"][0].decode("utf-8"))
                except IndexError:
                    pass
        else:
            file_names.append(metadata[b"info"][b"name"].decode("utf-8"))  # type: ignore

        return file_names

    async def test_client(self) -> TestClientResult:
        """
        Checks whether or not the torrent client is able
        to connect.

        Returns
        -------
        TestClientResult
            Whether the connection succeeded, and a human-readable
            error message explaining why it failed if it did not.
        """
        await self.update_config()

        try:
            return await self._client.test_client()
        except Exception as e:
            logger.exception("Failed to test torrent client.")
            return TestClientResult(False, f"Unexpected error while testing the torrent client: {e}")

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
        await self.update_config()

        return await self._client.check_torrent_completed(torrent_id)

    async def check_torrent_ratio(self, torrent_id: str) -> float | None:
        """
        Checks whether a torrent has a ratio of at least 1.0.

        Parameters
        ----------
        torrent_id: str
            The torrent ID to check.

        Returns
        -------
        Optional[float]:
            The torrent's ratio.
        """
        await self.update_config()

        return await self._client.check_torrent_ratio(torrent_id)

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
        await self.update_config()

        await self._client.delete_torrent(torrent_id, with_files=with_files)

    async def get_torrent_fp(self, torrent_id: str) -> Path | None:
        """
        Retrieves a torrent's downloaded location from a download client.

        The client reports this path in its own filesystem namespace, which is
        not necessarily ours. Every adapter returns through here, so this is
        the single point where the configured path mappings are applied and
        the rest of the app can treat the result as a local path.

        Parameters
        ----------
        torrent_id: str
            The torrent's ID (hash)

        Returns
        -------
        Optional[Path]:
            The torrent Path object.
        """
        await self.update_config()

        fp = await self._client.get_torrent_fp(torrent_id)
        if fp is None:
            return None

        return await PathMapping.translate(self.app, fp)

    async def add_torrent(self, magnet_url: str) -> str | None:
        """
        Adds a torrent to a download client.

        Parameters
        ----------
        magnet_url: str
            The torrent's magnet URL.

        Returns
        -------
        Optional[str]:
            The torrent's hash.
        """
        await self.update_config()

        return await self._client.add_torrent(magnet_url)
