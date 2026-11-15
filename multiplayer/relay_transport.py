"""In-process connection, kept for tests and the old LAN-era OnlineTable.

The real game does not use this: online play goes through SolitaireNet.exe
via net_client.open_peer(). This wrapper runs the SAME connector code
(netservice/connectors/) on a background thread inside the current process,
so tests can exercise room logic without starting a child process for every
player. tools/run_tests.py turns this on by setting SOLITAIRE_NET_INPROCESS=1;
the child-process path has its own tests (multiplayer/tests/test_net_client.py).

Interface (unchanged from the old RelayPeer): send(dict) -> bool, inbox
(queue.Queue), code, close().
"""
import asyncio
import queue
import sys
import threading
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.append(_ROOT)

from netservice import connectors  # noqa: E402


class RelayPeer:
    def __init__(self, hosting, address, name, code='', version=1):
        self.version = version
        self.hosting = hosting
        self.address = address
        self.name = name
        self.code = (code or '').strip().upper()
        self.inbox = queue.Queue()
        self.closed = threading.Event()
        self._loop = asyncio.new_event_loop()
        self._connection = None
        self._ready = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._ready.wait(5)

    def _set_code(self, code):
        self.code = code

    def _run(self):
        asyncio.set_event_loop(self._loop)
        try:
            try:
                self._connection = connectors.create(
                    self.address, hosting=self.hosting, name=self.name, code=self.code,
                    room_version=self.version, deliver=self.inbox.put, set_code=self._set_code)
            except ValueError as error:
                self.inbox.put({'type': 'disconnected', 'text': str(error)[:100]})
                return
            self._ready.set()
            self._loop.run_until_complete(self._connection.run())
        finally:
            self._ready.set()
            self.closed.set()
            self._loop.close()

    def send(self, message):
        if self.closed.is_set() or self._connection is None:
            return False
        try:
            self._loop.call_soon_threadsafe(self._connection.send, message)
            return True
        except RuntimeError:  # loop already finished
            return False

    def close(self):
        if self._connection is not None and not self.closed.is_set():
            try:
                self._loop.call_soon_threadsafe(self._connection.close)
            except RuntimeError:
                pass
