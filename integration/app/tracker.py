"""A minimal HTTP BitTorrent tracker for the local test environment.

No maintained tracker image exists on any public registry any more (the
opentracker and chihaya ones referenced around the web are all gone), and
pulling a stranger's personal image into a project's test setup is not worth
the supply chain risk when the job is this small. A swarm confined to one
Docker network only needs an /announce endpoint that remembers who announced
for an info hash and hands back the rest of the swarm.

Deliberately omitted: scrape, stats, IPv6, persistence. Restarting the
container just empties every swarm, which is the behaviour a test
environment wants anyway.
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import logging
import socket
import struct
import time
from typing import Any
import urllib.parse

ANNOUNCE_INTERVAL = 10
#: Peers that have not re-announced within this window are dropped.
PEER_TTL = 60
PORT = 6969

logging.basicConfig(level=logging.INFO, format="%(asctime)s tracker %(message)s")
logger = logging.getLogger("tracker")

#: info_hash -> {(ip, port): (last_seen, is_seeder)}
_swarms: dict[bytes, dict[tuple[str, int], tuple[float, bool]]] = {}


def bencode(value: Any) -> bytes:
    if isinstance(value, bool):
        raise TypeError("bencode has no boolean type")
    if isinstance(value, int):
        return b"i" + str(value).encode() + b"e"
    if isinstance(value, bytes):
        return str(len(value)).encode() + b":" + value
    if isinstance(value, str):
        return bencode(value.encode())
    if isinstance(value, list):
        return b"l" + b"".join(bencode(item) for item in value) + b"e"
    if isinstance(value, dict):
        body = b"".join(bencode(k) + bencode(v) for k, v in sorted(value.items()))
        return b"d" + body + b"e"
    raise TypeError(f"cannot bencode {type(value).__name__}")


def compact_peers(peers: list[tuple[str, int]]) -> bytes:
    """Pack peers into the 6-bytes-each form clients expect for compact=1."""
    packed = b""
    for ip, port in peers:
        try:
            packed += socket.inet_aton(ip) + struct.pack(">H", port)
        except OSError:
            # A non-IPv4 peer address; nothing in this environment produces
            # one, but a malformed announce should not take the tracker down.
            logger.warning(f"skipping un-packable peer address {ip}")
    return packed


class TrackerHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - name fixed by BaseHTTPRequestHandler
        # The default handler logs every request to stderr; announces happen
        # every ANNOUNCE_INTERVAL seconds per peer and drown out everything.
        pass

    def _respond(self, payload: dict[Any, Any], status: int = 200) -> None:
        body = bencode(payload)
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/healthz":
            self._respond({"ok": 1})
            return

        if parsed.path != "/announce":
            self._respond({"failure reason": "only /announce is implemented"}, status=404)
            return

        # latin-1 round-trips every byte, which matters because info_hash and
        # peer_id are raw 20-byte values, not text.
        query = urllib.parse.parse_qs(parsed.query, encoding="latin-1")

        try:
            info_hash = query["info_hash"][0].encode("latin-1")
            port = int(query["port"][0])
        except (KeyError, IndexError, ValueError):
            self._respond({"failure reason": "missing or malformed info_hash/port"})
            return

        ip = self.client_address[0]
        left = int(query.get("left", ["1"])[0])
        event = query.get("event", [""])[0]

        swarm = _swarms.setdefault(info_hash, {})

        if event == "stopped":
            swarm.pop((ip, port), None)
        else:
            swarm[(ip, port)] = (time.monotonic(), left == 0)

        now = time.monotonic()
        for peer, (last_seen, _) in list(swarm.items()):
            if now - last_seen > PEER_TTL:
                del swarm[peer]

        others = [peer for peer in swarm if peer != (ip, port)]
        seeders = sum(1 for _, is_seeder in swarm.values() if is_seeder)

        logger.info(f"announce {info_hash.hex()[:12]} from {ip}:{port} event={event or 'none'} swarm={len(swarm)} -> returning {len(others)} peer(s)")

        self._respond(
            {
                "interval": ANNOUNCE_INTERVAL,
                "complete": seeders,
                "incomplete": len(swarm) - seeders,
                "peers": compact_peers(others),
            }
        )


if __name__ == "__main__":
    logger.info(f"listening on :{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), TrackerHandler).serve_forever()
