"""Solitaire+ network service (built as SolitaireNet.exe).

All internet connection code for online play lives in this package, not in
the game. The multiplayer window starts this service as a child process and
talks to it over stdin/stdout (see protocol.py). The service only makes
outgoing connections and never accepts connections from other computers
(what triggers Windows Firewall prompts).

To add a new way of connecting (WebSocket, Steam, ...), add a module in
connectors/ and register its URL scheme there. The game does not change.
See docs/NETWORKING.md.
"""

# Version of this component only (not the game version). Bump it when you
# change anything in netservice/, so SolitaireNet.exe is rebuilt and shipped.
__version__ = "1.0.0"
