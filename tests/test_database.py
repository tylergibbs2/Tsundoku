import logging
from pathlib import Path
import sqlite3

import pytest

from tsundoku.database import migrate


async def test_schema_matches_migrated(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="tsundoku")

    db = tmp_path / "migration_test.db"
    await migrate(db)
    con = sqlite3.connect(db)
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
