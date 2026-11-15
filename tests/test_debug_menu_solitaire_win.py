"""D1 (complete): the F10 debug menu's 'Win this Solitaire round' button.

The designer's instant win used to be the F8 key at the Solitaire table (Phase 4 removed the key
and kept its body as games.solitaire.screen.instant_win_round()). The F10 menu now has a button
for it in the Solitaire column. It works only when the menu was opened from the Solitaire table
(the screen before the menu is PLAYING): it goes back to the table and wins the round, as F8 did.
Opened from anywhere else, the button is drawn disabled and a click on it does nothing.

The real menu screen, the real button hit boxes and the real instant win run here, on a real
Solitaire Game (card images not loaded), like tests/test_solitaire_debug_hotkeys.py.
"""
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.app import state, state_names
from solitaireplus.debug import menu, menu_screen
from solitaireplus.games.solitaire import screen as solitaire_screen
from solitaireplus.games.solitaire.rules import Game

LABEL = 'Win this Solitaire round'
OLD_F8_SUMMARY = {
    'moves': 112,
    'elapsed_seconds': 387,
    'base_score': 5000,
    'move_bonus': 1700,
    'time_bonus': 952,
    'score': 7652,
    'xp_earned': 150,
    'remark': 'Efficient work.',
}
STATE_NAMES = ('current_state', 'debug_previous_state', 'game_mouse_pos', 'current_game_mode',
               'game_pause_menu_open', 'confirm_return_to_menu')
# The disabled look of the other greyed-out buttons (Options: window sizes, Verified Solvable).
DISABLED_FILL = (72, 76, 74)
DISABLED_BORDER = (115, 120, 118)


def keep_state(test):
    missing = object()
    saved = {name: getattr(state, name, missing) for name in STATE_NAMES}

    def restore():
        for name, value in saved.items():
            if value is missing:
                if hasattr(state, name):
                    delattr(state, name)
            else:
                setattr(state, name, value)

    test.addCleanup(restore)


def win_button_rect():
    rect = menu._ACTION_RECTS.get(menu.ACTION_WIN_SOLITAIRE_ROUND)
    if rect is None:
        raise AssertionError('the debug menu has no Win this Solitaire round button')
    return rect


class WinButtonClickTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.surface = pygame.display.set_mode((1, 1))

    def setUp(self):
        keep_state(self)
        state.current_game_mode = 'free_play'
        state.game_pause_menu_open = False
        state.confirm_return_to_menu = False
        with patch.object(Game, 'load_card_images', return_value=None):
            self.game = Game(self.surface, Mock())
        self.sounds = MagicMock()
        for target, name, value in (
                (solitaire_screen, 'legacy', SimpleNamespace(game=self.game)),
                (menu_screen, 'sounds', self.sounds),
        ):
            patcher = patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def open_menu_from(self, previous_state):
        """What the F10 hotkey does: remember the screen, then show the menu."""
        state.debug_previous_state = previous_state
        state.current_state = state_names.STATE_DEBUG_MENU

    def click_win_button(self):
        state.game_mouse_pos = win_button_rect().center
        self.assertEqual(menu.get_debug_action(state.game_mouse_pos), menu.ACTION_WIN_SOLITAIRE_ROUND)
        menu_screen.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=state.game_mouse_pos))

    def assert_round_untouched(self):
        self.assertFalse(self.game.round_won)
        self.assertIsNone(self.game.round_summary)
        self.assertIsNone(self.game.victory_animation)
        self.game.audio.play_sound.assert_not_called()

    def test_from_the_solitaire_table_it_wins_the_round_like_f8(self):
        state.current_state = state_names.STATE_PLAYING
        self.open_menu_from(state_names.STATE_PLAYING)

        self.click_win_button()

        self.assertEqual(state.current_state, state_names.STATE_PLAYING, 'did not go back to the table')
        self.assertTrue(self.game.round_won)
        self.assertEqual(self.game.round_summary, OLD_F8_SUMMARY)
        self.game.audio.play_sound.assert_called_once_with('celebration_1')
        self.assertIsNotNone(self.game.victory_animation)
        self.assertEqual(len(self.game.victory_animation['cards']), 52)
        self.sounds.audio.play_sound.assert_called_once_with('button_click')

    def test_it_calls_the_solitaire_screens_instant_win(self):
        self.open_menu_from(state_names.STATE_PLAYING)
        with patch.object(solitaire_screen, 'instant_win_round') as instant_win:
            self.click_win_button()
        instant_win.assert_called_once_with()

    def test_from_any_other_screen_it_is_inert(self):
        for previous in (state_names.STATE_MENU, state_names.STATE_CAREER_HUB,
                         state_names.STATE_TEXAS_HOLDEM, state_names.STATE_OPTIONS, None):
            with self.subTest(previous=previous):
                self.sounds.reset_mock()
                self.open_menu_from(previous)

                self.click_win_button()

                self.assertEqual(state.current_state, state_names.STATE_DEBUG_MENU)
                self.assertEqual(state.debug_previous_state, previous)
                self.assert_round_untouched()
                self.sounds.audio.play_sound.assert_not_called()

    def test_it_is_inert_while_the_restart_prompt_is_open(self):
        # The old F8 key was swallowed by an open 'Restart this hand?' prompt; winning behind it
        # would leave the prompt over the victory animation.
        prompt = solitaire_screen.solitaire_restart_prompt
        self.addCleanup(setattr, prompt, 'open', prompt.open)
        prompt.open = True
        state.current_state = state_names.STATE_PLAYING
        self.open_menu_from(state_names.STATE_PLAYING)

        self.assertFalse(menu_screen.solitaire_win_available())
        self.click_win_button()

        self.assertEqual(state.current_state, state_names.STATE_DEBUG_MENU)
        self.assert_round_untouched()
        self.sounds.audio.play_sound.assert_not_called()

    def test_the_button_does_not_end_a_free_play_sandbox(self):
        # Like Close, it goes back to the running game instead of launching one (B21).
        self.assertNotIn(menu.ACTION_WIN_SOLITAIRE_ROUND, menu.LAUNCH_ACTIONS)
        self.assertNotIn(menu.ACTION_WIN_SOLITAIRE_ROUND, menu.CAREER_HUB_JUMP_ACTIONS)


class WinButtonLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()
        cls.font = pygame.font.Font(None, 22)

    def setUp(self):
        keep_state(self)

    def test_it_sits_in_the_solitaire_column_like_the_other_buttons(self):
        rect = win_button_rect()
        challenge = menu._ACTION_RECTS[menu.CHALLENGE_ENTRIES[-1][0]]
        self.assertEqual((rect.x, rect.width, rect.height), (challenge.x, challenge.width, challenge.height))
        self.assertGreater(rect.top, challenge.bottom, 'not below the Solitaire challenges')
        self.assertTrue(pygame.Rect(0, 0, 1366, 768).contains(rect))

    def test_it_overlaps_no_other_button_in_any_accordion_state(self):
        expanded = menu.get_expanded_minigame_category()
        self.addCleanup(self.set_accordion, expanded)
        for category_id in [None] + [entry[0] for entry in menu.MINIGAME_CATEGORIES]:
            with self.subTest(expanded=category_id):
                self.set_accordion(category_id)
                menu._rebuild_action_rects()
                rect = win_button_rect()
                others = {action: other for action, other in menu._ACTION_RECTS.items()
                          if action != menu.ACTION_WIN_SOLITAIRE_ROUND}
                self.assertEqual([action for action, other in others.items() if rect.colliderect(other)], [])

    @staticmethod
    def set_accordion(category_id):
        while menu.get_expanded_minigame_category() != category_id:
            current = menu.get_expanded_minigame_category()
            target = category_id if category_id is not None else current
            action = next(entry[1] for entry in menu.MINIGAME_CATEGORIES if entry[0] == target)
            menu.toggle_minigame_category(action)

    def draw(self, available, mouse_pos=None):
        surface = pygame.Surface((1366, 768))
        surface.fill((0, 0, 0))
        drawn = []

        def draw_menu_button(rect, text, mouse_pos, selected=False, font=None):
            drawn.append((pygame.Rect(rect), text, font))

        menu.draw_debug_menu(surface, mouse_pos, lambda **kwargs: None, lambda title: None,
                             draw_menu_button, self.font, self.font, solitaire_win_available=available)
        return surface, drawn

    def test_available_it_is_a_normal_menu_button(self):
        _surface, drawn = self.draw(True)
        self.assertIn((win_button_rect(), LABEL, self.font), drawn)

    def test_unavailable_it_is_drawn_disabled(self):
        surface, drawn = self.draw(False, mouse_pos=win_button_rect().center)
        rect = win_button_rect()
        self.assertNotIn(rect, [entry[0] for entry in drawn], 'drawn as a working button')
        self.assertEqual(tuple(surface.get_at((rect.left, rect.centery)))[:3], DISABLED_BORDER)
        self.assertEqual(tuple(surface.get_at((rect.left + 6, rect.centery)))[:3], DISABLED_FILL)
        # The label is still there (light grey text in the middle of the button).
        middle = surface.subsurface(rect.inflate(-40, -10))
        colours = {tuple(middle.get_at((x, y)))[:3] for x in range(middle.get_width())
                   for y in range(middle.get_height())}
        self.assertGreater(len(colours), 1, 'no label on the disabled button')

    def test_the_screen_enables_it_only_when_opened_from_the_table(self):
        fakes = {
            'window': SimpleNamespace(game_surface=object()),
            'panels': SimpleNamespace(draw_submenu_background=object(), draw_submenu_title=object()),
            'buttons': SimpleNamespace(draw_menu_button=object()),
            'fonts': SimpleNamespace(option_label_font=object(), difficulty_detail_font=object()),
        }
        for name, value in fakes.items():
            patcher = patch.object(menu_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        state.game_mouse_pos = None
        for previous, expected in ((state_names.STATE_PLAYING, True), (state_names.STATE_MENU, False),
                                   (state_names.STATE_CAREER_HUB, False), (None, False)):
            with self.subTest(previous=previous):
                state.debug_previous_state = previous
                with patch.object(menu_screen, 'draw_debug_menu') as draw_debug_menu:
                    menu_screen.draw()
                draw_debug_menu.assert_called_once()
                self.assertIs(draw_debug_menu.call_args.kwargs.get('solitaire_win_available'), expected)


if __name__ == '__main__':
    unittest.main()
