"""WebSocket listener for the relay server (wss:// for players, through Railway's HTTPS address).

Runs next to the plain-TCP listener in the same process and shares the same
rooms, so players on wss:// and on the old tcp:// address can be in one room.
Each WebSocket is wrapped to look like the (reader, writer) pair that
RelayServer.handle already understands: one WebSocket message = one line.

Railway (or any HTTPS proxy) ends the TLS encryption and passes the player's
address in the X-Forwarded-For header, which the guessing protection uses.
"""
import asyncio

from websockets.asyncio.server import serve
from websockets.exceptions import ConnectionClosed

from relay_server import MAX_LINE


class WebSocketStream:
    def __init__(self, websocket, trust_forwarded_for=True):
        self.websocket = websocket
        self.trust_forwarded_for = trust_forwarded_for
        self._pending = []
        self._lock = asyncio.Lock()

    async def readline(self):
        try:
            message = await self.websocket.recv()
        except ConnectionClosed:
            return b''
        data = message.encode('utf-8') if isinstance(message, str) else message
        if len(data) > MAX_LINE:
            raise ValueError('Message too large')
        return data.rstrip(b'\n') + b'\n'

    def write(self, data):
        self._pending.append(data)

    async def drain(self):
        async with self._lock:
            while self._pending:
                line = self._pending.pop(0).rstrip(b'\n').decode('utf-8')
                try:
                    await self.websocket.send(line)
                except ConnectionClosed:
                    raise ConnectionResetError('Player disconnected') from None

    def close(self):
        asyncio.ensure_future(self.websocket.close())

    async def wait_closed(self):
        await self.websocket.wait_closed()

    def get_extra_info(self, name, default=None):
        if name != 'peername':
            return default
        if self.trust_forwarded_for:
            forwarded = self.websocket.request.headers.get('X-Forwarded-For', '') if self.websocket.request else ''
            first = forwarded.split(',')[0].strip()
            if first:
                return (first, 0)
        return self.websocket.remote_address or default


async def serve_websockets(relay, host, port, trust_forwarded_for=True):
    """Start the WebSocket listener; returns the server object."""
    async def handler(websocket):
        stream = WebSocketStream(websocket, trust_forwarded_for)
        await relay.handle(stream, stream)

    return await serve(handler, host, port, max_size=MAX_LINE, ping_interval=20, ping_timeout=20)
