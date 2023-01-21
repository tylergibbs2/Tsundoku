from pathlib import Path
from typing import Optional


def mock_resolve_file(cls, path: Path, _) -> Optional[Path]:
    return path


async def mock_rename(src: Path, dst: Path) -> None:
    ...


async def mock_move(src: str, dst: str) -> None:
    ...


def mock_symlink_to(dst: Path) -> None:
    ...


def mock_mkdir(*_, **__) -> None:
    ...
