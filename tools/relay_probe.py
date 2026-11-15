"""Check which relay server version is actually running (e.g. on Railway).

    python tools/relay_probe.py                       # the game's default server
    python tools/relay_probe.py tcp://host:port       # any server
    python tools/relay_probe.py wss://host/           # the WebSocket address

What it does: opens one room like a host would, looks at the room code it
gets, then sends one message that only up-to-date relays accept, and closes.
The room disappears as soon as the probe disconnects. Nothing else changes.

It answers the questions in docs/RAILWAY_DEPLOY.md:
  * Can the server be reached at all?
  * Does it hand out 6-character codes (0.0.7+ relay) or 5-digit / 8-letter codes (older)?
  * Does it accept the party-game messages (Score Four, Blind Man's Bluff, Roulette)?
"""
from __future__ import annotations

import queue
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "multiplayer"), str(ROOT)]

from netservice.connectors import DEFAULT_ADDRESS  # noqa: E402
from relay_transport import RelayPeer  # noqa: E402


def wait_for(peer, kinds, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            message = peer.inbox.get(timeout=0.1)
        except queue.Empty:
            continue
        if message.get("type") in kinds:
            return message
    return None


def describe_code(code: str) -> str:
    if len(code) == 6 and code.isalnum():
        return "6 characters - current relay (0.0.7 or newer)"
    if len(code) == 5 and code.isdigit():
        return "5 digits - relay from before 0.0.7 (or one that ignored our request for long codes)"
    if len(code) == 8:
        return "8 characters - the OLD relay from the SolitaireMultiplayer repository; today's game cannot join its rooms"
    return f"{len(code)} characters - unknown relay version"


def main(argv: list[str]) -> int:
    address = argv[0] if argv else DEFAULT_ADDRESS
    print(f"Probing relay at {address} ...")
    peer = RelayPeer(True, address, "relay-probe", version=2)
    try:
        room = wait_for(peer, {"room", "disconnected"}, 15)
        if room is None:
            print("RESULT: no answer within 15 seconds. The server is down, asleep, or the address is wrong.")
            return 2
        if room["type"] == "disconnected":
            print(f"RESULT: could not open a room: {room.get('text')}")
            return 2
        print(f"Room code received: {room['code']}  ->  {describe_code(room['code'])}")

        peer.send({"type": "party_state", "target": 999, "phase": "probe"})
        refusal = wait_for(peer, {"disconnected"}, 3)
        if refusal and "Invalid host message" in str(refusal.get("text")):
            print("Party games: NOT supported. This relay rejects party-game messages, so hosting Score Four,")
            print("             Blind Man's Bluff or Roulette disconnects the host. Redeploy from this repository.")
            party_ok = False
        elif refusal:
            print(f"Party games: unclear - the relay closed the room: {refusal.get('text')}")
            party_ok = False
        else:
            print("Party games: supported.")
            party_ok = True
        current = len(room["code"]) == 6 and party_ok
        print("RESULT: " + ("this relay is up to date." if current else
                            "this relay is OUT OF DATE - see docs/RAILWAY_DEPLOY.md."))
        return 0 if current else 1
    finally:
        peer.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
