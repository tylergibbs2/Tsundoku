from collections.abc import AsyncGenerator
from dataclasses import dataclass
import json
from pathlib import Path

import aiofiles

from tsundoku.constants import DATA_DIR


@dataclass
class SourceKeyMapping:
    filename: str
    torrent: str

    @classmethod
    def from_object(cls, obj: dict) -> "SourceKeyMapping":
        required_keys = ("filename", "torrent")
        for key in required_keys:
            if key not in obj:
                raise Exception(f"Invalid RSS Source Key Mapping object, missing required key '{key}'")

        return cls(cls._get_true_key(obj["filename"]), cls._get_true_key(obj["torrent"]))

    @staticmethod
    def _get_true_key(value: str) -> str:
        if not value.startswith("$."):
            raise Exception(f"Invalid key mapping '{value}', must start with '$.'")

        value = value[2:]

        if len(value.split(".")) > 1:
            raise Exception(f"Invalid key mapping '{value}', must not contain '.'")

        return value

    def get_filename(self, item: dict) -> str:
        return item[self.filename]

    def get_torrent(self, item: dict) -> str:
        return item[self.torrent]


@dataclass
class Source:
    name: str
    version: str
    url: str

    rss_key_map: SourceKeyMapping

    @classmethod
    def from_object(cls, obj: dict) -> "Source":
        required_keys = ("name", "version", "url", "rssItemKeyMapping")
        for key in required_keys:
            if key not in obj:
                raise Exception(f"Invalid RSS Source object, missing required key '{key}'")

        if not isinstance(obj["name"], str):
            raise TypeError("Invalid RSS Source object, name must be a string")
        if not isinstance(obj["version"], str):
            raise TypeError("Invalid RSS Source object, version must be a string")
        if not isinstance(obj["url"], str):
            raise TypeError("Invalid RSS Source object, url must be a string")
        if not isinstance(obj["rssItemKeyMapping"], dict):
            raise TypeError("Invalid RSS Source object, rssItemKeyMapping must be a dictionary")

        mapping = SourceKeyMapping.from_object(obj["rssItemKeyMapping"])
        return cls(obj["name"], obj["version"], obj["url"], mapping)

    def get_filename(self, item: dict) -> str:
        return self.rss_key_map.get_filename(item)

    def get_torrent(self, item: dict) -> str:
        return self.rss_key_map.get_torrent(item)

    def __repr__(self) -> str:
        return f"<Source name={self.name} version={self.version} url={self.url}>"


async def get_all_sources() -> AsyncGenerator[Source, None]:
    source_path = DATA_DIR / "sources"
    source_path.mkdir(exist_ok=True, parents=True)

    if not (source_path / "COPIED").exists():
        default_sources = Path("default_sources").glob("*.json")
        for source in default_sources:
            source = source.name
            if not (source_path / source).exists():
                async with aiofiles.open(source_path / source, "wb") as fp:
                    async with aiofiles.open(Path.cwd() / "default_sources" / source, "rb") as default_fp:
                        await fp.write(await default_fp.read())

        async with aiofiles.open(source_path / "COPIED", "wb") as fp:
            await fp.write(b"")

    for source in source_path.glob("*.json"):
        async with aiofiles.open(source) as fp:
            yield Source.from_object(json.loads(await fp.read()))
