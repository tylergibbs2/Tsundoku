import sys

if sys.version_info < (3, 8):
    print("Please update Python to use version 3.8+")
    exit(1)

import argparse
import asyncio
import getpass
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile

try:
    from fluent.runtime import FluentBundle, FluentResource

    from tsundoku import __version__ as version, database
    from tsundoku.fluent import get_injector
except ImportError:
    print("Please install the dependencies before running Tsundoku.")
    print("Run `pip install -r requirements.txt` to install them.")
    exit(1)

fluent = get_injector(["cmdline"])


def bundle_zip() -> None:
    """
    Bundles the Tsundoku application into a zip file.
    """
    TO_ZIP = (
        "default_sources",
        "l10n",
        "migrations",
        "tsundoku",
        "LICENSE.md",
        "README.md",
        "requirements.txt",
    )

    INVALID_EXTS = (".pyc",)

    for fp in TO_ZIP:
        if not Path(fp).exists():
            print(f"Bundle process failed, missing '{fp}'...")
            exit(1)

    print("Running `yarn build`...")
    proc = subprocess.Popen(
        ["yarn", "build"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, err = proc.communicate()
    if err:
        print(err.decode())
        exit(1)

    print(out.decode())

    print("Zipping contents...")
    filename = f"tsundoku-{version}.zip"
    with ZipFile(filename, "w") as zip:
        for fp in TO_ZIP:
            print(f"Adding {fp}...")
            if Path(fp).is_dir():
                for path in Path(fp).rglob("*"):
                    if path.suffix in INVALID_EXTS:
                        continue
                    zip.write(str(path))
            else:
                zip.write(fp)

    print(f"Bundle process complete. '{filename}' created.")


def find_locale_duplicates(lang: str) -> None:
    """
    Finds duplicate keys in a given locale.

    Parameters
    ----------
    lang: str
        Locale to check.
    """
    locale_files = Path().rglob(f"l10n/{lang}/*.ftl")

    seen_keys = set()
    duplicates = set()
    for fp in locale_files:
        bundle = FluentBundle([lang])

        with open(str(fp), "r", encoding="utf-8") as text:
            bundle.add_resource(FluentResource(text.read()))

        for key in bundle._messages.keys():
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
    from_path = Path(f"l10n/{from_lang}")
    to_path = Path(f"l10n/{to_lang}")

    if not from_path.exists():
        print(fluent._("compare-missing-lang", {"missing": from_lang}))
        return
    elif not to_path.exists():
        print(fluent._("compare-missing-lang", {"missing": to_lang}))
        return

    conflicts = 0

    from_files = {Path(*fp.parts[2:]) for fp in from_path.rglob("*.ftl")}
    to_files = {Path(*fp.parts[2:]) for fp in to_path.rglob("*.ftl")}

    for fp in from_files.difference(to_files):
        conflicts += 1
        print(fluent._("compare-missing-file", {"lang": to_lang, "file": str(fp)}))

    for fp in from_files.intersection(to_files):
        from_file = from_path / fp
        to_file = to_path / fp

        from_bundle = FluentBundle([from_lang])
        to_bundle = FluentBundle([to_lang])

        with open(str(from_file), "r", encoding="utf-8") as text:
            from_bundle.add_resource(FluentResource(text.read()))
        with open(str(to_file), "r", encoding="utf-8") as text:
            to_bundle.add_resource(FluentResource(text.read()))

        from_keys = from_bundle._messages.keys()
        to_keys = to_bundle._messages.keys()

        missing_keys = set(from_keys).difference(set(to_keys))
        for key in missing_keys:
            conflicts += 1
            print(
                fluent._(
                    "compare-missing-key",
                    {"lang": to_lang, "file": str(fp), "key": key},
                )
            )

    if conflicts:
        print(fluent._("compare-conflict-count", {"count": conflicts, "to": to_lang}))
    else:
        print(fluent._("compare-no-conflict"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=fluent._("title"))
    parser.add_argument("--bundle", action="store_true", help="Bundle Tsundoku.")
    parser.add_argument("--test", action="store_true", help="Run unit tests.")
    parser.add_argument("--dbshell", action="store_true", help=fluent._("cmd-dbshell"))
    parser.add_argument("--migrate", action="store_true", help=fluent._("cmd-migrate"))
    parser.add_argument(
        "--create-user", action="store_true", help=fluent._("cmd-create-user")
    )
    parser.add_argument(
        "--l10n-compat", type=str, nargs=2, help=fluent._("cmd-l10n-compat")
    )
    parser.add_argument(
        "--l10n-duplicates", type=str, nargs=1, help=fluent._("cmd-l10n-duplicates")
    )
    args = parser.parse_args()

    if args.bundle:
        bundle_zip()
    elif args.test:
        os.system("pytest")
    elif args.dbshell:
        from tsundoku.database import spawn_shell

        spawn_shell()
    elif args.l10n_compat:
        from_lang, to_lang = args.l10n_compat
        compare_locales(from_lang, to_lang)
    elif args.l10n_duplicates:
        find_locale_duplicates(args.l10n_duplicates[0])
    elif args.migrate:
        asyncio.run(database.migrate())
    elif args.create_user:
        username = input(fluent._("username") + " ")
        match = False
        password = ""
        while not match:
            password = getpass.getpass(fluent._("password") + " ")
            conf_password = getpass.getpass(fluent._("conf-password") + " ")
            match = password == conf_password
            if not match:
                print("Password Mismatch")

        print(fluent._("creating-user"))
        from tsundoku import app

        asyncio.run(app.insert_user(username, password))
        print(fluent._("created-user"))
    else:
        from tsundoku import app

        asyncio.run(app.run())
