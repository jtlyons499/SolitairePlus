import random
import pygame

ACTION_BACK = "back"
ACTION_START = "start"
ACTION_RANDOMIZE = "randomize"
ACTION_CYCLE = "cycle"

WHITE = (245, 245, 240)
CREAM = (232, 220, 190)
GOLD = (230, 190, 72)
DARK = (18, 23, 24)
PANEL = (28, 42, 38)

BACK_RECT = pygame.Rect(55, 690, 180, 48)
RANDOM_RECT = pygame.Rect(915, 690, 180, 48)
START_RECT = pygame.Rect(1110, 690, 200, 48)

SLOT_RECTS = [
    pygame.Rect(255, 145 + i * 126, 855, 104)
    for i in range(4)
]
LEFT_RECTS = [pygame.Rect(rect.x + 14, rect.y + 28, 54, 48) for rect in SLOT_RECTS]
RIGHT_RECTS = [pygame.Rect(rect.right - 68, rect.y + 28, 54, 48) for rect in SLOT_RECTS]

_fonts = None


def _get_fonts():
    global _fonts
    if _fonts is None:
        _fonts = {
            "title": pygame.font.SysFont("cambria", 36, bold=True),
            "large": pygame.font.SysFont("cambria", 23, bold=True),
            "medium": pygame.font.SysFont("cambria", 18, bold=True),
            "small": pygame.font.SysFont("cambria", 14),
        }
    return _fonts


def _draw_button(surface, rect, text, mouse_pos, enabled=True, accent=False):
    fonts = _get_fonts()
    hovered = enabled and mouse_pos is not None and rect.collidepoint(mouse_pos)
    if not enabled:
        fill = (55, 58, 58)
        border = (100, 105, 103)
        color = (145, 148, 147)
    else:
        fill = (48, 94, 68) if hovered else (31, 69, 54)
        border = GOLD if (hovered or accent) else (205, 210, 205)
        color = WHITE
    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, border, rect, 3 if hovered else 2, border_radius=9)
    label = fonts["medium"].render(text, True, color)
    surface.blit(label, label.get_rect(center=rect.center))


def _npc_by_id(roster, npc_id):
    for npc in roster:
        if npc.get("id") == npc_id:
            return npc
    return None


def make_default_selection(roster, count=4, rng=None):
    rng = rng or random
    roster = list(roster or [])
    if len(roster) <= count:
        return [npc.get("id") for npc in roster]
    picks = rng.sample(roster, count)
    return [npc.get("id") for npc in picks]


def normalize_selection(roster, selected_ids, count=4):
    roster = list(roster or [])
    valid_ids = [npc.get("id") for npc in roster if npc.get("id")]
    cleaned = []
    for npc_id in list(selected_ids or []):
        if npc_id in valid_ids and npc_id not in cleaned:
            cleaned.append(npc_id)
    for npc_id in valid_ids:
        if len(cleaned) >= count:
            break
        if npc_id not in cleaned:
            cleaned.append(npc_id)
    return cleaned[:count]


def cycle_selection(roster, selected_ids, slot_index, direction):
    roster = list(roster or [])
    selected = normalize_selection(roster, selected_ids)
    if not roster or not (0 <= slot_index < len(selected)):
        return selected

    ids = [npc.get("id") for npc in roster if npc.get("id")]
    current_id = selected[slot_index]
    try:
        current_pos = ids.index(current_id)
    except ValueError:
        current_pos = 0

    used = set(selected)
    used.discard(current_id)
    step = 1 if direction >= 0 else -1
    for offset in range(1, len(ids) + 1):
        candidate = ids[(current_pos + step * offset) % len(ids)]
        if candidate not in used:
            selected[slot_index] = candidate
            break
    return selected


def draw_debug_poker_npc_select(
        surface,
        mouse_pos,
        game_label,
        roster,
        selected_ids,
        portrait_loader=None,
        can_start=True,
        cash=0,
):
    fonts = _get_fonts()
    surface.fill((20, 56, 42))

    title = fonts["title"].render(f"DEBUG {game_label.upper()} OPPONENTS", True, WHITE)
    surface.blit(title, title.get_rect(center=(683, 58)))

    subtitle = fonts["small"].render(
        "Choose the four NPCs at the table. Arrows cycle each seat independently.",
        True,
        CREAM,
    )
    surface.blit(subtitle, subtitle.get_rect(center=(683, 95)))

    selected = normalize_selection(roster, selected_ids)
    for slot_index, rect in enumerate(SLOT_RECTS):
        pygame.draw.rect(surface, PANEL, rect, border_radius=12)
        pygame.draw.rect(surface, GOLD if slot_index == 0 else (150, 160, 155), rect, 2, border_radius=12)

        _draw_button(surface, LEFT_RECTS[slot_index], "<", mouse_pos)
        _draw_button(surface, RIGHT_RECTS[slot_index], ">", mouse_pos)

        npc = _npc_by_id(roster, selected[slot_index]) if slot_index < len(selected) else None
        portrait_rect = pygame.Rect(rect.x + 88, rect.y + 12, 80, 80)
        if npc is not None and portrait_loader is not None:
            try:
                portrait = portrait_loader(npc, 80)
            except Exception:
                portrait = None
            if portrait is not None:
                portrait = pygame.transform.smoothscale(portrait, portrait_rect.size)
                surface.blit(portrait, portrait_rect)
            else:
                pygame.draw.rect(surface, (65, 72, 70), portrait_rect, border_radius=8)
        else:
            pygame.draw.rect(surface, (65, 72, 70), portrait_rect, border_radius=8)
        pygame.draw.rect(surface, (220, 220, 215), portrait_rect, 2, border_radius=8)

        if npc is not None:
            name = str(npc.get("name", "NPC"))
            tier = str(npc.get("skill_tier", "unknown")).replace("_", " ").title()
            age = npc.get("age", "?")
            hometown = str(npc.get("hometown", "Unknown"))
            personality = str(npc.get("game_personality", "balanced")).replace("_", " ").title()
            line1 = fonts["large"].render(f"Seat {slot_index + 1}: {name}", True, WHITE)
            line2 = fonts["small"].render(
                f"{tier}  |  {personality}  |  Age {age}  |  {hometown}",
                True,
                CREAM,
            )
            surface.blit(line1, (rect.x + 185, rect.y + 24))
            surface.blit(line2, (rect.x + 185, rect.y + 59))

    _draw_button(surface, BACK_RECT, "Back", mouse_pos)
    _draw_button(surface, RANDOM_RECT, "Randomize", mouse_pos)
    _draw_button(surface, START_RECT, "Start Table", mouse_pos, enabled=can_start, accent=True)

    if not can_start:
        warning = fonts["small"].render(
            f"Need at least $100 Career cash to start this debug table. Current cash: ${int(cash):,}",
            True,
            (245, 175, 120),
        )
        surface.blit(warning, warning.get_rect(center=(683, 665)))


def get_debug_poker_select_action(mouse_pos, can_start=True):
    if mouse_pos is None:
        return None
    if BACK_RECT.collidepoint(mouse_pos):
        return (ACTION_BACK, None)
    if RANDOM_RECT.collidepoint(mouse_pos):
        return (ACTION_RANDOMIZE, None)
    if can_start and START_RECT.collidepoint(mouse_pos):
        return (ACTION_START, None)
    for slot_index in range(4):
        if LEFT_RECTS[slot_index].collidepoint(mouse_pos):
            return (ACTION_CYCLE, (slot_index, -1))
        if RIGHT_RECTS[slot_index].collidepoint(mouse_pos):
            return (ACTION_CYCLE, (slot_index, 1))
    return None
