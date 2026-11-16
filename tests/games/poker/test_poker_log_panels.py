"""The poker tables' log and chat panels (B86 polish).

* P2: a hand-history line too wide for the GAME LOG panel to shrink legibly (a split or
  side-pot line) wraps onto several rows at the normal log font size in Hold'em, Five-Card
  Draw and Seven-Card Stud, instead of being shrunk (Draw, Stud) or squashed (Hold'em) until
  it was unreadable and still ran out of the panel. A line the old panel drew legibly (Hold'em
  squashed it to 65 % or more; Draw and Stud fitted it inside the panel, at 11 and 10 px or more)
  is still one row, drawn exactly as at 7195fb3: the showdown and winner lines of real hands are,
  so the end-of-hand views keep all their lines. Nothing is drawn
  outside the panel, the newest rows stay at the bottom and the log scrolls by rows. A log
  where nothing wraps is drawn exactly as before. Each line is wrapped (and its one-row
  decision made) once, not every frame (the history holds the whole session, up to 500
  lines); the unscrolled log starts on the first row of a line (not on 'kickers).'); the
  wheel stops where the oldest rows fill the panel; the Hold'em chat tab keeps its old pixels.
* P9: Seven-Card Stud's speech bubbles follow the 'Table Chat Pop-ups' setting, as at the
  Hold'em and Draw tables; the chat log always gets the line.
* P11: the Five-O chat strip shows the NPC's talk during the column reveal (no Quick Chat
  options then); before, it waited for the result.
"""
import importlib
import os
import random
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from solitaireplus.app import state, state_names
from solitaireplus.games.poker.log_rows import log_rows, max_log_scroll, visible_log_rows, wrap_log_line
from solitaireplus.ui import text as ui_text

SHORT = ["Hand 3 starts. Ada deals.", "Ada posts the small blind $10.", "Bo raises to $60.",
         "You call $50.", "Showdown."]
# Pot history lines of the review (b86_rr/ui_text/log_panels.py), in the B86 polish wording.
LONG = [
    "Main pot $300: split between Inshallah, Harpreet and Mohammed. Winning hand: Two Pair, "
    "Kings and Nines, 5 kicker. Each winner receives $100.",
    "Side pot 1 $201: split between Harpreet and Mohammed. Winning hand: Two Pair, Kings and "
    "Nines, 5 kicker. Each winner receives $100 (odd chip to Harpreet).",
    "Main pot $35: split between Bo, you and Ada. Winning hand: A-high. Each winner receives $11 "
    "(odd chips to Bo and you).",
    "Side pot 2 $26: nobody else could win it; Mohammed collects $26.",
    "Payouts: Inshallah $100; Harpreet $201; Mohammed $226.",
]
# The split lines, too long for any panel to shrink legibly: they wrap everywhere. (The side-pot and
# payouts lines are one row: Hold'em squashes them to 71 % and 80 %, Draw and Stud fit them at 12
# and 14 px.)
TOO_LONG = LONG[:3]
# The review's long log (b86_rr2/p2_long.py): at the oldest end four rows fit in Draw and Stud,
# the line start and three wrapped rows.
HAND_7 = ["Hand 7 starts. Ada deals.", LONG[0], LONG[1], LONG[3], LONG[4]]
# The end of a hand with a pot line: a pot line too long to shrink legibly (Draw and Stud would need
# 9 px, Hold'em 54 %) wraps onto two rows, then two lines that fit. Only the wrapped line's last row
# would fit at the top.
HAND_END = ["Main pot $411: Harpreet wins. Winning hand: 8-high Straight. Harpreet receives $411.",
            "Harpreet wins $411 with 8-high Straight.", "You are eliminated from the table."]
# The end-of-hand views of the harness (scenes poker_holdem and poker_draw, hand_result). In
# Hold'em the last two lines are a little too wide (squashed to 96 % and 91 %); in Draw (and Stud)
# the first one is (it fits at 14 px). Each is one row, drawn exactly as at 7195fb3.
HOLDEM_HAND_RESULT = ["You show 5S 8C (J-high, 9-8-7-5 kickers).",
                      "Rusty shows JD KH (Pair of Jacks, K-9-7 kickers).",
                      "Rusty wins $2,348 with Pair of Jacks, K-9-7 kickers."]
DRAW_HAND_RESULT = ["You show JD KH 6C 7D 7H (Pair of Sevens, K-J-6 kickers).",
                    "Harpreet shows 5S 8C 6D 7C 4C (8-high Straight).",
                    "Harpreet wins $411 with 8-high Straight."]
# End-of-hand logs of real engine hands (the B86 review's v_sim4/v_examples, roster first names):
# showdown, winner and elimination lines, each of which the 7195fb3 panel drew inside the panel.
# The unscrolled panel must still show the last three, as 7195fb3 drew them. They include each
# panel's longest showdown and winner lines (Hold'em squashed to 66 %, Draw at 11 px, Stud at 10 px).
REAL_HAND_ENDS = {
    "texas_holdem": [
        ["Ada shows 9C 9D (Pair of Nines, A-K-Q kickers).",
         "Cy wins $3,040 with Two Pair, Kings and Queens, A kicker.",
         "You are eliminated from the table.", "Ada is eliminated from the table."],
        ["Bo shows QS QD (Pair of Queens, A-K-9 kickers).",
         "Mohammed shows KH 9H (Two Pair, Kings and Nines, Q kicker).",
         "Mohammed wins $1,204 with Two Pair, Kings and Nines, Q kicker."],
        ["Inshallah shows 6C 4H (Two Pair, Fours and Threes, 7 kicker).",
         "Mohammed shows QC 7H (Two Pair, Queens and Sevens, 10 kicker).",
         "Mohammed wins $12,345 with Two Pair, Queens and Sevens, 10 kicker."],
    ],
    "five_card_draw": [
        ["Ada shows 10C 10S 10H 7S AD (Three of a Kind, Tens, A-7 kickers).",
         "Cy shows 4D 2C 8D 5D 9D (9-high, 8-5-4-2 kickers).",
         "Ada wins $2,317 with Three of a Kind, Tens, A-7 kickers."],
        ["Ada shows 8H 6D JD 6S 7C (Pair of Sixes, J-8-7 kickers).",
         "Di shows QD 9S 5S QC 9H (Two Pair, Queens and Nines, 5 kicker).",
         "Di wins $202 with Two Pair, Queens and Nines, 5 kicker."],
        ["Harpreet shows 5S 8C 6D 7C 4C (8-high Straight).",
         "Inshallah shows AC QH QC QS KH (Three of a Kind, Queens, A-K kickers).",
         "Inshallah wins $2,150 with Three of a Kind, Queens, A-K kickers."],
    ],
    "seven_card_stud": [
        ["You show AC 4D 2H KD QH 5D 7D (A-high, K-Q-7-5 kickers).",
         "Ada shows KH 10H 6H 3S JD 8D 3D (Pair of Threes, K-J-10 kickers).",
         "Ada wins $105 with Pair of Threes, K-J-10 kickers."],
        ["You show KH 4S 3D 8S 8D QH 8C (Three of a Kind, Eights, K-Q kickers).",
         "Di shows 2C 10C 8H JH 2S 7C 2D (Three of a Kind, Twos, J-10 kickers).",
         "You win $190 with Three of a Kind, Eights, K-Q kickers!"],
        ["Harpreet shows 5S 8C 6D 7C 7D 2H JH (Pair of Sevens, J-8-6 kickers).",
         "Mohammed shows 8C 7D 10C 3C 2H 2C 3H (Two Pair, Threes and Twos, 10 kicker).",
         "Mohammed wins $245 with Two Pair, Threes and Twos, 10 kicker."],
    ],
}
# Lines too wide for each panel's log font that the old panel drew legibly on one shrunk row (the
# harness's end-of-hand lines, a short side-pot line and the payouts line).
SLIGHTLY_LONG = {"texas_holdem": HOLDEM_HAND_RESULT[1:] + LONG[3:],
                 "five_card_draw": DRAW_HAND_RESULT[:1] + LONG[3:],
                 "seven_card_stud": DRAW_HAND_RESULT[:1] + LONG[3:]}
# The B86 hybrid's floor in Hold'em (squashed at or above it, the 7195fb3 drawing is legible): about
# 11 px text, the smallest size of the Draw log. Draw and Stud keep a line on one row when the 7195fb3
# panel fitted it inside the panel, at its smallest size (11 and 10 px) or larger.
LEGIBLE_SQUASH = 0.65
OLD_MINIMUM_SIZE = {"five_card_draw": 11, "seven_card_stud": 10}


def old_holdem_squash(line_surface, max_width):
    """How the Hold'em log and chat drew a rendered line at 7195fb3: squashed to ``max_width``,
    keeping its proportions, when wider (draw_holdem_log_panel's loop, verbatim)."""
    if line_surface.get_width() > max_width:
        scale = max_width / line_surface.get_width()
        new_width = max(1, int(line_surface.get_width() * scale))
        new_height = max(1, int(line_surface.get_height() * scale))
        line_surface = pygame.transform.smoothscale(line_surface, (new_width, new_height))
    return line_surface


def old_render_text_fit(text, font, color, max_width, minimum_size):
    """render_text_fit of five_card_draw_ui and seven_card_stud_ui at 7195fb3 (verbatim), and the
    Cambria size it fell back to (None: ``font`` itself fits)."""
    text = str(text)
    rendered = font.render(text, True, color)

    if rendered.get_width() <= max_width:
        return rendered, None

    current_size = max(minimum_size, font.get_height() - 2)

    while current_size >= minimum_size:
        smaller = ui_text.get_font("cambria", current_size, bold=True, sysfont=True)
        rendered = smaller.render(text, True, color)

        if rendered.get_width() <= max_width:
            return rendered, current_size

        current_size -= 1

    return rendered, minimum_size


class CountingFont:
    """A font that counts what it measures, and stops a measuring loop past ``limit`` characters."""

    def __init__(self, font, limit=None):
        self.font, self.limit = font, limit
        self.calls = self.chars = 0

    def size(self, text):
        self.calls += 1
        self.chars += len(text)
        if self.limit is not None and self.chars > self.limit:
            raise AssertionError(f"measured more than {self.limit} characters")
        return self.font.size(text)

    def __getattr__(self, name):
        return getattr(self.font, name)


def history(count):
    """``count`` hand-history lines, all different, some of them long enough to wrap and some
    only a little too wide (one shrunk row: 'Rusty wins', the payouts lines)."""
    lines = []
    while len(lines) < count:
        hand = len(lines) // 12 + 1
        lines += [f"Hand {hand} starts. Ada deals.", f"Ada posts the small blind ${hand}.",
                  f"Bo raises to ${hand * 6}.", f"You call ${hand * 5}."]
        lines += [f"{line} (hand {hand})" for line in LONG] + ["Showdown."]
        lines += [f"Rusty wins ${hand},348 with Pair of Jacks, K-9-7 kickers.",
                  f"Payouts: Inshallah ${hand}00; Harpreet $201; Mohammed $226."]
    return lines[:count]


def image_bytes(images):
    return [pygame.image.tobytes(image, "RGBA") for image in images]


class RecordingSurface(pygame.Surface):
    """A surface that remembers where each image was blitted (and the clip at the time)."""

    def __init__(self, size):
        super().__init__(size)
        self.blits = []

    def blit(self, image, dest, *args, **kwargs):
        rect = image.get_rect(topleft=dest) if not isinstance(dest, pygame.Rect) else pygame.Rect(dest)
        self.blits.append((image, rect, self.get_clip()))
        return super().blit(image, dest, *args, **kwargs)


class Panel:
    """One table's GAME LOG panel: how to draw it and where its text may go."""

    def __init__(self, key):
        from solitaireplus.games.poker import five_card_draw_ui, holdem_ui, seven_card_stud_ui
        self.key = key
        if key == "texas_holdem":
            self.ui, self.rect = holdem_ui, holdem_ui.HOLDEM_LOG_RECT
            self.font = holdem_ui.get_holdem_fonts()["small"]
            # The text box: the inner box (24 px narrower than the panel) less 24 px.
            self.width, self.left = self.rect.width - 48, self.rect.x + 22
            self.color = holdem_ui.WHITE
        elif key == "five_card_draw":
            self.ui, self.rect = five_card_draw_ui, five_card_draw_ui.DRAW_LOG_RECT
            self.font = five_card_draw_ui.get_draw_fonts()["tiny"]
            self.width, self.left, self.color = self.rect.width - 28, self.rect.x + 14, (220, 225, 220)
        else:
            self.ui, self.rect = seven_card_stud_ui, seven_card_stud_ui.STUD_LOG_RECT
            self.font = seven_card_stud_ui.get_stud_fonts()["tiny"]
            self.width, self.left, self.color = self.rect.width - 28, self.rect.x + 14, (232, 234, 230)

    def rows(self, lines):
        """The panel's log rows (its get_*_log_rows)."""
        if self.key == "texas_holdem":
            return self.ui.get_holdem_log_rows(list(lines))
        game = SimpleNamespace(get_hand_history_lines=lambda: list(lines))
        if self.key == "five_card_draw":
            return self.ui.get_five_card_draw_log_rows(game)
        return self.ui.get_seven_card_stud_log_rows(game)

    def old_image(self, text):
        """A log line as the panel drew it at 7195fb3: Hold'em squashed a line wider than the
        text box to fit, Draw and Stud drew it in a smaller font (render_text_fit, down to 11 and
        10 px)."""
        if self.key == "texas_holdem":
            return old_holdem_squash(self.font.render(text, True, self.color), self.width)
        return old_render_text_fit(text, self.font, self.color, self.width, OLD_MINIMUM_SIZE[self.key])[0]

    def old_blit(self, surface, image, index):
        """Blit a log line where the panel drew its line ``index`` (from the top) at 7195fb3:
        Draw rows 28 px apart from 50 px below the panel top, Stud 29 px from 52 px, Hold'em
        centred 23 px apart from 9 + 11 px into the inner box (48 px below the panel top)."""
        if self.key == "texas_holdem":
            surface.blit(image, image.get_rect(
                midleft=(self.rect.x + 22, self.rect.y + 48 + 9 + 23 * index + 11)))
        elif self.key == "five_card_draw":
            surface.blit(image, (self.rect.x + 14, self.rect.y + 50 + 28 * index))
        else:
            surface.blit(image, (self.rect.x + 14, self.rect.y + 52 + 29 * index))

    def old_panel(self, lines):
        """The panel showing ``lines`` (three at most) as it was drawn at 7195fb3."""
        surface = self.draw([])
        for index, line in enumerate(lines):
            self.old_blit(surface, self.old_image(line), index)
        return surface

    def legible(self, text):
        """Whether the 7195fb3 panel drew this line legibly on one row: it fits, or Hold'em
        squashed it to LEGIBLE_SQUASH or more, or Draw and Stud fitted it inside the panel (at
        their smallest size, OLD_MINIMUM_SIZE, or larger)."""
        if self.key == "texas_holdem":
            return self.width / self.font.render(text, True, self.color).get_width() >= LEGIBLE_SQUASH
        return self.old_image(text).get_width() <= self.width

    def threshold_lines(self):
        """The longest start of a long pot line that the old panel drew legibly, and the next
        longer one (one more character, or a space and one): just past the threshold."""
        text = "Side pot 1 $201:"
        rest = (" split between Harpreet and Mohammed. Winning hand: Two Pair, Kings and Nines, 5"
                " kicker. Each winner receives $100 (odd chip to Harpreet).")
        while True:
            step = 2 if rest[0] == " " else 1
            longer, rest = text + rest[:step], rest[step:]
            if not self.legible(longer):
                return text, longer
            text = longer

    def max_scroll(self, lines):
        """Where the mouse wheel stops: as far back as the log goes."""
        game = SimpleNamespace(get_hand_history_lines=lambda: list(lines))
        if self.key == "texas_holdem":
            state.holdem_active_tab = "log"
            self.ui.scroll_holdem_log(10 ** 6, len(self.rows(lines)))
            return state.holdem_log_scroll
        if self.key == "five_card_draw":
            self.ui._ui.draw_active_tab = "log"
            self.ui.scroll_five_card_draw_panel(10 ** 6, game)
            return self.ui._ui.draw_log_scroll
        self.ui._ui.stud_active_tab = "log"
        self.ui.scroll_seven_card_stud_panel(10 ** 6, game)
        return self.ui._ui.stud_log_scroll

    def layout(self):
        """visible_log_rows' height, line step, row step and row height for this panel."""
        if self.key == "texas_holdem":
            return self.ui.get_holdem_log_layout()
        if self.key == "five_card_draw":
            return self.ui.get_five_card_draw_log_layout()
        return self.ui.get_seven_card_stud_log_layout()

    def fonts(self):
        """The table's font dict and the key of the log font in it."""
        if self.key == "texas_holdem":
            return self.ui.get_holdem_fonts(), "small"
        if self.key == "five_card_draw":
            return self.ui.get_draw_fonts(), "tiny"
        return self.ui.get_stud_fonts(), "tiny"

    def rendered(self, texts):
        """The bytes of each text rendered as a log row."""
        return image_bytes(self.font.render(text, True, self.color) for text in texts)

    def drawn(self, lines, scroll=0):
        """The bytes of each log row the panel draws, top first."""
        return image_bytes(image for image, _rect, _clip in self.text_blits(self.draw(lines, scroll)))

    def draw(self, lines, scroll=0, surface=None):
        surface = surface or RecordingSurface((1366, 768))
        surface.fill((20, 80, 50))
        if self.key == "texas_holdem":
            state.holdem_log_scroll = scroll
            self.ui.draw_holdem_log_panel(surface, pygame.font.Font(None, 24), None, "log", list(lines))
        else:
            prefix = "draw" if self.key == "five_card_draw" else "stud"
            setattr(self.ui._ui, f"{prefix}_active_tab", "log")
            setattr(self.ui._ui, f"{prefix}_log_scroll", scroll)
            self.ui.draw_log_panel(surface, SimpleNamespace(get_hand_history_lines=lambda: list(lines)))
        return surface

    def text_blits(self, surface):
        """The log text images: every blit inside the panel's text box after the tabs."""
        return [(image, rect, clip) for image, rect, clip in surface.blits
                if rect.y >= self.rect.y + 48 and rect.x >= self.rect.x + 10
                and rect.height <= self.font.size("Ag")[1]]


class LogRowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.font = pygame.font.SysFont("cambria", 15, bold=True)

    def test_a_line_that_fits_is_one_unchanged_row(self):
        for line in SHORT + ["two  spaces  kept"]:
            self.assertEqual(wrap_log_line(self.font, line, 382), [line])

    def test_long_lines_wrap_at_spaces_and_every_row_fits(self):
        for line in LONG:
            rows = wrap_log_line(self.font, line, 382)
            self.assertEqual(" ".join(rows), " ".join(line.split()))
            for row in rows:
                self.assertLessEqual(self.font.size(row)[0], 382, row)
        # A word wider than the panel on its own is broken between characters.
        rows = wrap_log_line(self.font, "x" * 200, 100)
        self.assertEqual("".join(rows), "x" * 200)
        self.assertTrue(all(self.font.size(row)[0] <= 100 for row in rows))

    def test_visible_rows_are_the_newest_that_fit(self):
        rows = [("a", True), ("b", True), ("c1", True), ("c2", False), ("d", True)]
        # Lines 28 apart, wrapped rows 18 apart, rows 18 high, 86 px: c1, c2 and d fit (64 px);
        # adding b would need 92.
        self.assertEqual(visible_log_rows(rows, 0, 86, 28, 18, 18), [("c1", 0), ("c2", 18), ("d", 46)])
        # Scrolled back one row the window ends at c2 and starts with b (a would need 92).
        self.assertEqual(visible_log_rows(rows, 1, 86, 28, 18, 18), [("b", 0), ("c1", 28), ("c2", 46)])
        # Nothing wraps: the newest three lines, 28 apart.
        flat = [(name, True) for name in "abcde"]
        self.assertEqual(visible_log_rows(flat, 0, 86, 28, 18, 18), [("c", 0), ("d", 28), ("e", 56)])
        self.assertEqual(visible_log_rows(flat, 2, 86, 28, 18, 18), [("a", 0), ("b", 28), ("c", 56)])
        self.assertEqual(visible_log_rows(flat[:2], 0, 86, 28, 18, 18), [("a", 0), ("b", 28)])
        self.assertEqual(visible_log_rows([], 0, 86, 28, 18, 18), [])
        # One row always shows, even when it is taller than the panel.
        self.assertEqual(visible_log_rows([("x", True)], 0, 5, 28, 18, 18), [("x", 0)])

    def test_the_unscrolled_window_starts_on_a_line(self):
        # b and c fit with a2 above them, not with a1 (92 px): unscrolled, the end of line a is
        # left out and the window starts on b.
        rows = [("a1", True), ("a2", False), ("b", True), ("c", True)]
        self.assertEqual(visible_log_rows(rows, 0, 86, 28, 18, 18), [("b", 0), ("c", 28)])
        # Scrolled back, the window fills with every row that fits: one step shows all of line a.
        self.assertEqual(visible_log_rows(rows, 1, 86, 28, 18, 18), [("a1", 0), ("a2", 18), ("b", 46)])
        rows = [("z", True), ("a1", True), ("a2", False), ("a3", False), ("b", True)]
        self.assertEqual(visible_log_rows(rows, 2, 86, 28, 18, 18), [("z", 0), ("a1", 28), ("a2", 46)])
        # A newest line too long to show at once keeps its newest rows.
        rows = [("a", True)] + [(f"b{index}", index == 1) for index in range(1, 7)]
        self.assertEqual(visible_log_rows(rows, 0, 86, 28, 18, 18),
                         [("b3", 0), ("b4", 18), ("b5", 36), ("b6", 54)])

    def test_the_wheel_stops_where_the_oldest_rows_fill_the_window(self):
        flat = [(name, True) for name in "abcde"]
        # Nothing wraps: three lines fit (74 px of 86), so the wheel stops three lines from the
        # oldest, as it always did.
        self.assertEqual(max_log_scroll(flat, 86, 28, 18, 18), 2)
        self.assertEqual(max_log_scroll(flat[:3], 86, 28, 18, 18), 0)
        self.assertEqual(max_log_scroll(flat[:1], 86, 28, 18, 18), 0)
        self.assertEqual(max_log_scroll([], 86, 28, 18, 18), 0)
        # A line and three wrapped rows fit (82 px): there the window starts on the first row, and
        # one step less it does not.
        rows = [("a", True), ("b1", True), ("b2", False), ("b3", False), ("c", True), ("d", True)]
        top = max_log_scroll(rows, 86, 28, 18, 18)
        self.assertEqual(top, 2)
        self.assertEqual(visible_log_rows(rows, top, 86, 28, 18, 18),
                         [("a", 0), ("b1", 28), ("b2", 46), ("b3", 64)])
        self.assertEqual(visible_log_rows(rows, top - 1, 86, 28, 18, 18)[0][0], "b1")

    def test_each_line_is_wrapped_once(self):
        # The panels ask for the rows of the whole history every frame: only new lines are measured.
        font = CountingFont(self.font)
        lines = history(500)
        rows = log_rows(font, lines, 382)
        self.assertGreater(len(rows), len(lines))
        self.assertGreaterEqual(font.calls, len(lines))
        font.calls = 0
        self.assertEqual(log_rows(font, lines, 382), rows)
        self.assertEqual(font.calls, 0)
        self.assertEqual(log_rows(font, lines + ["Ada folds."], 382), rows + [("Ada folds.", True)])
        self.assertEqual(font.calls, 1)
        # The rows are the same as wrapping each line on its own; another width wraps afresh.
        self.assertEqual(rows, [(row, index == 0) for line in lines
                                for index, row in enumerate(wrap_log_line(self.font, line, 382))])
        self.assertEqual(log_rows(font, LONG, 200),
                         [(row, index == 0) for line in LONG
                          for index, row in enumerate(wrap_log_line(self.font, line, 200))])

    def test_a_very_long_word_wraps_in_linear_time(self):
        # Each row of a word wider than the panel costs about its own length in measurements; a
        # 2,000-character word used to measure millions of characters (seconds, every frame).
        for word in ("x" * 2000, "W" * 2000, "il" * 1000):
            with self.subTest(word=word[:2]):
                font = CountingFont(self.font, limit=40 * len(word))
                rows = wrap_log_line(font, word, 100)
                self.assertEqual("".join(rows), word)
                self.assertTrue(all(self.font.size(row)[0] <= 100 for row in rows))
                for row, after in zip(rows, rows[1:]):
                    # Each row is the longest start of the rest that fits.
                    self.assertGreater(self.font.size(row + after[0])[0], 100)


class LogPanelTests(unittest.TestCase):
    TABLES = ("texas_holdem", "five_card_draw", "seven_card_stud")

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))

    def setUp(self):
        from solitaireplus.games.poker import five_card_draw_ui, holdem_ui, seven_card_stud_ui
        for name in ("holdem_log_scroll", "holdem_chat_scroll", "holdem_active_tab"):
            self.addCleanup(setattr, state, name, getattr(state, name))
        for ui, prefix in ((five_card_draw_ui, "draw"), (seven_card_stud_ui, "stud")):
            for name in ("log_scroll", "active_tab"):
                attribute = f"{prefix}_{name}"
                self.addCleanup(setattr, ui._ui, attribute, getattr(ui._ui, attribute))
        self.addCleanup(holdem_ui.holdem_chat_history.__setitem__, slice(None),
                        list(holdem_ui.holdem_chat_history))

    def test_every_row_of_a_long_line_fits_the_panel(self):
        for key in self.TABLES:
            panel = Panel(key)
            rows = panel.rows(TOO_LONG)
            self.assertGreater(len(rows), len(TOO_LONG))
            seen = set()
            for scroll in range(panel.max_scroll(TOO_LONG) + 1):
                with self.subTest(key, scroll=scroll):
                    surface = panel.draw(TOO_LONG, scroll)
                    blits = panel.text_blits(surface)
                    self.assertTrue(blits)
                    for image, rect, clip in blits:
                        # At the normal log font size, inside the text width and the panel.
                        self.assertIn(image.get_height(), (panel.font.get_height(), panel.font.size("Ag")[1]))
                        self.assertLessEqual(image.get_width(), panel.width)
                        self.assertGreaterEqual(rect.left, panel.left)
                        self.assertLessEqual(rect.right, panel.left + panel.width)
                        self.assertTrue(panel.rect.contains(rect), (rect, panel.rect))
                        self.assertTrue(panel.rect.contains(clip), (clip, panel.rect))
                    seen.update(index for index in range(len(rows) - scroll - len(blits), len(rows) - scroll))
            with self.subTest(key, check="every row reachable, newest last"):
                # Scrolling back reaches every row; at scroll 0 the newest row is drawn last.
                self.assertEqual(seen, set(range(len(rows))))
                surface = panel.draw(TOO_LONG, 0)
                last_image = panel.text_blits(surface)[-1][0]
                expected = panel.font.render(rows[-1][0], True, panel.color)
                self.assertEqual(pygame.image.tobytes(last_image, "RGBA"), pygame.image.tobytes(expected, "RGBA"))

    def test_short_lines_are_drawn_exactly_as_before(self):
        # The pre-polish layout: each line at the full log font, Draw rows 28 px apart from 50 px
        # below the panel top, Stud 29 px from 52 px, Hold'em centred 23 px apart from 9 + 11 px
        # into the inner box (48 px below the panel top).
        for key in self.TABLES:
            panel = Panel(key)
            for lines in (SHORT[:1], SHORT[:2], SHORT[:3]):
                with self.subTest(key, count=len(lines)):
                    actual = panel.draw(lines)
                    expected = panel.draw([])
                    for index, line in enumerate(lines):
                        panel.old_blit(expected, panel.font.render(line, True, panel.color), index)
                    self.assertEqual(pygame.image.tobytes(actual, "RGB"), pygame.image.tobytes(expected, "RGB"))
            # More lines than fit: the newest three, scrolled one line per wheel step.
            for scroll in (0, 1, 2):
                with self.subTest(key, scroll=scroll):
                    drawn = [image for image, _rect, _clip in panel.text_blits(panel.draw(SHORT, scroll))]
                    wanted = SHORT[len(SHORT) - 3 - scroll:len(SHORT) - scroll]
                    self.assertEqual([pygame.image.tobytes(image, "RGBA") for image in drawn],
                                     [pygame.image.tobytes(panel.font.render(line, True, panel.color), "RGBA")
                                      for line in wanted])

    def test_a_slightly_long_line_is_one_row_drawn_as_before(self):
        # A line the old panel shrank legibly (Hold'em squashed it to 65 % or more, Draw and Stud
        # fitted it inside the panel) is still one row, a line of its own, drawn exactly as at
        # 7195fb3: the harness's end-of-hand lines, and the longest such line.
        for key in self.TABLES:
            panel = Panel(key)
            within, _past = panel.threshold_lines()
            for line in SLIGHTLY_LONG[key] + [within]:
                with self.subTest(key, line=line):
                    self.assertGreater(panel.font.size(line)[0], panel.width)
                    self.assertTrue(panel.legible(line))
                    self.assertEqual(panel.rows([line]), [(line, True)])
                    lines = [SHORT[0], line, SHORT[1]]
                    self.assertEqual(panel.rows(lines), [(text, True) for text in lines])
                    self.assertEqual(pygame.image.tobytes(panel.draw(lines), "RGB"),
                                     pygame.image.tobytes(panel.old_panel(lines), "RGB"))
                    # Scrolled by rows: the shrunk line is one row, one wheel step.
                    for scroll, shown in ((0, [line, SHORT[1], SHORT[2]]), (1, lines)):
                        self.assertEqual(panel.drawn(lines + [SHORT[2]], scroll),
                                         image_bytes(panel.old_image(text) for text in shown))
        # The end-of-hand views of the harness look as they did.
        for key, lines in (("texas_holdem", HOLDEM_HAND_RESULT), ("five_card_draw", DRAW_HAND_RESULT),
                           ("seven_card_stud", DRAW_HAND_RESULT)):
            with self.subTest(key, view="hand_result"):
                panel = Panel(key)
                self.assertEqual(panel.rows(lines), [(text, True) for text in lines])
                self.assertEqual(pygame.image.tobytes(panel.draw(lines), "RGB"),
                                 pygame.image.tobytes(panel.old_panel(lines), "RGB"))

    def test_real_end_of_hand_views_keep_their_lines(self):
        # The B86 review played real hands: with floors at 85 % / 13 px, common showdown and winner
        # lines ('Two Pair, Kings and Queens, A kicker', every seven-card showdown) wrapped, and the
        # three-row panel then dropped lines 7195fb3 showed, the winner line among them. Every line
        # here was drawn inside the 7195fb3 panel: each is one row, and the unscrolled panel shows the
        # last three exactly as 7195fb3 drew them.
        for key in self.TABLES:
            panel = Panel(key)
            for lines in REAL_HAND_ENDS[key]:
                with self.subTest(key, line=lines[-1]):
                    self.assertTrue(any(panel.font.size(line)[0] > panel.width for line in lines))
                    for line in lines:
                        self.assertTrue(panel.legible(line), line)
                    self.assertEqual(panel.rows(lines), [(text, True) for text in lines])
                    self.assertEqual(panel.drawn(lines), image_bytes(panel.old_image(text) for text in lines[-3:]))
                    if len(lines) == 3:
                        self.assertEqual(pygame.image.tobytes(panel.draw(lines), "RGB"),
                                         pygame.image.tobytes(panel.old_panel(lines), "RGB"))

    def test_a_line_just_past_the_threshold_wraps(self):
        # One character more than the longest line the old panel drew legibly, and the line wraps
        # at the normal log font size.
        for key in self.TABLES:
            with self.subTest(key):
                panel = Panel(key)
                within, past = panel.threshold_lines()
                self.assertTrue(panel.legible(within))
                self.assertFalse(panel.legible(past))
                self.assertTrue(past.startswith(within))
                self.assertLessEqual(len(past.replace(" ", "")) - len(within.replace(" ", "")), 1)
                rows = panel.rows([past])
                self.assertGreater(len(rows), 1)
                self.assertEqual([starts for _text, starts in rows], [True] + [False] * (len(rows) - 1))
                self.assertEqual(" ".join(text for text, _starts in rows), " ".join(past.split()))
                for text, _starts in rows:
                    self.assertLessEqual(panel.font.size(text)[0], panel.width)
                self.assertEqual(panel.drawn([past]), panel.rendered(text for text, _starts in rows))
                if key == "texas_holdem":
                    self.assertLess(panel.width / panel.font.size(past)[0], LEGIBLE_SQUASH)
                else:
                    # The old panel drew it at its smallest size, and it ran out of the panel; the
                    # line within the threshold fitted at that size.
                    minimum = OLD_MINIMUM_SIZE[key]
                    image, size = old_render_text_fit(past, panel.font, panel.color, panel.width, minimum)
                    self.assertEqual(size, minimum)
                    self.assertGreater(image.get_width(), panel.width)
                    self.assertEqual(old_render_text_fit(within, panel.font, panel.color, panel.width, minimum)[1],
                                     minimum)

    def test_the_log_scrolls_by_rows(self):
        from solitaireplus.games.poker import five_card_draw_ui, holdem_ui, seven_card_stud_ui
        game = SimpleNamespace(get_hand_history_lines=lambda: list(LONG))
        draw = Panel("five_card_draw")
        five_card_draw_ui._ui.draw_active_tab = "log"
        five_card_draw_ui.scroll_five_card_draw_panel(1000, game)
        self.assertEqual(five_card_draw_ui._ui.draw_log_scroll, max_log_scroll(draw.rows(LONG), *draw.layout()))

        stud = Panel("seven_card_stud")
        seven_card_stud_ui._ui.stud_active_tab = "log"
        seven_card_stud_ui.scroll_seven_card_stud_panel(1000, game)
        self.assertEqual(seven_card_stud_ui._ui.stud_log_scroll, max_log_scroll(stud.rows(LONG), *stud.layout()))

        # The Hold'em screen passes the row count of its log.
        from solitaireplus.games.poker import holdem_screen
        holdem_rows = len(holdem_ui.get_holdem_log_rows(LONG))
        self.assertGreater(holdem_rows, len(LONG))
        saved_history = list(holdem_ui.holdem_log_history)
        self.addCleanup(holdem_ui.holdem_log_history.__setitem__, slice(None), saved_history)
        holdem_ui.holdem_log_history[:] = LONG
        missing = object()
        for name, value in (("current_state", state_names.STATE_TEXAS_HOLDEM),
                            ("game_mouse_pos", holdem_ui.HOLDEM_LOG_RECT.center),
                            ("holdem_active_tab", "log")):
            before = getattr(state, name, missing)
            self.addCleanup(lambda name=name, before=before: delattr(state, name) if before is missing
                            else setattr(state, name, before))
            setattr(state, name, value)
        from solitaireplus.games.poker.holdem import TexasHoldemGame
        table = TexasHoldemGame()
        table.start_session([{"id": "npc_1", "name": "Rival 1"}, {"id": "npc_2", "name": "Rival 2"}], 1000, 10)
        with mock.patch.object(holdem_screen, "texas_holdem_game", table),                 mock.patch.object(holdem_screen, "scroll_holdem_log") as scroll:
            holdem_screen.loop_event_texas_holdem(pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=1))
        scroll.assert_called_once_with(1, holdem_rows)
        holdem_ui.scroll_holdem_log(1000, holdem_rows)
        self.assertEqual(state.holdem_log_scroll, holdem_rows - 3)
        # Hold'em always fits three rows and never four, so three rows from the oldest is where its
        # window starts on the first row.
        holdem = Panel("texas_holdem")
        for lines in (LONG, HAND_7, HAND_END, SHORT):
            self.assertEqual(max_log_scroll(holdem.rows(lines), *holdem.layout()),
                             max(0, len(holdem.rows(lines)) - 3))

    def test_the_wheel_stops_when_the_first_row_shows(self):
        # At the wheel's stop the window starts on the oldest row and one step less it does not, so
        # the last step shows the oldest row (in Draw and Stud it used to only drop the newest).
        for key in self.TABLES:
            with self.subTest(key):
                panel = Panel(key)
                rows = panel.rows(HAND_7)
                top = panel.max_scroll(HAND_7)
                drawn = panel.drawn(HAND_7, top)
                self.assertEqual(drawn, panel.rendered(text for text, _offset in
                                                       visible_log_rows(rows, top, *panel.layout())))
                self.assertEqual(drawn[0], panel.rendered([rows[0][0]])[0])
                self.assertNotEqual(panel.drawn(HAND_7, top - 1)[0], drawn[0])
                if key != "texas_holdem":
                    # There four rows fit: the line start and three wrapped rows.
                    self.assertEqual(len(drawn), 4)
                    self.assertEqual([starts for _text, starts in rows[:4]], [True, True, False, False])
        # Stud keeps a scroll past the stop at the stop when it draws.
        panel = Panel("seven_card_stud")
        self.assertEqual(panel.drawn(HAND_7, 10 ** 6), panel.drawn(HAND_7, panel.max_scroll(HAND_7)))

    def test_the_end_of_hand_view_starts_on_a_line(self):
        # Unscrolled, the log no longer starts with the end of the wrapped showdown line
        # ('kickers).'): the window starts on the next line.
        for key in self.TABLES:
            with self.subTest(key):
                panel = Panel(key)
                rows = panel.rows(HAND_END)
                self.assertEqual([starts for _text, starts in rows], [True, False, True, True])
                self.assertEqual(panel.drawn(HAND_END), panel.rendered(HAND_END[1:]))
                # One step back shows the whole showdown line.
                self.assertEqual(panel.drawn(HAND_END, 1), panel.rendered(text for text, _starts in rows[:3]))

    def test_the_one_row_decision_is_made_once_per_line(self):
        # Whether a line too wide for the panel stays on one shrunk row is asked once per line and
        # remembered with its rows, not asked again every frame.
        lines = history(500)
        for key in self.TABLES:
            with self.subTest(key):
                panel = Panel(key)
                name = ("_holdem_log_line_squashes_legibly" if key == "texas_holdem"
                        else "_log_line_fits_legibly")
                decide = getattr(panel.ui, name)
                asked = []

                def counting(font, text, width, decide=decide, asked=asked):
                    answer = decide(font, text, width)
                    asked.append((text, answer))
                    return answer

                # Patch the helper where the log code looks it up: the module that defines it
                # (Hold'em's log code is in holdem_ui_log.py since the Phase 12 split).
                owner = importlib.import_module(decide.__module__)
                with mock.patch.object(owner, name, counting):
                    first = pygame.image.tobytes(panel.draw(lines), "RGB")
                    texts = [text for text, _answer in asked]
                    self.assertEqual(len(texts), len(set(texts)))
                    self.assertEqual(set(texts), {line for line in lines if panel.font.size(line)[0] > panel.width})
                    # Some of them stay on one row, the others wrap.
                    self.assertEqual({answer for _text, answer in asked}, {True, False})
                    asked.clear()
                    self.assertEqual(pygame.image.tobytes(panel.draw(lines), "RGB"), first)
                    rows = panel.rows(lines)
                    self.assertEqual(asked, [])
                self.assertEqual(sum(starts for _text, starts in rows), len(lines))

    def test_a_long_history_is_not_rewrapped_every_frame(self):
        # The history holds the whole session (up to 500 lines). After the first frame, a frame
        # measures a few strings, not every line of the history.
        lines = history(500)
        for key in self.TABLES:
            with self.subTest(key):
                panel = Panel(key)
                fonts, name = panel.fonts()
                font = CountingFont(fonts[name])
                with mock.patch.dict(fonts, {name: font}):
                    first = pygame.image.tobytes(panel.draw(lines), "RGB")
                    self.assertGreaterEqual(font.calls, len(lines))
                    font.calls = 0
                    second = pygame.image.tobytes(panel.draw(lines), "RGB")
                    self.assertLess(font.calls, 10)
                self.assertEqual(first, second)
                self.assertEqual(second, pygame.image.tobytes(panel.draw(lines), "RGB"))

    def test_holdem_chat_rows_keep_their_old_place(self):
        # The fourth chat row's descenders reach the inner box's bottom edge, as they always did:
        # only the log is held inside the inner box.
        from solitaireplus.games.poker import holdem_ui
        panel = Panel("texas_holdem")
        chat = ["Ada: Nice hand, gjpqy.", "You: Thanks!", "Bo: Lucky river, typical.", "Cy: Glad I folded.",
                "Ada: Another one? Bring it on, gjqpy."]
        inner = pygame.Rect(panel.rect.x + 12, panel.rect.y + 48, panel.rect.width - 24, panel.rect.height - 58)
        for count in (4, 5):
            with self.subTest(count=count):
                holdem_ui.holdem_chat_history[:] = chat[:count]
                state.holdem_chat_scroll = 0
                surface = RecordingSurface((1366, 768))
                surface.fill((20, 80, 50))
                holdem_ui.draw_holdem_log_panel(surface, pygame.font.Font(None, 24), None, "chat", [])
                rows = [(rect, clip) for _image, rect, clip in surface.blits
                        if rect.x == inner.x + 10 and rect.y >= inner.y]
                self.assertEqual(len(rows), 4)
                self.assertGreater(rows[-1][0].bottom, inner.bottom)
                for rect, clip in rows:
                    self.assertTrue(clip.contains(rect), (rect, clip))
                    self.assertTrue(panel.rect.contains(clip), (clip, panel.rect))
        # A chat line too wide for the box is still squashed to fit by any amount, as at 7195fb3.
        wide = ["Mohammed: That river card was brutal, I had you beat on the turn, gjpqy.",
                "Ada: " + "Nice hand! " * 12]
        holdem_ui.holdem_chat_history[:] = chat[:2] + wide
        state.holdem_chat_scroll = 0
        surface = RecordingSurface((1366, 768))
        holdem_ui.draw_holdem_log_panel(surface, pygame.font.Font(None, 24), None, "chat", [])
        rows = [(image, rect) for image, rect, _clip in surface.blits
                if rect.x == inner.x + 10 and rect.y >= inner.y]
        expected = [old_holdem_squash(panel.font.render(line, True, panel.color), inner.width - 24)
                    for line in chat[:2] + wide]
        self.assertEqual(image_bytes(image for image, _rect in rows), image_bytes(expected))
        self.assertEqual([rect.center[1] for _image, rect in rows],
                         [inner.y + 9 + 18 * index + 9 for index in range(4)])
        self.assertLess(rows[-1][0].get_width() / panel.font.size(wide[-1])[0], 0.5)


class StudSpeechBubbleTests(unittest.TestCase):
    """P9: Stud's bubbles follow 'Table Chat Pop-ups', as five_card_draw_ui does."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))

    def setUp(self):
        from solitaireplus.games.poker import seven_card_stud_ui
        self.ui = seven_card_stud_ui
        saved = state.poker_chat_popups_enabled
        self.addCleanup(setattr, state, "poker_chat_popups_enabled", saved)
        self.addCleanup(self.ui.reset_seven_card_stud_ui_session)
        self.ui.reset_seven_card_stud_ui_session()

    def seat_bubbles(self, game):
        """The speech overlay draws made while one NPC seat is drawn."""
        surface = pygame.Surface((1366, 768))
        fronts = {}
        back = pygame.Surface((148, 207))
        with mock.patch.object(self.ui._stud_speech_overlay, "draw") as draw:
            self.ui.draw_npc_seat(surface, game, 0, game.npcs[0], (180, 430), fronts, back,
                                  lambda *args, **kwargs: None)
        return draw.call_args_list

    def stud_game(self):
        from solitaireplus.games.poker.seven_card_stud import SevenCardStudGame
        random.seed(9)
        game = SevenCardStudGame()
        game.start_session([{"id": f"npc{seat}", "name": name} for seat, name in
                            enumerate(("Ada", "Bo", "Cy", "Di"))], 1000, 10)
        return game

    def test_popups_off_posts_no_bubble_but_logs_the_line(self):
        state.poker_chat_popups_enabled = False
        self.ui.add_seven_card_stud_chat_message("Ada", "Nice hand.")
        self.assertEqual(self.ui._stud_speech_overlay.entries, {})
        self.assertEqual(self.ui._ui.stud_chat_history, ["Ada: Nice hand."])
        state.poker_chat_popups_enabled = True
        self.ui.add_seven_card_stud_chat_message("Ada", "Again.")
        self.assertIn("ada", self.ui._stud_speech_overlay.entries)
        self.assertEqual(self.ui._ui.stud_chat_history, ["Ada: Nice hand.", "Ada: Again."])

    def test_popups_off_draws_no_bubble(self):
        game = self.stud_game()
        state.poker_chat_popups_enabled = True
        self.ui.add_seven_card_stud_chat_message("Ada", "Nice hand.")
        self.assertEqual(len(self.seat_bubbles(game)), 1)
        # Turned off while a bubble is still showing: it is not drawn.
        state.poker_chat_popups_enabled = False
        self.assertEqual(self.seat_bubbles(game), [])


class FiveORevealTalkTests(unittest.TestCase):
    """P11: the history strip does not depend on the Quick Chat options."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1366, 768))

    def test_npc_talk_shows_during_the_column_reveal(self):
        from solitaireplus.games.poker import five_o_ui, variant_quick_chat
        from solitaireplus.games.poker.quick_chat import quick_chat_options_for_game
        from solitaireplus.games.poker.quick_chat_adapter import adapt_quick_chat_game
        from solitaireplus.games.poker.ai import get_poker_personality_profile
        from tests.support.poker_variants import ADAPTERS_BY_KEY

        class FixedRandom(random.Random):
            """The NPC always talks: random() is 0."""

            def random(self):
                return 0.0

        def forced(action):
            def decide(personality, context, rng=None):
                return {"action": action, "profile": get_poker_personality_profile("balanced"), "bluff": False}
            return decide

        five_o = ADAPTERS_BY_KEY["five_o_poker"]
        variant_quick_chat.reset_variant_quick_chat("five_o_poker")
        self.addCleanup(variant_quick_chat.reset_variant_quick_chat, "five_o_poker")
        self.addCleanup(setattr, state, "holdem_table_chat_enabled", state.holdem_table_chat_enabled)
        state.holdem_table_chat_enabled = True

        # The NPC opens with a bet and talks; the human calls: the column reveal starts.
        game = five_o.new_game(random.Random("reveal-talk"))
        game.npc_delay_seconds = 0
        game.hand_number = 1
        with mock.patch("solitaireplus.games.poker.five_o.decide_poker_action", forced("bet")):
            self.assertTrue(five_o.start_hand(game))
            game.rng = FixedRandom("reveal-talk")
            five_o.place_all_cards(game)
        line = game.last_npc_chat
        self.assertTrue(line)
        self.assertTrue(game.player_call())
        self.assertEqual(game.phase, "showdown")
        self.assertFalse(game.hand_complete)
        self.assertEqual(quick_chat_options_for_game(adapt_quick_chat_game(game, "five_o_poker")), ())

        surface = pygame.Surface((1366, 768))
        fonts = [pygame.font.Font(None, size) for size in (40, 28, 22)]
        fitted, buttons = [], []
        real_fit, real_button = variant_quick_chat._fit, variant_quick_chat._button
        with mock.patch.object(variant_quick_chat, "_fit",
                               lambda font, text, width, color=variant_quick_chat.WHITE:
                               fitted.append(text) or real_fit(font, text, width, color)), \
                mock.patch.object(variant_quick_chat, "_button",
                                  lambda surface, rect, label, *args, **kwargs:
                                  buttons.append(label) or real_button(surface, rect, label, *args, **kwargs)):
            five_o_ui.draw_five_o_poker(surface, None, game, "Player",
                                        lambda **_kwargs: surface.fill((0, 0, 0)), *fonts)
        self.assertIn(f"{game.get_npc_name()}: {line}", fitted)
        # No options, so no Quick Chat button.
        self.assertNotIn("QUICK CHAT", buttons)


if __name__ == "__main__":
    unittest.main()
