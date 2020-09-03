# Tsundoku (積ん読)

Tsundoku is an all-in-one utility to download, rename, and move anime from RSS feeds.
Anime is able to be matched from any source with an RSS feed. Out of the box, Tsundoku has a parser for HorribleSubs installed.

## Requirements

- Python 3.7+
- [Deluge WebAPI Plugin](https://github.com/idlesign/deluge-webapi) OR [qBittorrent](https://www.qbittorrent.org/) with WebUI enabled

## Installation

```sh
git clone https://github.com/tylergibbs2/Tsundoku
cd Tsundoku
python -m venv .venv
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
pip install -r requirements.txt
python -m tsundoku --migrate       # Loads the database schema into PSQL, must be done after PSQL config
python -m tsundoku --create-user   # Creates a user for logging in, must be done after PSQL config
```

Copy `config.ini.example` to `config.ini` and then [configure](#Configuration).

## Updating

```sh
git pull
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
pip install -r requirements.txt
python -m tsundoku --migrate
```

## Usage

```sh
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
python -m tsundoku
```

## Configuration

```ini
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

[TorrentClient]        # Torrent client connection info
client=deluge          # Can be either 'deluge' or 'qbittorrent'
host=localhost
port=8112
username=admin         # Only needed if using qBittorrent
password=password
secure=false           # Use HTTPS
```

## Parsers

Please see the [example parser](https://github.com/tylergibbs2/Tsundoku/blob/master/parsers/_example.py) for writing custom parsers.