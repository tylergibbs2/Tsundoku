"""
This install script is essentially performing the following operations:

1. Check for virtual environment
   1. Create one if it doesn't exist
2. Begin execution using the executable of the virtual environment
3. Installs `requirements.txt` with pip
4. Check if Yarn is required (required if the frontend is not built, or if the built frontend is out of date)
5. If Yarn is required:
   1. Check if Yarn is installed
   2. Install the `package.json` dependencies
   3. Run `yarn build`
6. Create the `run.py` script.

If any of the operations fail, the script exits.
"""

from __future__ import annotations
import sys

if sys.version_info < (3, 8):
    print("Please update Python to use version 3.8+")
    sys.exit(1)

import json
import os
from pathlib import Path
import shutil
import subprocess

try:
    from tsundoku import __version__ as version
except ImportError:
    print(
        "The main Tsundoku module is missing. Are you sure you're in the right directory?"
    )
    sys.exit(1)


RUN_SCRIPT = """
from __future__ import annotations
import sys

if sys.version_info < (3, 8):
    print("Please update Python to use version 3.8+")
    sys.exit(1)

import os
from pathlib import Path
import subprocess


class Runner:
    virtual_dir: str = ".venv"

    @property
    def python_executable(self) -> Path:
        if os.name == "nt":
            return Path(self.virtual_dir, "Scripts", "python.exe")
        else:
            return Path(self.virtual_dir, "bin", "python")

    def start(self) -> None:
        if not self.python_executable.exists():
            print("Virtual environment not found, please run `install.py` first.")
            sys.exit(1)

        print(f"Starting Tsundoku under virtual environment '{self.virtual_dir}'...")
        subprocess.run([self.python_executable, "-m", "tsundoku"] + sys.argv[1:])
        sys.exit(0)


if __name__ == "__main__":
    Runner().start()

"""


class Installer:
    virtual_dir: str = ".venv"

    REQUIRED_FILES: list[str] = ["tsundoku", "requirements.txt"]

    @property
    def python_executable(self) -> Path:
        if os.name == "nt":
            return Path(self.virtual_dir, "Scripts", "python.exe")
        else:
            return Path(self.virtual_dir, "bin", "python")

    @property
    def pip_executable(self) -> Path:
        if os.name == "nt":
            return Path(self.virtual_dir, "Scripts", "pip.exe")
        else:
            return Path(self.virtual_dir, "bin", "pip")

    def is_venv(self) -> bool:
        return Path(self.virtual_dir).exists() and Path(sys.prefix).samefile(
            self.virtual_dir
        )

    def is_yarn_required(self) -> bool:
        js_path = Path("tsundoku", "blueprints", "ux", "static", "js")
        # look for the built frontend
        if not js_path.exists():
            return True

        # if package.json is missing, assume that
        # the frontend is fully up-to-date. otherwise,
        # check the version
        if not Path("package.json").exists():
            return False

        # if the frontend is built, check if the version matches
        with open("package.json", "r") as f:
            package_info = json.load(f)

        if "version" not in package_info:
            print("Malformed package.json")
            sys.exit(1)

        return package_info["version"] != version

    def create_venv(self) -> None:
        if self.python_executable.exists():
            print("Virtual environment already exists.")
            return

        print("Creating virtual environment...")
        proc = subprocess.run([sys.executable, "-m", "venv", self.virtual_dir])
        if proc.returncode != 0:
            print(f"Failed to create virtual environment. Exit code {proc.returncode}")
            sys.exit(1)

        print("Virtual environment created.")

    def restart_under_venv(self) -> None:
        print(f"Restarting under virtual environment '{self.virtual_dir}'...")
        subprocess.run([self.python_executable, __file__] + sys.argv[1:])
        sys.exit(0)

    def check_required_files(self) -> None:
        missing = []
        for fp in self.REQUIRED_FILES:
            if not Path(fp).exists():
                missing.append(fp)

        if missing:
            print("Missing required files:")
            for fp in missing:
                print(f" - {fp}")

            sys.exit(1)

    def check_yarn_installed(self) -> None:
        print("Checking if Yarn is installed...")
        proc = subprocess.run(["yarn", "--version"], shell=True)
        if proc.returncode != 0:
            print("Yarn is not installed. Please install it before continuing.")
            sys.exit(1)

        print("Yarn is installed.")

    def install_python_requirements(self) -> None:
        print("Installing Python requirements...")
        proc = subprocess.run([self.pip_executable, "install", "wheel==0.38.4"])
        if proc.returncode != 0:
            print(f"Failed to install wheel. Exit code {proc.returncode}")
            sys.exit(1)

        proc = subprocess.run(
            [self.pip_executable, "install", "-r", "requirements.txt"]
        )
        if proc.returncode != 0:
            print(f"Failed to install requirements. Exit code {proc.returncode}")
            sys.exit(1)

        print("Requirements installed.")

    def install_yarn_requirements(self) -> None:
        print("Installing Yarn requirements...")
        proc = subprocess.run(["yarn"], shell=True)
        if proc.returncode != 0:
            print(f"Failed to install Yarn requirements. Exit code {proc.returncode}")
            sys.exit(1)

        print("Yarn requirements installed.")

    def build_frontend(self) -> None:
        print("Building frontend...")
        proc = subprocess.run(["yarn", "build"], shell=True)
        if proc.returncode != 0:
            print(f"Failed to build frontend. Exit code {proc.returncode}")
            sys.exit(1)

        print("Frontend built.")

    def create_run_script(self) -> None:
        print("Creating run script...")
        with open("run.py", "w") as f:
            f.write(RUN_SCRIPT)

        print("Run script created.")

    def run(self) -> None:
        if "--force-new-venv" in sys.argv:
            shutil.rmtree(self.virtual_dir, ignore_errors=True)

        if self.is_yarn_required():
            self.REQUIRED_FILES += ["yarn.lock", "package.json", "l10n"]

        self.check_required_files()

        if not self.is_venv():
            self.create_venv()
            self.restart_under_venv()  # exits this process

        try:
            self.install_python_requirements()
        except FileNotFoundError:
            print("There was an error with your installation.")
            print("Please run again with the '--force-new-venv' flag.")
            sys.exit(1)

        # Depending on how the user downloaded the source, the frontend may or may not be built.
        if self.is_yarn_required():
            self.check_yarn_installed()
            self.install_yarn_requirements()
            self.build_frontend()

        self.create_run_script()

        banner_width = 80
        print(f"\n\n{'-*' * (banner_width // 2 - 1)}-\n")
        print("Installation complete.".center(banner_width))
        print("Run Tsundoku with 'python run.py'".center(banner_width))
        print(f"\n{'-*' * (banner_width // 2 - 1)}-\n")


if __name__ == "__main__":
    Installer().run()
