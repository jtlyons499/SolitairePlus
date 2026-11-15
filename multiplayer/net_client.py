"""The game's side of online play: talks to SolitaireNet.exe.

NetPeer behaves exactly like the old in-game RelayPeer, so the room and duel
code did not change:
    peer = open_peer(hosting, address, name, code, version)
    peer.send({...}) -> bool      queue a message for the other players
    peer.inbox                    queue.Queue of incoming dicts (read with get_nowait)
    peer.code                     the room code, filled in when the server assigns it
    peer.close()

All socket code lives in SolitaireNet.exe (netservice/), which this module
starts as a hidden child process and talks to over stdin/stdout pipes.
Never add socket code here or anywhere in the game; add a connector in
netservice/connectors/ instead (see docs/NETWORKING.md).
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from multiplayer_paths import ROOT

# Must equal netservice/protocol.py API_VERSION (tests/test_netservice.py checks this).
API_VERSION = 1

SERVICE_EXE = "SolitaireNet.exe"
MISSING_TEXT = "Online play component (SolitaireNet.exe) is missing. Run the updater or reinstall."
STOPPED_TEXT = "Online play component stopped unexpectedly."
MISMATCH_TEXT = "Online play component is a different version. Run the updater."


def service_command() -> list[str]:
    """How to start the service: the packaged exe, or `python -m netservice` from source."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve().parent / SERVICE_EXE
        if not exe.is_file():
            raise FileNotFoundError(str(exe))
        return [str(exe)]
    return [sys.executable, "-m", "netservice"]


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    if getattr(sys, "frozen", False):
        # Same reason as multiplayer_launcher: a frozen child must not inherit our bootloader state.
        env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return env


class NetPeer:
    def __init__(self, hosting, address, name, code="", version=1, command=None):
        self.hosting = bool(hosting)
        self.name = name
        self.code = str(code or "").strip().upper()
        self.version = version
        self.inbox: queue.Queue = queue.Queue()
        self.closed = threading.Event()
        self.service_info: dict = {}
        self._write_lock = threading.Lock()
        self.process = None
        try:
            self.process = subprocess.Popen(
                command or service_command(), cwd=str(ROOT), env=_child_env(),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError:
            self.closed.set()
            self.inbox.put({"type": "disconnected", "text": MISSING_TEXT})
            return
        threading.Thread(target=self._read_events, daemon=True, name="netservice-reader").start()
        self._write({"op": "hello", "api": API_VERSION})
        self._write({"op": "open", "address": (address or "").strip() or None, "hosting": self.hosting,
                     "name": name, "code": self.code, "room_version": version})

    # ------------------------------------------------------------ public API (same as RelayPeer)
    def send(self, message) -> bool:
        if self.closed.is_set():
            return False
        return self._write({"op": "send", "msg": message})

    def close(self) -> None:
        if self.closed.is_set():
            return
        self.closed.set()
        self._write({"op": "close"})
        process = self.process
        if process is None:
            return
        try:
            process.stdin.close()  # end-of-input tells the service to exit
        except OSError:
            pass
        # Never block the game window: give the service a moment, then make sure it is gone.
        threading.Thread(target=_reap, args=(process,), daemon=True, name="netservice-reaper").start()

    # ------------------------------------------------------------ internals
    def _write(self, request: dict) -> bool:
        process = self.process
        if process is None:
            return False
        line = (json.dumps(request, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
        with self._write_lock:
            try:
                process.stdin.write(line)
                process.stdin.flush()
                return True
            except (OSError, ValueError):
                return False

    def _read_events(self) -> None:
        stdout = self.process.stdout
        try:
            for raw in iter(stdout.readline, b""):
                try:
                    event = json.loads(raw.decode("utf-8"))
                except ValueError:
                    continue
                if isinstance(event, dict):
                    self._handle(event)
        except (OSError, ValueError):
            pass
        if not self.closed.is_set():
            self.closed.set()
            self.inbox.put({"type": "disconnected", "text": STOPPED_TEXT})

    def _handle(self, event: dict) -> None:
        kind = event.get("ev")
        if kind == "msg" and isinstance(event.get("msg"), dict):
            self.inbox.put(event["msg"])
        elif kind == "code":
            self.code = str(event.get("code", ""))
        elif kind == "hello":
            self.service_info = event
            if event.get("api") != API_VERSION:
                self.inbox.put({"type": "disconnected", "text": MISMATCH_TEXT})
                self.close()
        elif kind == "error":
            self.inbox.put({"type": "disconnected", "text": str(event.get("text", "Network error"))[:100]})


def _reap(process) -> None:
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


def open_peer(hosting, address, name, code="", version=1):
    """Start an online connection. address None/"" = the default server.

    SOLITAIRE_NET_INPROCESS=1 (set only by tools/run_tests.py) runs the same
    connector code inside this process instead of starting SolitaireNet.exe.
    """
    if os.environ.get("SOLITAIRE_NET_INPROCESS") == "1":
        from relay_transport import RelayPeer
        return RelayPeer(hosting, address or None, name, code, version)
    return NetPeer(hosting, address, name, code, version)
