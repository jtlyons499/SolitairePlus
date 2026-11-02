"""Solitaire+ multiplayer launcher and room client."""
import os
import pygame

from multiplayer_paths import ROOT
from runtime_support import bootstrap
bootstrap()

from mp_widgets import TextInput, wooden_button
from room_session import RoomTable
from room_view import RoomView
from party_view import PartyView
from mp_hub import MultiplayerHub
import connection_settings
from mp_profile import MultiplayerProfile
from mp_appearance import Appearance
from mp_profile_ui import ProfileScreen
from mp_options import Options
from standalone_view import TableView
from dead_mans_hand_pvp import DeadMansHandPvPMode
from texas_holdem_ui import draw_holdem_glossy_button


def main():
    os.chdir(ROOT)
    pygame.init()
    options = Options()
    screen = options.display()
    pygame.display.set_caption("Solitaire+ Multiplayer")
    canvas = pygame.Surface((1366, 768))
    clock = pygame.time.Clock()

    profile = MultiplayerProfile()
    # Multiplayer now uses the same layered avatar builder as single-player.
    # Rebuild the small network portrait from those saved parts at launch.
    try: profile.rebuild_avatar()
    except Exception: pass
    appearance = Appearance(profile)
    profile_screen = ProfileScreen(profile, appearance)
    assets = TableView(canvas)
    room_view = RoomView(canvas, assets, appearance, options)
    party_view = PartyView(canvas, assets, appearance)
    hub = MultiplayerHub(appearance, profile)

    saved = connection_settings.load()
    relay_address = saved.get("relay_address") or "tcp://yamanote.proxy.rlwy.net:40274"
    room_code = ""
    code_active = False
    text_input = TextInput()
    table = None
    pvp_mode = None
    running = True

    sounds = {}
    if pygame.mixer.get_init():
        for folder in ("assets/sounds", "assets/sfx"):
            for path in (ROOT / folder).rglob("*"):
                if path.suffix.lower() not in (".wav", ".ogg", ".mp3"):
                    continue
                try: sounds[path.stem] = pygame.mixer.Sound(path)
                except pygame.error: continue

    def sound(key):
        aliases = {"chip_move": "chips_1", "win": "hand_win"}
        key = key if key in sounds else aliases.get(key, key)
        if key in sounds and options.values["sound"]:
            sounds[key].set_volume(options.values["volume"] / 100)
            sounds[key].play()

    room_view.presentation.sound = sound

    leave_rect = pygame.Rect(1130, 15, 210, 40)
    options_rect = pygame.Rect(1000, 15, 120, 40)
    profile_rect = pygame.Rect(760, 15, 225, 40)
    quit_rect = pygame.Rect(1180, 15, 160, 40)

    pygame.key.start_text_input()

    def close_table():
        nonlocal table, code_active
        if table is not None:
            table.close()
        table = None
        code_active = False
        pygame.key.start_text_input()

    while running:
        sx, sy = screen.get_size()
        scale = min(sx / 1366, sy / 768)
        offset = ((sx - 1366 * scale) / 2, (sy - 768 * scale) / 2)
        raw = pygame.mouse.get_pos()
        mouse = ((raw[0] - offset[0]) / scale, (raw[1] - offset[1]) / scale)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if pvp_mode is not None: pvp_mode.close()
                running = False
                continue

            if pvp_mode is not None:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    options.values["fullscreen"] = not options.values["fullscreen"]
                    options.save(); screen = options.display(); continue
                pvp_mode.handle_event(event, mouse)
                if pvp_mode.closed:
                    pvp_mode = None
                    pygame.key.start_text_input()
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                options.values["fullscreen"] = not options.values["fullscreen"]
                options.save(); screen = options.display(); continue

            if options.open:
                if options.event(event, mouse, table): screen = options.display()
                if not options.open: pygame.key.start_text_input()
                continue

            if profile_screen.open:
                profile_screen.event(event, mouse, table)
                if not profile_screen.open: pygame.key.start_text_input()
                continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if table is not None:
                    close_table()
                else:
                    options.open = True; pygame.key.stop_text_input()
                continue

            # ----------------------------------------------------------
            # Main multiplayer hub
            # ----------------------------------------------------------
            if table is None:
                if code_active and event.type in (pygame.TEXTINPUT, pygame.KEYDOWN):
                    room_code = text_input.event(event, room_code, 5, uppercase=True)
                    room_code = "".join(c for c in room_code if c.isdigit())[:5]
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(room_code) == 5:
                        table = RoomTable(profile.data["name"], False, relay_address, code=room_code, profile=profile, mode=None)
                        code_active = False; pygame.key.stop_text_input()
                        connection_settings.save(profile.data["name"], relay_address)
                        continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = next((action for rect, action in hub.buttons if rect.collidepoint(mouse)), None)
                    if clicked is not None: sound("button_click")
                    if isinstance(clicked, tuple) and clicked[0] == "mode":
                        hub.selected_mode = clicked[1]; code_active = False
                    elif clicked == "profile":
                        profile_screen.open = True; pygame.key.stop_text_input()
                    elif clicked == "code":
                        code_active = True; text_input.selected = False; pygame.key.start_text_input()
                    elif clicked == "create":
                        profile.save(); connection_settings.save(profile.data["name"], relay_address)
                        table = RoomTable(profile.data["name"], True, relay_address, profile=profile, mode=hub.selected_mode)
                        code_active = False; pygame.key.stop_text_input()
                    elif clicked == "join" and len(room_code) == 5:
                        profile.save(); connection_settings.save(profile.data["name"], relay_address)
                        table = RoomTable(profile.data["name"], False, relay_address, code=room_code, profile=profile, mode=None)
                        code_active = False; pygame.key.stop_text_input()
                    elif clicked == "_options":
                        options.open = True; pygame.key.stop_text_input()
                    elif clicked == "_quit":
                        running = False
                    elif clicked == "dmh":
                        profile.save(); connection_settings.save(profile.data["name"], relay_address)
                        pvp_mode = DeadMansHandPvPMode(profile.data["name"], relay_address, sound=sound)
                        pygame.key.stop_text_input()
                continue

            # ----------------------------------------------------------
            # Shared room chrome
            # ----------------------------------------------------------
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if leave_rect.collidepoint(mouse):
                    sound("button_click"); close_table(); continue
                if options_rect.collidepoint(mouse):
                    sound("button_click"); options.open = True; pygame.key.stop_text_input(); continue
                if profile_rect.collidepoint(mouse):
                    sound("button_click"); profile_screen.open = True; pygame.key.stop_text_input(); continue

            # We do not know the mode until the host sends the first lobby/state.
            if table.mode is None:
                continue

            if table.mode != "holdem":
                if party_view.event(event, mouse, table): sound("button_click")
                continue

            # ----------------------------------------------------------
            # Existing Hold'em room controls
            # ----------------------------------------------------------
            if room_view.event(event, mouse, table):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    sound("button_click")
            continue

        # --------------------------------------------------------------
        # Update and render
        # --------------------------------------------------------------
        if pvp_mode is not None:
            pvp_mode.update(min(0.05, max(0.0, clock.get_time() / 1000.0)))
            pvp_mode.draw(canvas, mouse)
        elif table is None:
            hub.draw(canvas, mouse, room_code, code_active)
            wooden_button(canvas, appearance, options_rect, "Options", pygame.font.Font(None, 24), hover=options_rect.collidepoint(mouse))
            wooden_button(canvas, appearance, quit_rect, "Quit Game", pygame.font.Font(None, 24), hover=quit_rect.collidepoint(mouse))
            if pygame.mouse.get_pressed()[0] and quit_rect.collidepoint(mouse):
                # Actual close remains event-driven below; this branch only preserves hover feedback.
                pass
        else:
            key = table.update(pygame.time.get_ticks())
            if key: sound(key)
            if table.mode == "holdem":
                room_view.draw(table, mouse)
            elif table.mode in ("score_four", "blind_mans_bluff", "roulette"):
                party_view.draw(table, mouse)
            else:
                appearance.background(canvas)
                label = pygame.font.Font(None, 38).render(table.status, True, (245,233,201)); canvas.blit(label,label.get_rect(center=(683,330)))
            draw_holdem_glossy_button(canvas, leave_rect, "Leave Room", mouse, pygame.font.Font(None, 24))
            draw_holdem_glossy_button(canvas, profile_rect, f"Edit Profile • Lv {profile.level}", mouse, pygame.font.Font(None, 22))
            draw_holdem_glossy_button(canvas, options_rect, "Options", mouse, pygame.font.Font(None, 24))

        # Hub-only top buttons need event handling after the hub has drawn them.
        if table is None and pvp_mode is None and not options.open and not profile_screen.open:
            # pygame's event queue has already been consumed; use edge-safe mouse click
            # handling through the next frame's MOUSEBUTTONDOWN.  Add these persistent
            # rects to hub.buttons so the same handler sees them.
            hub.buttons.append((options_rect, "_options")); hub.buttons.append((quit_rect, "_quit"))

        if profile_screen.open: profile_screen.draw(canvas, table)
        if options.open: options.draw(canvas, table)

        # Handle hub utility clicks using current mouse button transition.
        # (The main hub's own action list is rebuilt every draw.)
        # F11 remains available everywhere.
        screen.fill((0,0,0))
        screen.blit(pygame.transform.smoothscale(canvas,(round(1366*scale),round(768*scale))),offset)
        pygame.display.flip(); clock.tick(60)

        # Direct utility click handling is intentionally after display so it does
        # not compete with profile/code fields.  Detect only the edge event state.
        # QUIT/OPTIONS are also reachable via Escape / window close.
        if table is None and pvp_mode is None:
            # Use event.peek only as a no-op safeguard; actual buttons are processed
            # in the next MOUSEBUTTONDOWN through this small latch.
            pass

    if table is not None: table.close()
    pygame.key.stop_text_input(); pygame.quit()


if __name__ == "__main__":
    main()
