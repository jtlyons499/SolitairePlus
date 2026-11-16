# How online play works

This page is for maintainers and AI coding assistants. It explains who talks to whom when people play online, where
each piece of code lives, and how to add a new way of connecting without touching the game.

## The big picture

```text
 Player A's PC                                   Railway (internet)                Player B's PC
┌──────────────────────────────┐                ┌──────────────────┐             ┌──────────────────────────────┐
│ SolitairePlus.exe            │                │  relay server    │             │ SolitairePlus.exe            │
│  └ Multiplayer window        │                │ (relay_server.py │             │  └ Multiplayer window        │
│     (game rules run here     │  stdin/stdout  │  + room_relay.py)│             │     (shows the host's view)  │
│      when A is the host)     │◄──────────────►│                  │             │                              │
│  └ SolitaireNet.exe ─────────┼──── TCP ──────►│ forwards messages│◄──── TCP ───┼─ SolitaireNet.exe            │
└──────────────────────────────┘    (outbound)  │ by room code     │  (outbound) └──────────────────────────────┘
                                                └──────────────────┘
```

1. **The host's game is the referee.** When a player clicks Host, their Multiplayer window runs the real game rules
   (dealing, bets, NPCs) in `multiplayer/room_table.py` and `multiplayer/party_authority.py`.
2. **The relay server only forwards messages.** It hands out a room code, then passes messages between the host and
   the guests in that room. It stores no game state and runs no rules. Its code is `multiplayer/relay_server.py` and
   `multiplayer/room_relay.py`, and it runs on Railway, not on players' PCs.
3. **Players never connect to each other directly.** Every PC makes an *outgoing* connection to the relay. That's
   why nobody needs port forwarding or firewall rules.
4. **All internet code lives in `SolitaireNet.exe`.** The Multiplayer window starts it as a hidden child process and
   talks to it through pipes (stdin/stdout). It only makes outgoing connections and never accepts connections from
   other computers, which is what triggers Windows Firewall prompts.

## Where the code lives

| Piece | Files | Runs on | Changing it requires |
|---|---|---|---|
| Network service (`SolitaireNet.exe`) | `netservice/` | players' PCs | a new `SolitaireNet.exe` (the game exe is untouched) |
| Game's network client | `multiplayer/net_client.py` | players' PCs | an update to the loose `multiplayer\` files |
| Room logic, game rules, screens | `multiplayer/room_session.py`, `room_table.py`, `party_authority.py`, `*_view.py` | players' PCs | an update to the loose `multiplayer\` files |
| Relay server | `multiplayer/relay_server.py`, `multiplayer/room_relay.py`, `multiplayer/relay_websocket.py` | Railway | a redeploy on Railway only (see `docs/RAILWAY_DEPLOY.md`) |
| Default server address | `netservice/connectors/__init__.py` → `DEFAULT_ADDRESS` | players' PCs | a new `SolitaireNet.exe` |

## Connection types available today

| Address | Connector | Notes |
|---|---|---|
| `tcp://host:port` | `connectors/relay.py` | The original plain connection (not encrypted). The current default. |
| `tls://host:port` | `connectors/relay.py` | Encrypted TCP. Needs the relay started with `--cert/--key`. |
| `wss://host/` | `connectors/websocket.py` | Encrypted WebSocket through an HTTPS address (Railway provides one for free). Recommended next default; see `docs/RAILWAY_DEPLOY.md` Part 4. |
| `ws://host:port/` | `connectors/websocket.py` | Unencrypted WebSocket, for local testing only. |

The relay runs a TCP listener and, with `--ws-port` or `RELAY_WS_PORT`, a WebSocket listener in the same process.
Both share the same rooms, so players on different connection types can play together.

**Room codes:** clients send `"codes": 2` when creating a room and get 6 characters from `CODE_ALPHABET` (no 0/O, 1/I).
Older clients get 5 digits. Every wrong code costs the guesser a 1-second pause, and 10 wrong codes in a minute
from one address are refused for a while (`relay_server.py`: `FAILED_JOIN_*`).

**Is the live relay current?** `python tools/relay_probe.py [address]` (see `docs/RAILWAY_DEPLOY.md`).

## The game ↔ service contract

`multiplayer/net_client.py` (`NetPeer`) gives the room code the same small interface the old in-game transport had:

```python
peer = open_peer(hosting, address, name, code, version)  # address None = default server
peer.send({...})        # -> True if queued
peer.inbox.get_nowait() # incoming dicts, e.g. {"type": "status", "text": ...}
peer.code               # room code once the server assigns it
peer.close()
```

Underneath, it exchanges one JSON object per line with the service. The full list is in `netservice/protocol.py`.
In short:

* **Game → service:** `hello`, `open` (address, hosting, name, code, room_version), `send` (a message), `close`.
* **Service → game:** `hello` (API version, available connectors, default address), `code`, `msg` (goes straight
  into `peer.inbox`), `closed`, `error`.

`API_VERSION` exists in two places, `netservice/protocol.py` and `multiplayer/net_client.py`, and
`tests/test_netservice.py` fails if they differ. Change it only for an incompatible protocol change. If the
versions don't match, the game tells the player to run the updater.

## Adding a new way to connect (a "connector")

Example: a WebSocket relay at `wss://relay.example.com`.

1. Create `netservice/connectors/websocket.py` with a class shaped like `RelayConnection` in `relay.py`:
   `__init__(address, *, hosting, name, code, room_version, deliver, set_code)`, `async run()`, `send(dict)`, and
   `close()`.
2. Follow the rules at the top of `netservice/connectors/__init__.py`:
   * Deliver the same message types the relay produces.
   * Call `set_code` when the room code is known.
   * Deliver exactly one `{"type": "disconnected", "text": ...}` when the connection fails, unless `close()` was
     called first.
   * Never block the asyncio loop.
3. Register the URL scheme in `SCHEMES` in `netservice/connectors/__init__.py`, e.g. `"wss": WebSocketConnection`.
4. If it should become the default, change `DEFAULT_ADDRESS`.
5. Add tests to `tests/test_netservice.py` using a fake local server (see the existing relay tests).
6. Bump `netservice.__version__` in `netservice/__init__.py`.

The game doesn't change: players get the new connection method through an update that replaces `SolitaireNet.exe`.

## Things that look odd but are on purpose

* **`connection.json` doesn't store the default server.** `%LOCALAPPDATA%\SolitaireMultiplayer\connection.json`
  only stores a server address the player typed themselves. Older versions saved the default address there every
  time, which would have kept players on an old server forever. `multiplayer/connection_settings.py` ignores those
  old saved defaults.
* **`multiplayer/relay_transport.py` still exists.** It runs the same connector code inside the current process. Only
  the tests use it (set by `tools/run_tests.py` via `SOLITAIRE_NET_INPROCESS=1`), so room tests can connect
  `RoomTable` clients to a local test relay without starting a `SolitaireNet` child process per player. The shipped
  game always uses `SolitaireNet.exe`. (The old LAN table and the offline Practice table were removed in Phase 11;
  online play is rooms only.)
* **The service checks the connection is alive.** It sends a ping every 20 seconds, and if nothing at all comes back
  for 45 seconds it reports "Lost contact with the server". Before, a silently dropped connection could leave a
  player waiting forever.
* **Crash logs:** if `SolitaireNet.exe` itself crashes, the details are written to
  `%LOCALAPPDATA%\SimpleSolitaire\logs\netservice.log` (only the latest crash is kept).

## Rules for AI assistants

* Never put `socket`, `ssl`, `asyncio` networking, or HTTP code in the game or in `multiplayer/`. It belongs in
  `netservice/connectors/`.
* Don't hard-code a server address anywhere except `DEFAULT_ADDRESS`.
* Keep `netservice/` free of game imports (pygame, game modules). It must stay small and independent so it can be
  updated on its own.
