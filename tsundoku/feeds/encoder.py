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
from tsundoku.constants import VALID_MINIMUM_FILE_SIZES, VALID_ENCODERS
from tsundoku.manager import Entry
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
    media.

    Media will be re-encoded to the h.264 or h.265
    video encoding format at a user-specified
    Constant Rate Factor (CRF).
    """

    app: TsundokuApp

    ENABLED: bool
    ENCODER: str
    MAX_ENCODES: int
    CRF: int
    SPEED_PRESET: str
    MIN_FILE_BYTES: int

    TIMED_ENCODING: bool
    HOUR_START: int
    HOUR_END: int

    __start_lock: asyncio.Lock
    __ffmpeg_procs: Dict[int, asyncio.subprocess.Process]
    __available_encoders: set[str]

    def __init__(self, app_context: Any) -> None:
        self.app = app_context.app

        self.app.add_url_rule(
            "/api/v1/encode/<int:entry_id>",
            view_func=self.receive_encode_progress,
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

        self.__start_lock = asyncio.Lock()
        self.__ffmpeg_procs = {}
        self.__available_encoders = set()

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
        self.ENCODER = cfg.encoder
        self.MAX_ENCODES = cfg.maximum_encodes if cfg.maximum_encodes > 0 else 1
        self.TIMED_ENCODING = cfg.timed_encoding
        self.HOUR_START = cfg.hour_start
        self.HOUR_END = cfg.hour_end

        logger.debug("Encode config updated")

    async def resume(self) -> None:
        """
        Resumes the encoder process.

        Pulls items from the encode table where the
        `ended_at` column is null and begins encoding
        them.
        """
        logger.debug("Encoder task resuming...")

        await self.update_config()
        available_encoders = await self.get_available_encoders()
        if self.ENCODER not in available_encoders:
            cfg = await EncodeConfig.retrieve(self.app)
            for encoder in VALID_ENCODERS.values():
                if encoder in available_encoders:
                    cfg.encoder = self.ENCODER = encoder
                    await cfg.save()
                    break

        async with self.app.acquire_db() as con:
            # Remove any partial encodes
            await con.execute(
                """
                UPDATE
                    encode
                SET
                    started_at = NULL
                WHERE
                    ended_at IS NULL;
                """
            )

        await self.process_next()
        logger.debug("Encoder task resumed.")

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

        outfile = infile.with_suffix(self.TEMP_SUFFIX)

        return (
            f'ffmpeg -hide_banner -loglevel error -i "{infile}" -map 0 -c copy -c:v {self.ENCODER} -crf {self.CRF}'
            f' -tune animation -preset {self.SPEED_PRESET} -c:a copy -progress {url} -y "{outfile}"'
        )

    async def queue(self, entry_id: int) -> None:
        """
        Queues an entry to be encoded.

        Parameters
        ----------
        entry_id:
            The entry to be encoded.
        """
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

        if not self.__ffmpeg_procs:
            await self.process_next()

    def launch_process_task(self, entry_id: int) -> None:
        """
        Launches a process task.

        Parameters
        ----------
        entry_id: int
            The entry ID to encode.
        """
        logger.debug(f"Launching new process task for <e{entry_id}>")
        self.app._tasks.append(
            asyncio.create_task(self.process(entry_id), name=f"encode-{entry_id}")
        )

    async def process(self, entry_id: int) -> None:
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

        if self.TIMED_ENCODING:
            to_sleep = seconds_until(self.HOUR_START, self.HOUR_END)
            logger.debug(
                f"Timed encoding enabled, sleeping '{to_sleep:,}' seconds before encoding..."
            )
            await asyncio.sleep(to_sleep)

        if len(self.__ffmpeg_procs) >= self.MAX_ENCODES:
            logger.debug(
                f"Reached maximum encodes when processing, <e{entry_id}> is queued."
            )
            return

        async with self.__start_lock:
            ret = False
            try:
                ret = await self.launch_ffmpeg(entry_id)
            except Exception as e:
                logger.error(
                    f"Failed to launch ffmpeg process for <e{entry_id}>: {e}",
                    exc_info=True,
                )

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

                await self.process_next()

    async def process_next(self) -> None:
        """
        Attempts to retrieve the next item to encode and
        then start the task.
        """
        if len(self.__ffmpeg_procs) >= self.MAX_ENCODES:
            logger.debug("Reached maximum encodes, skipping request to process next.")
            return

        queue = await self.get_queue()
        if not queue:
            logger.debug("Encode queue is empty, nothing to process next.")
            return

        next_ = int(queue[0]["entry_id"])
        self.launch_process_task(next_)

    async def launch_ffmpeg(self, entry_id: int) -> bool:
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
        elif entry_id in self.__ffmpeg_procs:
            logger.warning(
                f"Error when attempting to encode entry <e{entry_id}>: entry is already being encoded"
            )
            return False

        logger.debug(f"Starting new encode process for entry <e{entry_id}>...")

        infile = Path(entry["file_path"]).resolve()
        if not infile.exists():
            logger.warning(
                f"Error when attemping to encode entry <e{entry_id}>: input fp does not exist"
            )
            return False
        elif not infile.is_file():
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
            proc = await create_subprocess_shell(cmd)
        except Exception as e:
            logger.error(
                f"Failed starting new encode for entry <e{entry_id}>: {e}",
                exc_info=True,
            )
        else:
            self.__ffmpeg_procs[entry_id] = proc
            async with self.app.acquire_db() as con:
                await con.execute(
                    """
                    UPDATE
                        encode
                    SET
                        initial_size = ?,
                        started_at = CURRENT_TIMESTAMP
                    WHERE
                        entry_id = ?;
                """,
                    file_bytecount,
                    entry_id,
                )
            return True

        return False

    @staticmethod
    def process_progress_data(data: bytes) -> Dict[str, str]:
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

    async def receive_encode_progress(self, entry_id: int) -> str:
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
            logger.debug(f"Encode progress entry <e{entry_id}>: `{last_received}`")

        ret = await self.__ffmpeg_procs[entry_id].wait()
        del self.__ffmpeg_procs[entry_id]

        if ret != 0:
            logger.error(
                f"Error occurred with end of ffmpeg process for entry <e{entry_id}>: error code {ret}"
            )

        try:
            if last_received.get("progress") == "end":
                await self.handle_encode_finished(entry_id)
        except Exception:
            logger.exception(
                f"Error occurred when handling finished encode for entry <e{entry_id}>"
            )
        finally:
            await self.process_next()

        return "{}"

    async def handle_encode_finished(self, entry_id: int) -> None:
        logger.debug(f"Encode finished for entry <e{entry_id}>, move required")
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

            encoded_size = os.path.getsize(encoded)
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

        # The torrent has to be removed from the download client
        # because the contents of the file will be completely
        # different after encoding, and we cannot move the encoded
        # file to the new file if it is in use by the dl client process.
        entry = await Entry.from_entry_id(self.app, entry_id)
        try:
            await self.app.dl_client.delete_torrent(entry.torrent_hash)
        except Exception as e:
            logger.warning(
                f"Failed removing entry <e{entry_id}> from torrent client: {e}"
            )

        original = original.resolve()
        try:
            original.unlink(missing_ok=True)
        except Exception as e:
            logger.exception(
                f"Failed moving finished encode for entry <e{entry_id}>: {e}"
            )
        else:
            await move(encoded.resolve(), original)
            logger.debug(
                f"Encode moved for entry <e{entry_id}>: encoding process finished"
            )

    async def has_ffmpeg(self) -> bool:
        """
        Checks if ffmpeg is available to use.

        Returns
        -------
        bool
            If ffmpeg is available.
        """
        await self.get_available_encoders()
        return bool(self.__available_encoders)

    async def get_available_encoders(self) -> set[str]:
        """
        Returns all available ffmpeg video encoders.
        Also sets the __available_encoders class attribute.

        Possible encoders: libx264, libx265

        Returns
        -------
        set[str]
            Available video encoders.
        """
        if self.__available_encoders:
            return self.__available_encoders

        proc = await asyncio.create_subprocess_shell(
            "ffmpeg -buildconf",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return set()

        output = stdout.decode("utf-8")

        res = set()
        for encoder in VALID_ENCODERS.keys():
            if encoder in output:
                res.add(VALID_ENCODERS[encoder])

        self.__available_encoders = res
        return res

    async def get_queue(self, page: int = 0) -> List[Dict[str, str]]:
        """
        Returns the active encode queue.

        Keys:
        queued_at   - time the encode was queued at
        started_at  - time the encode was started at (possibly null)
        title       - name of the show that is being encoded
        episode     - episode of the show that is being encoded
        entry_id    - id of the entry that is being encoded
        """
        logger.debug("Retrieving encode queue...")

        async with self.app.acquire_db() as con:
            queue = await con.fetchall(
                """
                SELECT
                    encode.queued_at,
                    encode.started_at,
                    show_entry.id as entry_id,
                    show_entry.episode,
                    shows.title
                FROM
                    encode
                JOIN
                    show_entry ON encode.entry_id = show_entry.id
                JOIN
                    shows ON show_entry.show_id = shows.id
                WHERE
                    encode.ended_at IS NULL
                AND
                    encode.started_at IS NULL
                ORDER BY
                    encode.queued_at ASC
                LIMIT ?, 15;
            """,
                (page * 15),
            )

        return [dict(item) for item in queue]

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
                    started_at IS NOT NULL
                AND
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

    def cleanup(self) -> None:
        """
        Cancels all active ffmpeg processes.
        """
        logger.debug("Cleanup: Attempting to terminate encoding processes...")
        failed_to_cancel = 0
        for entry_id, proc in self.__ffmpeg_procs.items():
            try:
                proc.terminate()
                del self.__ffmpeg_procs[entry_id]
            except Exception:
                logger.warning(
                    f"Could not cancel encode process for entry {entry_id}!",
                    exc_info=True,
                )
                failed_to_cancel += 1
            else:
                logger.debug(f"Cleanup: Encode process for entry {entry_id} cancelled.")
        logger.debug(
            f"Cleanup: Encode processes cancelled. [{failed_to_cancel} failed to cancel]"
        )
