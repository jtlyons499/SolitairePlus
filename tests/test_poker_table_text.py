"""What the poker tables show while the B86 rules run (B86 review follow-ups).

* Blind Man's Bluff: during an NPC's thinking pause the table says whose turn it is
  ("<name> is thinking…"); before, the engine set the text but the table never drew it.
  When the human faces a bet it may not raise (a short all-in that is not a full raise, or
  nobody left to answer a raise), the engine prompt, the table's prompt and its stake line
  do not name raising, as at the Five-O table (B86 review F8).
* Five-Card Draw and Seven-Card Stud: their showdown banner is one fixed-width line, so a
  multi-winner payout lists names and amounts only (Hold'em, whose banner wraps, names the
  hands too). The text fits the banner at the table font.
* Five-O: the bet-size preset also sizes the NPC's bet (one bet unit per round), so it cannot
  be changed while the NPC is thinking.
* NPC table talk (B86 review F14): every table uses one talk chance per action
  (holdem_chat.npc_action_chat_chance; Blind Man's Bluff used a flat 22% and Five-O 25%), with
  "all_in" for a call, bet or raise that leaves the NPC no chips. Five-O now shows its NPC's
  talk in the table's chat strip (with chat popups on); before, nothing drew it.
"""
import os
import random
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state
from solitaireplus.games.poker.ai import get_poker_personality_profile
from solitaireplus.games.poker.core import evaluate_best_hand
from solitaireplus.games.poker.holdem_chat import ACTION_CHAT_CHANCE, npc_action_chat_chance
from solitaireplus.games.poker.variant_quick_chat import controller_for, reset_variant_quick_chat
from solitaireplus.npc.personality import get_npc_traits
from tests.support.poker_variants import ADAPTERS_BY_KEY

BMB = ADAPTERS_BY_KEY["blind_mans_bluff"]
FIVE_O = ADAPTERS_BY_KEY["five_o_poker"]
SUIT_NAMES = {"c": "Clubs", "d": "Diamonds", "h": "Hearts", "s": "Spades"}


def cards(text):
    return [{"rank": item[:-1], "suit": SUIT_NAMES[item[-1]]} for item in text.split()]


def score(text):
    return evaluate_best_hand(cards(text))[0]


TWO_PAIR = score("Kc Kd 9h 9s 5c")          # Two Pair, Kings and Nines, 5 kicker
TRIPS = score("Ac Ad Ah 2s 3c")             # Three of a Kind, Aces, 3-2 kickers
WEAK = score("2c 4d 6h 8s 10c")


def forced(action):
    def decide(personality, context, rng=None):
        return {"action": action, "profile": get_poker_personality_profile("balanced"), "bluff": False}

    return decide


class FixedRandom(random.Random):
    """An engine rng whose random() is always `value` (choice and shuffle still vary)."""

    def __init__(self, value, seed="fixed"):
        super().__init__(seed)
        self.value = value

    def random(self):
        return self.value


class RecordingFont:
    """A real pygame font that remembers every string it renders."""

    def __init__(self, size, texts):
        self.font = pygame.font.Font(None, size)
        self.texts = texts

    def render(self, text, *args, **kwargs):
        self.texts.append(str(text))
        return self.font.render(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.font, name)


class TableTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    # ------------------------------------------------------------------ Blind Man's Bluff

    def draw_bluff(self, game):
        from solitaireplus.games.poker import blind_mans_bluff_ui
        texts = []
        surface = pygame.Surface((1366, 768))
        fonts = [RecordingFont(size, texts) for size in (40, 30, 23)]
        blind_mans_bluff_ui.draw_blind_mans_bluff(surface, None, game, "Player",
                                                  lambda **_kwargs: surface.fill((10, 20, 20)), *fonts)
        return texts

    def test_blind_mans_bluff_shows_who_is_thinking(self):
        game = BMB.new_game(random.Random("table-text-thinking"))
        game.npc_delay_seconds = 0.5
        game.hand_number = 1   # hand 2: seat 1 opens, so the hand starts with its pause
        with mock.patch("solitaireplus.games.poker.blind_mans_bluff.decide_poker_action", forced("check")):
            self.assertTrue(BMB.start_hand(game))
            for seat in (1, 2, 3):
                self.assertEqual(game.current_actor, seat)
                self.assertTrue(game.pending_npc_at)
                thinking = f"{game.get_name(seat)} is thinking…"
                self.assertEqual(game.result_text, thinking)
                self.assertIn(thinking, self.draw_bluff(game))
                game.pending_npc_at -= 1000.0   # the pause is over
                self.assertTrue(game.update())
        # The human's turn: no NPC is thinking and the usual prompt is back.
        self.assertEqual(game.current_actor, 0)
        texts = self.draw_bluff(game)
        self.assertFalse([text for text in texts if "is thinking" in text], texts)
        self.assertIn("Everyone else can see your card. Read their betting.", texts)

    def face_short_all_in_raises(self, all_in_stacks):
        """Every NPC checks, the human bets 100, then the NPCs answer with all-ins of
        all_in_stacks (seat 1 and 2) and seat 3 calls: the human faces the bet again."""
        game = BMB.new_game(random.Random("table-text-raise-prompt"))
        game.npc_delay_seconds = 0
        stacks = [500, *all_in_stacks, 500]
        BMB.force_open_round(game, stacks)
        script = {seat: ("raise", stacks[seat]) for seat in (1, 2)}
        script[3] = ("call", None)
        with mock.patch.object(game, "_npc_take_turn", lambda seat: game._act(seat, *script[seat])):
            game.current_actor = 0
            self.assertTrue(game.player_bet(100))
        self.assertEqual(game.current_actor, 0)
        self.assertEqual(game.bet_state, "player_response")
        return game

    def test_blind_mans_bluff_prompt_names_raising_only_when_the_human_may_raise(self):
        # F8 in BMB: short all-ins to 130 and 160 do not add up to a full raise of 100 over
        # the human's bet, so betting is not reopened for the human.
        game = self.face_short_all_in_raises([130, 160])
        self.assertEqual(game.get_player_actions(), ["fold", "call"])
        self.assertFalse(game.can_player_raise())
        self.assertEqual(game.result_text, "Call $60 or fold.")
        texts = self.draw_bluff(game)
        self.assertIn("Call $60 or fold blind.", texts)
        self.assertIn("Bet $160", texts)
        self.assertFalse([text for text in texts if "raise" in text.lower() and "Raised to" not in text], texts)

    def test_blind_mans_bluff_prompt_names_raising_when_the_human_may_raise(self):
        # A full raise (seat 2 all-in to 300) reopens the betting for the human.
        game = self.face_short_all_in_raises([130, 300])
        self.assertEqual(game.get_player_actions(), ["fold", "call", "raise"])
        self.assertEqual(game.result_text, "Call $200, raise, or fold.")
        texts = self.draw_bluff(game)
        self.assertIn("Call $200, raise, or fold blind.", texts)
        self.assertIn(f"Bet $300  •  Minimum raise to ${game.get_minimum_raise_to():,}", texts)

    # ------------------------------------------------------------------ Draw / Stud banner

    def showdown(self, key, contributions, live, scores):
        adapter = ADAPTERS_BY_KEY[key]
        game = adapter.new_game(random.Random(f"table-text-{key}"))
        adapter._force_end_state(game, contributions, live, 0)
        results = {seat: (scores[seat], []) for seat in range(adapter.seat_count) if live[seat]}
        with mock.patch.object(game, "get_showdown_result", side_effect=results.get):
            game.showdown()
        return game

    # Review cases: a two-way tie with two pair, and a three-winner side-pot result.
    CASES = (
        ([0, 1250, 0, 1250, 0], [False, True, False, True, False], [WEAK, TWO_PAIR, WEAK, TWO_PAIR, WEAK]),
        ([50, 100, 100, 100, 0], [True, True, False, True, False], [TRIPS, TWO_PAIR, WEAK, TWO_PAIR, WEAK]),
    )

    def test_holdem_payouts_name_each_winners_hand(self):
        game = self.showdown("texas_holdem", *self.CASES[0])
        name = game.get_table_player_name
        self.assertEqual(game.result_text,
                         f"Payouts: {name(1)} $1,250 with Two Pair, Kings and Nines, 5 kicker; "
                         f"{name(3)} $1,250 with Two Pair, Kings and Nines, 5 kicker.")

    def test_draw_and_stud_payouts_fit_their_one_line_banner(self):
        from solitaireplus.games.poker import five_card_draw_ui, seven_card_stud_ui
        banners = {
            "five_card_draw": (five_card_draw_ui, "draw_draw_showdown_banner"),
            "seven_card_stud": (seven_card_stud_ui, "draw_stud_showdown_banner"),
        }
        for key, (ui, banner) in banners.items():
            for contributions, live, scores in self.CASES:
                with self.subTest(key, contributions=contributions):
                    game = self.showdown(key, contributions, live, scores)
                    name = game.get_table_player_name
                    winners = [seat for seat in game.winner_indexes]
                    self.assertGreater(len(winners), 1)
                    self.assertNotIn(" with ", game.result_text)
                    if len(winners) == 2:
                        self.assertEqual(game.result_text, f"Payouts: {name(1)} $1,250; {name(3)} $1,250.")
                    else:
                        self.assertEqual(game.result_text, f"Payouts: You $200; {name(1)} $75; {name(3)} $75.")
                    # The screen may add " You are out of chips."; even then it fits at the table font.
                    for suffix in ("", " You are out of chips."):
                        game.result_text += suffix
                        fitted = []
                        real_fit = ui.render_text_fit

                        def fit(text, font, color, max_width, minimum_size=10):
                            rendered = real_fit(text, font, color, max_width, minimum_size)
                            fitted.append((text, rendered.get_width(), max_width, font.get_height()))
                            return rendered

                        with mock.patch.object(ui, "render_text_fit", fit):
                            getattr(ui, banner)(pygame.Surface((1366, 768)), game)
                        [(text, width, max_width, height)] = fitted
                        self.assertEqual(text, game.result_text)
                        self.assertLessEqual(width, max_width, text)

    # ------------------------------------------------------------------ Five-O presets

    # ------------------------------------------------------------------ NPC table talk

    def test_the_talk_chance_is_the_hold_em_one(self):
        npc = {"name": "Talker", "skill_tier": "mid"}
        unpredictability = get_npc_traits(npc)["unpredictability"]
        for action, chance in ACTION_CHAT_CHANCE.items():
            self.assertAlmostEqual(npc_action_chat_chance(npc, action),
                                   chance + 0.008 * (unpredictability - 1))

    def bluff_npc_talks(self, action, value, stacks=(500, 500, 500, 500), current_bet=0):
        """Seat 1 takes `action`; True if it talked with the engine rng at `value`."""
        game = BMB.new_game(random.Random("table-talk-bmb"))
        BMB.force_open_round(game, list(stacks))
        if current_bet:
            game._act(0, "bet", current_bet)
        BMB.give_turn(game, 1)
        game.rng = FixedRandom(value)
        BMB.npc_turn(game, 1, action)
        return bool(game.last_chat[1])

    def test_blind_mans_bluff_npcs_talk_as_often_as_at_hold_em(self):
        game = BMB.new_game(random.Random("table-talk-bmb"))
        npc = game.get_npc(1)
        check = npc_action_chat_chance(npc, "check")
        self.assertTrue(self.bluff_npc_talks("check", check - 0.001))
        self.assertFalse(self.bluff_npc_talks("check", check + 0.001))   # a flat 22% talked here
        # A call that puts the NPC all-in is an all-in for its talk, as at the Hold'em tables.
        all_in = npc_action_chat_chance(npc, "all_in")
        self.assertTrue(self.bluff_npc_talks("call", all_in - 0.001, (500, 50, 500, 500), 100))
        self.assertFalse(self.bluff_npc_talks("call", all_in + 0.001, (500, 50, 500, 500), 100))

    def five_o_after_npc_opens(self, action, value):
        game = FIVE_O.new_game(random.Random("table-talk-five-o"))
        game.npc_delay_seconds = 0
        game.hand_number = 1   # start_hand deals hand 2: the NPC opens the betting
        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", forced(action)):
            self.assertTrue(FIVE_O.start_hand(game))
            game.rng = FixedRandom(value)
            FIVE_O.place_all_cards(game)
        self.assertEqual(game.phase, "betting")
        return game

    def test_five_o_npc_talks_as_often_as_at_hold_em(self):
        npc = FIVE_O.new_game(random.Random("table-talk-five-o")).npc
        check = npc_action_chat_chance(npc, "check")
        self.assertTrue(self.five_o_after_npc_opens("check", check - 0.001).last_npc_chat)
        # A flat 25% talked here.
        self.assertEqual(self.five_o_after_npc_opens("check", check + 0.001).last_npc_chat, "")

    def test_five_o_shows_its_npc_talk_in_the_chat_strip(self):
        from solitaireplus.games.poker import five_o_ui
        reset_variant_quick_chat("five_o_poker")
        self.addCleanup(reset_variant_quick_chat, "five_o_poker")
        strip = controller_for("five_o_poker").local_history
        saved = state.poker_chat_popups_enabled
        self.addCleanup(setattr, state, "poker_chat_popups_enabled", saved)
        self.addCleanup(setattr, state, "holdem_table_chat_enabled", state.holdem_table_chat_enabled)
        state.holdem_table_chat_enabled = True
        surface = pygame.Surface((1366, 768))
        fonts = [pygame.font.Font(None, size) for size in (40, 28, 22)]

        def draw(game):
            five_o_ui.draw_five_o_poker(surface, None, game, "Player",
                                        lambda **_kwargs: surface.fill((0, 0, 0)), *fonts)

        state.poker_chat_popups_enabled = True
        game = self.five_o_after_npc_opens("bet", 0.0)
        line = game.last_npc_chat
        self.assertTrue(line)
        draw(game)
        self.assertEqual(strip, [f"{game.get_npc_name()}: {line}"])
        draw(game)   # shown once
        self.assertEqual(strip, [f"{game.get_npc_name()}: {line}"])

        # B86 polish P10: the strip is a chat log, so 'Table Chat Pop-ups' (speech bubbles)
        # does not drop its lines...
        reset_variant_quick_chat("five_o_poker")
        strip = controller_for("five_o_poker").local_history
        state.poker_chat_popups_enabled = False
        game = self.five_o_after_npc_opens("bet", 0.0)
        draw(game)
        self.assertEqual(strip, [f"{game.get_npc_name()}: {game.last_npc_chat}"])

        # ...the 'Table Chat' setting does, as at the other tables' chat tab (and the line is
        # not kept for later).
        reset_variant_quick_chat("five_o_poker")
        strip = controller_for("five_o_poker").local_history
        state.poker_chat_popups_enabled = True
        state.holdem_table_chat_enabled = False
        game = self.five_o_after_npc_opens("bet", 0.0)
        draw(game)
        state.holdem_table_chat_enabled = True
        draw(game)
        self.assertEqual(strip, [])

    def test_five_o_bet_size_is_locked_while_the_npc_is_thinking(self):
        from solitaireplus.games.poker import five_o_ui
        game = FIVE_O.new_game(random.Random("table-text-five-o"))
        game.npc_delay_seconds = 0.3
        game.hand_number = 1   # hand 2: the NPC opens the betting after its pause
        self.assertTrue(FIVE_O.start_hand(game))
        while game.phase == "placement":
            game.place_player_card(game.get_available_player_columns()[0])
        self.assertEqual(game.bet_state, "npc_open")
        self.assertTrue(game.pending_npc_at)
        self.assertEqual(game.bet_fraction, 0.5)
        unit = game.get_effective_bet_unit()

        # Clicking MAX (or any preset) while the NPC thinks changes nothing.
        self.assertFalse(game.can_select_bet_fraction())
        self.assertIsNone(five_o_ui.get_five_o_action(five_o_ui.BET_PRESET_RECTS[3].center, game))
        self.assertFalse(game.select_bet_fraction(100))
        self.assertEqual(game.bet_fraction, 0.5)

        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", forced("bet")):
            game.pending_npc_at -= 1000.0   # the pause is over
            game.update()
        self.assertEqual(game.current_bet, unit)   # the size set before the NPC's turn
        self.assertEqual(game.bet_state, "player_response")

        # The human's turn: the presets work again.
        self.assertTrue(game.can_select_bet_fraction())
        self.assertEqual(five_o_ui.get_five_o_action(five_o_ui.BET_PRESET_RECTS[0].center, game), "ui_click")
        self.assertEqual(game.bet_fraction, 0.25)


class PolishTableTextTests(unittest.TestCase):
    """B86 polish: showdown chat (P5), result grammar (P6), Blind Man's Bluff status panel (P7)."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    # ------------------------------------------------------------------ P5 showdown chat

    def showdown_reactions(self, key, contributions, live, ranks):
        from solitaireplus.games.poker import holdem_chat
        adapter = ADAPTERS_BY_KEY[key]
        game = adapter.force_showdown(adapter.new_game(random.Random(f"chat-split-{key}")),
                                      contributions, live, ranks, 0)
        picked = []
        with mock.patch.object(holdem_chat, "get_showdown_phrase",
                               side_effect=lambda g, npc, kind: picked.append((npc + 1, kind)) or "phrase"), \
                mock.patch.object(holdem_chat.random, "random", return_value=0.0):
            holdem_chat.generate_showdown_chat(game)
        return game, picked

    def test_showdown_chat_calls_it_a_split_only_when_a_pot_was_shared(self):
        # Reviewer repro b86_rr/money/chat_split.py: two seats that each won a different pot.
        for key in ("texas_holdem", "five_card_draw", "seven_card_stud"):
            with self.subTest(key):
                # You win the main pot, seat 2 the contested side pot: no split. A seat that
                # won nothing (not seat 2) reacts to losing.
                game, picked = self.showdown_reactions(
                    key, [50, 100, 100, 0, 0], [True, True, True, False, False], [14, 9, 12, 2, 2])
                self.assertEqual([award["winners"] for award in game.last_pot_awards], [[0], [2]])
                self.assertEqual(game.winner_indexes, [0, 2])
                self.assertEqual(len(picked), 1)
                self.assertEqual(picked[0][1], "loss")
                self.assertNotIn(picked[0][0], (0, 2))
                # Seat 1 wins the main pot and seat 2 the side pot; you lose: a win, not a split.
                game, picked = self.showdown_reactions(
                    key, [100, 50, 100, 100, 0], [True, True, True, True, False], [5, 14, 12, 9, 2])
                self.assertEqual([award["winners"] for award in game.last_pot_awards], [[1], [2]])
                self.assertEqual([kind for _seat, kind in picked], ["win"])
                # A real split: you tie seat 1 for the only pot.
                game, picked = self.showdown_reactions(
                    key, [20, 20, 0, 0, 0], [True, True, False, False, False], [14, 14, 2, 2, 2])
                self.assertEqual(picked, [(1, "split")])
                # Seats 1 and 2 tie for the only pot and you lose: a split.
                game, picked = self.showdown_reactions(
                    key, [20, 20, 20, 0, 0], [True, True, True, False, False], [5, 14, 14, 2, 2])
                self.assertEqual([kind for _seat, kind in picked], ["split"])
                self.assertIn(picked[0][0], (1, 2))

    # ------------------------------------------------------------------ P6 grammar

    def test_blind_mans_bluff_and_five_o_results_use_you_win(self):
        import re
        wrong = re.compile(r"\bYou (wins|takes|receives|collects|folds|calls|checks|bets|raises)\b")
        cases = []
        game = BMB.force_fold_win(BMB.new_game(random.Random("grammar-bmb")), [60, 20, 10, 0], 0)
        self.assertTrue(game.result_text.startswith("You win $50 after the folds. Uncalled $40 returned to you."), game.result_text)
        cases.append(game.result_text)
        game = BMB.force_fold_win(BMB.new_game(random.Random("grammar-bmb")), [20, 60, 10, 0], 1)
        self.assertTrue(game.result_text.startswith(f"{game.get_name(1)} wins $50 after the folds."),
                        game.result_text)
        cases.append(game.result_text)
        for ranks in ([14, 9, 5, 2], [9, 14, 5, 2], [14, 14, 5, 2]):
            game = BMB.force_showdown(BMB.new_game(random.Random("grammar-bmb")), [50, 100, 100, 0],
                                      [True, True, True, False], ranks, 3)
            cases.append(game.result_text)
        for winner in (0, 1):
            contributions = [25, 5] if winner == 0 else [5, 25]
            game = FIVE_O.force_fold_win(FIVE_O.new_game(random.Random("grammar-five-o")), contributions, winner)
            self.assertIn("You win $10 (uncalled $20 returned)." if winner == 0
                          else f"{game.get_npc_name()} wins $10 (uncalled $20 returned).", game.result_text)
            cases.append(game.result_text)
        for ranks in ([14, 3], [3, 14], [9, 9]):
            game = FIVE_O.force_showdown(FIVE_O.new_game(random.Random("grammar-five-o")), [40, 40],
                                         [True, True], ranks, 1)
            cases.append(game.pending_showdown_result_text or game.result_text)
        for text in cases:
            self.assertFalse(wrong.search(text), text)

    def five_o_result_rows(self, game):
        """Draw the Five-O table; return [(text, rect)] of the hand-result rows."""
        from solitaireplus.games.poker import five_o_ui
        images, drawn = {}, []
        real_fit = five_o_ui._fit_line

        def fit(font, value, width, color):
            image = real_fit(font, value, width, color)
            images[id(image)] = (str(value), image)
            return image

        class Surface(pygame.Surface):
            def blit(self, image, dest, *args, **kwargs):
                entry = images.get(id(image))
                if entry and entry[1] is image and entry[0] and entry[0] in game.result_text:
                    drawn.append((entry[0], image.get_rect(topleft=dest)))
                return super().blit(image, dest, *args, **kwargs)

        surface = Surface((1366, 768))
        with mock.patch.object(five_o_ui, "_fit_line", fit):
            five_o_ui.draw_five_o_poker(surface, None, game, "Player", lambda **_kwargs: surface.fill((0, 0, 0)),
                                        *[pygame.font.SysFont(None, size) for size in (60, 34, 24)])
        return [(text, rect) for text, rect in drawn if rect.x == 32 and rect.y > 540]

    def test_five_o_fold_result_stays_clear_of_the_chat_strip(self):
        # P1 follow-up: every Five-O fold now returns the winner's uncalled bet. The result
        # says so briefly, keeps to two rows and grows upward, so the chat strip (y 618) never
        # covers it. A one-row result stays where it was (y 594).
        controller_for("five_o_poker").reset_session()
        self.addCleanup(reset_variant_quick_chat, "five_o_poker")
        controller_for("five_o_poker").add_history_line("Inshallah", "Big bet, small pot.")
        for winner in (0, 1):
            with self.subTest(winner=winner):
                game = FIVE_O.new_game(random.Random("five-o-fold-rows"))
                game.npc["name"] = "Inshallah Test"
                FIVE_O.force_fold_win(game, [12505, 5] if winner == 0 else [5, 12505], winner)
                self.assertTrue(game.result_text.endswith("$10 (uncalled $12,500 returned)."), game.result_text)
                rows = self.five_o_result_rows(game)
                self.assertEqual(" ".join(text for text, _rect in rows), game.result_text)
                self.assertEqual(len(rows), 2)
                self.assertEqual([rect.y for _text, rect in rows], [571, 594])
                for _text, rect in rows:
                    self.assertLessEqual(rect.bottom, 618)
                    self.assertLessEqual(rect.width, 296)
        game = FIVE_O.force_showdown(FIVE_O.new_game(random.Random("five-o-fold-rows")), [40, 40],
                                     [True, True], [14, 3], 1)
        rows = self.five_o_result_rows(game)
        self.assertEqual([(text, rect.y) for text, rect in rows], [(game.result_text, 594)])

    # ------------------------------------------------------------------ P7 BMB status panel

    STATUS_PANEL = pygame.Rect(438, 355, 490, 105)

    def draw_status(self, game):
        """Draw the BMB table with the real font sizes; return [(text, width, centre)] for
        every text blitted by its rect (the status panel's lines are)."""
        from solitaireplus.games.poker import blind_mans_bluff_ui
        rendered = {}
        drawn = []

        class Font:
            def __init__(self, size):
                self.font = pygame.font.SysFont(None, size)

            def render(self, text, *args, **kwargs):
                image = self.font.render(text, *args, **kwargs)
                rendered[id(image)] = (str(text), image)
                return image

            def __getattr__(self, name):
                return getattr(self.font, name)

        class Surface(pygame.Surface):
            def blit(self, image, dest, *args, **kwargs):
                if id(image) in rendered and isinstance(dest, pygame.Rect):
                    text, kept = rendered[id(image)]
                    if kept is image:
                        drawn.append((text, image.get_width(), dest.center))
                return super().blit(image, dest, *args, **kwargs)

        surface = Surface((1366, 768))
        blind_mans_bluff_ui.draw_blind_mans_bluff(surface, None, game, "Player",
                                                  lambda **_kwargs: surface.fill((10, 20, 20)),
                                                  Font(60), Font(34), Font(24))
        return drawn

    def status_texts(self, game):
        return [(text, width) for text, width, centre in self.draw_status(game)
                if self.STATUS_PANEL.collidepoint(centre)]

    def test_bluff_stake_line_shows_the_all_in_raise_the_button_offers(self):
        # P7a (reviewer repro b86_rr/ui_text/bmb_short_raise.py): 380 is all the human has,
        # less than the full raise to 470, so the raise button offers 380.
        game = TableTextTests.face_short_all_in_raises(self, [130, 300])
        game.player_stack = 380 - game.round_bets[0]
        self.assertEqual(game.get_player_bet_presets(), [("MIN", 380)])
        self.assertEqual(game.get_minimum_raise_to(), 470)
        texts = [text for text, _width in self.status_texts(game)]
        self.assertIn("Bet $300  •  All-in raise to $380", texts)
        self.assertFalse([text for text in texts if "Minimum raise" in text], texts)
        # With a full raise in reach the line still shows the minimum.
        game.player_stack = 500
        texts = [text for text, _width in self.status_texts(game)]
        self.assertIn("Bet $300  •  Minimum raise to $470", texts)

    def test_bluff_open_range_shows_only_on_the_human_turn_to_open(self):
        # P7b: the human's own turn to open shows its range.
        game = BMB.new_game(random.Random("bluff-open-range"))
        BMB.force_open_round(game, [500, 500, 500, 500])
        game.current_actor, game.bet_state = 0, "player_open"
        stakes = [text for text, _w in self.status_texts(game) if text.startswith("Ante")]
        self.assertEqual(stakes, [f"Ante ${game.ante:,}  •  Open ${game.get_min_open_bet():,}-$500"])
        # An NPC's thinking pause: just the ante, not the human's range.
        game = BMB.new_game(random.Random("bluff-open-range"))
        game.npc_delay_seconds = 0.5
        game.hand_number = 1   # seat 1 opens hand 2, after its pause
        self.assertTrue(BMB.start_hand(game))
        self.assertTrue(game.pending_npc_at)
        stakes = [text for text, _w in self.status_texts(game) if text.startswith("Ante")]
        self.assertEqual(stakes, [f"Ante ${game.ante:,}"])
        # After the hand (here the human folded): just the ante, never "Open $0-$0".
        game = BMB.force_showdown(BMB.new_game(random.Random("bluff-open-range")), [10, 60, 60, 10],
                                  [False, True, True, False], [14, 13, 12, 11], 0)
        texts = [text for text, _w in self.status_texts(game)]
        self.assertIn(f"Ante ${game.ante:,}", texts)
        self.assertFalse([text for text in texts if "Open $" in text], texts)

    def test_bluff_status_panel_text_fits_the_panel(self):
        # P7c: the open-turn prompt was 559 px in the 490 px panel.
        game = BMB.new_game(random.Random("bluff-fit"))
        BMB.force_open_round(game, [500, 500, 500, 500])
        game.current_actor, game.bet_state = 0, "player_open"
        texts = self.status_texts(game)
        self.assertIn("Everyone else can see your card. Read their betting.", [text for text, _w in texts])
        for text, width in texts:
            self.assertLessEqual(width, self.STATUS_PANEL.width - 24, text)
        # P1 follow-up: a long fold-win result (an uncalled refund) wraps onto the free
        # prompt row instead of running out of the panel.
        game = BMB.new_game(random.Random("bluff-fit"))
        game.npcs[0]["name"] = "Harpreet Test"
        game = BMB.force_fold_win(game, [20, 1250, 10, 0], 1)
        self.assertEqual(game.result_text, "Harpreet wins $50 after the folds. Uncalled $1,230 returned to Harpreet.")
        self.assertGreater(pygame.font.SysFont(None, 24).size(game.result_text)[0], self.STATUS_PANEL.width)
        texts = self.status_texts(game)
        rows = [text for text, _w in texts if text not in ("Pot: $0", f"Ante ${game.ante:,}")]
        self.assertEqual(" ".join(rows), game.result_text)
        self.assertEqual(len(rows), 2)
        for text, width in texts:
            self.assertLessEqual(width, self.STATUS_PANEL.width - 24, text)


if __name__ == "__main__":
    unittest.main()
