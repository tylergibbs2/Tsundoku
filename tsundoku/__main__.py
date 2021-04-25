import sys

if sys.version_info < (3, 7):
    print("Please update Python to use version 3.7+")
    exit(1)

import argparse
import asyncio
import getpass
from pathlib import Path

from fluent.runtime import FluentBundle, FluentResource

from tsundoku import app, git
from tsundoku.fluent import get_injector

fluent = get_injector(["cmdline"])


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

    from_files = {Path(*fp.parts[2:]) for fp in from_path.rglob("*")}
    to_files = {Path(*fp.parts[2:]) for fp in to_path.rglob("*")}

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
            print(fluent._("compare-missing-key", {"lang": to_lang, "file": str(fp), "key": key}))

    if conflicts:
        print(fluent._("compare-conflict-count", {"count": conflicts, "to": to_lang}))
    else:
        print(fluent._("compare-no-conflict"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=fluent._("title"))
    parser.add_argument("--migrate", action="store_true", help=fluent._("cmd-migrate"))
    parser.add_argument("--create-user", action="store_true", help=fluent._("cmd-create-user"))
    parser.add_argument("--l10n-compat", type=str, nargs=2, help=fluent._("cmd-l10n-compat"))
    args = parser.parse_args()

    if args.l10n_compat:
        from_lang, to_lang = args.l10n_compat
        compare_locales(from_lang, to_lang)
    elif args.migrate:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(git.migrate())
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

        loop = asyncio.get_event_loop()

        print(fluent._("creating-user"))
        loop.run_until_complete(app.insert_user(username, password))
        print(fluent._("created-user"))
    else:
        app.run()
