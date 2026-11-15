"""Relay server room codes and protection against guessing them (relay_server.py, room_relay.py)."""
import asyncio
import json
import unittest
from unittest import mock

import relay_server
from relay_server import CODE_ALPHABET, RelayServer


async def talk(port, request, extra=()):
    """Open one connection, send the first request (+ extra lines), return the first reply."""
    reader, writer = await asyncio.open_connection('127.0.0.1', port)
    for message in (request, *extra):
        writer.write((json.dumps(message) + '\n').encode())
    await writer.drain()
    reply = json.loads(await asyncio.wait_for(reader.readline(), 10))
    return reply, writer


class RelayCodeTests(unittest.TestCase):
    def run_scenario(self, scenario):
        async def main():
            relay = RelayServer()
            server = await asyncio.start_server(relay.handle, '127.0.0.1', 0, limit=65536)
            port = server.sockets[0].getsockname()[1]
            writers = []
            try:
                return await scenario(port, writers)
            finally:
                for writer in writers:
                    writer.close()
                server.close()
        return asyncio.run(main())

    def test_new_clients_get_six_character_codes_without_look_alikes(self):
        async def scenario(port, writers):
            codes = []
            for version in (1, 2):
                reply, writer = await talk(port, {'type': 'create', 'version': version, 'name': 'H', 'codes': 2})
                writers.append(writer)
                codes.append(reply['code'])
            return codes
        for code in self.run_scenario(scenario):
            self.assertEqual(len(code), 6)
            self.assertTrue(set(code) <= set(CODE_ALPHABET))
            self.assertFalse(set(code) & set('01OI'))

    def test_older_clients_still_get_codes_they_can_type(self):
        async def scenario(port, writers):
            reply, writer = await talk(port, {'type': 'create', 'version': 2, 'name': 'Old'})
            writers.append(writer)
            return reply['code']
        code = self.run_scenario(scenario)
        self.assertEqual(len(code), 5)
        self.assertTrue(code.isdigit())

    def test_guessing_codes_is_slowed_and_then_refused_even_for_a_right_code(self):
        async def scenario(port, writers):
            host, writer = await talk(port, {'type': 'create', 'version': 2, 'name': 'H', 'codes': 2})
            writers.append(writer)
            wrong = []
            for _ in range(3):
                reply, w = await talk(port, {'type': 'join', 'version': 2, 'code': 'ZZZZZZ', 'name': 'G'})
                writers.append(w)
                wrong.append(reply['text'])
            right, w = await talk(port, {'type': 'join', 'version': 2, 'code': host['code'], 'name': 'G'})
            writers.append(w)
            return wrong, right
        with mock.patch.object(relay_server, 'FAILED_JOIN_LIMIT', 3), \
             mock.patch.object(relay_server, 'FAILED_JOIN_DELAY', 0.01):
            wrong, right = self.run_scenario(scenario)
        self.assertTrue(all('not found' in text for text in wrong))
        self.assertEqual(right['type'], 'error')
        self.assertIn('Too many wrong room codes', right['text'])

    def test_a_right_code_is_not_slowed_down(self):
        async def scenario(port, writers):
            host, writer = await talk(port, {'type': 'create', 'version': 2, 'name': 'H', 'codes': 2})
            writers.append(writer)
            started = asyncio.get_running_loop().time()
            reply, w = await talk(port, {'type': 'join', 'version': 2, 'code': host['code'].lower(), 'name': 'G'})
            writers.append(w)
            return reply, asyncio.get_running_loop().time() - started
        reply, seconds = self.run_scenario(scenario)
        self.assertEqual(reply['type'], 'joined')
        self.assertLess(seconds, relay_server.FAILED_JOIN_DELAY)


if __name__ == '__main__':
    unittest.main()
