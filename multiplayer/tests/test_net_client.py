"""The real game path: NetPeer -> SolitaireNet child process -> relay server.

These tests start `python -m netservice` as a child process for each player,
exactly as the game does from source (the packaged game starts
SolitaireNet.exe instead). The relay server runs inside the test process.
"""
import time
import unittest

import test_relay
from net_client import MISSING_TEXT, NetPeer


class NetClientTests(unittest.TestCase):
    # Reuse the in-process relay server fixture from test_relay.py.
    setUp = test_relay.RelayTests.setUp
    tearDown = test_relay.RelayTests.tearDown

    def wait(self, peer, kind, seconds=15):
        # Generous limit: each player starts a Python child process first.
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                message = peer.inbox.get(timeout=.05)
            except Exception:
                continue
            if message.get('type') == kind:
                return message
        self.fail('Timed out waiting for ' + kind)

    def peer(self, *args, **kwargs):
        peer = NetPeer(*args, **kwargs)
        self.peers.append(peer)
        return peer

    def test_two_players_pair_and_exchange_messages_through_the_service(self):
        host = self.peer(True, self.address, 'Host')
        self.assertIn('Waiting for friend', self.wait(host, 'status')['text'])
        self.assertEqual(len(host.code), 6)  # code arrives as a separate "code" event (6 characters since 0.0.7)
        guest = self.peer(False, self.address, 'Guest', host.code)
        self.assertEqual(self.wait(host, 'hello')['name'], 'Guest')
        self.assertEqual(self.wait(guest, 'hello')['name'], 'Host')
        guest.send({'type': 'action', 'action': 'fold', 'revision': 0})
        self.assertEqual(self.wait(host, 'action')['action'], 'fold')
        host.send({'type': 'state', 'revision': 2, 'text': 'héllo ♠'})
        self.assertEqual(self.wait(guest, 'state')['text'], 'héllo ♠')
        guest.close()
        self.assertIn('disconnected', self.wait(host, 'disconnected')['text'])

    def test_six_seat_room_codes_and_join_events(self):
        host = self.peer(True, self.address, 'Host', version=2)
        room = self.wait(host, 'room')
        self.assertEqual(room['identity'], 0)
        guest = self.peer(False, self.address, 'Guest', room['code'], version=2)
        self.assertEqual(self.wait(guest, 'joined')['code'], room['code'])
        self.assertEqual(self.wait(host, 'peer_joined')['name'], 'Guest')

    def test_service_reports_its_api_version(self):
        host = self.peer(True, self.address, 'Host')
        self.wait(host, 'status')
        self.assertEqual(host.service_info.get('api'), 1)
        self.assertIn('tcp', host.service_info.get('connectors', []))

    def test_unknown_address_type_is_a_clear_error(self):
        peer = self.peer(True, 'carrierpigeon://coop:1', 'Host')
        self.assertIn('Unsupported', self.wait(peer, 'disconnected')['text'])

    def test_missing_service_exe_is_reported_not_crashed(self):
        peer = self.peer(True, self.address, 'Host', command=[r'C:\does-not-exist\SolitaireNet.exe'])
        self.assertEqual(self.wait(peer, 'disconnected', 2)['text'], MISSING_TEXT)
        self.assertFalse(peer.send({'type': 'action'}))

    def test_close_ends_the_service_process(self):
        peer = self.peer(True, self.address, 'Host')
        self.wait(peer, 'status')
        peer.close()
        peer.process.wait(timeout=5)
        self.assertIsNotNone(peer.process.returncode)


class ConnectionSettingsTests(unittest.TestCase):
    """The default server must never be saved as if the player chose it."""

    def setUp(self):
        import tempfile
        from unittest import mock
        self.folder = tempfile.TemporaryDirectory()
        self.env = mock.patch.dict('os.environ', {'LOCALAPPDATA': self.folder.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.folder.cleanup()

    def test_old_saved_default_is_ignored_so_a_new_default_can_take_over(self):
        import json
        import connection_settings
        target = connection_settings.path()
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({'name': 'Ana', 'relay_address': 'tcp://yamanote.proxy.rlwy.net:40274'}))
        self.assertEqual(connection_settings.load(), {'name': 'Ana', 'relay_address': ''})

    def test_only_a_custom_address_is_saved(self):
        import json
        import connection_settings
        connection_settings.save('Ana', None)
        self.assertNotIn('relay_address', json.loads(connection_settings.path().read_text()))
        connection_settings.save('Ana', 'tls://my.server:443')
        self.assertEqual(connection_settings.load()['relay_address'], 'tls://my.server:443')


if __name__ == '__main__':
    unittest.main()
