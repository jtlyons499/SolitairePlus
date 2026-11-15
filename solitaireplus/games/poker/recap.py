"""Exact pot awards with a player-controlled review screen."""
import pygame
from solitaireplus.games.poker.core import collected_uncontested
from solitaireplus.ui import text as ui_text

OPEN = pygame.Rect(278, 580, 150, 26)
CLOSE = pygame.Rect(898, 652, 198, 48)
PREV = pygame.Rect(272, 652, 160, 48)
NEXT = pygame.Rect(444, 652, 160, 48)
ROWS = 9


def _pot_shares(pot):
    """Yield (seat, chips, share) for each winner of one pot record, in odd-chip order."""
    winners = pot.get('winners', [])
    payouts = pot.get('payouts')
    share = int(pot.get('share', 0))
    if 'share' not in pot and winners:
        share = int(pot.get('amount', 0)) // len(winners)
    for order, seat in enumerate(winners):
        if payouts is not None:
            amount = int(payouts.get(seat, 0))
        else:
            amount = share + (order < int(pot.get('remainder', 0)))
        yield seat, amount, share


def received_total(game, seat=0):
    """Every chip ``seat`` got back from the last hand: its pot payouts plus its refunds.

    The recap's 'You received' and Hold'em's collapsed showdown banner both show this.
    """
    total = sum(
        amount
        for pot in getattr(game, 'last_pot_awards', [])
        for winner, amount, _share in _pot_shares(pot)
        if winner == seat
    )
    return total + int(getattr(game, 'last_refunds', {}).get(seat, 0))


def player_hand_net(game):
    """The human's net for the last hand: received_total minus its hand contribution.

    The recap's 'Your net for this hand' line shows it, and the Hold'em, Draw and Stud
    tables pay cash-win fans on it when it is above 0 (as every casino game pays on its net).
    """
    return received_total(game, 0) - int(getattr(game, 'player_hand_contribution', 0))


def pot_explanation(pot, awards):
    """What decided one pot: its winning hand, or why no hand won it.

    A pot nobody else could win at a showdown names no hand (core.collected_uncontested);
    a fold win's pot says everyone else folded.
    """
    if collected_uncontested(pot, awards):
        return 'Nobody else could win it'
    return pot.get('hand') or 'Everyone else folded'


def recap_lines(game):
    lines = []
    for index, pot in enumerate(game.last_pot_awards):
        label = 'Main pot' if index == 0 else f'Side pot {index}'
        lines.append(f"{label}: ${pot.get('amount', 0):,} — {pot_explanation(pot, game.last_pot_awards)}")
        for seat, amount, share in _pot_shares(pot):
            name = game.get_table_player_name(seat)
            verb = "receive" if seat == 0 else "receives"
            lines.append(f"    {name} {verb} ${amount:,}" + (' (odd chip included)' if amount > share else ''))
        eligible = [game.get_table_player_name(seat) for seat in pot.get('eligible', [])]
        lines.append('    Eligible: ' + ', '.join(eligible))
    # Uncalled chips go back to whoever bet them: not a pot, but part of what you got back.
    # They get their own heading so they do not read as part of the last pot.
    refunds = sorted(getattr(game, 'last_refunds', {}).items())
    if refunds:
        lines.append('Returned (uncalled):')
    for seat, amount in refunds:
        name = 'you' if seat == 0 else game.get_table_player_name(seat)
        lines.append(f"    Uncalled ${int(amount):,} returned to {name}")
    if not lines:
        lines.append(game.result_text or 'No resolved pot.')
    your_total = received_total(game, 0)
    contribution = int(getattr(game, 'player_hand_contribution', 0))
    net = player_hand_net(game)
    sign = '+' if net >= 0 else '−'
    lines.extend([f'You received: ${your_total:,}', f'Your hand contribution: ${contribution:,}',
                  f'Your net for this hand: {sign}${abs(net):,}'])
    return lines


def _indent(value):
    """The leading spaces of a recap line (its place under a heading)."""
    return value[:len(value) - len(value.lstrip(' '))]


def _wrap_recap_line(font, value):
    """Wrap one recap line into rows at most 800 px wide; every row keeps the line's indent."""
    indent = _indent(value)
    width = 800 - font.size(indent)[0]
    rows = []
    row = ''
    for word in value.split():
        trial = (row + ' ' + word).strip()
        if row and font.size(trial)[0] > width:
            rows.append(indent + row)
            row = word
        else:
            row = trial
    rows.append(indent + row)
    return rows


def _continued(heading):
    """A heading repeated at the top of the next page: 'Main pot: $300 — Aces (continued)',
    'Returned (uncalled) (continued):'."""
    if heading.endswith(':'):
        return heading[:-1] + ' (continued):'
    return heading + ' (continued)'


def recap_pages(game):
    """The recap's rows split into pages of ROWS rows.

    A heading (a line with indented lines under it: a pot, or 'Returned (uncalled):')
    never ends a page: when it and its first indented row do not both fit, it starts
    the next page. When a page still ends inside a heading's rows, the next page starts
    with that heading again, marked '(continued)'. Other rows flow on as they come.
    """
    font = ui_text.get_font(None, 32)
    lines = recap_lines(game)
    pages = [[]]
    heading_line = None   # the heading the current indented rows belong to
    for index, value in enumerate(lines):
        rows = _wrap_recap_line(font, value)
        indented = bool(_indent(value))
        heading = (not indented and index + 1 < len(lines)
                   and bool(_indent(lines[index + 1])))
        if not indented:
            heading_line = value if heading else None
        needed = len(rows) + (1 if heading else 0)
        if heading and pages[-1] and len(pages[-1]) + needed > ROWS and needed <= ROWS:
            pages.append([])
        for row in rows:
            if len(pages[-1]) == ROWS:
                pages.append([])
                continued = (_wrap_recap_line(font, _continued(heading_line))
                             if indented and heading_line is not None else [])
                if len(continued) < ROWS:
                    pages[-1].extend(continued)
            pages[-1].append(row)
    return pages


def recap_display_lines(game):
    """Every recap row in page order (recap_pages), wrapped at a fixed readable size.

    Indented lines keep their indent on every row, so the hierarchy under each pot
    and under 'Returned (uncalled):' shows on screen. A heading a page break split
    from its rows appears again, marked '(continued)'.
    """
    return [row for page in recap_pages(game) for row in page]


def get_recap_action(mouse, game):
    if not game.hand_complete or mouse is None:
        return None
    if getattr(game, 'recap_open', False):
        for rect, name in ((CLOSE, 'recap_close'), (PREV, 'recap_prev'), (NEXT, 'recap_next')):
            if rect.collidepoint(mouse):
                return name
        return 'recap_block'
    if OPEN.collidepoint(mouse):
        return 'recap_open'
    return None


def handle_recap_action(game, action):
    if not action or not action.startswith('recap_'):
        return False
    if action == 'recap_open':
        game.recap_open, game.recap_page = True, 0
    elif action == 'recap_close':
        game.recap_open = False
    elif action in ('recap_prev', 'recap_next'):
        pages = len(recap_pages(game))
        game.recap_page = max(0, min(pages - 1, getattr(game, 'recap_page', 0) + (1 if action == 'recap_next' else -1)))
    return True


def draw_recap(surface, mouse, game):
    if not game.hand_complete:
        return
    font = ui_text.get_font(None, 29)
    def button(rect, value, enabled=True):
        hover = enabled and mouse is not None and rect.collidepoint(mouse)
        pygame.draw.rect(surface, (52,100,78) if hover else (29,57,49), rect, border_radius=8)
        pygame.draw.rect(surface, (232,195,105) if enabled else (95,110,105), rect, 2, border_radius=8)
        text = ui_text.get_font(None, 24 if rect == OPEN else 29).render(value, True, (245,240,221) if enabled else (130,145,139))
        surface.blit(text, text.get_rect(center=rect.center))
    if not getattr(game, 'recap_open', False):
        button(OPEN, 'Payout details')
        return
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0,0,0,195));surface.blit(overlay,(0,0))
    panel = pygame.Rect(242, 58, 882, 658)
    pygame.draw.rect(surface, (22,40,38), panel, border_radius=18)
    pygame.draw.rect(surface, (230,191,98), panel, 3, border_radius=18)
    title = ui_text.get_font(None, 42).render('HAND / POT RECAP', True, (240,202,119))
    surface.blit(title, (272,82))
    surface.blit(font.render('Auto-deal and cash-out pause while you review.', True, (188,207,195)), (272,133))
    all_pages = recap_pages(game)
    pages = len(all_pages)
    page = max(0,min(pages-1,getattr(game,'recap_page',0)))
    for i, value in enumerate(all_pages[page]):
        image = ui_text.get_font(None, 32).render(value, True, (243,236,216))
        surface.blit(image, (272,184+i*46))
    surface.blit(font.render(f'Page {page+1} / {pages}',True,(207,219,210)),(652,665))
    button(PREV,'Previous',page>0);button(NEXT,'Next',page+1<pages);button(CLOSE,'Back to table')

