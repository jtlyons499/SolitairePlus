"""Table timers and per-session screen state are reset by every Hold'em-family table (B86 group 4).

games/poker/table_timers.py holds the one list of screen timers. Every session starter resets
them (plus the processed-showdown marker and the table-sweep flag) and every session finisher
zeroes them. Before, Hold'em's finisher zeroed only its hand-win sound timer and its starter left
that timer alone.

NEW-5: the Hold'em chat, its scroll, unread flag, speech bubbles and queued quick-chat replies
are cleared when a session starts (Five-Card Draw and Stud already cleared theirs). B86 review
F12: so are a half-typed manual bet, a bet-slider drag and an open quick-chat menu, as in
Five-Card Draw's reset.

B86 review F12 follow-up: Five-Card Draw, Seven-Card Stud, Five-O and Blind Man's Bluff share
a Quick Chat controller per table that the screens reuse with one engine. A new session now
closes its menu, drops queued NPC replies and clears its history (it reset only when the engine
object changed).

NEW-2 (fixed in group 2, asserted here through the Stud screen): last_resolved_pot is 0 when a
hand starts and the resolved pot after a showdown.

The real session starters and finishers run with career cash and NPC selection stubbed, as in
tests/games/poker/test_holdem_session_end_timer.py (tests/support/poker_screens.py).
"""
import unittest
from unittest import mock

from solitaireplus.app import state
from solitaireplus.games.poker import (blind_mans_bluff_screen, five_card_draw_screen, five_o_screen,
                                       holdem_screen, holdem_ui, seven_card_stud_screen)
from solitaireplus.games.poker.blind_mans_bluff import BlindMansBluffGame
from solitaireplus.games.poker.five_o import FiveOPokerGame
from solitaireplus.games.poker.variant_quick_chat import controller_for
from solitaireplus.games.poker.ai import get_poker_personality_profile
from solitaireplus.games.poker.five_card_draw import FiveCardDrawGame
from solitaireplus.games.poker.holdem import TexasHoldemGame
from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame
from solitaireplus.games.poker.table_timers import TABLE_TIMERS, reset_table_session, reset_table_timers
from tests.support.poker_screens import OPPONENTS, ScreenHarness

# prefix, screen module, engine class, session starter, session finisher
TABLES = (
    ("texas_holdem", holdem_screen, TexasHoldemGame,
     "start_texas_holdem_session", "finish_texas_holdem_session"),
    ("five_card_draw", five_card_draw_screen, FiveCardDrawGame,
     "start_five_card_draw_session", "finish_five_card_draw_session"),
    ("seven_card_stud", seven_card_stud_screen, SevenCardStudGame,
     "start_seven_card_stud_session", "finish_seven_card_stud_session"),
)
PREFIXES = tuple(table[0] for table in TABLES)
SESSION_FIELDS = ("last_processed_showdown_hand", "table_sweep_rewarded")


def make_stale(prefix):
    """Leftovers from an earlier session: every timer pending, a showdown processed, a sweep paid."""
    for number, name in enumerate(TABLE_TIMERS, 1):
        setattr(state, f"{prefix}_{name}", 90_000 + number)
    setattr(state, f"{prefix}_last_processed_showdown_hand", 7)
    setattr(state, f"{prefix}_table_sweep_rewarded", True)


def timers(prefix):
    return {name: getattr(state, f"{prefix}_{name}") for name in TABLE_TIMERS}


def always_call(personality, context, rng=None):
    return {"action": "call", "profile": get_poker_personality_profile("balanced"), "bluff": False}


class TableTimerModuleTests(unittest.TestCase):
    def setUp(self):
        ScreenHarness(self)   # restores app state afterwards

    def test_the_timer_list(self):
        self.assertEqual(TABLE_TIMERS, ("next_npc_action_at", "round_advance_at", "next_hand_at",
                                        "session_end_at", "hand_win_sound_at"))

    def test_every_field_exists_in_app_state_with_a_cleared_default(self):
        from pathlib import Path
        import ast
        source = Path(state.__file__).read_text(encoding="utf-8")
        assigned = {node.targets[0].id: node.value
                    for node in ast.parse(source).body
                    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}

        def default(name):
            self.assertIn(name, assigned, f"state.py has no {name}")
            return ast.literal_eval(assigned[name])

        for prefix in PREFIXES:
            for name in TABLE_TIMERS:
                self.assertEqual(default(f"{prefix}_{name}"), 0, f"{prefix}_{name}")
            self.assertEqual(default(f"{prefix}_last_processed_showdown_hand"), 0)
            self.assertIs(default(f"{prefix}_table_sweep_rewarded"), False)

    def test_reset_table_timers_clears_only_that_tables_timers(self):
        for prefix in PREFIXES:
            with self.subTest(prefix):
                for other in PREFIXES:
                    make_stale(other)
                reset_table_timers(prefix)
                self.assertEqual(set(timers(prefix).values()), {0})
                self.assertEqual(getattr(state, f"{prefix}_last_processed_showdown_hand"), 7)
                self.assertIs(getattr(state, f"{prefix}_table_sweep_rewarded"), True)
                for other in PREFIXES:
                    if other != prefix:
                        self.assertNotIn(0, timers(other).values())

    def test_reset_table_session_also_clears_the_showdown_marker_and_sweep_flag(self):
        for prefix in PREFIXES:
            with self.subTest(prefix):
                make_stale(prefix)
                reset_table_session(prefix)
                self.assertEqual(set(timers(prefix).values()), {0})
                self.assertEqual(getattr(state, f"{prefix}_last_processed_showdown_hand"), 0)
                self.assertIs(getattr(state, f"{prefix}_table_sweep_rewarded"), False)


class SessionStartAndFinishTests(unittest.TestCase):
    def test_start_resets_and_finish_zeroes_every_timer(self):
        for prefix, module, game_class, start, finish in TABLES:
            with self.subTest(prefix):
                screen = ScreenHarness(self)
                game = screen.stub(module, game_class())
                screen.ticks = 50_000
                make_stale(prefix)
                self.assertTrue(getattr(module, start)(1000, OPPONENTS))
                self.assertTrue(game.hand_number >= 1)
                self.assertEqual(timers(prefix), dict.fromkeys(TABLE_TIMERS, 0))
                self.assertEqual(getattr(state, f"{prefix}_last_processed_showdown_hand"), 0)
                self.assertIs(getattr(state, f"{prefix}_table_sweep_rewarded"), False)

                make_stale(prefix)
                getattr(module, finish)()
                self.assertEqual(timers(prefix), dict.fromkeys(TABLE_TIMERS, 0))


class HoldemChatResetTests(unittest.TestCase):
    """NEW-5: a new Hold'em session starts with an empty chat."""

    def setUp(self):
        self.screen = ScreenHarness(self)
        self.game = self.screen.stub(holdem_screen, TexasHoldemGame())
        self.addCleanup(holdem_ui.holdem_chat_history.clear)
        self.addCleanup(holdem_ui.holdem_quick_chat_pending.clear)
        self.addCleanup(holdem_ui._holdem_speech_overlay.clear)

    def test_start_clears_the_chat_left_by_the_last_session(self):
        state.holdem_table_chat_enabled = True
        state.poker_chat_popups_enabled = True
        chat = holdem_ui.holdem_chat_history
        holdem_ui.add_holdem_chat_message("Rival 1", "See you next time.")
        holdem_ui.holdem_quick_chat_pending.append((99_999, "Rival 2", "A late reply."))
        state.holdem_active_tab = "log"
        state.holdem_chat_unread = True
        state.holdem_chat_scroll = 4
        self.assertTrue(chat)
        self.assertTrue(holdem_ui._holdem_speech_overlay.entries)

        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        self.assertIs(holdem_ui.holdem_chat_history, chat)   # cleared in place, still shared
        self.assertEqual(chat, [])
        self.assertEqual(holdem_ui.holdem_quick_chat_pending, [])
        self.assertEqual(holdem_ui._holdem_speech_overlay.entries, {})
        self.assertIs(state.holdem_chat_unread, False)
        self.assertEqual(state.holdem_chat_scroll, 0)

    def test_start_clears_the_bet_entry_slider_drag_and_quick_chat_menu(self):
        state.holdem_manual_bet_active = True
        state.holdem_manual_bet_text = "125"
        state.holdem_bet_slider_dragging = True
        state.holdem_quick_chat_open = True
        state.holdem_quick_chat_target_mode = "crush"
        self.assertTrue(holdem_screen.start_texas_holdem_session(1000, OPPONENTS))
        self.assertIs(state.holdem_manual_bet_active, False)
        self.assertEqual(state.holdem_manual_bet_text, "")
        self.assertIs(state.holdem_bet_slider_dragging, False)
        self.assertIs(state.holdem_quick_chat_open, False)
        self.assertIsNone(state.holdem_quick_chat_target_mode)

    def test_reset_texas_holdem_ui_session_alone(self):
        state.holdem_table_chat_enabled = True
        holdem_ui.add_holdem_chat_message("Rival 1", "Hello.")
        state.holdem_chat_scroll = 2
        holdem_ui.reset_texas_holdem_ui_session()
        self.assertEqual(holdem_ui.holdem_chat_history, [])
        self.assertEqual(state.holdem_chat_scroll, 0)
        self.assertIs(state.holdem_chat_unread, False)


class VariantQuickChatResetTests(unittest.TestCase):
    """F12 at the tables with the shared Quick Chat controller."""

    TABLES = (
        ("five_card_draw", five_card_draw_screen, FiveCardDrawGame,
         lambda: five_card_draw_screen.start_five_card_draw_session(1000, OPPONENTS)),
        ("seven_card_stud", seven_card_stud_screen, SevenCardStudGame,
         lambda: seven_card_stud_screen.start_seven_card_stud_session(1000, OPPONENTS)),
        ("five_o_poker", five_o_screen, FiveOPokerGame,
         lambda: five_o_screen.start_five_o_poker_session(1000)),
        ("blind_mans_bluff", blind_mans_bluff_screen, BlindMansBluffGame,
         lambda: blind_mans_bluff_screen.start_blind_mans_bluff_session(1000)),
    )

    def test_a_new_session_closes_the_menu_and_drops_the_last_session_chat(self):
        for game_id, module, engine, start in self.TABLES:
            with self.subTest(game_id):
                screen = ScreenHarness(self)
                game = screen.stub(module, engine())
                controller = controller_for(game_id)
                self.addCleanup(controller.reset_session)
                self.assertTrue(start())
                controller.bind(game)
                adapter = controller.adapter
                # The last session ends with the menu open and an NPC reply still queued.
                controller.open = True
                controller.target_key = "crush"
                controller.pending.append((99_999, "Old Rival", "A late reply."))
                controller.local_history.append("Old Rival: See you.")

                self.assertTrue(start())   # the same engine object, a new session
                self.assertIs(controller.open, False)
                self.assertIsNone(controller.target_key)
                self.assertEqual(controller.pending, [])
                self.assertEqual(controller.local_history, [])
                # The next bind builds a fresh adapter for the reused engine.
                self.assertIsNot(controller.bind(game), adapter)


class StudResolvedPotScreenTests(unittest.TestCase):
    """NEW-2 through the Seven-Card Stud screen: the resolved pot belongs to the hand just played."""

    def setUp(self):
        self.screen = ScreenHarness(self)
        self.game = self.screen.stub(seven_card_stud_screen, SevenCardStudGame())
        for name, value in (("post_seven_card_stud_chat", lambda entry: None),
                            ("generate_npc_action_chat", lambda game, index: None)):
            patcher = mock.patch.object(seven_card_stud_screen, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def play_frames(self, until, limit=5000):
        """Run the screen 100 ms a frame; the human presses Check / Call whenever it may act."""
        game = self.game
        for _ in range(limit):
            if until():
                return
            if game.can_player_act_now():
                self.assertTrue(game.player_call() if game.can_player_call() else game.player_check())
            self.screen.ticks += 100
            seven_card_stud_screen.loop_late_seven_card_stud()
        self.fail("the Stud table did not get there")

    def play_first_hand(self, human_wins):
        """Every seat calls to the end; the showdown ranks decide whether the human wins.

        The ranks are forced (a high-card score per seat: the human 14 or 2, seat 1 13, the rest
        9), so the fan-award check below runs on every run instead of only when the shuffle
        happens to favour the human."""
        game = self.game
        game.last_resolved_pot = 999   # left over from an earlier session
        self.screen.ticks = 1000
        self.assertTrue(seven_card_stud_screen.start_seven_card_stud_session(1000, OPPONENTS))
        self.assertEqual(game.hand_number, 1)
        self.assertEqual(game.last_resolved_pot, 0)

        ranks = [14 if human_wins else 2, 13, 9, 9, 9]
        with mock.patch("solitaireplus.games.poker.holdem.decide_poker_action", always_call), \
                mock.patch.object(game, "get_showdown_result",
                                  side_effect=lambda seat: ((0, ranks[seat]), [])):
            self.play_frames(lambda: game.hand_complete)
            self.assertEqual(game.current_stage, "showdown")
            # Every seat called to the end: a real showdown, not a fold win.
            self.assertEqual(sorted(game.last_pot_awards[0]["eligible"]), [0, 1, 2, 3, 4])
            self.assertEqual(game.winner_indexes, [0] if human_wins else [1])
            resolved = sum(award["amount"] for award in game.last_pot_awards)
            self.assertGreater(resolved, 0)
            self.assertEqual(game.last_resolved_pot, resolved)
            self.assertEqual(game.get_display_pot_amount(), resolved)
            self.play_frames(lambda: state.seven_card_stud_last_processed_showdown_hand == 1)
            # The fan award for a won hand is the human's net (the pot less its own chips);
            # a lost hand earns none.
            net = resolved - game.player_hand_contribution
            self.assertGreater(net, 0)
            self.assertEqual(self.screen.cash_wins, [net] if human_wins else [])

            # The auto-deal starts hand 2 with a clean record.
            self.play_frames(lambda: game.hand_number == 2)
            self.assertEqual(game.last_resolved_pot, 0)
            self.assertEqual(game.last_pot_awards, [])

    def test_last_resolved_pot_is_reset_at_the_start_and_set_at_showdown(self):
        self.play_first_hand(human_wins=True)

    def test_a_lost_showdown_earns_no_fan_award(self):
        self.play_first_hand(human_wins=False)


if __name__ == "__main__":
    unittest.main()
