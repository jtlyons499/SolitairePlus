"""B17 / B44: screens (first in legacy.py, now partly moved out) must not build pygame fonts every frame.

Starts the game's modules headless (as the game does, saves in a temporary folder), then draws
each screen that used to call pygame.font.Font / SysFont per frame twice: only the first draw
may build a font. B44 added Score Four (mode, difficulty and table screens, the opponent panel,
hint and solution lines), the career story nights (Bigfoot / Alien), Head-to-Head (opponent
select and the race countdown), the Solitaire restart prompt and the Ace Invaders fallback enemy
(drawn only when the enemy art is missing). It also covers Card.draw in games/solitaire/card.py:
nothing in the game calls it (the Solitaire table draws its own cards), but it uses the cache too.
"""
import os
import random
import sys
import tempfile
import unittest
from collections import ChainMap
from fractions import Fraction
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

PACKAGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solitaireplus')
MONOTONIC = 5_000.0   # a fixed time.monotonic() for the Score Four timers, so frames match
LONG_NAME = 'Bartholomew Featherstonehaugh-Montgomery III'   # too wide: the fit loops shrink it


def counted(filename):
    """Fonts built anywhere in the game package count (screens move out of legacy.py phase by phase)."""
    filename = os.path.abspath(filename)
    return os.path.commonpath([filename, PACKAGE]) == PACKAGE


class FontCounter:
    def __init__(self, real):
        self.real, self.calls = real, []

    def __call__(self, *args, **kwargs):
        caller = sys._getframe(1).f_code
        if counted(caller.co_filename):
            self.calls.append((caller.co_name, args))
        return self.real(*args, **kwargs)


class LegacyFontSiteTests(unittest.TestCase):
    maxDiff = None   # show every font a failing frame built
    @classmethod
    def setUpClass(cls):
        cls.data = tempfile.TemporaryDirectory()
        cls.old_local_app_data = os.environ.get('LOCALAPPDATA')
        os.environ['LOCALAPPDATA'] = cls.data.name
        from solitaireplus.app import runtime_support
        saves = os.path.join(cls.data.name, 'saves')
        os.makedirs(saves, exist_ok=True)
        runtime_support.save_directory = lambda: saves
        from solitaireplus import legacy
        from solitaireplus.app import state
        from solitaireplus.ui import text as ui_text
        cls.legacy, cls.state, cls.ui_text = legacy, state, ui_text
        state.game_mouse_pos = None
        state.menu_mouse_pos = None

    @classmethod
    def tearDownClass(cls):
        if cls.old_local_app_data is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = cls.old_local_app_data
        cls.data.cleanup()

    def setUp(self):
        clear = getattr(self.ui_text, 'clear_font_cache', None)
        if clear is not None:
            clear()

    def assert_fonts_built_once(self, draw):
        font, sysfont = FontCounter(pygame.font.Font), FontCounter(pygame.font.SysFont)
        with patch('pygame.font.Font', font), patch('pygame.font.SysFont', sysfont):
            draw()
            first = font.calls + sysfont.calls
            del font.calls[:], sysfont.calls[:]
            draw()
            second = font.calls + sysfont.calls
        self.assertTrue(first, 'the screen did not reach its font code')
        self.assertEqual(second, [], 'fonts were built again on the second frame')

    def screens(self):
        legacy, state = self.legacy, self.state
        from solitaireplus.menus import customize
        from solitaireplus.profile import profile_editor
        from solitaireplus.career import hub_screen, leaderboard_engine, leaderboards_screen, real_estate_screen
        from solitaireplus.career.events import event_select_screen, summary_screen

        def score_four_opponent_select():
            from solitaireplus.games.cards import score_four_screen
            if not state.score_four_opponent_choices:
                state.score_four_opponent_choices = legacy.get_score_four_opponent_choices()
            score_four_screen.draw_score_four_opponent_select()

        def career_event_summary():
            state.career_event_summary_title = 'Casino Night'
            state.career_event_summary_lines = [f'Result line {n}' for n in range(9)]   # > 7 lines
            summary_screen.draw_career_event_summary()

        real_leaderboard = leaderboard_engine.get_career_leaderboard

        def leaderboard_with_changes(*args, **kwargs):
            board = real_leaderboard(*args, **kwargs)
            for entry in board:
                entry['last_change'] = 3
            return board

        def career_leaderboards():
            with patch.object(leaderboard_engine, 'get_career_leaderboard', leaderboard_with_changes):
                leaderboards_screen.draw_career_leaderboards()

        def career_event_select():
            from solitaireplus.debug import actions as debug_actions   # the F10 actions (Phase 10)
            debug_actions.debug_open_casino_night()
            event_select_screen.draw_career_event_select()

        def battle_bosses_opponent_select():
            from solitaireplus.games.arcade import machine_select
            if not state.battle_bosses_opponent_choices:
                state.battle_bosses_opponent_choices = machine_select.build_battle_bosses_opponent_choices()
            machine_select.draw_battle_bosses_opponent_select()

        return {
            'draw_score_four_opponent_select': score_four_opponent_select,
            'draw_career_event_summary': career_event_summary,
            'draw_career_hub': hub_screen.draw_career_hub,
            'draw_career_real_estate': real_estate_screen.draw_career_real_estate,
            'draw_career_leaderboards': career_leaderboards,
            'draw_career_event_select': career_event_select,
            'draw_battle_bosses_opponent_select': battle_bosses_opponent_select,
            'draw_customize_menu': customize.draw_customize_menu,
            'draw_profile_screen': profile_editor.draw_profile_screen,
            **self.b44_screens(),
        }

    def b44_screens(self):
        """The B44 screens, each in a fixed state (the same on every draw, so the frames can be compared)."""
        legacy, state = self.legacy, self.state
        from solitaireplus.app import fonts, window
        from solitaireplus.career import activities
        from solitaireplus.career.activities_ui import CareerActivityScreen
        from solitaireplus.career.alien_night import STORY as ALIEN_STORY
        from solitaireplus.career.events import event_screen
        from solitaireplus.games.arcade.ace_invaders_game import AceInvadersGame
        from solitaireplus.games.cards import score_four_screen, score_four_ui
        from solitaireplus.games.cards.score_four import ScoreFourGame
        from solitaireplus.games.solitaire import head_to_head_screen
        from solitaireplus.games.solitaire.card import Card
        from solitaireplus.games.solitaire.head_to_head import HeadToHeadRace
        from solitaireplus.games.solitaire.head_to_head_ui import draw_head_to_head_hud
        from solitaireplus.games.solitaire.restart import RestartPrompt

        def score_four_opponent():
            if not state.score_four_opponent_choices:
                state.score_four_opponent_choices = legacy.get_score_four_opponent_choices()
            return dict(state.score_four_opponent_choices[0], name=LONG_NAME)

        def score_four_game(mode):
            game = ScoreFourGame()
            game.mode = mode
            game.original_numbers = [3, 8, 4, 6]
            game.values = [Fraction(n) for n in game.original_numbers]
            game.card_suits = ['Spades', 'Hearts', 'Clubs', 'Diamonds']
            game.puzzle_start_time = game.last_hint_at = MONOTONIC - 12.0
            return game

        def score_four_namespace(game, **extra):
            # Writes (the table's button rects) go to the first map, not to the game's namespace.
            base = score_four_screen.score_four_namespace()
            return ChainMap(dict(score_four_game=game, score_four_opponent_npc=score_four_opponent(), **extra),
                            *base.maps)

        def score_four(draw, game, **extra):
            namespace = score_four_namespace(game, **extra)

            def frame():
                with patch('time.monotonic', return_value=MONOTONIC):
                    draw(window.game_surface, game, None, namespace)
            return frame

        mode_select = score_four_game('solo')
        mode_select.rating_info_open = True          # the rating rewards overlay too
        solo_hint = score_four_game('solo')
        solo_hint.hint_text = ' '.join(['Combine 8 and 4 with minus to make 4, then multiply by 6.'] * 3)
        competitive = score_four_game('competitive')
        competitive.round_complete, competitive.round_result = True, 'npc'
        competitive.round_result_time = MONOTONIC - 2.0
        competitive.solution = ' × '.join(['((8 − 4) × 6) ÷ (3 ÷ 3)'] * 3)   # too wide: the fit loop runs

        def score_four_difficulty_select():
            namespace = score_four_namespace(score_four_game('solo'))
            with patch('time.monotonic', return_value=MONOTONIC):
                score_four_ui.draw_difficulty_select(window.game_surface, None, namespace)

        story = activities.new_story()
        night = activities.start_night(story)
        alien_story = activities.new_story(data=ALIEN_STORY)
        alien_night = dict(activities.start_night(alien_story, data=ALIEN_STORY), kind='alien')

        def career_activity(view, activity, activity_story):
            screen = CareerActivityScreen()

            def frame():
                screen.identity = (id(activity), activity.get('scene'), activity['night'], activity['claimed'])
                screen.view, screen.page = view, 0
                screen.draw(window.game_surface, activity, None, 500, activity_story)
            return frame

        def head_to_head_select():
            if not state.head_to_head_opponents:
                head_to_head_screen.start_head_to_head_event()
            state.head_to_head_selected_index = 0
            event_screen.draw_head_to_head_event()

        def head_to_head_countdown():
            if not state.head_to_head_opponents:
                head_to_head_screen.start_head_to_head_event()
            race = HeadToHeadRace(rng=random.Random(44))   # the same race on every frame
            race.prepare(state.head_to_head_opponents[0], player_rating=1000, now_ms=0)
            draw_head_to_head_hud(window.game_surface, race, 3, 500, legacy.get_npc_portrait_surface,
                                  fonts.option_label_font, fonts.difficulty_detail_font, fonts.ui_small_font)

        restart_prompt = RestartPrompt()
        invaders = AceInvadersGame()
        invaders.start_session('standard', rng_seed=44)

        def ace_invaders_fallback_enemy():
            # No enemy artwork at all: the game draws a framed "A♠"-style glyph instead.
            with patch.object(invaders, '_fit_image', return_value=None):
                for enemy in invaders.enemies[:4]:
                    invaders._draw_enemy(window.game_surface, enemy)

        card = Card('Hearts', 'Q')
        card.face_up = True

        return {
            'score_four_mode_select': score_four(score_four_ui.draw_mode_select, mode_select),
            'score_four_difficulty_select': score_four_difficulty_select,
            'score_four_table_solo_hint': score_four(score_four_ui.draw_score_four_table, solo_hint),
            'score_four_table_competitive_npc_solved': score_four(score_four_ui.draw_score_four_table, competitive),
            'career_activity_intro': career_activity('intro', night, story),
            'career_activity_choices': career_activity('choices', night, story),
            'career_activity_alien_intro': career_activity('intro', alien_night, alien_story),
            'draw_head_to_head_selection': head_to_head_select,
            'draw_head_to_head_hud_countdown': head_to_head_countdown,
            'restart_prompt': lambda: restart_prompt.draw(window.game_surface, None),
            'ace_invaders_fallback_enemy': ace_invaders_fallback_enemy,
            'card_draw_unused_by_game': lambda: card.draw(window.game_surface, 100, 100),
        }

    def test_screens_build_their_fonts_only_once(self):
        for name, draw in self.screens().items():
            with self.subTest(screen=name):
                self.setUp()
                self.assert_fonts_built_once(draw)

    def test_shared_fonts_draw_the_same_pixels_as_fresh_ones(self):
        """A frame drawn with cached fonts (after another frame used them) matches the old way,
        which built every font fresh; a shared font changed by a draw would show up here."""
        from solitaireplus.app import window
        real_font, real_sysfont = pygame.font.Font, pygame.font.SysFont

        def fresh_font(name, size, bold=False, italic=False, sysfont=False):
            if sysfont:
                return real_sysfont(name, size, bold=bold, italic=italic)
            return real_font(name, size)

        def frame(draw):
            window.game_surface.fill((90, 20, 140))
            draw()
            return pygame.image.tobytes(window.game_surface, 'RGB')

        with patch('pygame.time.get_ticks', return_value=123_456):
            for name, draw in self.screens().items():
                with self.subTest(screen=name):
                    self.setUp()
                    with patch.object(self.ui_text, 'get_font', fresh_font):
                        old = frame(draw)
                        self.assertEqual(frame(draw), old, 'the screen is not deterministic')
                    frame(draw)
                    self.assertEqual(frame(draw), old)


if __name__ == '__main__':
    unittest.main()
