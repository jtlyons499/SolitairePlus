"""Rows for the GAME LOG panels of the Hold'em, Draw and Stud tables.

A log line wider than its panel used to be drawn on one row shrunk to fit: Draw and
Stud stepped the font down (to 11 or 10 px), Hold'em squashed the whole line by any
amount. A showdown or winner line lost a few points and could still be read; a very
long one (a 2- to 4-way split, a side pot) became unreadably small, and in Draw and
Stud still ran out of the panel.

So the rule is a hybrid. A line the old code drew legibly on one row (each panel says
which, through log_rows' one_row: Hold'em squashed to 65 % or more, about 11 px; Draw
and Stud fitted inside the panel, at 11 or 10 px or more) is still one row, drawn
exactly as before by the panel's shrink-to-fit renderer, so a log where nothing is
too long for that looks the same. Only a longer line wraps onto several rows at the
normal log font size. A line that fits is one row, unchanged.

The panels show three rows, so a line that wraps pushes older lines out of the view;
the floors are low enough that the showdown and winner lines of real hands stay one
row each, and the end-of-hand view keeps the lines it always showed.

The panels scroll by rows: scroll 0 shows the newest rows, each wheel step one row
further back. A line drawn on one row, shrunk or not, is one row, so when nothing
wraps a row is a line and scrolling is as before.

The panels ask for the rows of the whole session's hand history (up to 500 lines)
every frame, so each line's rows, and whether it stays on one shrunk row, are worked
out once and remembered (_line_rows).
"""

from functools import lru_cache


def wrap_log_line(font, text, width, one_row=None):
    """Split one log line into rows no wider than ``width`` at ``font``'s size.

    A line that fits is returned whole and unchanged. So is a wider line for which
    ``one_row(font, text, width)`` is true: its panel draws it on one row, shrunk
    to fit (log_rows). Otherwise words wrap at spaces; a single word wider than
    ``width`` is broken between characters.
    """
    return [row for row, _starts_line in _line_rows(font, str(text), width, one_row)]


# Comfortably more than the 500 lines a hand history keeps, so drawing every frame
# never pushes out a line it still shows.
@lru_cache(maxsize=4096)
def _line_rows(font, text, width, one_row=None):
    """wrap_log_line's rows for one line, each marked with whether it starts the line.

    one_row is asked only about a line wider than ``width``, once per line (the
    answer is remembered with the rows).
    """
    if font.size(text)[0] <= width or (one_row is not None and one_row(font, text, width)):
        return ((text, True),)

    rows = _wrap(font, text, width)
    return tuple((row, index == 0) for index, row in enumerate(rows))


def _wrap(font, text, width):
    """The rows of a line wider than ``width``, wrapped at spaces."""
    rows = []
    row = ""

    for word in text.split():
        trial = f"{row} {word}" if row else word

        if font.size(trial)[0] <= width:
            row = trial
            continue

        if row:
            rows.append(row)

        # A word too wide on its own row is cut into its longest starts that fit (at
        # least one character each). Each start is measured growing from the front,
        # so a row costs about its own length in measurements and even a very long
        # word wraps in linear time.
        too_wide = font.size(word)[0] > width

        while too_wide and len(word) > 1:
            cut = 1
            while cut < len(word) and font.size(word[:cut + 1])[0] <= width:
                cut += 1

            if cut == len(word):
                break

            rows.append(word[:cut])
            word = word[cut:]

        row = word

    if row:
        rows.append(row)

    return rows or [""]


def log_rows(font, lines, width, one_row=None):
    """Every log line wrapped (wrap_log_line): ``[(row text, starts a line)]``.

    one_row(font, text, width): whether the panel draws a line wider than ``width``
    legibly on one row, shrunk to fit as it always did; such a line is one row, its
    whole text. It must be a function that always gives the same answer for the
    same line (a module-level function, say): the rows are remembered by it. The
    panel draws every row with its shrink-to-fit renderer, which leaves a row that
    fits as it is. Without one_row every line wider than ``width`` wraps.
    """
    rows = []

    for line in lines:
        rows.extend(_line_rows(font, str(line), width, one_row))

    return rows


def _fill(rows, first, last, step, height, line_step, row_step, row_height):
    """How far from row ``first`` a window can grow towards ``last`` (step -1 or +1)
    and still fit ``height``: the index of the furthest row that fits.

    The first row of a line sits ``line_step`` below the row above it and a wrapped
    row ``row_step`` below; ``row_height`` is one row's height.
    """
    index = first
    extent = row_height

    while index != last:
        below = index if step < 0 else index + step
        extent += line_step if rows[below][1] else row_step

        if extent > height:
            break

        index += step

    return index


def visible_log_rows(rows, scroll, height, line_step, row_step, row_height):
    """The rows a log panel shows, oldest first: ``[(row text, y offset)]``.

    rows: from log_rows. scroll: rows scrolled back from the newest (0 shows the
    newest row last). The newest rows whose extent fits ``height`` are shown, from
    offset 0: the first row of a line sits ``line_step`` below the row above it, and
    a wrapped row ``row_step`` below (``row_height`` is one row's height). At least
    one row is shown. When nothing wraps these are the newest lines, ``line_step``
    apart, as the panels always drew them.

    Unscrolled (the view the panel normally shows) the window starts on the first
    row of a line: when only the end of an older line would fit at the top (say its
    last row, 'kickers).'), those rows are left out, unless the whole window is one
    line too long to show at once. Scrolled back, the window is filled with every
    row that fits above its newest row, so the rows above come into view.
    """
    end = max(0, min(len(rows), len(rows) - max(0, int(scroll))))

    if not end:
        return []

    start = _fill(rows, end - 1, 0, -1, height, line_step, row_step, row_height)

    if end == len(rows) and start > 0 and not rows[start][1]:
        start = next(
            (index for index in range(start, end) if rows[index][1]),
            start
        )

    shown = []
    offset = 0

    for index, (text, starts_line) in enumerate(rows[start:end]):
        if index:
            offset += line_step if starts_line else row_step
        shown.append((text, offset))

    return shown


def max_log_scroll(rows, height, line_step, row_step, row_height):
    """The furthest a log panel scrolls back (visible_log_rows' ``scroll``).

    There the window shows the oldest rows that fit, from the first; one step less
    and the first row is not shown. When nothing wraps this is the line count less
    the lines that fit, as the wheel always stopped.
    """
    if not rows:
        return 0

    last = _fill(rows, 0, len(rows) - 1, 1, height, line_step, row_step, row_height)

    return len(rows) - 1 - last
