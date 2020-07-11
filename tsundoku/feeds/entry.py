from pathlib import Path
from quart import current_app as app

from asyncpg import Record


class Entry:
    def __init__(self, record: Record):
        self.id = record["id"]
        self.show_id = record["show_id"]
        self.episode = record["episode"]
        self.state = record["current_state"]
        self.torrent_hash = record["torrent_hash"]

        fp = record["file_path"]
        self.file_path = Path(fp) if fp is not None else None

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
        async with self.app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE show_entry SET
                    current_state = $1
                WHERE id=$2;
            """, new_state, self.id)

    async def set_path(self, new_path: Path) -> None:
        """
        Updates the database and local object's file path.

        Parameters
        ----------
        new_path: str
            The new path to update to.
        """
        self.file_path = new_path
        async with self.app.db_pool.acquire() as con:
            await con.execute("""
                UPDATE show_entry SET
                    file_path = $1
                WHERE id=$2;
            """, str(new_path), self.id)
