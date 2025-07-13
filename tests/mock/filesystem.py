from pathlib import Path


def mock_resolve_file(cls, path: Path, _) -> Path | None:
    return path


async def mock_rename(src: Path, dst: Path) -> None: ...


async def mock_move(src: str, dst: str) -> None: ...


def mock_symlink_to(dst: Path) -> None: ...


def mock_mkdir(*_, **__) -> None: ...
