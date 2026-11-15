"""Registry of connection methods ("connectors"), chosen by URL scheme.

Every connector is a class with this shape (see relay.py for the real one):

    class MyConnector:
        def __init__(self, address, *, hosting, name, code, room_version, deliver, set_code): ...
        async def run(self) -> None   # connect, then exchange messages until the end
        def send(self, message: dict) -> bool
        def close(self) -> None

Rules every connector must follow (the game relies on them):
* Call deliver(dict) for every message the game should see, using the same
  message types as the relay ("status", "room", "joined", "peer_joined",
  "peer_left", "hello", "state", "action", "ack", ...).
* Call set_code(code) as soon as the room code is known.
* When the connection fails or ends unexpectedly, call
  deliver({"type": "disconnected", "text": <short reason>}) exactly once,
  unless close() was called first.
* Never block: run() is a coroutine on the service's asyncio loop.

To add a new method: write the class in a new module, then add its URL
scheme(s) to SCHEMES below. The game does not change.
"""
from __future__ import annotations

from .relay import RelayConnection

# The server players use unless they type a different address.
# This is the ONLY place the default server is defined. Moving the server
# means changing this line and shipping a new SolitaireNet.exe.
DEFAULT_ADDRESS = "tcp://yamanote.proxy.rlwy.net:40274"

SCHEMES = {
    "tcp": RelayConnection,   # relay server, plain TCP
    "tls": RelayConnection,   # relay server, TLS-encrypted TCP
}


def scheme_of(address: str) -> str:
    """'tls://host:1' -> 'tls'. An address without a scheme is plain TCP."""
    scheme, separator, _ = address.partition("://")
    return scheme.strip().lower() if separator else "tcp"


def create(address, *, hosting, name, code, room_version, deliver, set_code):
    """Build the connector for an address. Raises ValueError for unknown schemes."""
    address = (address or "").strip() or DEFAULT_ADDRESS
    scheme = scheme_of(address)
    connector = SCHEMES.get(scheme)
    if connector is None:
        supported = ", ".join(f"{name}://" for name in sorted(SCHEMES))
        raise ValueError(f"Unsupported server address type '{scheme}://' (supported: {supported})")
    return connector(address, hosting=hosting, name=name, code=code, room_version=room_version,
                     deliver=deliver, set_code=set_code)
