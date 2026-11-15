"""WebSocket connector: wss://host/path (encrypted) and ws://host:port/path (testing only).

Same relay protocol as relay.py; only the transport differs. Each WebSocket
text message carries exactly one JSON message. Why this exists:
* wss:// is encrypted (TLS), so names and chat are private on the internet.
* It is ordinary HTTPS on port 443, like a website: no port forwarding or
  firewall changes for players, and it gets through networks that block
  unusual ports. Railway provides the HTTPS address and certificate for free.
The relay server side is multiplayer/relay_websocket.py.
"""
from __future__ import annotations

import asyncio

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake, InvalidURI

from ..protocol import MAX_LINE
from .relay import RelayConnection


class _WebSocketStream:
    """Gives a WebSocket the small reader/writer interface RelayConnection uses (one message = one line)."""

    def __init__(self, websocket):
        self.websocket = websocket
        self._pending: list[bytes] = []
        self._lock = asyncio.Lock()

    # reader side
    async def readline(self) -> bytes:
        try:
            message = await self.websocket.recv()
        except ConnectionClosed:
            return b""  # same as a closed TCP connection
        data = message.encode("utf-8") if isinstance(message, str) else message
        if len(data) > MAX_LINE:
            raise ValueError("Message too large")
        return data.rstrip(b"\n") + b"\n"

    # writer side
    def write(self, data: bytes) -> None:
        self._pending.append(data)

    async def drain(self) -> None:
        async with self._lock:  # keep messages in order even if two senders drain at once
            while self._pending:
                line = self._pending.pop(0).rstrip(b"\n").decode("utf-8")
                try:
                    await self.websocket.send(line)
                except ConnectionClosed:
                    raise ConnectionError("Relay disconnected") from None

    def close(self) -> None:
        asyncio.ensure_future(self.websocket.close())

    async def wait_closed(self) -> None:
        await self.websocket.wait_closed()


class WebSocketConnection(RelayConnection):
    async def _open(self):
        try:
            websocket = await connect(self.address, max_size=MAX_LINE, open_timeout=None,
                                      user_agent_header="SolitairePlus")
        except InvalidURI:
            raise ValueError("The server address is not a valid ws:// or wss:// address") from None
        except InvalidHandshake as error:
            raise ConnectionError(f"The server refused the connection ({error.__class__.__name__})") from None
        stream = _WebSocketStream(websocket)
        return stream, stream
