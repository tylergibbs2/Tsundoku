from typing import Optional

from quart import current_app as app
from quart_auth import AuthUser


class User(AuthUser):
    # TODO
    def __init__(self, auth_id: Optional[str]) -> None:
        super().__init__(auth_id)
        self._resolved = False
        self._username = None

    async def _resolve(self) -> None:
        if not self._resolved:
            async with app.db_pool.acquire() as con:
                self._username = await con.fetchval("""
                    SELECT
                        username
                    FROM
                        users
                    WHERE id = $1;
                """, self.auth_id)
            self._resolved = True

    @property
    async def username(self) -> str:
        await self._resolve()
        return self._username
