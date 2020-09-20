from pathlib import Path

from asyncpg import Record

from tsundoku.webhooks import send


class Entry:
    def __init__(self, app, record: Record):
        self.id = record["id"]
        self.show_id = record["show_id"]
        self.episode = record["episode"]
        self.state = record["current_state"]
        self.torrent_hash = record["torrent_hash"]

        fp = record["file_path"]
        self.file_path = Path(fp) if fp is not None else None

        self._app = app
        self._record = record

    async def set_state(self, new_state: str) -> None:
        """
        Updates the database and local object's state.

        Parameters
        ----------
        new_state: str
            The new state to update to.
        """
        self.state = new_state
        async with self._app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE show_entry SET
                    current_state = $1
                WHERE id=$2;
            """, new_state, self.id)

        await self._handle_webhooks()

    async def set_path(self, new_path: Path) -> None:
        """
        Updates the database and local object's file path.

        Parameters
        ----------
        new_path: str
            The new path to update to.
        """
        self.file_path = new_path
        async with self._app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE show_entry SET
                    file_path = $1
                WHERE id=$2;
            """, str(new_path), self.id)

    async def _handle_webhooks(self) -> None:
        """
        On a state change, if the state is listed as a post event
        for this show, then send this entry to the webhook handling.

        This is an internal method and shouldn't be called unless
        a state change occurs. If called improperly, duplicate
        sends could occur.

        Uses the `self.state` attribute, so call this after
        that is updated.
        """
        async with self._app.db_pool.acquire() as con:
            trigger = await con.fetchval("""
                SELECT
                    wh.id
                FROM
                    webhook wh
                LEFT JOIN wh_trigger t
                    ON wh.id = t.wh_id
                WHERE wh.show_id = $1 AND t.trigger = $2;
            """, self.show_id, self.state)

        if trigger:
            await send(
                trigger,
                self.show_id,
                self.episode,
                self.state
            )
