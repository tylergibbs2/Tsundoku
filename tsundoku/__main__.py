import argparse
import asyncio
import getpass

from argon2 import PasswordHasher
import asyncpg
from yoyo import get_backend
from yoyo import read_migrations

from tsundoku import app
from tsundoku.config import get_config_value


hasher = PasswordHasher()


async def insert_user(username: str, password: str):
    host = get_config_value("PostgreSQL", "host")
    port = get_config_value("PostgreSQL", "port")
    user = get_config_value("PostgreSQL", "user")
    db_password = get_config_value("PostgreSQL", "password")
    database = get_config_value("PostgreSQL", "database")

    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=db_password,
        database=database
    )

    pw_hash = hasher.hash(password)

    await conn.execute("""
        INSERT INTO users (username, password_hash) VALUES ($1, $2);
    """, username, pw_hash)

    await conn.close()


async def migrate():
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

    await con.close()

    backend = get_backend(f"postgres://{user}:{db_password}@{host}:{port}/{database}")
    migrations = read_migrations("migrations")

    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tsundoku Command Line")
    parser.add_argument("--migrate", action="store_true")
    parser.add_argument("--create-user", action="store_true")
    args = parser.parse_args()

    if args.migrate:
        loop = asyncio.get_event_loop()

        print("Applying database migrations...")
        loop.run_until_complete(migrate())
        print("Database migrations applied.")
    elif args.create_user:
        username = input("Username: ")
        match = False
        while not match:
            password = getpass.getpass()
            conf_password = getpass.getpass("Confirm Password: ")
            match = password == conf_password
            if not match:
                print("Password Mismatch")

        loop = asyncio.get_event_loop()

        print("Creating user...")
        loop.run_until_complete(insert_user(username, password))
        print("User created.")
    else:
        app.run()
