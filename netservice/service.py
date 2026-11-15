"""The SolitaireNet.exe main loop: read requests on stdin, answer on stdout.

See protocol.py for the message format. Runs one connection at a time and
exits when the game closes its end of stdin (or the game process ends).
"""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import traceback
from pathlib import Path

from . import __version__
from . import connectors
from .protocol import API_VERSION, decode, encode


class Service:
    def __init__(self, stdin=None, stdout=None):
        self.stdin = stdin if stdin is not None else sys.stdin.buffer
        self.stdout = stdout if stdout is not None else sys.stdout.buffer
        self.connection = None
        self.connection_task = None
        self.lines: asyncio.Queue | None = None

    # ------------------------------------------------------------ output
    def emit(self, event: dict) -> None:
        try:
            self.stdout.write(encode(event))
            self.stdout.flush()
        except (OSError, ValueError):
            pass  # the game is gone; stdin EOF will end the service

    def deliver(self, message: dict) -> None:
        self.emit({"ev": "msg", "msg": message})

    def set_code(self, code: str) -> None:
        self.emit({"ev": "code", "code": code})

    # ------------------------------------------------------------ input
    def _read_stdin(self, loop: asyncio.AbstractEventLoop) -> None:
        """Blocking reads on a helper thread, handed to the asyncio loop."""
        try:
            for raw in iter(self.stdin.readline, b""):
                loop.call_soon_threadsafe(self.lines.put_nowait, raw)
        except (OSError, ValueError):
            pass
        finally:
            try:
                loop.call_soon_threadsafe(self.lines.put_nowait, None)
            except RuntimeError:
                pass  # loop already closed

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        self.lines = asyncio.Queue()
        threading.Thread(target=self._read_stdin, args=(loop,), daemon=True, name="stdin").start()
        while True:
            raw = await self.lines.get()
            if raw is None:
                break
            if raw.strip():
                self.handle(raw)
        await self.shutdown()

    async def shutdown(self) -> None:
        if self.connection is not None:
            self.connection.close()
        if self.connection_task is not None:
            try:
                await asyncio.wait_for(self.connection_task, 3)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass

    # ------------------------------------------------------------ requests
    def handle(self, raw: bytes) -> None:
        try:
            request = decode(raw)
        except ValueError as error:
            self.emit({"ev": "error", "text": f"Bad request: {error}"[:200]})
            return
        op = request.get("op")
        if op == "hello":
            self.emit({"ev": "hello", "api": API_VERSION, "service_version": __version__,
                       "connectors": sorted(connectors.SCHEMES), "default_address": connectors.DEFAULT_ADDRESS})
        elif op == "open":
            self.open(request)
        elif op == "send":
            message = request.get("msg")
            if self.connection is None or not isinstance(message, dict):
                self.emit({"ev": "error", "text": "Nothing to send to: no open connection"})
            else:
                self.connection.send(message)
        elif op == "close":
            if self.connection is not None:
                self.connection.close()
        else:
            self.emit({"ev": "error", "text": f"Unknown request {str(op)[:40]!r}"})

    def open(self, request: dict) -> None:
        if self.connection is not None:
            self.emit({"ev": "error", "text": "A connection is already open"})
            return
        try:
            self.connection = connectors.create(
                request.get("address"),
                hosting=bool(request.get("hosting")),
                name=str(request.get("name") or "Player")[:32],
                code=str(request.get("code") or ""),
                room_version=int(request.get("room_version") or 1),
                deliver=self.deliver,
                set_code=self.set_code,
            )
        except (ValueError, TypeError) as error:
            self.deliver({"type": "disconnected", "text": str(error)[:100]})
            self.emit({"ev": "closed"})
            return
        self.connection_task = asyncio.ensure_future(self._run_connection())

    async def _run_connection(self) -> None:
        try:
            await self.connection.run()
        except Exception as error:  # a connector bug must still end in a clean disconnect
            write_crash_log(traceback.format_exc())
            self.deliver({"type": "disconnected", "text": f"Network error: {error}"[:100]})
        self.emit({"ev": "closed"})


def write_crash_log(text: str) -> None:
    """Keep only the latest service crash: %LOCALAPPDATA%\\SimpleSolitaire\\logs\\netservice.log."""
    try:
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local/share")
        folder = base / "SimpleSolitaire" / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "netservice.log").write_text(text, encoding="utf-8")
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--version" in argv:
        print(f"SolitaireNet {__version__} (api {API_VERSION})")
        return 0
    if "--selftest" in argv:
        # Used by CI on the built exe: proves every module and connector imports.
        print(f"SolitaireNet {__version__} ok; connectors: {', '.join(sorted(connectors.SCHEMES))}")
        return 0
    try:
        asyncio.run(Service().run())
    except KeyboardInterrupt:
        return 0
    except Exception:
        write_crash_log(traceback.format_exc())
        return 1
    return 0
