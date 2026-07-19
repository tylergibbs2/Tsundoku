import logging
from pathlib import Path
import sqlite3

import pytest

from tsundoku.database import migrate

_SCHEMA_QUERY = """
    SELECT
        m.name as table_name,
        p.name as column_name
    FROM
        sqlite_master AS m
    JOIN
        pragma_table_info(m.name) AS p
    WHERE
        m.type = 'table'
        -- Exclude yoyo migration bookkeeping and SQLite internal tables,
        -- which aren't part of schema.sql.
        AND m.name NOT LIKE '%yoyo%'
        AND m.name NOT LIKE 'sqlite_%'
    -- Sort by column name rather than physical position (p.cid): a column
    -- appended by a later migration is logically equivalent to schema.sql
    -- declaring it earlier, so ordering shouldn't fail the comparison.
    ORDER BY
        m.name,
        p.name;
"""


def _schema(con: sqlite3.Connection) -> list[tuple[str, str]]:
    """Return every (table_name, column_name) pair defined in the connection."""
    return con.execute(_SCHEMA_QUERY).fetchall()


def _expected_schema() -> list[tuple[str, str]]:
    """Build the schema an empty database gets by applying schema.sql."""
    con = sqlite3.connect(":memory:")
    con.executescript(Path("schema.sql").read_text())
    return _schema(con)


async def test_schema_matches_migrated(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="tsundoku")

    db = tmp_path / "migration_test.db"
    await migrate(db)
    migrated_schema = _schema(sqlite3.connect(db))

    assert migrated_schema == _expected_schema()
