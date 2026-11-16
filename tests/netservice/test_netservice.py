"""netservice/ (SolitaireNet.exe): protocol handling and the relay connector.

Each connector test runs a tiny fake relay server on 127.0.0.1 inside the
test, so no internet connection is needed.
"""
import asyncio
import io
import json
import re
import unittest
from pathlib import Path
from unittest import mock

from netservice import connectors
from netservice.connectors import relay
from netservice.connectors.relay import RelayConnection, parse_address
from netservice.protocol import API_VERSION
from netservice.service import Service

ROOT = Path(__file__).resolve().parents[2]


def run_against(handler, seconds=5, before_run=None, **options):
    """Run one RelayConnection against a fake server. Returns (delivered, codes, server_lines)."""
    delivered, codes, server_lines = [], [], []

    async def scenario():
        async def serve(reader, writer):
            try:
                await handler(reader, writer, server_lines)
            finally:
                writer.close()

        server = await asyncio.start_server(serve, '127.0.0.1', 0)
        port = server.sockets[0].getsockname()[1]
        settings = dict(hosting=True, name='Tester', code='', room_version=2)
        settings.update(options)
        connection = RelayConnection(f'tcp://127.0.0.1:{port}', deliver=delivered.append,
                                     set_code=codes.append, **settings)
        if before_run:
            before_run(connection)
        try:
            await asyncio.wait_for(connection.run(), seconds)
        finally:
            server.close()
            await server.wait_closed()

    asyncio.run(scenario())
    return delivered, codes, server_lines


async def read_lines(reader, sink, count):
    for _ in range(count):
        line = await reader.readline()
        if not line:
            return
        sink.append(json.loads(line))


async def send(writer, message):
    writer.write((json.dumps(message) + '\n').encode())
    await writer.drain()


class AddressTests(unittest.TestCase):
    def test_address_forms(self):
        self.assertEqual(parse_address('tcp://example.com:40274'), ('example.com', 40274, False))
        self.assertEqual(parse_address('tls://example.com:443'), ('example.com', 443, True))
        self.assertEqual(parse_address('example.com:1234'), ('example.com', 1234, False))
        self.assertEqual(parse_address('example.com'), ('example.com', 50008, False))

    def test_empty_address_means_default_server_and_unknown_types_are_rejected(self):
        made = connectors.create(None, hosting=True, name='a', code='', room_version=1,
                                 deliver=print, set_code=print)
        self.assertEqual(made.address, connectors.DEFAULT_ADDRESS)
        with self.assertRaises(ValueError):
            connectors.create('carrierpigeon://x:1', hosting=True, name='a', code='', room_version=1,
                              deliver=print, set_code=print)

    def test_game_and_service_agree_on_the_api_version(self):
        source = (ROOT / 'multiplayer' / 'net_client.py').read_text(encoding='utf-8')
        game_api = int(re.search(r'^API_VERSION = (\d+)', source, re.MULTILINE).group(1))
        self.assertEqual(game_api, API_VERSION)


class RelayConnectorTests(unittest.TestCase):
    def test_room_code_status_and_room_message_are_delivered(self):
        async def handler(reader, writer, lines):
            await read_lines(reader, lines, 1)
            await send(writer, {'type': 'room', 'code': '12345', 'identity': 0})
            await send(writer, {'type': 'pong'})
        delivered, codes, lines = run_against(handler)
        self.assertEqual(lines[0], {'type': 'create', 'version': 2, 'code': '', 'name': 'Tester', 'codes': 2})
        self.assertEqual(codes, ['12345'])
        self.assertEqual(delivered[0]['type'], 'status')
        self.assertEqual(delivered[1], {'type': 'room', 'code': '12345', 'identity': 0})
        self.assertEqual(delivered[-1]['type'], 'disconnected')  # server then hung up
        self.assertNotIn('pong', [m['type'] for m in delivered])

    def test_malformed_server_reply_disconnects_instead_of_hanging(self):
        async def handler(reader, writer, lines):
            await read_lines(reader, lines, 1)
            await send(writer, {'type': 'room'})        # no code
            await reader.read()                          # keep the socket open until the client leaves
        delivered, codes, _ = run_against(handler)
        self.assertEqual(codes, [])
        self.assertEqual(delivered[-1]['type'], 'disconnected')

    def test_silent_server_is_detected_by_the_watchdog(self):
        async def handler(reader, writer, lines):
            await read_lines(reader, lines, 1)
            await reader.read()                          # never answers, not even pings
        with mock.patch.object(relay, 'WATCHDOG_SECONDS', 0.4):
            delivered, _, _ = run_against(handler)
        self.assertIn('Lost contact', delivered[-1]['text'])

    def test_server_error_is_reported(self):
        async def handler(reader, writer, lines):
            await read_lines(reader, lines, 1)
            await send(writer, {'type': 'error', 'text': 'Room not found'})
        delivered, _, _ = run_against(handler, hosting=False, code='99999')
        self.assertEqual(delivered[-1], {'type': 'disconnected', 'text': 'Room not found'})

    def test_paired_triggers_hello_version_1(self):
        async def handler(reader, writer, lines):
            await read_lines(reader, lines, 1)
            await send(writer, {'type': 'paired'})
            await read_lines(reader, lines, 1)
        _, _, lines = run_against(handler, room_version=1)
        self.assertEqual(lines[1], {'type': 'hello', 'version': 1, 'name': 'Tester'})

    def test_many_queued_messages_are_all_sent_in_order(self):
        # The old transport silently dropped messages after 32 were waiting.
        async def handler(reader, writer, lines):
            await read_lines(reader, lines, 201)

        def queue_before_connecting(connection):
            for number in range(200):
                connection.send({'type': 'action', 'n': number})
        _, _, lines = run_against(handler, before_run=queue_before_connecting)
        self.assertEqual(lines[0]['type'], 'create')
        self.assertEqual([m['n'] for m in lines[1:]], list(range(200)))

    def test_close_is_quiet(self):
        async def handler(reader, writer, lines):
            await reader.read()
        delivered, _, _ = run_against(handler, before_run=lambda c: c.close())
        self.assertEqual(delivered, [])


class ServiceProtocolTests(unittest.TestCase):
    def run_service(self, *requests):
        stdin = io.BytesIO(b''.join(r if isinstance(r, bytes) else (json.dumps(r) + '\n').encode()
                                    for r in requests))
        stdout = io.BytesIO()
        asyncio.run(asyncio.wait_for(Service(stdin, stdout).run(), 10))
        return [json.loads(line) for line in stdout.getvalue().splitlines()]

    def test_hello_reports_api_version_and_connectors(self):
        reply = self.run_service({'op': 'hello', 'api': 1})[0]
        self.assertEqual(reply['ev'], 'hello')
        self.assertEqual(reply['api'], API_VERSION)
        self.assertEqual(reply['default_address'], connectors.DEFAULT_ADDRESS)
        self.assertIn('tls', reply['connectors'])

    def test_bad_requests_get_errors_not_crashes(self):
        events = self.run_service(b'not json\n', {'op': 'dance'}, {'op': 'send', 'msg': {'type': 'x'}})
        self.assertEqual([e['ev'] for e in events], ['error', 'error', 'error'])

    def test_unsupported_address_disconnects_cleanly(self):
        events = self.run_service({'op': 'open', 'address': 'carrierpigeon://x:1', 'hosting': True})
        self.assertEqual(events[0]['ev'], 'msg')
        self.assertEqual(events[0]['msg']['type'], 'disconnected')
        self.assertEqual(events[1]['ev'], 'closed')


if __name__ == '__main__':
    unittest.main()
