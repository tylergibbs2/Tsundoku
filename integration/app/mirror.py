"""Swap a real torrent for a synthetic one of the same shape.

Given a real magnet or .torrent URL, this reads the release's *names* (which
are public metadata) and produces a brand new torrent with the same file
names and directory structure but locally generated content, announced to the
local tracker and dropped into the seeder's watch directory.

The point is that an info hash commits to the exact bytes of the content, so
a real torrent can never be completed without the real data. Faking the
tracker or the peers does not help -- clients verify every piece against the
info dict and would simply never finish. Substituting the torrent itself is
the only way to get a real client to really download something, end to end,
without touching the internet or the real swarm.

What is faithful: file names, directory layout, file count, and therefore
everything Tsundoku derives from them (anitomy parsing, episode matching,
renaming, the move into a library). What is not: the bytes, and the file
sizes, which are shrunk so downloads finish in seconds.
"""

import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import logging
import os
from pathlib import Path
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

import bencodepy

ANNOUNCE = os.environ.get("TRACKER_ANNOUNCE", "http://tracker:6969/announce")
SEED_DATA = Path(os.environ.get("SEED_DATA", "/seed/data"))
SEED_WATCH = Path(os.environ.get("SEED_WATCH", "/seed/watch"))
#: Every synthetic file is this size regardless of the real one, so that a
#: 1.4GB batch release still downloads in a couple of seconds.
FILE_BYTES = int(os.environ.get("SYNTHETIC_FILE_BYTES", str(1024 * 1024)))
PIECE_LENGTH = 32 * 1024
PORT = int(os.environ.get("PORT", "8081"))
FETCH_UA = "Mozilla/5.0 (compatible; TsundokuTestMirror/1.0)"
CACHE_DIR = Path(os.environ.get("SOURCE_CACHE", "/seed/cache"))
#: nyaa's robots.txt asks for Crawl-delay: 5 on /download (and disallows it
#: for every agent), so retries are spaced accordingly rather than hammering.
CRAWL_DELAY = float(os.environ.get("CRAWL_DELAY", "5"))
FETCH_ATTEMPTS = int(os.environ.get("FETCH_ATTEMPTS", "4"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s mirror %(message)s")
logger = logging.getLogger("mirror")


class MirrorError(Exception):
    """A source that could not be turned into a synthetic torrent."""


def safe_parts(parts: list[bytes]) -> list[bytes]:
    """Strip anything that would let a torrent write outside the seed root."""
    cleaned = [part for part in parts if part not in (b"", b".", b"..") and not part.startswith(b"/")]
    if not cleaned:
        raise MirrorError("torrent contains a file with an unusable path")
    return cleaned


def synthetic_size(real_size: int) -> int:
    """Shrink only what needs shrinking.

    Capping rather than flattening keeps zero-byte and small files at their
    real size, which matters because real releases genuinely contain both and
    a mirror that turns every file into the same size is not reproducing the
    structure it claims to.
    """
    return min(real_size, FILE_BYTES)


def is_padding(entry: dict[bytes, Any]) -> bool:
    """Whether a files[] entry is BitTorrent padding rather than content."""
    if b"p" in entry.get(b"attr", b""):
        return True
    path = entry.get(b"path") or []
    return bool(path) and path[0].startswith(b".pad")


def describe_magnet(src: str) -> tuple[bytes, list[tuple[list[bytes], int]]]:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(src).query)
    names = query.get("dn")
    if not names:
        raise MirrorError("magnet has no display name (dn), so there is no file name to reproduce")

    # parse_qs gave us str; recover the bytes the sender actually encoded.
    name = names[0].encode("utf-8", "surrogateescape")
    return name, [([name], FILE_BYTES)]


def describe_torrent(src: str) -> tuple[bytes, list[tuple[list[bytes], int]]]:
    """Fetch and describe a .torrent by URL.

    Convenience route, for pasting a URL at the mirror by hand. Tsundoku
    itself uses the POST route instead, handing over bytes it has already
    fetched: that keeps this container off the source tracker entirely (whose
    robots.txt disallows /download for every agent) and means a .torrent
    behind a tracker login still works, since only Tsundoku holds the session.
    """
    return describe_bytes(fetch_source(src))


def fetch_source(src: str) -> bytes:
    """Fetch a source .torrent, at most once ever.

    The synthetic torrent built from a source is fully deterministic, so there
    is never a reason to fetch the same URL twice. Caching to disk also keeps
    a dev loop off the source tracker entirely after the first hit, which
    matters when roughly 40% of requests to it fail and its robots.txt asks
    for a crawl delay.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIR / f"{hashlib.sha256(src.encode('utf-8', 'surrogateescape')).hexdigest()}.torrent"

    if cached.exists():
        logger.info(f"source cache hit: {src[:88]}")
        return cached.read_bytes()

    last: Exception | None = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        request = urllib.request.Request(src, headers={"User-Agent": FETCH_UA})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            last = e
            logger.warning(f"fetch attempt {attempt}/{FETCH_ATTEMPTS} failed ({type(e).__name__}); source trackers are frequently flaky")
            if attempt < FETCH_ATTEMPTS:
                time.sleep(CRAWL_DELAY)
            continue

        cached.write_bytes(raw)
        logger.info(f"fetched and cached source ({len(raw)} bytes) on attempt {attempt}: {src[:88]}")
        return raw

    raise MirrorError(f"could not fetch the source torrent after {FETCH_ATTEMPTS} attempts: {last}")


def describe_bytes(raw: bytes) -> tuple[bytes, list[tuple[list[bytes], int]]]:
    try:
        meta: Any = bencodepy.decode(raw)
        info = meta[b"info"]
        # Names stay as raw bytes the whole way through. Torrent names are not
        # required to be UTF-8 -- Shift-JIS and CP1251 releases are common --
        # and decoding with a replacement character would hand back a name
        # that differs from the real one, which is the one thing a mirror
        # must not do.
        name: bytes = info[b"name"]
    except Exception as e:
        raise MirrorError(f"source did not parse as a .torrent: {e}") from e

    if b"files" in info:
        files = [(safe_parts(entry[b"path"]), synthetic_size(entry[b"length"])) for entry in info[b"files"] if not is_padding(entry)]
    elif b"length" in info:
        files = [([name], synthetic_size(info[b"length"]))]
    else:
        # BitTorrent v2 keeps the layout in `file tree` instead; nothing in
        # this environment produces one, but failing clearly beats a KeyError.
        raise MirrorError("torrent has no v1 file list (BitTorrent v2-only torrents are not supported)")

    if not files:
        raise MirrorError("torrent contains no non-padding files")
    if sum(size for _, size in files) == 0:
        raise MirrorError("torrent has no content to reproduce")

    return name, files


def synthetic_bytes(seed: bytes, size: int) -> bytes:
    """Deterministic filler, so the same release always yields one info hash."""
    blob = bytearray()
    counter = 0
    while len(blob) < size:
        blob += hashlib.sha256(seed + str(counter).encode()).digest()
        counter += 1
    return bytes(blob[:size])


def is_multi_file(name: bytes, files: list[tuple[list[bytes], int]]) -> bool:
    """A single file directly under the torrent name is the single-file form."""
    return len(files) > 1 or files[0][0] != [name]


def to_path(root: Path, parts: list[bytes]) -> Path:
    # fsdecode with surrogateescape round-trips arbitrary bytes through str,
    # so a Shift-JIS name lands on disk as the bytes it really is.
    return root.joinpath(*(os.fsdecode(part) for part in parts))


def write_content(name: bytes, files: list[tuple[list[bytes], int]]) -> list[bytes]:
    """Materialize the synthetic files for the seeder, returning their bytes."""
    root = SEED_DATA / os.fsdecode(name) if is_multi_file(name, files) else SEED_DATA

    payloads = []
    for parts, size in files:
        target = to_path(root, parts)
        data = synthetic_bytes(b"/".join([name, *parts]), size)
        payloads.append(data)

        if target.exists() and target.stat().st_size == size:
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    return payloads


def build_torrent(name: bytes, files: list[tuple[list[bytes], int]], payloads: list[bytes]) -> tuple[bytes, str]:
    # Pieces run across the concatenation of every file, in order.
    stream = b"".join(payloads)
    pieces = b"".join(hashlib.sha1(stream[offset : offset + PIECE_LENGTH]).digest() for offset in range(0, len(stream), PIECE_LENGTH))

    if is_multi_file(name, files):
        info: dict[bytes, Any] = {
            b"name": name,
            b"files": [{b"length": size, b"path": parts} for parts, size in files],
        }
    else:
        info = {b"name": name, b"length": files[0][1]}

    info[b"piece length"] = PIECE_LENGTH
    info[b"pieces"] = pieces

    encoded_info = bencodepy.encode(info)
    torrent = bencodepy.encode({b"announce": ANNOUNCE.encode(), b"info": info})

    return torrent, hashlib.sha1(encoded_info).hexdigest()


def mirror(src: str) -> tuple[bytes, bytes, str]:
    """Mirror by source string: a magnet, or a .torrent URL this host can reach."""
    name, files = describe_magnet(src) if src.startswith("magnet:?") else describe_torrent(src)
    return produce(name, files)


def mirror_body(body: bytes) -> tuple[bytes, bytes, str]:
    """Mirror from bytes the caller already fetched.

    The caller is Tsundoku, running wherever a real deployment runs, so this
    path works for any source it can reach regardless of what this container
    can.
    """
    if body.startswith(b"magnet:?"):
        name, files = describe_magnet(body.decode("utf-8", "surrogateescape").strip())
    else:
        name, files = describe_bytes(body)

    return produce(name, files)


def produce(name: bytes, files: list[tuple[list[bytes], int]]) -> tuple[bytes, bytes, str]:
    payloads = write_content(name, files)
    torrent, info_hash = build_torrent(name, files, payloads)
    display = os.fsdecode(name)

    SEED_WATCH.mkdir(parents=True, exist_ok=True)
    watch_target = SEED_WATCH / f"{info_hash}.torrent"
    if not watch_target.exists():
        # Written atomically: the seeder watches this directory and would
        # happily pick up a half-written file.
        temporary = watch_target.with_suffix(".partial")
        temporary.write_bytes(torrent)
        temporary.rename(watch_target)
        logger.info(f"handed to seeder: {display} ({len(files)} file(s), {sum(s for _, s in files)} bytes) info_hash={info_hash}")
    else:
        logger.info(f"already seeded: {display} info_hash={info_hash}")

    return torrent, name, info_hash


class MirrorHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - name fixed by BaseHTTPRequestHandler
        pass

    def _send(self, body: bytes, status: int = 200, content_type: str = "application/x-bittorrent") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve(self, produce_result: Any) -> None:
        try:
            torrent, name, _ = produce_result()
        except MirrorError as e:
            logger.warning(f"refusing request: {e}")
            self._send(str(e).encode(), status=502, content_type="text/plain")
            return
        except Exception:
            logger.exception("unexpected failure while mirroring")
            self._send(b"internal mirror error", status=500, content_type="text/plain")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/x-bittorrent")
        self.send_header("Content-Disposition", f'attachment; filename="{urllib.parse.quote(name)}.torrent"')
        self.send_header("Content-Length", str(len(torrent)))
        self.end_headers()
        self.wfile.write(torrent)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/healthz":
            self._send(b"ok", content_type="text/plain")
            return

        if parsed.path != "/mirror":
            self._send(b"only /mirror is implemented", status=404, content_type="text/plain")
            return

        sources = urllib.parse.parse_qs(parsed.query).get("src")
        if not sources:
            self._send(b"missing ?src=", status=400, content_type="text/plain")
            return

        self._serve(lambda: mirror(sources[0]))

    def do_POST(self) -> None:
        """Mirror a .torrent (or magnet) the caller has already fetched."""
        if urllib.parse.urlparse(self.path).path != "/mirror":
            self._send(b"only /mirror is implemented", status=404, content_type="text/plain")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send(b"bad Content-Length", status=400, content_type="text/plain")
            return

        if length <= 0:
            self._send(b"empty request body", status=400, content_type="text/plain")
            return

        body = self.rfile.read(length)
        self._serve(lambda: mirror_body(body))


if __name__ == "__main__":
    for directory in (SEED_DATA, SEED_WATCH, CACHE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"listening on :{PORT} announce={ANNOUNCE} file_bytes={FILE_BYTES}")
    ThreadingHTTPServer(("0.0.0.0", PORT), MirrorHandler).serve_forever()
