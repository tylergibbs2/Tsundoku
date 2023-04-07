from __future__ import annotations

import asyncio
import logging
import os
import statistics
from asyncio import create_subprocess_shell
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp

from quart import request

from tsundoku.config import GeneralConfig, EncodeConfig
from tsundoku.constants import VALID_MINIMUM_FILE_SIZES
from tsundoku.utils import move

logger = logging.getLogger("tsundoku")


def seconds_until(start: int, end: int) -> int:
    now = datetime.now()
    if start <= now.hour <= end - 1:
        return 0

    start_dt = datetime(now.year, now.month, now.day, start)
    if now.hour > end - 1:
        start_dt += timedelta(days=1)

    return int((start_dt - now).total_seconds())


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

    app: TsundokuApp

    ENABLED: bool
    MAX_ENCODES: int
    CRF: int
    SPEED_PRESET: str
    MIN_FILE_BYTES: int

    TIMED_ENCODING: bool
    HOUR_START: int
    HOUR_END: int

    __encode_queue: List[int]
    __active_encodes: int
    __has_ffmpeg: bool

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app

        self.app.add_url_rule(
            "/api/v1/encode/<int:entry_id>",
            view_func=self.encode_progress,
            methods=["POST"],
        )

        self.TEMP_SUFFIX = ".encoded.mkv"

        self.ENABLED = False
        self.MAX_ENCODES = 2
        self.CRF = 21
        self.SPEED_PRESET = "medium"
        self.MIN_FILE_BYTES = 0

        self.TIMED_ENCODING = False
        self.HOUR_START = 3
        self.HOUR_END = 6

        self.__encode_queue: List[int] = []
        self.__active_encodes = 0
        self.__has_ffmpeg = False

    async def update_config(self) -> None:
        """
        Updates the instances config with what
        is in the database.
        """
        cfg = await EncodeConfig.retrieve(self.app)

        self.CRF = {"high": 18, "moderate": 21, "low": 24}.get(cfg.quality_preset, 21)

        self.SPEED_PRESET = cfg.speed_preset
        self.MIN_FILE_BYTES = VALID_MINIMUM_FILE_SIZES[cfg.minimum_file_size]

        self.ENABLED = cfg.enabled
        self.MAX_ENCODES = cfg.maximum_encodes if cfg.maximum_encodes > 0 else 1
        self.TIMED_ENCODING = cfg.timed_encoding
        self.HOUR_START = cfg.hour_start
        self.HOUR_END = cfg.hour_end

        logger.debug("Encode config updated")

    async def resume(self) -> None:
        """
        Starts watching for new media to encode
        and also starts the encoding process.
        """
        logger.debug("Encoder task started.")

        async with self.app.acquire_db() as con:
            leftovers = await con.fetchall(
                """
                SELECT
                    entry_id
                FROM
                    encode
                WHERE
                    ended_at IS NULL
                ORDER BY started_at ASC;
            """
            )

        for entry in leftovers:
            await self.encode(entry["entry_id"])

    async def build_cmd(self, entry_id: int, infile: Path) -> str:
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

        cfg = await GeneralConfig.retrieve(self.app)
        domain, port = cfg.host, cfg.port

        url = f"{protocol}://{domain}:{port}/{route}"

        encoder = "libx264"

        outfile = infile.with_suffix(self.TEMP_SUFFIX)
        return (
            f'ffmpeg -hide_banner -loglevel error -i "{infile}" -map 0 -c copy -c:v {encoder} -crf {self.CRF}'
            f' -tune animation -preset {self.SPEED_PRESET} -c:a copy -progress {url} -y "{outfile}"'
        )

    def encode_task(self, entry_id: int) -> None:
        """
        Launches an encode task.

        Parameters
        ----------
        entry_id: int
            THe entry ID to encode.
        """
        logger.debug(f"Launching new encode task for <e{entry_id}>")
        self.app._tasks.append(
            asyncio.create_task(self.encode(entry_id), name=f"encode-{entry_id}")
        )

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
            return

        async with self.app.acquire_db() as con:
            await con.execute(
                """
                INSERT OR IGNORE INTO
                    encode (
                        entry_id
                    )
                VALUES (?);
            """,
                entry_id,
            )

        if self.TIMED_ENCODING:
            to_sleep = seconds_until(self.HOUR_START, self.HOUR_END)
            logger.debug(
                f"Timed encoding enabled, sleeping '{to_sleep:,}' seconds before encoding..."
            )
            await asyncio.sleep(to_sleep)

        if self.__active_encodes >= self.MAX_ENCODES:
            logger.debug(f"Reached maximum encodes, queuing <e{entry_id}>")
            self.__encode_queue.append(entry_id)
            return

        ret = False
        try:
            ret = await self._encode(entry_id)
        except Exception as e:
            logger.error(f"Failed to encode <e{entry_id}>: {e}", exc_info=True)

        if not ret:
            async with self.app.acquire_db() as con:
                await con.execute(
                    """
                    DELETE FROM
                        encode
                    WHERE
                        entry_id = ?;
                """,
                    entry_id,
                )

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
            entry = await con.fetchone(
                """
                SELECT
                    file_path,
                    current_state
                FROM
                    show_entry
                WHERE
                    id=?;
            """,
                entry_id,
            )

        if entry["file_path"] is None:
            logger.warning(
                f"Error when attempting to encode entry <e{entry_id}>: file path is None"
            )
            return False
        elif entry["current_state"] != "completed":
            logger.warning(
                f"Error when attempting to encode entry <e{entry_id}>: cannot encode a non-completed entry"
            )
            return False

        logger.debug(f"Starting new encode process for entry <e{entry_id}>...")

        infile = Path(entry["file_path"])
        if not infile.exists():
            logger.warning(
                f"Error when attemping to encode entry <e{entry_id}>: input fp does not exist"
            )
            return False
        elif not infile.is_file() or infile.is_symlink():
            logger.warning(
                f"Error when attemping to encode entry <e{entry_id}>: input fp is not a file, or is a symlink"
            )
            return False

        file_bytecount = infile.stat().st_size
        if file_bytecount < self.MIN_FILE_BYTES:
            logger.info(
                f"Skipping encode for <e{entry_id}>. Byte count is `{file_bytecount}`, does not meet minimum of `{self.MIN_FILE_BYTES}`."
            )
            return False

        cmd = await self.build_cmd(entry_id, infile)
        try:
            await create_subprocess_shell(cmd)
        except Exception as e:
            logger.error(
                f"Failed starting new encode for entry <e{entry_id}>: {e}",
                exc_info=True,
            )
        else:
            self.__active_encodes += 1
            file_size = os.path.getsize(str(infile))
            async with self.app.acquire_db() as con:
                await con.execute(
                    """
                    UPDATE
                        encode
                    SET
                        initial_size = ?
                    WHERE
                        entry_id = ?;
                """,
                    file_size,
                    entry_id,
                )
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
            logger.debug(
                f"Encode progress entry <e{entry_id}>: `{last_received.get('out_time')}`"
            )

        self.__active_encodes -= 1
        await self.encode_next()
        if last_received.get("progress") == "end":
            await self.handle_finished(entry_id)

        return "{}"

    async def handle_finished(self, entry_id: int) -> None:
        logger.debug(f"Encode finished for entry <e{entry_id}>")
        async with self.app.acquire_db() as con:
            entry_path = await con.fetchval(
                """
                SELECT
                    file_path
                FROM
                    show_entry
                WHERE
                    id=?;
            """,
                entry_id,
            )

            if entry_path is None:
                logger.warning(
                    f"Error when finalizing encode for entry <e{entry_id}>: file path is None"
                )
                return

            original = Path(entry_path)
            encoded = original.with_suffix(self.TEMP_SUFFIX)

            encoded_size = os.path.getsize(str(encoded))
            await con.execute(
                """
                UPDATE
                    encode
                SET
                    ended_at = CURRENT_TIMESTAMP,
                    final_size = ?
                WHERE
                    entry_id = ?;
            """,
                encoded_size,
                entry_id,
            )

        await move(encoded, original)
        logger.debug(f"Encode moved for entry <e{entry_id}>")

    async def has_ffmpeg(self) -> bool:
        """
        Checks if ffmpeg is available to use.

        Returns
        -------
        bool
            If ffmpeg is available.
        """
        if self.__has_ffmpeg:
            return self.__has_ffmpeg

        proc = await asyncio.create_subprocess_shell(
            "ffmpeg -buildconf",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            self.__has_ffmpeg = False
            return self.__has_ffmpeg

        output = stdout.decode("utf-8")
        self.__has_ffmpeg = "--enable-libx264" in output
        return self.__has_ffmpeg

    async def get_stats(self) -> Dict[str, float]:
        """
        Returns global encoding statistics.

        Keys:
        total_encoded           - total number of encodes completed
        total_saved_bytes       - total bytes saved across all encodes
        avg_saved_bytes         - average amount of bytes saved per item
        median_time_spent_hours - median time spent encoding one item in hours
        avg_time_spent_hours    - average time spent encoding one item in hours

        Returns
        -------
        Dict[str, float]
            The global encoding statistics.
        """
        async with self.app.acquire_db() as con:
            # initial_size and final_size are stored in bytes
            stats = await con.fetchone(
                """
                SELECT
                    COUNT(*) AS total_encoded,
                    SUM(initial_size - final_size) AS total_saved_bytes,
                    AVG(initial_size - final_size) AS avg_saved_bytes
                FROM
                    encode
                WHERE
                    ended_at IS NOT NULL;
            """
            )

            times = await con.fetchall(
                """
                SELECT
                    started_at,
                    ended_at
                FROM
                    encode
                WHERE
                    ended_at IS NOT NULL;
            """
            )

        stats = dict(stats)
        durations = [(t["ended_at"] - t["started_at"]).total_seconds() for t in times]
        try:
            stats["median_time_spent_hours"] = statistics.median(durations) / 3600
        except statistics.StatisticsError:
            stats["median_time_spent_hours"] = 0
        if len(durations) != 0:
            stats["avg_time_spent_hours"] = (sum(durations) / len(durations)) / 3600
        else:
            stats["avg_time_spent_hours"] = 0

        return stats
