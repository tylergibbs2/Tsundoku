from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Row
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tsundoku.app import TsundokuApp


@dataclass
class Library:
    app: "TsundokuApp"

    id_: int
    folder: Path
    is_default: bool

    def to_dict(self) -> dict:
        return {
            "id_": self.id_,
            "folder": str(self.folder),
            "is_default": self.is_default,
        }

    @classmethod
    def from_data(cls, app: "TsundokuApp", row: Row) -> "Library":
        return cls(app, id_=row["id"], folder=Path(row["folder"]), is_default=row["is_default"])

    @classmethod
    async def from_id(cls, app: "TsundokuApp", id_: int) -> "Library":
        async with app.acquire_db() as con:
            library = await con.fetchone(
                """
                SELECT
                    id,
                    folder,
                    is_default
                FROM
                    library
                WHERE
                    id=?;
                """,
                (id_,),
            )

        if library is None:
            raise ValueError(f"Library with ID '{id_}' does not exist")

        return Library.from_data(app, library)

    @classmethod
    async def all(cls, app: "TsundokuApp") -> list["Library"]:
        async with app.acquire_db() as con:
            libraries = await con.fetchall(
                """
                SELECT
                    id,
                    folder,
                    is_default
                FROM
                    library
                ORDER BY id ASC;
            """
            )

        return [Library.from_data(app, row) for row in libraries]

    @classmethod
    async def new(cls, app: "TsundokuApp", folder: Path, is_default: bool = False) -> "Library":
        async with app.acquire_db() as con:
            async with con.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO
                        library (
                            folder,
                            is_default
                        )
                    VALUES
                        (?, ?);
                """,
                    (str(folder), False),
                )
                id_ = cur.lastrowid
                if id_ is None:
                    raise Exception("Failed to create new library, lastrowid is None")

        instance = cls(app, id_=id_, folder=folder, is_default=False)
        if is_default:
            await instance.set_default()

        return instance

    async def save(self) -> None:
        async with self.app.acquire_db() as con:
            await con.execute(
                """
                UPDATE
                    library
                SET
                    folder = ?
                WHERE
                    id = ?;
                """,
                (str(self.folder), self.id_),
            )

    async def delete(self) -> None:
        async with self.app.acquire_db() as con:
            await con.execute(
                """
                    DELETE FROM
                        library
                    WHERE
                        id = ?;
                """,
                (self.id_,),
            )

    async def set_default(self) -> None:
        async with self.app.acquire_db() as con:
            async with con.transaction():
                await con.execute(
                    """
                    UPDATE
                        library
                    SET
                        is_default = ?
                    WHERE
                        id = ?;
                """,
                    (
                        True,
                        self.id_,
                    ),
                )

                await con.execute(
                    """
                    UPDATE
                        library
                    SET
                        is_default = ?
                    WHERE
                        id != ?;
                """,
                    (False, self.id_),
                )

                self.is_default = True
