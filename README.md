# Tsundoku (積ん読)

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-blue.svg)](https://opensource.org/licenses/MPL-2.0)
[![Discord Invite](https://img.shields.io/discord/801396820772257802)](https://discord.gg/thxN858gXm)

Tsundoku is an all-in-one utility to download, rename, and move anime from RSS feeds.
Anime is able to be matched from any source with an RSS feed. Out of the box, Tsundoku has a parser for SubsPlease installed.

[Chat on Discord](https://discord.gg/thxN858gXm)

## Key Features

- Parse various RSS feeds for the latest anime
- Rename and move downloaded files automatically
- Search Nyaa for existing releases and batches
- Import third-party RSS parsers to search other feeds
- Send updates to Discord or Slack with webhooks
- View airing status of shows
- Full-fledged backend RESTful API for easy integration ([docs](https://tsundoku.moe/docs))

## Requirements

- Python 3.7+
- One of: [Deluge WebAPI Plugin](https://github.com/idlesign/deluge-webapi), [qBittorrent](https://www.qbittorrent.org/) with WebUI enabled, [Transmission](https://transmissionbt.com/)

## Docker Installation (Recommended)

1. Copy the `docker-compose.yml` file from the repository.
2. Replace the file paths.
3. Run `docker compose up -d`.

Updating is as simple as running `docker compose pull` and `docker compose up -d`.

## Source Installation

### Initial Setup

```bash
$ git clone https://github.com/tylergibbs2/Tsundoku
$ cd Tsundoku
$ python -m venv .venv
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
$ pip install -r requirements.txt
```

### Updating

```bash
$ git pull
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
$ pip install -r requirements.txt
```

### Usage

```bash
# WINDOWS: .venv\Scripts\activate.bat
# LINUX:   source .venv/bin/activate
$ python -m tsundoku
```

## Parsers

Please see the [example parser](https://github.com/tylergibbs2/Tsundoku/blob/master/default_parsers/_example.py) for writing custom parsers.
