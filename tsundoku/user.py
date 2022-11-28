from typing import Optional

from quart import current_app as app
from quart_auth import AuthUser


class User(AuthUser):
    def __init__(self, auth_id: Optional[str]) -> None:
        super().__init__(auth_id)
        self._resolved = False
        self._username = ""
        self._api_key = ""

    async def _resolve(self) -> None:
        if not self._resolved:
            async with app.acquire_db() as con:
                await con.execute(
                    """
                    SELECT
                        username,
                        api_key
                    FROM
                        users
                    WHERE id = ?;
                """,
                    self.auth_id,
                )
                user = await con.fetchone()
            self._username = user["username"]
            self._api_key = user["api_key"]
            self._resolved = True

    @property
    async def username(self) -> str:
        await self._resolve()
        return self._username

    @property
    async def api_key(self) -> str:
        await self._resolve()
        return self._api_key
