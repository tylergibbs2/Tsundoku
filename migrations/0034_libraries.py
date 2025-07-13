from pathlib import Path
from sqlite3 import Connection

from yoyo import step

__depends__ = {"0033_encode_encoder"}


VALID_SEASON_REPLACEMENTS = {"{s00}", "{s}"}
VALID_REPLACEMENTS = {
    "{n}",
    "{name}",
    "{title}",
    "{s}",
    "{season}",
    "{e}",
    "{episode}",
    "{s00}",
    "{e00}",
    "{s00e00}",
    "{S00E00}",
    "{sxe}",
    "{version}",
    "{ext}",
}


def grab_default_library(con: Connection) -> None:
    cur = con.cursor()
    cur.execute(
        """
        SELECT
            default_desired_folder
        FROM
            general_config
        LIMIT 1;
    """
    )
    config = cur.fetchone()
    if config is None:
        default_folder = Path("/")
    else:
        default_folder = Path(config[0])

    use_season_folder = any(any(s in part for s in VALID_SEASON_REPLACEMENTS) for part in default_folder.parts)

    library_folder = Path(
        *(p for p in default_folder.parts if all(val not in p for val in VALID_REPLACEMENTS))
    ).resolve()

    cur.execute(
        """
        INSERT INTO
            library (
                folder,
                is_default
            )
        VALUES
            (?, ?)
    """,
        (str(library_folder), True),
    )

    cur.execute(
        """
        UPDATE
            general_config
        SET
            use_season_folder = ?;
    """,
        (use_season_folder,),
    )

    cur.execute(
        """
        ALTER TABLE
            general_config
        DROP COLUMN
            default_desired_folder;
    """
    )


def rollback_default_library(con: Connection) -> None:
    cur = con.cursor()

    cur.execute(
        """
        DELETE FROM library;
    """
    )

    cur.execute(
        """
        UPDATE
            general_config
        SET
            use_season_folder = 1;
    """
    )


steps = (
    step(
        """
        CREATE TABLE library (
            id INTEGER PRIMARY KEY,
            folder TEXT NOT NULL,
            is_default BOOLEAN NOT NULL
        );
    """,
        "DROP TABLE library;",
    ),
    step(
        """
        ALTER TABLE
            general_config
        ADD COLUMN
            use_season_folder BOOLEAN NOT NULL DEFAULT '1';
    """,
        "ALTER TABLE general_config DROP COLUMN use_season_folder;",
    ),
    step(grab_default_library, rollback_default_library),
)
