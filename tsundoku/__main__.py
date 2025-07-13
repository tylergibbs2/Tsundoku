import argparse
import asyncio
import getpass
from pathlib import Path
import re

try:
    from fluent.runtime import FluentBundle, FluentResource
except ImportError:
    print("Please install the dependencies before running Tsundoku.")
    print("Run `pip install -r requirements.txt` to install them.")
    exit(1)


def find_locale_duplicates(lang: str) -> None:
    """
    Finds duplicate keys in a given locale.

    Parameters
    ----------
    lang: str
        Locale to check.
    """
    locale_file = Path(f"l10n/{lang}.ftl")
    if not locale_file.exists():
        print(f"Locale '{lang}' could not be found or does not exist.")
        exit(1)

    seen_keys = set()
    duplicates = set()

    text = locale_file.read_text(encoding="utf-8")
    for match in re.finditer(r"^([\w\-]+) =", text, re.MULTILINE):
        key = match.group(1)
        if key in seen_keys:
            duplicates.add(key)
        else:
            seen_keys.add(key)

    if not duplicates:
        print("No duplicates found.")
    else:
        print(f"Found {len(duplicates)} duplicate keys:\n{', '.join(duplicates)}")


def compare_locales(from_lang: str, to_lang: str) -> None:
    """
    Compares two whole languages in the Tsundoku
    translation files. Will point out any missing
    files or keys that do not exist in `to_lang` from
    `from_lang`.

    Parameters
    ----------
    from_lang: str
        Origin locale.
    to_lang: str
        Destination locale.
    """
    from_path = Path(f"l10n/{from_lang}.ftl")
    to_path = Path(f"l10n/{to_lang}.ftl")

    if not from_path.exists():
        print(f"Language '{from_lang}' could not be found or does not exist.")
        return
    if not to_path.exists():
        print(f"Language '{to_lang}' could not be found or does not exist.")
        return

    from_bundle = FluentBundle([from_lang])
    to_bundle = FluentBundle([to_lang])

    from_bundle.add_resource(FluentResource(from_path.read_text(encoding="utf-8")))
    to_bundle.add_resource(FluentResource(to_path.read_text(encoding="utf-8")))

    from_keys = from_bundle._messages.keys()
    to_keys = to_bundle._messages.keys()

    conflicts = 0
    missing_keys = set(from_keys).difference(set(to_keys))
    for key in missing_keys:
        conflicts += 1
        print(f"Language '{to_lang}' is missing key: '{key}'.")

    if conflicts:
        print(f"{conflicts} different conflicts were found in language '{to_lang}'.")

        print(f"'{to_lang}' is {100 - (len(missing_keys) / len(from_keys)) * 100:.2f}% compatible with '{from_lang}'.")
        print(f"(missing {len(missing_keys)} keys out of {len(from_keys)})")
    else:
        print("No conflicts found. Both locales have the same features.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tsunduku Command Line Interface")
    parser.add_argument(
        "--dbshell",
        action="store_true",
        help="Launch a sqlite shell into the Tsundoku database.",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrates the Tsundoku database to match any updates.",
    )
    parser.add_argument("--create-user", action="store_true", help="Creates a new login user.")
    parser.add_argument(
        "--l10n-compat",
        type=str,
        nargs=2,
        help="Compares two languages, will point out missing translations in the second one.",
    )
    parser.add_argument(
        "--l10n-duplicates",
        type=str,
        nargs=1,
        help="Finds duplicate keys in a given language.",
    )
    args = parser.parse_args()

    if args.dbshell:
        from tsundoku.database import spawn_shell

        spawn_shell()
    elif args.l10n_compat:
        from_lang, to_lang = args.l10n_compat
        compare_locales(from_lang, to_lang)
    elif args.l10n_duplicates:
        find_locale_duplicates(args.l10n_duplicates[0])
    elif args.migrate:
        from tsundoku.constants import DATA_DIR, DATABASE_FILE_NAME
        from tsundoku.database import migrate

        database_source = DATA_DIR / DATABASE_FILE_NAME
        asyncio.run(migrate(database_source))
    elif args.create_user:
        username = input("Username: ")
        match = False
        password = ""
        while not match:
            password = getpass.getpass("Password: ")
            conf_password = getpass.getpass("Confirm Password: ")
            match = password == conf_password
            if not match:
                print("Password Mismatch")

        print("Creating user...")
        from tsundoku import app

        asyncio.run(app.insert_user(username, password))
        print("User created successfully.")
    else:
        from tsundoku import app

        asyncio.run(app.run())
