import argparse
import asyncio
import getpass

from tsundoku import app, git


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tsundoku Command Line")
    parser.add_argument("--migrate", action="store_true")
    parser.add_argument("--create-user", action="store_true")
    parser.add_argument("--no-ui", action="store_true")
    args = parser.parse_args()

    if args.migrate:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(git.migrate())
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
    elif args.no_ui:
        app.run(with_ui=False)
    else:
        app.run()
