"""Messages between the game and SolitaireNet.exe ("the service").

Transport: one JSON object per line (UTF-8), game -> service on the service's
stdin, service -> game on its stdout. One service process serves one
connection; the game starts a new process for each room it hosts or joins.

Game -> service ("op"):
    {"op": "hello", "api": 1}
    {"op": "open", "address": "tcp://host:port" | null, "hosting": true,
     "name": "Player", "code": "12345", "room_version": 1 | 2}
         address null/"" means "use the service's default server".
    {"op": "send", "msg": {...}}     a message for the other players
    {"op": "close"}                  hang up (closing stdin also does this)

Service -> game ("ev"):
    {"ev": "hello", "api": 1, "service_version": "1.0.0",
     "connectors": ["tcp", "tls"], "default_address": "tcp://..."}
    {"ev": "code", "code": "12345"}  the room code is known or changed
    {"ev": "msg", "msg": {...}}      put this dict in the game's inbox. These are
                                     exactly the dicts the old in-game
                                     RelayPeer put in its inbox, e.g.
                                     {"type": "status", "text": ...},
                                     {"type": "disconnected", "text": ...},
                                     plus every message relayed from other players.
    {"ev": "closed"}                 the connection has ended
    {"ev": "error", "text": "..."}   a bad request from the game

API_VERSION changes only when this contract changes incompatibly. The game
keeps its own copy of the number in multiplayer/net_client.py; a test checks
that both copies match.
"""
from __future__ import annotations

import json

API_VERSION = 1

# Largest single line in either direction, matching the relay server's limit.
MAX_LINE = 65536


def encode(message: dict) -> bytes:
    return (json.dumps(message, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def decode(raw: bytes) -> dict:
    """Parse one line. Raises ValueError for anything that is not a JSON object."""
    if len(raw) > MAX_LINE:
        raise ValueError("line too long")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    return value
