# Running the online relay on Railway

This guide is for whoever manages the Railway account. You don't need to be a programmer: it's mostly clicking in
Railway's website and running one checking command. (Railway sometimes renames buttons; if a name below doesn't match
exactly, look for the closest one.)

## What the relay is, in one paragraph

When people play online, their games don't connect to each other directly. Every player's game connects **out** to
one small program on the internet, the **relay**, which hands out room codes and passes messages between the players
in the same room. It stores no game data and runs no game rules (the host's game does that). The relay's code is in
this repository at `multiplayer/relay_server.py`, `multiplayer/room_relay.py` and `multiplayer/relay_websocket.py`.
It runs on **Railway**, a hosting service. Changing the relay never changes anything on players' PCs.

## Before you start

* A login to the Railway project that runs the relay.
* This repository on your PC with its Python environment (`py -3.14 -m venv .venv`, then
  `.venv\Scripts\python.exe -m pip install -r requirements.txt`), so you can run the checking tool.

## Part 1: Check what is running now (5 minutes)

The checking tool opens one room like a player would, looks at the answer, and closes it again. It changes nothing.

```powershell
.\.venv\Scripts\python.exe tools\relay_probe.py
```

What the result means:

| The tool says | Meaning | What to do |
|---|---|---|
| `6 characters - current relay` and `this relay is up to date` | All good. | Nothing; skip to Part 4 if you want the encrypted address. |
| `5 digits` and `Party games: supported` | The relay from this repository, but from before version 0.0.7. | Part 2 (redeploy) to get longer room codes and the guessing protection. |
| `8 characters - the OLD relay` and/or `Party games: NOT supported` | Railway runs the old code from the separate `SolitaireMultiplayer` repository. Players **can't join** its rooms from today's game, and hosting party games disconnects the host. | Part 2 now. |
| `no answer` / `could not open a room` | The relay is down or asleep, or the address changed. | Check Railway (Part 5, "logs"). |

In Railway you can also see what is deployed: open the project → the relay service → **Deployments**. The latest
deployment shows which **repository** and **commit** it was built from.

## Part 2: Run the relay from this repository (10 minutes)

Until now Railway built the relay from `jtlyons499/SolitaireMultiplayer`, a separate repository that has fallen out of
step with the game. From now on, **this repository is the only source**.

1. Railway → the relay service → **Settings** → **Source**: change the connected repository to
   **`jtlyons499/SolitairePlus`**, branch **`main`**.
2. **Root Directory**: `multiplayer`
   (Railway then installs what `multiplayer/requirements.txt` lists, which is just the `websockets` library.)
3. **Custom Start Command**:
   ```text
   python relay_server.py --bind 0.0.0.0 --port 50008
   ```
4. **Watch Paths** (so changes to the *game* don't restart the relay and kick players out):
   ```text
   multiplayer/relay_server.py
   multiplayer/room_relay.py
   multiplayer/relay_websocket.py
   multiplayer/requirements.txt
   ```
5. **Networking** → keep the existing **TCP Proxy** exactly as it is. It must still point to port **50008**. Its
   public address (currently `yamanote.proxy.rlwy.net:40274`) is what players' games use, so it must not change.
6. Click **Deploy** (or wait for the automatic deploy) and watch the logs (Part 5). You should see
   `Relay listening on 0.0.0.0:50008 (plain TCP)`.
7. Run the checking tool again. It should now say `this relay is up to date`.

Once that works, the old `SolitaireMultiplayer` repository is no longer used. You can archive it on GitHub
(repository **Settings** → **Archive**) so nobody edits the wrong copy.

## Part 3: What changed for players (no action needed)

* **Room codes** are now 6 letters/digits (no confusable 0/O or 1/I) for players on version 0.0.7 or newer. Players
  who haven't updated still get 5-digit codes they can type. Everyone can join everyone.
* **Guessing protection**: each wrong room code makes that player wait a second, and after 10 wrong codes in a minute
  they're told to wait. A correct code is never slowed down.
  * Note: through the plain TCP address, Railway may make every player look like they come from the same internet
    address. If many players mistype codes at the same moment, they could briefly share that limit. It clears within
    a minute. The encrypted address in Part 4 doesn't have this limitation.

## Part 4: Turn on the encrypted address (wss://) (10 minutes)

The plain TCP address isn't encrypted: names and chat cross the internet readable. Railway can give the relay a
normal **HTTPS** address for free, and players then connect with encrypted WebSockets (`wss://`). For players this
needs **no setup at all**: no firewall changes and no port forwarding. It's the same kind of connection as opening a
website, and it even gets through networks that block unusual ports.

1. Railway → relay service → **Variables** → add `RELAY_WS_PORT` with the value `8080`.
2. **Settings** → **Networking** → **Generate Domain** (public HTTP). If it asks for a port, enter `8080`.
   Railway shows an address like `something.up.railway.app`.
3. Keep the TCP Proxy too. Players who haven't updated still use it.
4. Redeploy. The logs should now also show `Relay listening for WebSocket players on 0.0.0.0:8080`.
5. Check it, using your new address:
   ```powershell
   .\.venv\Scripts\python.exe tools\relay_probe.py wss://something.up.railway.app/
   ```
   Expected: `this relay is up to date`.
6. **Switch players over.** This is a game update, so ask whoever does releases:
   * In `netservice/connectors/__init__.py`, set `DEFAULT_ADDRESS = "wss://something.up.railway.app/"`.
   * In `multiplayer/connection_settings.py`, add the old `tcp://yamanote.proxy.rlwy.net:40274` to
     `LEGACY_DEFAULT_ADDRESSES` if it isn't already listed. (It is today.)
   * Bump `__version__` in `netservice/__init__.py`, add a CHANGELOG line, and release (`docs/RELEASING.md`). Only
     `SolitaireNet.exe` changes, so the update is tiny.
7. Leave the TCP Proxy running for at least a month after that release, so players who update late can still play.
   Then remove it.

## Part 5: Everyday tasks

**Redeploy after a relay change.** Merge the change into `main`. If it touched a file in Watch Paths, Railway deploys
automatically. Otherwise use **Deployments** → **Redeploy**. Players in a game at that moment are disconnected and
need to create a new room, so prefer quiet hours.

**Read the logs.** Relay service → **Deployments** → latest → **View Logs**. Normal lines:
`Relay listening on ...`. Error lines with `Traceback` mean the relay crashed. Copy them into an issue or give them to
the AI assistant.

**Undo a bad deploy.** **Deployments** → pick the last deployment that worked → **⋯** → **Redeploy**. Then run the
checking tool.

**Confirm it works.** `tools\relay_probe.py` (Part 1). Then two people host and join a room from the game. Try one
party game (for example Score Four) as host.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Players: "Room not found" for a code they just got | Host and guest are on different relays (old and new). | Make sure both addresses point to the same Railway service; run the probe on each. |
| Host of a party game is disconnected right after starting | Old relay code. | Part 2. |
| Probe: `no answer` | Service sleeping or crashed. | Check the logs; redeploy. |
| Logs: `ModuleNotFoundError: No module named 'websockets'` | Root Directory isn't `multiplayer`, so `multiplayer/requirements.txt` wasn't installed. | Part 2, step 2. |
| Players: "Too many wrong room codes" | Many mistyped codes from one address within a minute. | Wait a minute. See the note in Part 3. |
