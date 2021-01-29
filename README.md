# Tsundoku (積ん読)

[![Documentation Status](https://readthedocs.org/projects/tsundoku/badge/?version=latest)](https://tsundoku.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Ftylergibbs2%2FTsundoku.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2Ftylergibbs2%2FTsundoku?ref=badge_shield)

Tsundoku is an all-in-one utility to download, rename, and move anime from RSS feeds.
Anime is able to be matched from any source with an RSS feed. Out of the box, Tsundoku has a parser for Erai-raws and SubsPlease installed.

## Requirements

- Python 3.7+
- [Deluge WebAPI Plugin](https://github.com/idlesign/deluge-webapi) OR [qBittorrent](https://www.qbittorrent.org/) with WebUI enabled
- PostgreSQL 9+

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

## Installation (Docker)

- Containerized PostgreSQL is required. I recommend that your PostgreSQL container is setup to be persistent.
  [Here's a link to a StackOverflow question](https://stackoverflow.com/questions/41637505/how-to-persist-data-in-a-dockerized-postgres-database-using-volumes) which will help you ensure your PostgreSQL data is persistent.

1. Copy the `docker-compose.yml` file from the repository.
2. Copy the `config.ini.example` file and rename it `config.ini`.
3. Copy any parsers that you want and put them in a new folder.
4. [Configure](#Configuration) the configuration file.
5. Replace the file paths and replace the Postgres Docker service name.
6. Run `docker-compose up -d`.

I will not be providing an example on how to start the container using
`docker run`.

You will then need to perform the following commands:
```sh
docker container exec -it tsundoku python -m tsundoku --migrate
docker container exec -it tsundoku python -m tsundoku --create-user
```

When pointing to directories within Tsundoku, make sure that you begin
your target directory with `/target/...`.

For the sake of example, here is my personal entry for Tsundoku in `docker-compose.yml`:
```yml
version: "3.8"
services:
  tsundoku:
    image: tylergibbs2/tsundoku
    container_name: tsundoku
    environment:
      - PUID=1000
      - PGID=1000
    volumes:
      - /opt/appdata/tsundoku/config.ini:/app/config.ini
      - /opt/appdata/tsundoku/parsers:/app/parsers
      - /mediadrives/Downloaded:/downloaded
      - /mediadrives/Anime:/target
    ports:
      - "6439:6439"
    depends_on:
      - postgres
    restart: always
```

`/opt/appdata/tsundoku/config.ini` is the absolute path where I put the `config.ini` file.

`/opt/appdata/tsundoku/parsers` is the folder where I manually placed all the parsers I use.

`/mediadrives/Downloaded` is the absolute path where Tsundoku will look for completed torrents.

`/mediadrives/Anime` is the absolute path where Tsundoku will move completed torrents.


And [here](https://i.imgur.com/BkNz7P4.png) is an example of what it looks like when adding a show using Docker.

## Configuration

```ini
[Tsundoku]
host = localhost         # IP that Tsundoku will be hosted at
port = 6439              # Port to use for hosting
parsers = [              # List of parsers in "parsers/"
    "parsers.subsplease",
    "parsers.erairaws"
    ]
polling_interval = 900   # How often, in seconds, Tsundoku should check parsers
do_update_checks = true  # Will always be false regardless of setting if in Docker
check_every_n_days = 1   # How often (in days) to perform update checks
git_path = git           # Path to Git executable, only needed for update checks

[PostgreSQL]             # PSQL connection info
host = localhost
port = 5432
database = tsundoku
user = postgres
password = password

[TorrentClient]          # Torrent client connection info
client = deluge          # Can be either 'deluge' or 'qbittorrent'
host = localhost
port = 8112
username = admin         # Only needed if using qBittorrent
password = password
secure = false           # Use HTTPS
```

## Parsers

Please see the [example parser](https://github.com/tylergibbs2/Tsundoku/blob/master/parsers/_example.py) for writing custom parsers.

## License
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2Ftylergibbs2%2FTsundoku.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2Ftylergibbs2%2FTsundoku?ref=badge_large)