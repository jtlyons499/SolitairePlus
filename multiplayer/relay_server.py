"""Room relay: no poker rules or hidden-card state is stored here."""
import argparse
import asyncio
import collections
import json
import secrets
import ssl
import time

MAX_LINE = 65536

# Room codes. Clients from 0.0.7 on send "codes": 2 and get 6 characters from an alphabet
# without look-alikes (no 0/O, 1/I): about a billion possibilities. Older clients only let
# players type 5 digits, so they keep getting 5-digit codes until everyone has updated.
CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

# Guessing protection: every wrong room code costs the guesser a pause, and an address that
# gets too many wrong in a short time is told to wait. A correct code is never slowed down.
FAILED_JOIN_DELAY = 1.0
FAILED_JOIN_LIMIT = 10
FAILED_JOIN_WINDOW = 60.0


def new_room_code(rooms, request):
    long_codes = str(request.get('codes', '1')) == '2'
    while True:
        if long_codes:
            code = ''.join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        else:
            code = f'{secrets.randbelow(100000):05d}'
        if code not in rooms:
            return code


def client_address(writer):
    peer = writer.get_extra_info('peername')
    return peer[0] if isinstance(peer, (tuple, list)) and peer else 'unknown'

async def send(writer, message):
    writer.write((json.dumps(message, separators=(',', ':')) + '\n').encode())
    await asyncio.wait_for(writer.drain(), 10)

class RelayServer:
    def __init__(self):
        self.rooms = {}
        self.failed_joins = {}  # address -> deque of times a wrong code was tried

    def _recent_failures(self, address):
        now = time.monotonic()
        attempts = self.failed_joins.get(address)
        while attempts and now - attempts[0] > FAILED_JOIN_WINDOW:
            attempts.popleft()
        if attempts is not None and not attempts:
            del self.failed_joins[address]
            return 0
        return len(attempts or ())

    def check_join_allowed(self, writer):
        if self._recent_failures(client_address(writer)) >= FAILED_JOIN_LIMIT:
            raise ValueError('Too many wrong room codes. Wait a minute and try again.')

    async def record_failed_join(self, writer):
        address = client_address(writer)
        if len(self.failed_joins) > 10000:  # keep memory bounded if many addresses guess
            for key in list(self.failed_joins)[:5000]:
                self.failed_joins.pop(key, None)
        self.failed_joins.setdefault(address, collections.deque()).append(time.monotonic())
        await asyncio.sleep(FAILED_JOIN_DELAY)

    async def handle(self, reader, writer):
        room = None
        code = None
        role = None
        try:
            raw = await asyncio.wait_for(reader.readline(), 10)
            request = json.loads(raw)
            if isinstance(request, dict) and request.get('version') == 2:
                from room_relay import handle_room
                await handle_room(self, reader, writer, request)
                return
            if not isinstance(request, dict) or request.get('version') != 1:
                raise ValueError('Unsupported relay protocol')
            role = request.get('type')
            if role == 'create':
                if len(self.rooms) >= 500:
                    raise ValueError('Relay is full')
                code = new_room_code(self.rooms, request)
                room = {'host': writer, 'guest': None}
                self.rooms[code] = room
                await send(writer, {'type': 'room', 'code': code})
            elif role == 'join':
                self.check_join_allowed(writer)
                code = str(request.get('code', '')).upper().strip()
                room = self.rooms.get(code)
                if room is None or room.get('version') == 2:
                    await self.record_failed_join(writer)
                    raise ValueError('Room not found or uses a newer game version')
                if room['guest'] is not None:
                    raise ValueError('Room already has two players')
                room['guest'] = writer
                await send(room['host'], {'type': 'paired'})
                await send(writer, {'type': 'paired'})
            else:
                raise ValueError('Choose create or join')
            while True:
                raw = await asyncio.wait_for(reader.readline(), 900)
                if not raw:
                    break
                if len(raw) > MAX_LINE:
                    raise ValueError('Message too large')
                message = json.loads(raw)
                if not isinstance(message, dict):
                    raise ValueError('Invalid message')
                if message.get('type') == 'ping':
                    await send(writer, {'type': 'pong'})
                    continue
                allowed = {'hello', 'state', 'ack'} if role == 'create' else {'hello', 'action'}
                if message.get('type') not in allowed:
                    raise ValueError('Invalid room message')
                target = room['guest' if role == 'create' else 'host']
                if target is not None:
                    await send(target, message)
        except (ValueError, OSError, asyncio.TimeoutError) as error:
            try:
                await send(writer, {'type': 'error', 'text': str(error)[:100]})
            except (OSError, asyncio.TimeoutError):
                pass
        finally:
            # A rejected third join must never remove an existing room.
            if room and writer in (room['host'], room['guest']):
                self.rooms.pop(code, None)
                other = room['guest' if writer is room['host'] else 'host']
                if other:
                    try:
                        await send(other, {'type': 'error', 'text': 'Other player disconnected. Table paused; create a new room.'})
                    except (OSError, asyncio.TimeoutError):
                        pass
                    other.close()
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

async def serve(args):
    context = None
    if args.cert or args.key:
        if not (args.cert and args.key):
            raise ValueError('Supply both --cert and --key')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(args.cert, args.key)
    relay = RelayServer()
    server = await asyncio.start_server(relay.handle, args.bind, args.port, ssl=context, limit=MAX_LINE)
    print(f'Relay listening on {args.bind}:{args.port} ({"TLS" if context else "plain TCP"})', flush=True)
    listeners = [server.serve_forever()]
    if args.ws_port:
        # Same rooms as the TCP listener; players on either can meet (see relay_websocket.py).
        from relay_websocket import serve_websockets
        ws_server = await serve_websockets(relay, args.bind, args.ws_port)
        print(f'Relay listening for WebSocket players on {args.bind}:{args.ws_port}', flush=True)
        listeners.append(ws_server.serve_forever())
    async with server:
        await asyncio.gather(*listeners)


if __name__ == '__main__':
    import os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=50008, help='plain TCP port (Railway TCP proxy target)')
    parser.add_argument('--ws-port', type=int, default=int(os.environ.get('RELAY_WS_PORT') or 0) or None,
                        help="WebSocket port (Railway's HTTPS address forwards here); off when not given")
    parser.add_argument('--cert')
    parser.add_argument('--key')
    try:
        asyncio.run(serve(parser.parse_args()))
    except KeyboardInterrupt:
        pass
