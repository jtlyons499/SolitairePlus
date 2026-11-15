"""Relay-server connector: tcp://host:port and tls://host:port.

This is the logic that used to live in multiplayer/relay_transport.py
(RelayPeer), moved here so networking changes no longer touch the game.
Behaviour is the same as before, with four fixes:
* A malformed server reply (e.g. a "room" message without a code) now
  disconnects cleanly. Before, it killed the network thread and left the game
  stuck on "Waiting for friend".
* A watchdog: if nothing at all arrives for WATCHDOG_SECONDS (the server
  answers our pings every PING_SECONDS), the connection is reported as lost.
* Outgoing messages are never silently dropped (the old queue held 32).
* Event-driven I/O (asyncio) instead of checking the socket every 50 ms.

Relay protocol summary (server code: multiplayer/relay_server.py, room_relay.py):
* First line we send: {"type": "create"|"join", "version": 1|2, "code", "name"}.
* "room" -> our room code (hosting). "paired" (version 1) -> we send "hello".
* "error" -> the server refused or closed the room. "pong" answers "ping".
"""
from __future__ import annotations

import asyncio
import json
import ssl

from ..protocol import MAX_LINE

DEFAULT_PORT = 50008
CONNECT_TIMEOUT = 8.0
SEND_TIMEOUT = 10.0
PING_SECONDS = 20.0
WATCHDOG_SECONDS = 45.0


def _line(message: dict) -> bytes:
    payload = (json.dumps(message, separators=(",", ":")) + "\n").encode()
    if len(payload) > MAX_LINE:
        raise ValueError("Message too large")
    return payload


def parse_address(address: str) -> tuple[str, int, bool]:
    """Return (host, port, use_tls) for 'tcp://h:p', 'tls://h:p', 'h:p' or 'h'."""
    address = address.strip()
    secure = address.lower().startswith("tls://")
    for prefix in ("tls://", "tcp://"):
        if address.lower().startswith(prefix):
            address = address[len(prefix):]
    host, separator, port = address.rpartition(":")
    if not separator:
        host, port = address, str(DEFAULT_PORT)
    host = host.strip("[]")
    if not host:
        raise ValueError("Server address is missing a host name")
    return host, int(port), secure


class RelayConnection:
    def __init__(self, address, *, hosting, name, code, room_version, deliver, set_code):
        self.address = address
        self.hosting = bool(hosting)
        self.name = name
        self.code = str(code or "").strip().upper()
        self.room_version = room_version
        self.deliver = deliver
        self.set_code = set_code
        self._outbox: asyncio.Queue = asyncio.Queue()   # unbounded on purpose
        self._stop = asyncio.Event()
        self._closed = False

    # ------------------------------------------------------------ public API
    def send(self, message) -> bool:
        if self._closed or not isinstance(message, dict):
            return False
        self._outbox.put_nowait(message)
        return True

    def close(self) -> None:
        self._closed = True
        self._stop.set()

    async def run(self) -> None:
        writer = None
        tasks = []
        try:
            host, port, secure = parse_address(self.address)
            context = ssl.create_default_context() if secure else None
            connect = asyncio.ensure_future(asyncio.wait_for(
                asyncio.open_connection(host, port, ssl=context, server_hostname=host if secure else None,
                                        limit=MAX_LINE + 1),
                CONNECT_TIMEOUT))
            stop = asyncio.ensure_future(self._stop.wait())
            await asyncio.wait({connect, stop}, return_when=asyncio.FIRST_COMPLETED)
            if self._closed:
                connect.cancel()
                stop.cancel()
                return
            stop.cancel()
            try:
                reader, writer = connect.result()
            except asyncio.TimeoutError:
                raise ConnectionError("Could not reach the server (timed out)") from None
            # The handshake must be the first line the server sees, even if the game
            # queued messages while we were still connecting.
            writer.write(_line({"type": "create" if self.hosting else "join", "version": self.room_version,
                                "code": self.code, "name": self.name}))
            tasks = [asyncio.ensure_future(job) for job in
                     (self._read_loop(reader), self._write_loop(writer), self._ping_loop(), self._stop.wait())]
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()  # re-raise the error that ended the connection, if any
        except asyncio.CancelledError:
            raise
        except (OSError, ValueError, UnicodeError, KeyError, TypeError, ConnectionError) as error:
            self._report(str(error) or error.__class__.__name__)
        finally:
            for task in tasks:
                task.cancel()
            if writer is not None:
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), 2)
                except (OSError, asyncio.TimeoutError, ssl.SSLError):
                    pass

    # ------------------------------------------------------------ internals
    def _report(self, text: str) -> None:
        if not self._closed:
            self._closed = True
            self.deliver({"type": "disconnected", "text": text[:100]})

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        while True:
            try:
                raw = await asyncio.wait_for(reader.readline(), WATCHDOG_SECONDS)
            except asyncio.TimeoutError:
                raise ConnectionError(f"Lost contact with the server (no reply for {int(WATCHDOG_SECONDS)} seconds)")
            if not raw or not raw.endswith(b"\n"):
                raise ConnectionError("Relay disconnected")
            if len(raw) > MAX_LINE:
                raise ValueError("Message too large")
            message = json.loads(raw)
            if not isinstance(message, dict):
                raise ValueError("Invalid relay message")
            self._handle(message)

    def _handle(self, message: dict) -> None:
        kind = message.get("type")
        if kind == "room":
            self.code = str(message["code"])  # KeyError -> clean disconnect
            self.set_code(self.code)
            self.deliver({"type": "status", "text": "Room " + self.code + " • Waiting for friend"})
            if self.room_version == 2:
                self.deliver(message)
        elif kind == "paired":
            self.send({"type": "hello", "version": 1, "name": self.name})
        elif kind == "error":
            raise ConnectionError(str(message.get("text", "Relay error")))
        elif kind != "pong":
            self.deliver(message)

    async def _write_loop(self, writer: asyncio.StreamWriter) -> None:
        while True:
            message = await self._outbox.get()
            writer.write(_line(message))
            try:
                await asyncio.wait_for(writer.drain(), SEND_TIMEOUT)
            except asyncio.TimeoutError:
                raise ConnectionError("The server stopped accepting data") from None

    async def _ping_loop(self) -> None:
        while True:
            await asyncio.sleep(PING_SECONDS)
            self.send({"type": "ping"})
