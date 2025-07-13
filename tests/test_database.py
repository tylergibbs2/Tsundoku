from __future__ import annotations

import logging
import sqlite3

from pytest import LogCaptureFixture

from tests.mock import MockTsundokuApp
from tsundoku.database import migrate


# async def test_migrate_from_empty(caplog: LogCaptureFixture) -> None:
#     caplog.set_level(logging.ERROR, logger="tsundoku")

#     await migrate("file:migration_test1?mode=memory")


async def test_schema_matches_migrated(caplog: LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="tsundoku")

    await migrate("file:migration_test2?mode=memory&cache=shared")
    con = sqlite3.connect("file:migration_test2?mode=memory&cache=shared", uri=True)
    cur = con.execute(
        """
        SELECT
            m.name as table_name,
            p.name as column_name
        FROM
            sqlite_master AS m
        JOIN
            pragma_table_info(m.name) AS p
        WHERE
            m.type = 'table'
        ORDER BY
            m.name,
            p.cid;
    """
    )
    print(cur.fetchall())
