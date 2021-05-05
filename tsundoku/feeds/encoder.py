import asyncio
import logging
import os
from asyncio import create_subprocess_shell
from pathlib import Path
from typing import Any, Dict, List

from quart import request

from tsundoku.config import get_config_value
from tsundoku.feeds.downloader import move

logger = logging.getLogger("tsundoku")


VALID_SPEEDS = (
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow"
)


class Encoder:
    """
    Handles the post-process encoding of downloaded
    media. In order to be considered for encoding,
    media must pass a certain, configurable bitrate
    threshold.

    If such media passes this threshold, then it will
    be re-encoded to the h.264 video encoding format
    at a user-specified Constant Rate Factor (CRF).
    """

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app

        self.app.add_url_rule(
            "/api/v1/encode/<int:entry_id>",
            view_func=self.encode_progress,
            methods=["POST"]
        )

        self.TEMP_SUFFIX = ".encoded.mkv"

        self.ENABLED = False
        self.MAX_ENCODES = 2
        self.CRF = 23
        self.SPEED_PRESET = "medium"
        self.RETRY_ON_FAIL = False

        self.__encode_queue: List[int] = []
        self.__active_encodes = 0

    async def update_config(self) -> None:
        """
        Updates the instances config with what
        is in the database.
        """
        async with self.app.acquire_db() as con:
            await con.execute("""
                INSERT OR IGNORE INTO
                    encode_config (
                        id
                    )
                VALUES
                    (0);
            """)
            await con.execute("""
                SELECT
                    enabled,
                    quality_preset,
                    speed_preset,
                    maximum_encodes,
                    retry_on_fail
                FROM
                    encode_config;
            """)
            cfg = await con.fetchone()

        self.CRF = {
            "high": 18,
            "moderate": 22,
            "low": 26
        }.get(cfg["quality_preset"], 22)

        if cfg["speed_preset"] not in VALID_SPEEDS:
            self.SPEED_PRESET = "medium"
        else:
            self.SPEED_PRESET = cfg["speed_preset"]

        self.ENABLED = cfg["enabled"]
        self.RETRY_ON_FAIL = cfg["retry_on_fail"]
        self.MAX_ENCODES = cfg["maximum_encodes"] if cfg["maximum_encodes"] > 0 else 1

        logger.debug(f"Encode config updated: {dict(cfg)}")

    async def resume(self) -> None:
        """
        Starts watching for new media to encode
        and also starts the encoding process.
        """
        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    entry_id
                FROM
                    encode
                WHERE
                    ended_at IS NULL
                ORDER BY started_at ASC;
            """)
            leftovers = await con.fetchall()

        for entry in leftovers:
            await self.encode(entry["entry_id"])

    def build_cmd(self, entry_id: int, infile: Path) -> str:
        """
        Builds the ffmpeg command for encoding.

        Parameters
        ----------
        entry_id: int
            The entry being encoded.
        infile: Path
            The input file to encode.
        """
        route = f"api/v1/encode/{entry_id}"
        protocol = "http"
        domain = get_config_value("Tsundoku", "host")
        port = get_config_value("Tsundoku", "port")

        url = f"{protocol}://{domain}:{port}/{route}"

        encoder = "libx264"

        outfile = infile.with_suffix(self.TEMP_SUFFIX)
        return (f"ffmpeg -hide_banner -loglevel error -i \"{infile}\" -map 0 -c copy -c:v {encoder} -crf {self.CRF}"
                f" -tune animation -preset {self.SPEED_PRESET} -c:a copy -progress {url} -y \"{outfile}\"")

    async def encode(self, entry_id: int) -> None:
        """
        Either starts an encode process or adds
        the encode to the queue.

        Parameters
        ----------
        entry_id: int
            The entry ID to encode.
        """
        await self.update_config()
        has_ffmpeg = await self.has_ffmpeg()
        if not self.ENABLED:
            logger.debug(f"Encoding is disabled, skipping for <e{entry_id}>")
            return
        elif not has_ffmpeg:
            logger.warning(f"Unable to encode <e{entry_id}>: ffmpeg is not installed")

        async with self.app.acquire_db() as con:
            await con.execute("""
                INSERT OR IGNORE INTO
                    encode (
                        entry_id
                    )
                VALUES (?);
            """, entry_id)

        if self.__active_encodes >= self.MAX_ENCODES:
            self.__encode_queue.append(entry_id)
            return

        ret = False
        try:
            ret = await self._encode(entry_id)
        except Exception as e:
            logger.error(f"Failed to encode <e{entry_id}>: {e}")

        if not ret and self.RETRY_ON_FAIL:
            await self.encode(entry_id)
        elif not ret and not self.RETRY_ON_FAIL:
            async with self.app.acquire_db() as con:
                await con.execute("""
                    DELETE FROM
                        encode
                    WHERE
                        entry_id = ?;
                """, entry_id)
        elif not ret:
            await self.encode_next()

    async def encode_next(self) -> None:
        """
        Attempts to retrieve the next item to encode and
        then start the task.
        """
        try:
            next_ = self.__encode_queue.pop(0)
        except IndexError:
            return

        await self.encode(next_)

    async def _encode(self, entry_id: int) -> bool:
        """
        Starts the ffmpeg encoding subprocess.

        Also builds the ffmpeg command and stores the
        starting state of the input file.

        Parameters
        ----------
        entry_id: int
            The entry ID to encode.

        Returns
        -------
        bool
            True if successfully started, False if error occurred.
        """
        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    file_path,
                    current_state
                FROM
                    show_entry
                WHERE
                    id=?;
            """, entry_id)
            entry = await con.fetchone()

        if entry["file_path"] is None:
            logger.warn(f"Error when attempting to encode entry <e{entry_id}>: file path is None")
            return False
        elif entry["current_state"] != "completed":
            logger.warn(f"Error when attempting to encode entry <e{entry_id}>: cannot encode a non-completed entry")
            return False

        logger.debug(f"Starting new encode process for entry <e{entry_id}>...")

        infile = Path(entry["file_path"])
        if not infile.exists():
            logger.warn(f"Error when attemping to encode entry <e{entry_id}>: input fp does not exist")
            return False
        elif not infile.is_file() or infile.is_symlink():
            logger.warn(
                f"Error when attemping to encode entry <e{entry_id}>: input fp is not a file, or is a symlink")
            return False

        cmd = self.build_cmd(entry_id, infile)
        try:
            await create_subprocess_shell(cmd)
        except Exception as e:
            logger.error(f"Failed starting new encode for entry <e{entry_id}>: {e}")
        else:
            self.__active_encodes += 1
            file_size = os.path.getsize(str(infile))
            async with self.app.acquire_db() as con:
                await con.execute("""
                    UPDATE
                        encode
                    SET
                        initial_size = ?
                    WHERE
                        entry_id = ?;
                """, file_size, entry_id)
            return True

        return False

    def process_progress_data(self, data: bytes) -> Dict[str, str]:
        """
        Processes the byte data of an ffmpeg progress stream.

        Parameters
        ----------
        data: bytes
            The byte data of the stream.

        Returns
        -------
        Dict[str, str]
            The parsed byte data.
        """
        out = {}

        text = data.decode("utf-8")
        for kvalp in text.split("\n"):
            if not kvalp:
                continue

            k, v = kvalp.split("=")
            out[k.strip()] = v.strip()

        return out

    async def encode_progress(self, entry_id: int) -> str:
        """
        Receives encode progress data from ffmpeg to
        track the overall progress of an encode.

        Parameters
        ----------
        entry_id: int
            The ID of the show entry to encode.

        Returns
        -------
        str
            Empty dict response.
        """
        logger.debug(f"Encode started for entry <e{entry_id}>")
        last_received = {}
        async for data in request.body:
            last_received = self.process_progress_data(data)
            logger.debug(f"Encode progress entry <e{entry_id}>: `{last_received.get('out_time')}`")

        self.__active_encodes -= 1
        await self.encode_next()
        if last_received.get("progress") == "end":
            await self.handle_finished(entry_id)

        return "{}"

    async def handle_finished(self, entry_id: int) -> None:
        logger.debug(f"Encode finished for entry <e{entry_id}>")
        async with self.app.acquire_db() as con:
            await con.execute("""
                SELECT
                    file_path
                FROM
                    show_entry
                WHERE
                    id=?;
            """, entry_id)
            entry_path = await con.fetchval()

            if entry_path is None:
                logger.warn(f"Error when finalizing encode for entry <e{entry_id}>: file path is None")
                return

            original = Path(entry_path)
            encoded = original.with_suffix(self.TEMP_SUFFIX)

            encoded_size = os.path.getsize(str(encoded))
            await con.execute("""
                UPDATE
                    encode
                SET
                    ended_at = CURRENT_TIMESTAMP,
                    final_size = ?
                WHERE
                    entry_id = ?;
            """, encoded_size, entry_id)

        await move(encoded, original)
        logger.debug(f"Encode moved for entry <e{entry_id}>")

    async def has_ffmpeg(self) -> bool:
        """
        Checks if ffmpeg is available to use.
        """
        proc = await asyncio.create_subprocess_shell(
            "ffmpeg -buildconf",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()

        output = stdout.decode("utf-8")
        return "--enable-libx264" in output
