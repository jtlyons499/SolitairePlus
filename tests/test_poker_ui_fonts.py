"""B44: the poker hand recap and the Five-O table must not build pygame fonts every frame.

draw_recap built four kinds of fonts on every frame (one per button and one per recap row),
recap_display_lines built one on every call (every Previous / Next click), and the Five-O
table built one per card plus three more every frame. They now take their fonts from the
shared font cache (ui_text.get_font), so each font is built once. The screens must look
exactly as before.
"""
import os
import random
import sys
import unittest
from collections import Counter
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

PACKAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solitaireplus')
# Fonts built by these helpers are not part of this fix: Score Four's text() is fixed in its own
# phase (B44), and the shared variant Quick Chat overlay that draws over the Five-O table.
NOT_COUNTED = {'score_four_ui.py', 'variant_quick_chat.py'}
TICKS = 123_456
SUITS = ('Clubs', 'Diamonds', 'Hearts', 'Spades')
RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')


def counted(filename):
    """Fonts built anywhere in the game package count (the font cache lives there too)."""
    filename = os.path.abspath(filename)
    return (os.path.commonpath([filename, PACKAGE]) == PACKAGE
            and os.path.basename(filename) not in NOT_COUNTED)


class FontCounter:
    def __init__(self, real):
        self.real, self.calls = real, []

    def __call__(self, *args, **kwargs):
        caller = sys._getframe(1).f_code
        if counted(caller.co_filename):
            self.calls.append((caller.co_name, args, tuple(sorted(kwargs.items()))))
        return self.real(*args, **kwargs)


def card(rank, suit):
    return {'rank': rank, 'suit': suit}


def recap_game(page=None):
    """A finished Hold'em hand with a main and a side pot; page=None leaves the recap closed."""
    from solitaireplus.games.poker.holdem import TexasHoldemGame
    random.seed(44)
    g = TexasHoldemGame()
    g.start_session([{'id': 'a', 'name': 'Alex'}, {'id': 'b', 'name': 'Blake'}], 1000, 10)
    g.start_hand()
    g.community_cards = [card('2', 'Clubs'), card('3', 'Diamonds'), card('4', 'Hearts'),
                         card('8', 'Spades'), card('9', 'Clubs')]
    g.player_hand = [card('A', 'Spades'), card('A', 'Diamonds')]
    g.npc_hands = [[card('K', 'Hearts'), card('K', 'Clubs')], [card('Q', 'Hearts'), card('Q', 'Spades')]]
    g.player_hand_contribution = 100
    g.npc_hand_contributions = [200, 200]
    g.pot = 500
    g.player_stack = 1000 - g.player_hand_contribution
    g.npc_stacks = [1000 - x for x in g.npc_hand_contributions]
    g.player_folded, g.npc_folded = False, [False, False]
    g.player_busted, g.npc_busted = False, [False, False]
    g.current_stage = 'river'
    g.showdown()
    g.last_pot_awards *= 2   # enough rows for two pages
    if page is not None:
        g.recap_open, g.recap_page = True, page
    return g


def five_o_game(stage):
    from solitaireplus.games.poker.five_o import FiveOPokerGame
    game = FiveOPokerGame(random.Random(44))
    game.start_session({'name': 'Rival'}, 1000)
    placements = {'placement': 7}.get(stage, 99)
    while game.phase == 'placement' and placements:
        game.place_player_card(game.get_available_player_columns()[0])
        placements -= 1
    if stage in ('complete', 'options', 'quit'):
        game._showdown()
        game.showdown_pending_finish = False
        game._finish_hand()
        game.showdown_revealed_columns = 5
        game.result_text = game.pending_showdown_result_text
        game.options_open = {'options': True, 'quit': 'quit'}.get(stage, False)
    return game


def pixels(surface):
    return surface.get_size(), pygame.image.tobytes(surface, 'RGBA')


class PokerUIFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))
        from solitaireplus.ui import text as ui_text
        from solitaireplus.games.poker import recap, five_o_ui
        cls.ui_text, cls.recap, cls.five_o_ui = ui_text, recap, five_o_ui
        cls.table_fonts = [pygame.font.Font(None, n) for n in (40, 30, 23)]
        fronts = {}
        for s, suit in enumerate(SUITS):
            for r, rank in enumerate(RANKS):
                front = pygame.Surface((120, 168))
                front.fill((200 + s * 10, 120 + r * 9, 90 + s * 30))
                fronts[f"{rank}{suit[0]}"] = front
        cls.card_fronts = fronts
        cls.card_back = pygame.Surface((148, 207))
        cls.card_back.fill((40, 60, 150))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.ui_text.clear_font_cache()
        ticks = patch('pygame.time.get_ticks', return_value=TICKS)
        ticks.start()
        self.addCleanup(ticks.stop)

    # ------------------------------------------------------------------ the screens

    def recap_draw(self, page):
        game = recap_game(page)
        surface = pygame.Surface((1366, 768))

        def draw():
            surface.fill((30, 70, 50))
            self.recap.draw_recap(surface, None, game)
            return surface
        return draw

    def five_o_draw(self, stage, fronts):
        game = five_o_game(stage)
        surface = pygame.Surface((1366, 768))
        card_fronts = self.card_fronts if fronts else None
        card_back = self.card_back if fronts else None

        def draw():
            surface.fill((10, 20, 20))
            self.five_o_ui.draw_five_o_poker(surface, None, game, 'Player', lambda **kw: surface.fill((10, 20, 20)),
                                             *self.table_fonts, card_fronts=card_fronts, card_back_surface=card_back)
            return surface
        return draw

    def screens(self):
        screens = {
            'recap_closed': self.recap_draw(None),
            'recap_page_1': self.recap_draw(0),
            'recap_page_2': self.recap_draw(1),
        }
        for stage in ('placement', 'betting', 'complete', 'options', 'quit'):
            for fronts in (False, True):
                screens[f"five_o_{stage}{'_card_fronts' if fronts else ''}"] = self.five_o_draw(stage, fronts)
        return screens

    def test_states_reach_their_drawing_code(self):
        self.assertEqual(five_o_game('placement').phase, 'placement')
        self.assertTrue(five_o_game('placement').player_drawn_card)
        self.assertEqual(five_o_game('betting').phase, 'betting')
        self.assertTrue(five_o_game('complete').hand_complete)
        game = recap_game(0)
        self.assertGreater(len(self.recap.recap_display_lines(game)), self.recap.ROWS)

    # ------------------------------------------------------------------ fonts built once

    def test_screens_build_each_font_once(self):
        for name, draw in self.screens().items():
            with self.subTest(screen=name):
                self.ui_text.clear_font_cache()
                font, sysfont = FontCounter(pygame.font.Font), FontCounter(pygame.font.SysFont)
                with patch('pygame.font.Font', font), patch('pygame.font.SysFont', sysfont):
                    draw()
                    first = font.calls + sysfont.calls
                    del font.calls[:], sysfont.calls[:]
                    draw()
                    second = font.calls + sysfont.calls
                self.assertTrue(first, 'the screen did not reach its font code')
                built = [(args, kwargs) for _, args, kwargs in first]
                repeated = {call: n for call, n in Counter(built).items() if n > 1}
                self.assertEqual(repeated, {}, 'a font was built more than once in one frame')
                self.assertEqual(second, [], 'fonts were built again on the second frame')

    def test_recap_page_clicks_build_no_font(self):
        game = recap_game(0)
        self.recap.draw_recap(pygame.Surface((1366, 768)), None, game)
        font = FontCounter(pygame.font.Font)
        with patch('pygame.font.Font', font):
            for action in ('recap_next', 'recap_prev', 'recap_next'):
                self.assertTrue(self.recap.handle_recap_action(game, action))
            self.recap.recap_display_lines(game)
        self.assertEqual(game.recap_page, 1)
        self.assertEqual(font.calls, [])

    # ------------------------------------------------------------------ same pixels

    def test_frames_match_fresh_fonts(self):
        """A frame drawn with cached fonts (after another frame used them) is byte-identical to one
        drawn the old way, with every font built fresh; a shared font changed by a draw shows here."""
        real_font, real_sysfont = pygame.font.Font, pygame.font.SysFont

        def fresh_font(name, size, bold=False, italic=False, sysfont=False):
            if sysfont:
                return real_sysfont(name, size, bold=bold, italic=italic)
            font = real_font(name, size)
            font.set_bold(bold)
            font.set_italic(italic)
            return font

        for name, draw in self.screens().items():
            with self.subTest(screen=name):
                self.ui_text.clear_font_cache()
                with patch.object(self.ui_text, 'get_font', fresh_font):
                    old = pixels(draw())
                    self.assertEqual(pixels(draw()), old, 'the screen is not deterministic')
                self.assertEqual(pixels(draw()), old)
                self.assertEqual(pixels(draw()), old)   # with the cached fonts

    def test_recap_rows_match_fresh_fonts(self):
        game = recap_game(0)
        with patch.object(self.ui_text, 'get_font', lambda name, size, **kw: pygame.font.Font(name, size)):
            old = self.recap.recap_display_lines(game)
        self.assertEqual(self.recap.recap_display_lines(game), old)
        self.assertEqual(self.recap.recap_display_lines(game), old)


if __name__ == '__main__':
    unittest.main()
