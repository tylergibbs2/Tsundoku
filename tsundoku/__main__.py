import argparse
import asyncio
import getpass

from argon2 import PasswordHasher
import asyncpg

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


async def load_schema():
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

    with open("create_db.sql", "r") as f:
        await con.execute(f.read())

    await con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tsundoku Command Line")
    parser.add_argument("--load-schema", action="store_true")
    parser.add_argument("--create-user", action="store_true")
    args = parser.parse_args()

    if args.load_schema:
        loop = asyncio.get_event_loop()

        print("Loading database schema...")
        loop.run_until_complete(load_schema())
        print("Database schema loaded.")
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
