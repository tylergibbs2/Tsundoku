import argparse
import asyncio
import getpass

from tsundoku import app


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tsundoku Command Line")
    parser.add_argument("--migrate", action="store_true")
    parser.add_argument("--create-user", action="store_true")
    args = parser.parse_args()

    if args.migrate:
        loop = asyncio.get_event_loop()

        print("Applying database migrations...")
        loop.run_until_complete(app.migrate())
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
        loop.run_until_complete(app.insert_user(username, password))
        print("User created.")
    else:
        app.run()
