# Tsundoku (積ん読)

[![Documentation Status](https://readthedocs.org/projects/tsundoku/badge/?version=latest)](https://tsundoku.readthedocs.io/en/latest/?badge=latest)
[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Discord Invite](https://img.shields.io/discord/801396820772257802)](https://discord.gg/thxN858gXm)

Tsundoku is an all-in-one utility to download, rename, and move anime from RSS feeds.
Anime is able to be matched from any source with an RSS feed. Out of the box, Tsundoku has a parser for SubsPlease installed.

[Chat on Discord](https://discord.gg/thxN858gXm)

## Key Features

* Parse various RSS feeds for the latest anime
* Rename and move downloaded files automatically
* Search Nyaa for existing releases and batches
* Import third-party RSS parsers to search other feeds
* Send updates to Discord or Slack with webhooks
* View airing status of shows
* Full-fledged backend RESTful API for easy integration ([docs](https://tsundoku.readthedocs.io/en/latest/))

## Requirements

* Python 3.7+
* [Deluge WebAPI Plugin](https://github.com/idlesign/deluge-webapi) OR [qBittorrent](https://www.qbittorrent.org/) with WebUI enabled

## Installation

```sh
$ git clone https://github.com/tylergibbs2/Tsundoku
$ cd Tsundoku
$ python -m venv .venv
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
$ pip install -r requirements.txt
$ python -m tsundoku --create-user   # Creates a user for logging in
```

## Updating

```sh
$ git pull
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
$ pip install -r requirements.txt
```

## Usage

```sh
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
$ python -m tsundoku
```

## Installation (Docker)

1. Copy the `docker-compose.yml` file from the repository.
2. Copy any parsers that you want and put them in a new folder.
3. Replace the file paths.
4. Run `docker-compose up -d`.

I will not be providing an example on how to start the container using
`docker run`.

You will then need to perform the following commands:
```sh
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
      - /opt/appdata/tsundoku/data:/app/data
      - /opt/appdata/tsundoku/parsers:/app/parsers
      - /mediadrives/Downloaded:/downloaded
      - /mediadrives/Anime:/target
    ports:
      - "6439:6439"
    restart: always
```

`/opt/appdata/tsundoku/parsers` is the folder where I manually placed all the parsers I use.

`/mediadrives/Downloaded` is the absolute path where Tsundoku will look for completed torrents.

`/mediadrives/Anime` is the absolute path where Tsundoku will move completed torrents.


And [here](https://i.imgur.com/BkNz7P4.png) is an example of what it looks like when adding a show using Docker.


## Parsers

Please see the [example parser](https://github.com/tylergibbs2/Tsundoku/blob/master/parsers/_example.py) for writing custom parsers.
