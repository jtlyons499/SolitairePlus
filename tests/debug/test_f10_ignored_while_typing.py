"""D1 (complete): the F10 debug menu hotkey does nothing while the player types in a text field.

The text fields of the single-player game that take the keyboard focus:
* the Profile screen's name, country, age, hometown and bio (state.profile_*_active);
* the manual bet box at the Texas Hold'em table (state.holdem_manual_bet_active);
* the manual bet box at the Five-Card Draw table (five_card_draw_ui.five_card_draw_manual_bet_active()).
With one of them focused, F10 neither opens the debug menu nor changes the field: the key goes to
the screen like any other key, and the fields ignore it. Without a focused field F10 works as before.

The real main loop (solitaireplus/app/loop.py) and the real Profile key handling run in a fake
namespace (the helpers of tests/app/test_loop_mouse_and_screen_hooks.py), so the game is never started.
"""
import os
import types
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.app import state_names
from tests.app import test_loop_mouse_and_screen_hooks as loop_test
from tests.support import locate

PROFILE_FILE = 'solitaireplus/profile/profile_editor.py'
PROFILE_FIELDS = ('name', 'country', 'age', 'hometown', 'bio')
PROFILE_TEXTS = {'name': 'Dan', 'country': 'USA', 'age': '41', 'hometown': 'Dayton', 'bio': 'Plays a lot.'}


def f10():
    return loop_test.key(pygame.KEYDOWN, pygame.K_F10)


def typed(char):
    return pygame.event.Event(pygame.KEYDOWN, key=ord(char), mod=0, unicode=char)


def text_field_values(active=(), holdem_bet=False, draw_bet=False):
    """The loop's view of every text field (none focused unless named)."""
    values = {f'profile_{field}_active': field in active for field in PROFILE_FIELDS}
    values.update({f'profile_{field}_text': text for field, text in PROFILE_TEXTS.items()})
    values['holdem_manual_bet_active'] = holdem_bet
    values['five_card_draw_manual_bet_active'] = lambda: draw_bet
    return values


class F10WhileTyping(unittest.TestCase):

    def run_frames(self, current_state, events, **fields):
        """Run the main loop on `current_state` for one frame of `events`; return env and the keys
        the screen itself received."""
        keys = []
        module = types.SimpleNamespace(loop_event_screen=lambda event: keys.append(event.key))
        frames = [((0, 0), []), ((0, 0), list(events)), ((0, 0), [])]
        env = loop_test.loop_env(frames, module, {current_state: 'screen', state_names.STATE_DEBUG_MENU: 'debug_menu'},
                                 current_state)
        env.update(text_field_values(**fields))
        loop_test.run_loop(env)
        return env, keys

    def run_profile(self, events, active=(), current_state=state_names.STATE_PROFILE):
        """Like run_frames, with the real Profile screen key handling."""
        frames = [((0, 0), []), ((0, 0), list(events)), ((0, 0), [])]
        env = loop_test.loop_env(frames, None, {state_names.STATE_PROFILE: 'solitaireplus.profile.profile_editor',
                                                state_names.STATE_DEBUG_MENU: 'debug_menu'}, current_state)
        env.update(text_field_values(active=active))
        locate.exec_functions(['handle_event'], env, path=PROFILE_FILE)
        loop_test.run_loop(env)
        return env

    def assert_menu_stayed_shut(self, env, current_state):
        self.assertEqual(env['current_state'], current_state, 'F10 opened the debug menu while typing')
        self.assertIsNone(env['debug_previous_state'])

    def assert_menu_opened(self, env, from_state):
        self.assertEqual(env['current_state'], state_names.STATE_DEBUG_MENU)
        self.assertEqual(env['debug_previous_state'], from_state)

    # ------------------------------------------------------------------ the Profile screen

    def test_f10_with_an_active_profile_field_leaves_the_state_unchanged(self):
        for field in PROFILE_FIELDS:
            with self.subTest(field=field):
                env = self.run_profile([f10()], active=(field,))

                self.assert_menu_stayed_shut(env, state_names.STATE_PROFILE)
                self.assertEqual({name: env[f'profile_{name}_active'] for name in PROFILE_FIELDS},
                                 {name: name == field for name in PROFILE_FIELDS}, 'the field lost the focus')
                self.assertEqual({name: env[f'profile_{name}_text'] for name in PROFILE_FIELDS}, PROFILE_TEXTS)

    def test_typing_goes_on_after_an_ignored_f10(self):
        env = self.run_profile([typed('a'), f10(), typed('n')], active=('name',))

        self.assert_menu_stayed_shut(env, state_names.STATE_PROFILE)
        self.assertEqual(env['profile_name_text'], 'Danan')
        self.assertTrue(env['profile_name_active'])

    def test_f10_on_the_profile_screen_without_a_focused_field_opens_the_menu(self):
        env = self.run_profile([f10()])
        self.assert_menu_opened(env, state_names.STATE_PROFILE)

    def test_a_stale_profile_flag_on_another_screen_does_not_block_f10(self):
        # The Profile fields exist only on the Profile screen.
        env, _keys = self.run_frames(state_names.STATE_MENU, [f10()], active=('name',))
        self.assert_menu_opened(env, state_names.STATE_MENU)

    # ------------------------------------------------------------------ the poker manual bet boxes

    def test_f10_while_typing_a_holdem_bet_leaves_the_state_unchanged(self):
        env, keys = self.run_frames(state_names.STATE_TEXAS_HOLDEM, [f10()], holdem_bet=True)
        self.assert_menu_stayed_shut(env, state_names.STATE_TEXAS_HOLDEM)
        self.assertTrue(env['holdem_manual_bet_active'])
        self.assertEqual(keys, [pygame.K_F10], 'the bet box did not get the key like any other key')

    def test_f10_at_the_holdem_table_without_the_bet_box_opens_the_menu(self):
        env, keys = self.run_frames(state_names.STATE_TEXAS_HOLDEM, [f10()])
        self.assert_menu_opened(env, state_names.STATE_TEXAS_HOLDEM)
        self.assertEqual(keys, [])

    def test_f10_while_typing_a_five_card_draw_bet_leaves_the_state_unchanged(self):
        env, _keys = self.run_frames(state_names.STATE_FIVE_CARD_DRAW, [f10()], draw_bet=True)
        self.assert_menu_stayed_shut(env, state_names.STATE_FIVE_CARD_DRAW)

    def test_f10_at_the_five_card_draw_table_without_the_bet_box_opens_the_menu(self):
        env, _keys = self.run_frames(state_names.STATE_FIVE_CARD_DRAW, [f10()])
        self.assert_menu_opened(env, state_names.STATE_FIVE_CARD_DRAW)

    # ------------------------------------------------------------------ F10 still works elsewhere

    def test_f10_still_opens_and_closes_the_menu(self):
        env, keys = self.run_frames(state_names.STATE_MENU, [f10(), f10()])
        self.assertEqual(env['current_state'], state_names.STATE_MENU)
        self.assertEqual(env['debug_previous_state'], state_names.STATE_MENU)
        self.assertEqual(keys, [])


class FiveCardDrawBetBoxFocus(unittest.TestCase):
    def test_the_focus_flag_is_readable_outside_the_module(self):
        from solitaireplus.games.poker import five_card_draw_ui

        saved = (five_card_draw_ui._ui.draw_manual_bet_active, five_card_draw_ui._ui.draw_manual_bet_text)
        self.addCleanup(setattr, five_card_draw_ui._ui, 'draw_manual_bet_active', saved[0])
        self.addCleanup(setattr, five_card_draw_ui._ui, 'draw_manual_bet_text', saved[1])

        five_card_draw_ui._ui.draw_manual_bet_active = True
        self.assertIs(five_card_draw_ui.five_card_draw_manual_bet_active(), True)
        five_card_draw_ui.clear_five_card_draw_manual_bet()
        self.assertIs(five_card_draw_ui.five_card_draw_manual_bet_active(), False)


if __name__ == '__main__':
    unittest.main()
