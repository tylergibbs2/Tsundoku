import logging
import os
from contextlib import asynccontextmanager
from sqlite3 import OperationalError
from typing import Any, AsyncGenerator

from yoyo import get_backend, read_migrations

from tsundoku.config import get_config_value

from . import asqlite

HAS_ASYNCPG = True
try:
    import asyncpg
except ImportError:
    HAS_ASYNCPG = False


logger = logging.getLogger("tsundoku")


if os.getenv("IS_DOCKER"):
    fp = "data/tsundoku.db"
else:
    fp = "tsundoku.db"


@asynccontextmanager
async def acquire() -> AsyncGenerator[Any, Any]:
    async with asqlite.connect(fp) as con:
        async with con.cursor() as cur:
            yield cur


async def backport_psql() -> None:
    if not HAS_ASYNCPG:
        return

    async with acquire() as con:
        try:
            await con.execute("""
                SELECT
                    *
                FROM
                    _yoyo_migration;
            """)
            rows = await con.fetchall()
        except OperationalError:
            rows = []

    if rows:
        return

    host = get_config_value("PostgreSQL", "host")
    port = get_config_value("PostgreSQL", "port")
    user = get_config_value("PostgreSQL", "user")
    db_password = get_config_value("PostgreSQL", "password")
    database = get_config_value("PostgreSQL", "database")

    try:
        con = await asyncpg.connect(
            host=host,
            user=user,
            password=db_password,
            port=port,
            database=database
        )
    except asyncpg.InvalidCatalogNameError:
        sys_con = await asyncpg.connect(
            host=host,
            user=user,
            password=db_password,
            port=port,
            database="template1"
        )
        await sys_con.execute(f"""
            CREATE DATABASE "{database}" OWNER "{user}";
        """)
        await sys_con.close()

    con = await asyncpg.connect(
        host=host,
        user=user,
        password=db_password,
        port=port,
        database=database
    )

    backend = get_backend(f"postgres://{user}:{db_password}@{host}:{port}/{database}")
    migrations = read_migrations("migrations")

    first_sqlite = migrations.items[14:][0]
    migrations.items = migrations.items[:14]

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    migrations.items = [first_sqlite]
    backend = get_backend(f"sqlite:///{fp}")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))

    users = await con.fetch("""
        SELECT
            id,
            username,
            password_hash,
            created_at,
            api_key::TEXT
        FROM
            users;
    """)
    shows = await con.fetch("""
        SELECT
            id,
            title,
            desired_format,
            desired_folder,
            season,
            episode_offset,
            created_at
        FROM
            shows;
    """)
    show_entry = await con.fetch("""
        SELECT
            id,
            show_id,
            episode,
            current_state,
            torrent_hash,
            file_path,
            last_update
        FROM
            show_entry;
    """)
    kitsu_info = await con.fetch("""
        SELECT
            show_id,
            kitsu_id,
            cached_poster_url,
            show_status,
            slug,
            last_updated
        FROM
            kitsu_info;
    """)
    webhook_base = await con.fetch("""
        SELECT
            id,
            name,
            base_service,
            base_url,
            content_fmt
        FROM
            webhook_base;
    """)
    webhook = await con.fetch("""
        SELECT
            show_id,
            base
        FROM
            webhook;
    """)
    webhook_trigger = await con.fetch("""
        SELECT
            show_id,
            base,
            trigger
        FROM
            webhook_trigger;
    """)
    async with acquire() as sqlite:
        await sqlite.executemany("""
            INSERT INTO
                users
            VALUES (:id, :username, :password_hash, :created_at, :api_key);
        """, [dict(user) for user in users])

        await sqlite.executemany("""
            INSERT INTO
                shows
            VALUES
                (:id, :title, :desired_format, :desired_folder, :season, :episode_offset, :created_at);
        """, [dict(show) for show in shows])

        await sqlite.executemany("""
            INSERT INTO
                show_entry
            VALUES
                (:id, :show_id, :episode, :current_state, :torrent_hash, :file_path, :last_update);
        """, [dict(entry) for entry in show_entry])

        await sqlite.executemany("""
            INSERT INTO
                kitsu_info
            VALUES
                (:show_id, :kitsu_id, :cached_poster_url, :show_status, :slug, :last_updated);
        """, [dict(info) for info in kitsu_info])

        await sqlite.executemany("""
            INSERT INTO
                webhook_base
            VALUES
                (:id, :name, :base_service, :base_url, :content_fmt);
        """, [dict(wh_base) for wh_base in webhook_base])

        await sqlite.executemany("""
            INSERT INTO
                webhook
            VALUES
                (:show_id, :base);
        """, [dict(wh) for wh in webhook])

        await sqlite.executemany("""
            INSERT INTO
                webhook_trigger
            VALUES
                (:show_id, :base, :trigger);
        """, [dict(trigger) for trigger in webhook_trigger])

    await con.close()


async def migrate() -> None:
    await backport_psql()

    backend = get_backend(f"sqlite:///{fp}")
    migrations = read_migrations("migrations")
    migrations.items = migrations.items[14:]

    logger.info("Applying database migrations...")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
    logger.info("Database migrations applied.")
