"""Small user-local connection preferences, separate from career profiles.

Stored in %LOCALAPPDATA%\\SolitaireMultiplayer\\connection.json.

relay_address is saved ONLY when the player typed their own server address.
An empty value means "use the default server", and the default lives in
SolitaireNet.exe (netservice/connectors/__init__.py DEFAULT_ADDRESS), so
moving the server never requires a game update. Older versions saved the
default address into this file on every host/join, which pinned players to
that server forever; load() treats those old defaults as "not customised".
"""
import json
import os
from pathlib import Path

# Addresses that were once the built-in default. Never treat them as a player's choice.
LEGACY_DEFAULT_ADDRESSES = {
    'tcp://yamanote.proxy.rlwy.net:40274',
}


def path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home()/'.config'))/'SolitaireMultiplayer'/'connection.json'


def load():
    try:
        data = json.loads(path().read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return {}
    except (OSError, ValueError):
        return {}
    address = str(data.get('relay_address') or '').strip()[:128]
    if address.lower() in LEGACY_DEFAULT_ADDRESSES:
        address = ''
    return {'name': str(data.get('name') or '')[:128], 'relay_address': address}


def save(name, address):
    values = {'name': name}
    address = str(address or '').strip()
    if address and address.lower() not in LEGACY_DEFAULT_ADDRESSES:
        values['relay_address'] = address
    try:
        target = path(); target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(values), encoding='utf-8')
    except OSError:
        pass
