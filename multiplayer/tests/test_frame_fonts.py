"""N74: the multiplayer screens build their pygame fonts once, not on every frame.

Each screen multiplayer/main.py draws is drawn twice while pygame.font.Font and
pygame.font.SysFont are counted; the second draw must build no font. The screens: the
hub (with its logo, and the SOLITAIRE+ title it writes when the logo is missing), the
party lobby (with the room code), Score-Four, Blind Man's Bluff and Roulette (with chips
on the board and the chat open), the Hold'em room table, the profile screen and the
options panel. The fixed lines use the shared font cache (solitaireplus.ui.text.get_font),
so each test empties it first: the first draw of a fixed screen must build its font.
Every party table comes from the real host code (party_authority), seeded.
"""
import os
import random
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import pygame

from solitaireplus.app import window
from solitaireplus.ui import text as ui_text
from mp_appearance import Appearance
from mp_assets import TableView
from mp_hub import MultiplayerHub
from mp_options import Options
from mp_profile import MultiplayerProfile
from mp_profile_ui import ProfileScreen
from party_authority import BlindBluffAuthority, RouletteAuthority, ScoreFourAuthority
from party_view import PartyView
from room_protocol import ClientGame
from room_table import RoomAuthority
from room_view import RoomView

TICKS = 41_500   # a fixed pygame.time.get_ticks(), so both frames show the same moment


class FontCounter:
    """Stands in for pygame.font.Font or SysFont: builds the real font and records its arguments."""

    def __init__(self, real, built):
        self.real, self.built = real, built

    def __call__(self, *args, **kwargs):
        self.built.append(args)
        return self.real(*args, **kwargs)


class Table(SimpleNamespace):
    """Stands in for room_session.RoomTable: the host's view of a party room, seen by the host."""

    def __init__(self, authority):
        super().__init__(message=authority.view(0), mode=authority.mode, game=None, pending=False,
                         failed=False, hosting=True, code='12345', status='', public_profiles={},
                         leave_notice='', leave_notice_seq=0)

    def act(self, action, amount=0):
        return False


def party_room(authority_class, start=True):
    """A seeded party room: the host, a second human and an NPC; started unless start=False."""
    authority = authority_class('Host', rng=random.Random(7))
    authority.join(1, 'Bea')
    assert authority.act_lobby(0, 'npc_toggle', {'seat': 2})
    if start:
        assert authority.start(now=0)
    return authority


class MultiplayerFrameFontTests(unittest.TestCase):
    maxDiff = None   # show every font a failing frame built

    def setUp(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1366, 768))
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        # The options panel and the profiles read and write under LOCALAPPDATA.
        environment = mock.patch.dict(os.environ, {'LOCALAPPDATA': self.folder.name})
        environment.start()
        self.addCleanup(environment.stop)
        ticks = mock.patch('pygame.time.get_ticks', return_value=TICKS)
        ticks.start()
        self.addCleanup(ticks.stop)
        ui_text.clear_font_cache()
        self.profile = MultiplayerProfile(directory=self.folder.name)
        self.appearance = Appearance(self.profile)
        self.canvas = pygame.Surface((1366, 768))
        self.assets = TableView(self.canvas)

    def count_fonts(self, draw):
        """The font arguments built by the first and by the second draw()."""
        built = []
        with mock.patch('pygame.font.Font', FontCounter(pygame.font.Font, built)), \
                mock.patch('pygame.font.SysFont', FontCounter(pygame.font.SysFont, built)):
            draw()
            first = list(built)
            del built[:]
            draw()
        return first, built

    def assert_second_frame_builds_no_font(self, draw, first_builds=None):
        first, second = self.count_fonts(draw)
        if first_builds is not None:
            self.assertIn(first_builds, first, 'the screen did not reach the fixed font code')
        self.assertEqual(second, [], 'fonts were built again on the second frame')

    def party_view(self):
        return PartyView(self.canvas, self.assets, self.appearance)

    # ---- the fixed screens
    def test_hub_title_without_the_logo(self):
        hub = MultiplayerHub(self.appearance, self.profile)
        real_image = self.appearance.image

        def no_logo(path, size):
            return None if path.endswith('floating_logo.png') else real_image(path, size)

        with mock.patch.object(self.appearance, 'image', side_effect=no_logo):
            self.assert_second_frame_builds_no_font(lambda: hub.draw(self.canvas, (0, 0), '123', True),
                                                    first_builds=(None, 64))

    def test_party_lobby_room_code(self):
        view = self.party_view()
        table = Table(party_room(RouletteAuthority, start=False))
        self.assertEqual(table.message['type'], 'lobby')
        self.assert_second_frame_builds_no_font(lambda: view.draw(table, (0, 0)), first_builds=(None, 48))

    def test_roulette_chips_on_the_board(self):
        authority = party_room(RouletteAuthority)
        self.assertTrue(authority.act(0, 'bet', {'type': 'number', 'value': '17', 'amount': 1000},
                                      authority.revision))
        self.assertTrue(authority.act(1, 'bet', {'type': 'color', 'value': 'red', 'amount': 50},
                                      authority.revision))
        view = self.party_view()
        view.chat_open = True
        table = Table(authority)
        self.assertTrue(any(table.message['all_bets']))
        self.assert_second_frame_builds_no_font(lambda: view.draw(table, (0, 0)), first_builds=(None, 13))

    # ---- the other screens (their fonts were already made once)
    def test_hub_with_the_logo(self):
        hub = MultiplayerHub(self.appearance, self.profile)
        self.assert_second_frame_builds_no_font(lambda: hub.draw(self.canvas, (0, 0)))
        hub.selected_mode = 'dmh'
        self.assert_second_frame_builds_no_font(lambda: hub.draw(self.canvas, (0, 0)))

    def test_score_four_and_bluff_tables(self):
        for authority_class in (ScoreFourAuthority, BlindBluffAuthority):
            with self.subTest(mode=authority_class.mode):
                view = self.party_view()
                view.chat_open = True
                table = Table(party_room(authority_class))
                self.assertEqual(table.message['type'], 'party_state')
                self.assert_second_frame_builds_no_font(lambda: view.draw(table, (0, 0)))

    def test_room_table(self):
        room = RoomAuthority('Al')
        room.start()
        message = room.view(0)
        game = ClientGame()
        game.apply(message)
        table = SimpleNamespace(game=game, message=message, failed=False, status='', code='12345',
                                public_profiles={}, pending=False)
        view = RoomView(self.canvas, self.assets, self.appearance)
        self.assert_second_frame_builds_no_font(lambda: view.draw(table, (0, 0)))

    def test_profile_screen_and_options_panel(self):
        profile_screen = ProfileScreen(self.profile, self.appearance)
        self.assert_second_frame_builds_no_font(lambda: profile_screen.draw(self.canvas))
        with mock.patch.object(window, 'usable_area', return_value=(3840, 2082)):
            options = Options()
            self.assert_second_frame_builds_no_font(
                lambda: options.draw(self.canvas, SimpleNamespace(hosting=True)))


if __name__ == '__main__':
    unittest.main()
