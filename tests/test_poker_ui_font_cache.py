"""The poker tables must not build pygame fonts every frame (same class of bug as B17 / B44).

Five-Card Draw and Seven-Card Stud built a Font(None, 23) for the session status line on every
frame, and their render_text_fit helpers built one SysFont per size tried whenever a name or
result did not fit. Hold'em built a Font(None, 24) for its rating line every frame and a
Font(None, 32) for the showdown banner, Blind Man's Bluff's chip effects a Font(None, 27), and
the shared variant Quick Chat overlay (Draw, Stud, Five-O, Blind Man's Bluff) a SysFont for every
button, ribbon and chat line. They now come from the shared font cache (ui_text.get_font) with
the same arguments, so each font is built once and the tables look exactly as before.

The tables are put in the states the poker harness scenes show (hand start, mid-hand, the draw
round, the hand result, the buy-in screens) and drawn twice: the second frame must build no font.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POKER = os.path.normcase(os.path.join(ROOT, 'solitaireplus', 'games', 'poker'))
TEXT_PY = os.path.normcase(os.path.join(ROOT, 'solitaireplus', 'ui', 'text.py'))
TICKS = 123_456
SUITS = ('Clubs', 'Diamonds', 'Hearts', 'Spades')
RANKS = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')
NPCS = tuple({'id': f'npc{index}', 'name': name} for index, name in enumerate(('Alex', 'Blake', 'Casey', 'Drew')))
LONG_NAME = 'Bartholomew Featherstonehaugh-Montgomery III'
WHITE = (245, 245, 245)


def fresh_font(name, size, bold=False, italic=False, sysfont=False):
    """What the poker call sites did before: build a new font on every call."""
    if sysfont:
        return pygame.font.SysFont(name, size, bold, italic)
    font = pygame.font.Font(name, size)
    if bold:
        font.set_bold(True)
    if italic:
        font.set_italic(True)
    return font


def poker_site(frame):
    """(file, function) of the poker code that built a font, or None for code outside the poker package.

    A font built by the shared cache (ui_text.get_font) or by fresh_font counts for the poker code
    that asked for it."""
    code = frame.f_code
    if code is fresh_font.__code__ or os.path.normcase(os.path.abspath(code.co_filename)) == TEXT_PY:
        frame = frame.f_back
        code = frame.f_code
    filename = os.path.normcase(os.path.abspath(code.co_filename))
    if os.path.commonpath([filename, POKER]) != POKER:
        return None
    return os.path.basename(filename), code.co_name


class FontBuilds:
    """Records every pygame.font.Font / SysFont built for poker code while active."""

    def __init__(self):
        self.calls = []
        self._patches = []

    def _wrap(self, real):
        def build(*args, **kwargs):
            site = poker_site(sys._getframe(1))
            if site is not None:
                name = args[0] if args else kwargs.get('name')
                size = args[1] if len(args) > 1 else kwargs.get('size')
                self.calls.append((*site, name, size))
            return real(*args, **kwargs)
        return build

    def __enter__(self):
        self._patches = [patch('pygame.font.Font', self._wrap(pygame.font.Font)),
                         patch('pygame.font.SysFont', self._wrap(pygame.font.SysFont))]
        for active in self._patches:
            active.start()
        return self

    def __exit__(self, *exc):
        for active in reversed(self._patches):
            active.stop()
        return False

    def sites(self):
        return {(filename, function) for filename, function, _name, _size in self.calls}


def built_fonts(draw):
    with FontBuilds() as builds:
        draw()
    return builds.calls


def pixels(surface):
    return surface.get_size(), pygame.image.tobytes(surface, 'RGBA')


def play(game, done, limit=800):
    """Check / call for the player, stand pat in the draw and run the NPCs until done(game)."""
    for _ in range(limit):
        if done(game):
            return game
        if game.hand_complete:
            break
        if game.current_stage == 'draw' and not game.player_draw_complete and not game.player_folded:
            game.player_draw([])
        elif game.current_actor == 0 and game.can_player_act_now():
            if not game.player_call():
                game.player_check()
        elif game.is_betting_round_complete():
            game.advance_after_betting_round()
        else:
            game.run_next_npc_action()
    raise AssertionError(f'the hand never reached the wanted state (stage {game.current_stage!r})')


def poker_table(game_class, stage):
    """A Hold'em / Draw / Stud table in one of the states the harness scenes show."""
    random.seed(45)
    game = game_class()
    game.start_session([dict(npc) for npc in NPCS], 1000, 10)
    game.start_hand()
    first_stage = game.current_stage
    wanted = {
        'hand_start': lambda g: True,
        'mid_hand': lambda g: g.current_stage != first_stage,
        'draw_round': lambda g: g.current_stage == 'draw',
        'hand_result': lambda g: g.hand_complete,
    }[stage]
    return play(game, wanted)


def bluff_table(stage):
    from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
    game = BlindMansBluffGame(random.Random(45))
    game.start_session([dict(npc) for npc in NPCS[:3]], 1000)
    while stage == 'showdown' and not game.hand_complete:
        actions = game.get_player_actions()
        if not actions or not (game.player_check() if 'check' in actions else game.player_call()):
            raise AssertionError(f'Blind Man\'s Bluff got stuck in phase {game.phase!r}')
    return game


def five_o_table(stage):
    from solitaireplus.games.poker.five_o import FiveOPokerGame
    game = FiveOPokerGame(random.Random(45))
    game.start_session({'name': 'Rival'}, 1000)
    if stage == 'complete':
        game._showdown()
        game.showdown_pending_finish = False
        game._finish_hand()
        game.showdown_revealed_columns = 5
        game.result_text = game.pending_showdown_result_text
    return game


class PokerUIFontCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))
        from solitaireplus.ui import text as ui_text
        from solitaireplus.games.poker import (
            blind_mans_bluff_ui, five_card_draw_ui, five_o_ui, holdem_ui, seven_card_stud_ui, variant_quick_chat)
        cls.ui_text = ui_text
        cls.holdem_ui, cls.draw_ui, cls.stud_ui = holdem_ui, five_card_draw_ui, seven_card_stud_ui
        cls.bluff_ui, cls.five_o_ui, cls.quick_chat = blind_mans_bluff_ui, five_o_ui, variant_quick_chat
        cls.table_fonts = [pygame.font.Font(None, size) for size in (40, 30, 23)]
        fronts = {}
        for s, suit in enumerate(SUITS):
            for r, rank in enumerate(RANKS):
                front = pygame.Surface((120, 168))
                front.fill((200 + s * 10, 120 + r * 9, 90 + s * 30))
                fronts[f"{rank}{suit[0]}"] = front
        cls.card_fronts = fronts
        cls.card_back = pygame.Surface((148, 207))
        cls.card_back.fill((40, 60, 150))
        cls.felt = pygame.Surface((1366, 768))
        cls.felt.fill((30, 105, 55))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.ui_text.clear_font_cache()
        ticks = patch('pygame.time.get_ticks', return_value=TICKS)
        ticks.start()
        self.addCleanup(ticks.stop)

    # ------------------------------------------------------------------ the screens

    def surface(self):
        surface = pygame.Surface((1366, 768))

        def background(**_kwargs):
            surface.fill((10, 20, 20))

        def portrait(_npc, rect, _style):
            pygame.draw.rect(surface, (90, 96, 104), rect)
        return surface, background, portrait

    def holdem_draw(self, stage):
        from solitaireplus.games.poker.holdem import TexasHoldemGame
        game = poker_table(TexasHoldemGame, stage)
        surface, background, portrait = self.surface()

        def draw():
            self.holdem_ui.draw_texas_holdem(
                surface, None, game, self.card_fronts, self.card_back, background,
                lambda *a, **k: None, lambda *a, **k: None, portrait, *self.table_fonts, 'Player', self.felt)
            return surface
        return draw

    def variant_draw(self, ui, function, game_class, stage, player_name='Player', quick_chat=None):
        game = poker_table(game_class, stage)
        surface, background, portrait = self.surface()
        if quick_chat is not None:
            controller = self.quick_chat.controller_for(quick_chat)
            controller.bind(game)
            controller.open = True
            self.addCleanup(setattr, controller, 'open', False)

        def draw():
            getattr(ui, function)(surface, None, game, self.card_fronts, self.card_back, background,
                                  portrait, player_name, self.felt)
            return surface
        return draw

    def draw_draw(self, stage, player_name='Player', quick_chat=None):
        from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
        return self.variant_draw(self.draw_ui, 'draw_five_card_draw', FiveCardDrawGame, stage, player_name, quick_chat)

    def stud_draw(self, stage, player_name='Player'):
        from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame
        return self.variant_draw(self.stud_ui, 'draw_seven_card_stud', SevenCardStudGame, stage, player_name)

    def bluff_draw(self, stage):
        game = bluff_table(stage)
        surface, background, _portrait = self.surface()

        def draw():
            self.bluff_ui.draw_blind_mans_bluff(surface, None, game, 'Player', background, *self.table_fonts,
                                                card_fronts=self.card_fronts, card_back_surface=self.card_back)
            return surface
        return draw

    def five_o_draw(self, stage, chat_history=False):
        game = five_o_table(stage)
        surface, background, _portrait = self.surface()
        if chat_history:
            controller = self.quick_chat.controller_for('five_o_poker')
            controller.bind(game)
            saved = list(controller.local_history)
            controller.local_history[:] = ['You: Nice hand.', 'Rival: Luck is a skill when I have it.']
            self.addCleanup(controller.local_history.__setitem__, slice(None), saved)

        def draw():
            self.five_o_ui.draw_five_o_poker(surface, None, game, 'Player', background, *self.table_fonts,
                                             card_fronts=self.card_fronts, card_back_surface=self.card_back)
            return surface
        return draw

    def buy_in_draw(self, ui, function):
        surface, background, _portrait = self.surface()

        def draw():
            getattr(ui, function)(surface, None, 25_000, background)
            return surface
        return draw

    def screens(self):
        """name -> (draw, the poker code each frame of it must ask for a font)."""
        holdem = {('holdem_ui.py', 'draw_texas_holdem')}
        draw = {('five_card_draw_ui.py', 'draw_five_card_draw'), ('variant_quick_chat.py', '_font')}
        stud = {('seven_card_stud_ui.py', 'draw_seven_card_stud'), ('variant_quick_chat.py', '_font')}
        return {
            'holdem_hand_start': (self.holdem_draw('hand_start'), holdem),
            'holdem_mid_hand': (self.holdem_draw('mid_hand'), holdem),
            'holdem_hand_result': (self.holdem_draw('hand_result'),
                                   holdem | {('holdem_ui.py', 'draw_holdem_showdown_banner')}),
            'holdem_buy_in': (self.buy_in_draw(self.holdem_ui, 'draw_texas_holdem_buy_in'), set()),
            'draw_hand_start': (self.draw_draw('hand_start'), draw),
            'draw_draw_round': (self.draw_draw('draw_round'), draw),
            'draw_hand_result': (self.draw_draw('hand_result'), draw),
            'draw_long_player_name': (self.draw_draw('hand_start', LONG_NAME),
                                      draw | {('five_card_draw_ui.py', 'render_text_fit')}),
            'draw_quick_chat_open': (self.draw_draw('hand_start', quick_chat='five_card_draw'), draw),
            'draw_buy_in': (self.buy_in_draw(self.draw_ui, 'draw_five_card_draw_buy_in'), set()),
            'stud_hand_start': (self.stud_draw('hand_start'), stud),
            'stud_mid_hand': (self.stud_draw('mid_hand'), stud),
            'stud_hand_result': (self.stud_draw('hand_result'), stud),
            'stud_long_player_name': (self.stud_draw('hand_start', LONG_NAME),
                                      stud | {('seven_card_stud_ui.py', 'render_text_fit')}),
            'stud_buy_in': (self.buy_in_draw(self.stud_ui, 'draw_seven_card_stud_buy_in'), set()),
            'bluff_start': (self.bluff_draw('start'),
                            {('bluff_presentation.py', 'draw_bluff_effects'), ('variant_quick_chat.py', '_font')}),
            'bluff_showdown': (self.bluff_draw('showdown'),
                               {('bluff_presentation.py', 'draw_bluff_effects'), ('variant_quick_chat.py', '_font')}),
            'five_o_placement': (self.five_o_draw('placement'), {('variant_quick_chat.py', '_font')}),
            'five_o_complete': (self.five_o_draw('complete'), {('variant_quick_chat.py', '_font')}),
            'five_o_chat_history': (self.five_o_draw('placement', chat_history=True),
                                    {('variant_quick_chat.py', '_font')}),
        }

    def test_states_match_the_harness_scenes(self):
        from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
        from solitaireplus.games.poker.holdem import TexasHoldemGame
        from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame
        self.assertEqual(poker_table(TexasHoldemGame, 'hand_start').current_stage, 'preflop')
        self.assertIn(poker_table(TexasHoldemGame, 'mid_hand').current_stage, ('flop', 'turn', 'river'))
        holdem_result = poker_table(TexasHoldemGame, 'hand_result')
        self.assertEqual(holdem_result.current_stage, 'showdown')
        self.assertTrue(holdem_result.result_text)      # so the showdown banner is drawn
        self.assertEqual(poker_table(FiveCardDrawGame, 'draw_round').current_stage, 'draw')
        self.assertTrue(poker_table(FiveCardDrawGame, 'hand_result').hand_complete)
        self.assertNotEqual(poker_table(SevenCardStudGame, 'mid_hand').current_stage, 'third')
        self.assertTrue(poker_table(SevenCardStudGame, 'hand_result').hand_complete)
        self.assertTrue(bluff_table('showdown').hand_complete)
        self.assertTrue(five_o_table('complete').hand_complete)

        self.draw_draw('hand_start', quick_chat='five_card_draw')()
        self.assertTrue(self.quick_chat.controller_for('five_card_draw').open, 'the Quick Chat popup did not open')

    # ------------------------------------------------------------------ fonts built once

    def test_second_frame_builds_no_font(self):
        for name, (draw, expected) in self.screens().items():
            with self.subTest(screen=name):
                self.ui_text.clear_font_cache()
                first = built_fonts(draw)
                second = built_fonts(draw)
                if expected:
                    self.assertTrue(first, 'the screen did not reach its font code')
                repeated = {call: n for call, n in Counter(first).items() if n > 1}
                self.assertEqual(repeated, {}, 'a font was built more than once in one frame')
                self.assertEqual(second, [], 'fonts were built again on the second frame')

    def test_screens_reach_the_font_code(self):
        """With every font request building a font, each screen asks for the fonts this fix is about."""
        for name, (draw, expected) in self.screens().items():
            with self.subTest(screen=name):
                with FontBuilds() as builds, patch.object(self.ui_text, 'get_font', fresh_font):
                    draw()
                self.assertLessEqual(expected, builds.sites())

    def test_fit_helpers_build_each_size_once(self):
        cases = ((self.draw_ui, self.draw_ui.get_draw_fonts), (self.stud_ui, self.stud_ui.get_stud_fonts))
        for ui, fonts in cases:
            with self.subTest(module=ui.__name__):
                font = fonts()['title']
                fit = lambda: ui.render_text_fit(LONG_NAME, font, WHITE, 160, minimum_size=10)
                self.ui_text.clear_font_cache()
                first = built_fonts(fit)
                self.assertTrue(first, 'the text fitted without trying smaller fonts')
                self.assertEqual(built_fonts(fit), [])
                with patch.object(self.ui_text, 'get_font', fresh_font):
                    old = pixels(fit())
                self.assertEqual(pixels(fit()), old)

        # Hold'em's fit helper scales the rendered text down instead; it builds no font at all.
        surface = pygame.Surface((300, 60))
        font = self.holdem_ui.get_holdem_fonts()['title']
        fit = lambda: self.holdem_ui.blit_text_fit(surface, LONG_NAME, font, WHITE, pygame.Rect(0, 0, 160, 40))
        self.assertEqual(built_fonts(fit), [])
        self.assertEqual(built_fonts(fit), [])

    # ------------------------------------------------------------------ same pixels

    def test_frames_match_fresh_fonts(self):
        """A frame drawn with the cached fonts (after another frame used them) is byte-identical to
        one drawn the old way, with every font built fresh."""
        for name, (draw, _expected) in self.screens().items():
            with self.subTest(screen=name):
                self.ui_text.clear_font_cache()
                with patch.object(self.ui_text, 'get_font', fresh_font):
                    old = pixels(draw())
                    self.assertEqual(pixels(draw()), old, 'the screen is not deterministic')
                self.assertEqual(pixels(draw()), old)
                self.assertEqual(pixels(draw()), old)   # with the cached fonts


if __name__ == '__main__':
    unittest.main()
