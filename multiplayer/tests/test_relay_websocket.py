"""WebSocket play (ws:// here; wss:// online): the relay's WebSocket listener and the client connector.

Runs a real relay with BOTH listeners (TCP and WebSocket) in the test, and
checks that a WebSocket player and a TCP player can share a room.
"""
import asyncio
import queue
import threading
import time
import unittest

from net_client import NetPeer
from relay_server import RelayServer
from relay_transport import RelayPeer
from relay_websocket import serve_websockets


class RelayWebSocketTests(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        self.relay = RelayServer()

        async def start():
            tcp = await asyncio.start_server(self.relay.handle, '127.0.0.1', 0, limit=65536)
            ws = await serve_websockets(self.relay, '127.0.0.1', 0)
            return tcp, ws
        self.tcp, self.ws = asyncio.run_coroutine_threadsafe(start(), self.loop).result(5)
        self.tcp_address = '127.0.0.1:' + str(self.tcp.sockets[0].getsockname()[1])
        self.ws_address = 'ws://127.0.0.1:' + str(list(self.ws.sockets)[0].getsockname()[1]) + '/'
        self.peers = []

    def tearDown(self):
        for peer in self.peers:
            peer.close()

        async def stop():
            self.tcp.close()
            self.ws.close()
            await asyncio.sleep(.1)
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        asyncio.run_coroutine_threadsafe(stop(), self.loop).result(5)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)
        self.loop.close()

    def wait(self, peer, kind, seconds=10):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                message = peer.inbox.get(timeout=.05)
            except queue.Empty:
                continue
            if message.get('type') == kind:
                return message
        self.fail('Timed out waiting for ' + kind)

    def peer(self, *args, cls=RelayPeer, **kwargs):
        peer = cls(*args, **kwargs)
        self.peers.append(peer)
        return peer

    def test_websocket_and_tcp_players_share_a_room(self):
        host = self.peer(True, self.ws_address, 'Host', version=2)
        room = self.wait(host, 'room')
        self.assertEqual(len(room['code']), 6)
        guest = self.peer(False, self.tcp_address, 'Guest', room['code'], version=2)
        self.assertEqual(self.wait(guest, 'joined')['code'], room['code'])
        self.assertEqual(self.wait(host, 'peer_joined')['name'], 'Guest')
        guest.send({'type': 'action', 'action': 'chat', 'amount': 'hi ♠'})
        self.assertEqual(self.wait(host, 'action')['amount'], 'hi ♠')
        host.send({'type': 'lobby', 'target': 1, 'revision': 3})
        self.assertEqual(self.wait(guest, 'lobby')['revision'], 3)

    def test_two_player_duel_over_websocket(self):
        host = self.peer(True, self.ws_address, 'Host')
        self.wait(host, 'status')
        guest = self.peer(False, self.ws_address, 'Guest', host.code)
        self.assertEqual(self.wait(host, 'hello')['name'], 'Guest')
        guest.close()
        self.assertIn('disconnected', self.wait(host, 'disconnected')['text'])

    def test_real_service_process_connects_over_websocket(self):
        host = self.peer(True, self.ws_address, 'Host', version=2, cls=NetPeer)
        self.assertEqual(len(self.wait(host, 'room', 20)['code']), 6)
        self.assertIn('wss', host.service_info.get('connectors', []))

    def test_bad_websocket_address_is_a_clean_error(self):
        peer = self.peer(True, 'ws://127.0.0.1:1/', 'Host')
        self.assertEqual(self.wait(peer, 'disconnected')['type'], 'disconnected')


if __name__ == '__main__':
    unittest.main()
