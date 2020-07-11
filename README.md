# Tsundoku (積ん読)

Tsundoku is an all-in-one utility to download, rename, and move anime from RSS feeds.
Anime is able to be matched from any source with an RSS feed. Out of the box, Tsundoku has a parser for HorribleSubs installed.

## Requirements

- Python 3.7+

## Installation

```sh
git clone https://github.com/tylergibbs2/Tsundoku
cd Tsundoku
python -m venv .venv
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
pip install -r requirements.txt
python -m tsundoku --create-user   # Creates a user for logging in, passwords are securely stored
```

Copy `config.ini.example` to `config.ini` and then [configure](#Configuration).

## Usage

```sh
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
python -m tsundoku
```

## Configuration

```
[Tsundoku]
host=localhost         # IP that Tsundoku will be hosted at
port=6439              # Port to use for hosting
parsers=[              # List of parsers in "parsers/"
    "horriblesubs"
    ]
polling_interval=900   # How often, in seconds, Tsundoku should check parsers

[PostgreSQL]           # PSQL connection info
host=localhost
port=5432
database=tsundoku
user=postgres
password=password

[Deluge]               # Deluge connection info
host=localhost
port=8112
password=password
secure=false           # Use HTTPS
```

## Parsers

Please see the [example parser](https://github.com/tylergibbs2/Tsundoku/blob/master/parsers/_example.py) for writing custom parsers.