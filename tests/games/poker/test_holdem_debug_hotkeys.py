"""D1 (Hold'em): the F7 / Space / B debug hotkeys are gone from the Hold'em table.

F7 rigged a heads-up hand (debug_setup_holdem_heads_up), Space dealt the next street without any
betting and B bet $50 and printed the table to the console. The F10 debug menu never called
debug_setup_holdem_heads_up, so it is gone too. The real table controls (manual bet entry keys,
log scrolling, bet slider, Next Hand / Fold / Check-Call / Bet buttons) must keep working.
"""
import ast
import contextlib
import io
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame

from solitaireplus.app import state, state_names
from solitaireplus.games.poker import holdem_screen
from solitaireplus.games.poker.holdem import TexasHoldemGame

SCREEN_FILE = Path(holdem_screen.__file__)
DEBUG_KEYS = ('K_F7', 'K_SPACE', 'K_b')
STATE_NAMES = (
    'current_state', 'game_mouse_pos', 'career_event_has_activity', 'success', 'player_chat_action',
    'texas_holdem_starting_stack', 'texas_holdem_session_net', 'texas_holdem_next_npc_action_at',
    'texas_holdem_round_advance_at', 'texas_holdem_next_hand_at', 'texas_holdem_session_end_at',
)


def opponents(count=2):
    return [{'id': 'npc_%d' % seat, 'name': 'Rival %d' % seat} for seat in range(1, count + 1)]


class HoldemDebugHotkeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def setUp(self):
        missing = object()
        saved = {name: getattr(state, name, missing) for name in STATE_NAMES}

        def restore():
            for name, value in saved.items():
                if value is missing:
                    if hasattr(state, name):
                        delattr(state, name)
                else:
                    setattr(state, name, value)

        self.addCleanup(restore)
        state.current_state = state_names.STATE_TEXAS_HOLDEM
        state.game_mouse_pos = (0, 0)
        state.career_event_has_activity = False
        state.texas_holdem_starting_stack = 1000
        state.texas_holdem_session_net = 0
        state.texas_holdem_next_npc_action_at = 0
        state.texas_holdem_round_advance_at = 0
        state.texas_holdem_next_hand_at = 0
        state.texas_holdem_session_end_at = 0

        self.game = TexasHoldemGame()
        self.game.start_session(opponents(), 1000, 10)
        self.sounds = MagicMock()
        # The manual bet entry is closed: its key handler lets every key through.
        self.manual_bet_key = MagicMock(return_value=False)
        for name, value in (('texas_holdem_game', self.game), ('sounds', self.sounds),
                            ('handle_holdem_manual_bet_key', self.manual_bet_key)):
            patcher = patch.object(holdem_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    # ------------------------------------------------------------------ helpers

    def press(self, key, unicode=''):
        event = pygame.event.Event(pygame.KEYDOWN, key=key, mod=0, unicode=unicode)
        holdem_screen.loop_event_texas_holdem(event)
        return event

    def snapshot(self):
        g = self.game
        return {
            'stage': g.current_stage, 'hand_number': g.hand_number, 'hand_complete': g.hand_complete,
            'player_stack': g.player_stack, 'npc_stacks': list(g.npc_stacks), 'pot': g.pot,
            'current_bet': g.current_bet, 'player_round_bet': g.player_round_bet,
            'npc_round_bets': list(g.npc_round_bets), 'current_actor': g.current_actor,
            'community': [dict(card) for card in g.community_cards],
            'player_hand': [dict(card) for card in g.player_hand],
            'player_busted': g.player_busted, 'npc_busted': list(g.npc_busted),
            'timers': (state.texas_holdem_next_npc_action_at, state.texas_holdem_round_advance_at,
                       state.texas_holdem_next_hand_at, state.texas_holdem_session_end_at),
            'activity': state.career_event_has_activity,
        }

    def assert_key_changes_nothing(self, key, unicode=''):
        before = self.snapshot()
        out = io.StringIO()
        with contextlib.redirect_stdout(out), \
                patch.object(self.game, 'start_hand', wraps=self.game.start_hand) as start_hand, \
                patch.object(self.game, 'player_bet', wraps=self.game.player_bet) as player_bet:
            self.press(key, unicode)
        start_hand.assert_not_called()
        player_bet.assert_not_called()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(out.getvalue(), '', 'debug key printed to the console')
        self.sounds.audio.play_sound.assert_not_called()

    def start_hand(self):
        self.assertTrue(self.game.start_hand())
        self.assertEqual(self.game.current_stage, 'preflop')
        self.sounds.reset_mock()

    # ------------------------------------------------------------------ the debug keys are gone

    def test_space_before_a_hand_does_not_deal(self):
        self.assertIn(self.game.current_stage, ('idle', 'ready', 'showdown'))
        self.assert_key_changes_nothing(pygame.K_SPACE, ' ')

    def test_space_during_a_hand_does_not_deal_the_next_street(self):
        self.start_hand()
        for _ in range(4):
            self.assert_key_changes_nothing(pygame.K_SPACE, ' ')
        self.assertEqual(self.game.community_cards, [])

    def test_space_at_the_river_does_not_force_a_showdown(self):
        self.start_hand()
        self.game.current_stage = 'river'
        with patch.object(self.game, 'showdown', wraps=self.game.showdown) as showdown:
            self.assert_key_changes_nothing(pygame.K_SPACE, ' ')
        showdown.assert_not_called()

    def test_b_does_not_bet_or_print(self):
        self.start_hand()
        # A postflop spot where a $50 bet would be legal: nothing to call, player to act.
        self.game.current_stage = 'flop'
        self.game.current_bet = 0
        self.game.player_round_bet = 0
        self.game.npc_round_bets = [0 for _ in self.game.npcs]
        self.game.current_actor = 0
        self.assert_key_changes_nothing(pygame.K_b, 'b')

    def test_f7_does_not_rig_a_heads_up_hand(self):
        self.start_hand()
        self.assert_key_changes_nothing(pygame.K_F7)

    def test_debug_heads_up_setup_is_removed(self):
        self.assertFalse(hasattr(holdem_screen, 'debug_setup_holdem_heads_up'))

    def test_table_handler_binds_no_debug_key(self):
        tree = ast.parse(SCREEN_FILE.read_text(encoding='utf-8'))
        handler = next(node for node in ast.walk(tree)
                       if isinstance(node, ast.FunctionDef) and node.name == 'loop_event_texas_holdem')
        keys = {node.attr for node in ast.walk(handler)
                if isinstance(node, ast.Attribute) and node.attr in DEBUG_KEYS}
        self.assertEqual(keys, set(), "Hold'em table still binds a debug hotkey")

    # ------------------------------------------------------------------ the real controls still work

    def test_keys_still_reach_the_manual_bet_entry(self):
        self.manual_bet_key.return_value = True
        self.start_hand()
        before = self.snapshot()
        for key, char in ((pygame.K_5, '5'), (pygame.K_SPACE, ' '), (pygame.K_b, 'b'), (pygame.K_F7, '')):
            event = self.press(key, char)
            self.manual_bet_key.assert_called_with(event, self.game)
        self.assertEqual(self.manual_bet_key.call_count, 4)
        self.assertEqual(self.snapshot(), before)

    def test_mouse_wheel_over_the_log_scrolls_it(self):
        state.game_mouse_pos = holdem_screen.HOLDEM_LOG_RECT.center
        with patch.object(holdem_screen, 'scroll_holdem_log') as scroll:
            holdem_screen.loop_event_texas_holdem(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-1))
        scroll.assert_called_once()
        self.assertEqual(scroll.call_args.args[0], -1)

    def test_bet_slider_drag_and_release(self):
        state.game_mouse_pos = (321, 456)
        with patch.object(holdem_screen, 'drag_holdem_bet_slider') as drag, \
                patch.object(holdem_screen, 'stop_holdem_bet_slider_drag') as stop:
            holdem_screen.loop_event_texas_holdem(
                pygame.event.Event(pygame.MOUSEMOTION, pos=(321, 456), rel=(1, 0), buttons=(1, 0, 0)))
            holdem_screen.loop_event_texas_holdem(
                pygame.event.Event(pygame.MOUSEBUTTONUP, pos=(321, 456), button=1))
        drag.assert_called_once_with((321, 456))
        stop.assert_called_once_with()

    def click_action(self, action):
        state.game_mouse_pos = (500, 500)
        patches = (
            patch.object(holdem_screen, 'is_holdem_options_open', return_value=False),
            patch.object(holdem_screen, 'handle_holdem_manual_bet_click', return_value=False),
            patch.object(holdem_screen, 'handle_holdem_panel_click', return_value=False),
            patch.object(holdem_screen, 'update_holdem_bet_slider', return_value=False),
            patch.object(holdem_screen, 'get_texas_holdem_action', return_value=action),
            patch.object(holdem_screen, 'post_texas_holdem_chat'),
        )
        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            holdem_screen.loop_event_texas_holdem(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(500, 500), button=1))

    def test_next_hand_button_deals(self):
        hand_number = self.game.hand_number
        self.click_action(holdem_screen.HOLDEM_ACTION_NEXT_HAND)
        self.assertEqual(self.game.hand_number, hand_number + 1)
        self.assertEqual(self.game.current_stage, 'preflop')
        self.assertEqual(len(self.game.player_hand), 2)

    def test_check_call_button_calls_the_big_blind(self):
        self.start_hand()
        self.assertEqual(self.game.current_actor, 0)
        to_call = self.game.get_player_amount_to_call()
        self.assertGreater(to_call, 0)
        stack = self.game.player_stack
        self.click_action(holdem_screen.HOLDEM_ACTION_CHECK_CALL)
        self.assertEqual(self.game.player_stack, stack - to_call)
        self.assertEqual(self.game.get_player_amount_to_call(), 0)

    def test_fold_button_folds(self):
        self.start_hand()
        self.assertEqual(self.game.current_actor, 0)
        self.click_action(holdem_screen.HOLDEM_ACTION_FOLD)
        self.assertTrue(self.game.player_folded)


if __name__ == '__main__':
    unittest.main()
