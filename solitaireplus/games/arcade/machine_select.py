"""The arcade machines' opponent and difficulty pickers (moved out of legacy.py)."""
from solitaireplus.games.arcade.ace_invaders import ACE_INVADERS_DIFFICULTIES
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.games.arcade.battle_bosses import BATTLE_BOSSES_DIFFICULTIES
from solitaireplus.games.arcade.king_pong import KING_PONG_DIFFICULTIES
from solitaireplus.npc.manager import NPCS
from solitaireplus.games.arcade.suit_snake import SUIT_SNAKE_MODES
from solitaireplus.games.arcade.suit_snake import SUIT_SNAKE_MOVEMENT_STYLES
from solitaireplus.games.arcade.battle_bosses import build_battle_bosses_choices
from solitaireplus.games.arcade.support import get_machine_cost
from solitaireplus.app import paths
import pygame
import random
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.app.lazy import lazy
machine_screens = lazy("solitaireplus.games.arcade.machine_screens")
hub_screens = lazy("solitaireplus.games.arcade.hub_screens")
game_portraits = lazy("solitaireplus.npc.game_portraits")
images = lazy("solitaireplus.ui.images")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")


king_pong_opponent_rects = [
    pygame.Rect(103 + index * 292, 205, 266, 340)
    for index in range(4)
]
king_pong_opponent_back_rect = pygame.Rect(103, 657, 220, 54)
king_pong_opponent_tokens_rect = pygame.Rect(573, 657, 220, 54)
king_pong_opponent_play_rect = pygame.Rect(1043, 657, 220, 54)

battle_bosses_choice_rects = [
    pygame.Rect(108 + (index % 2) * 590, 205 + (index // 2) * 210, 552, 185)
    for index in range(4)
]
battle_bosses_back_rect = pygame.Rect(108, 651, 240, 54)
battle_bosses_refresh_rect = pygame.Rect(563, 651, 240, 54)
battle_bosses_future_play_rect = pygame.Rect(1018, 651, 240, 54)

ace_invaders_difficulty_rects = [
    pygame.Rect(103 + index * 292, 220, 266, 320)
    for index in range(4)
]
ace_invaders_back_rect = pygame.Rect(103, 657, 220, 54)
ace_invaders_tokens_rect = pygame.Rect(573, 657, 220, 54)
ace_invaders_play_rect = pygame.Rect(1043, 657, 220, 54)

suit_snake_mode_rects = [
    pygame.Rect(103 + index * 292, 212, 266, 300)
    for index in range(4)
]
suit_snake_step_movement_rect = pygame.Rect(438, 548, 230, 52)
suit_snake_smooth_movement_rect = pygame.Rect(698, 548, 230, 52)
suit_snake_back_rect = pygame.Rect(103, 657, 220, 54)
suit_snake_tokens_rect = pygame.Rect(573, 657, 220, 54)
suit_snake_play_rect = pygame.Rect(1043, 657, 220, 54)


def build_king_pong_opponent_choices():
    """Pick one current Career NPC for each arcade difficulty tier."""
    choices = []
    used_ids = set()
    fallback_pool = [
        npc for npc in NPCS
        if isinstance(npc, dict) and npc.get("name")
    ]

    for difficulty_id, config in KING_PONG_DIFFICULTIES.items():
        tier = config.get("npc_tier", "mid")
        tier_pool = [
            npc for npc in fallback_pool
            if npc.get("skill_tier", "mid") == tier
            and npc.get("id") not in used_ids
        ]

        if not tier_pool:
            tier_pool = [
                npc for npc in fallback_pool
                if npc.get("id") not in used_ids
            ]

        if tier_pool:
            npc = random.choice(tier_pool)
            npc_id = npc.get("id")
            if npc_id is not None:
                used_ids.add(npc_id)
        else:
            npc = {
                "id": f"arcade_{difficulty_id}",
                "name": f"{config.get('label', difficulty_id.title())} Arcade Bot",
                "skill_tier": tier,
            }

        choices.append({
            "difficulty_id": difficulty_id,
            "npc": npc,
        })

    return choices


def open_king_pong_opponent_select(refresh=True):

    if refresh or len(state.king_pong_opponent_choices) != len(KING_PONG_DIFFICULTIES):
        state.king_pong_opponent_choices = build_king_pong_opponent_choices()
        state.king_pong_selected_opponent_index = None

    state.arcade_pending_launch_game_id = None
    state.current_state = state_names.STATE_KING_PONG_OPPONENT_SELECT


def build_battle_bosses_opponent_choices():
    return build_battle_bosses_choices(NPCS)


def open_battle_bosses_opponent_select(refresh=True):

    if refresh or len(state.battle_bosses_opponent_choices) != len(BATTLE_BOSSES_DIFFICULTIES):
        state.battle_bosses_opponent_choices = build_battle_bosses_opponent_choices()
        state.battle_bosses_selected_choice_index = None

    state.current_state = state_names.STATE_BATTLE_BOSSES_OPPONENT_SELECT


def open_ace_invaders_difficulty_select(reset_selection=False):

    if reset_selection:
        state.ace_invaders_selected_difficulty_index = None

    state.arcade_pending_launch_game_id = None
    state.current_state = state_names.STATE_ACE_INVADERS_DIFFICULTY_SELECT


def get_selected_ace_invaders_difficulty():
    difficulty_ids = list(ACE_INVADERS_DIFFICULTIES)
    if (
            state.ace_invaders_selected_difficulty_index is None
            or state.ace_invaders_selected_difficulty_index < 0
            or state.ace_invaders_selected_difficulty_index >= len(difficulty_ids)
    ):
        return None
    return difficulty_ids[state.ace_invaders_selected_difficulty_index]


def open_suit_snake_difficulty_select(reset_selection=False):
    """Open Suit Snake's mode/movement setup screen.

    The state name is retained for debug/navigation compatibility even though
    Suit Snake now selects cabinet modes instead of speed difficulties.
    """

    if reset_selection:
        state.suit_snake_selected_mode_index = None
        state.suit_snake_selected_movement_style = "step"

    state.arcade_pending_launch_game_id = None
    state.current_state = state_names.STATE_SUIT_SNAKE_DIFFICULTY_SELECT


def get_selected_suit_snake_mode():
    mode_ids = list(SUIT_SNAKE_MODES)
    if (
            state.suit_snake_selected_mode_index is None
            or state.suit_snake_selected_mode_index < 0
            or state.suit_snake_selected_mode_index >= len(mode_ids)
    ):
        return None
    return mode_ids[state.suit_snake_selected_mode_index]


def get_selected_battle_bosses_choice():
    if (
            state.battle_bosses_selected_choice_index is None
            or state.battle_bosses_selected_choice_index < 0
            or state.battle_bosses_selected_choice_index >= len(state.battle_bosses_opponent_choices)
    ):
        return None
    return state.battle_bosses_opponent_choices[state.battle_bosses_selected_choice_index]


def get_selected_king_pong_choice():
    if (
            state.king_pong_selected_opponent_index is None
            or state.king_pong_selected_opponent_index < 0
            or state.king_pong_selected_opponent_index >= len(state.king_pong_opponent_choices)
    ):
        return None
    return state.king_pong_opponent_choices[state.king_pong_selected_opponent_index]

def draw_king_pong_opponent_select():
    hub_screens.draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = images.get_event_ui_asset(
        str(paths.asset("arcade/king_pong/logo.png")),
        (330, 94),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 100)))
    else:
        title = fonts.options_title_font.render("KING PONG", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 92)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a rival. Harder opponents move faster and pay more tickets.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 154)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS: {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS: {int(state.arcade_state.get('tickets', 0)):,}",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 181)))

    difficulty_descriptions = {
        "low": "Slow reactions / wide tracking error",
        "medium": "Balanced arcade opponent",
        "high": "Fast reactions / accurate tracking",
        "expert": "Very fast / very small tracking error",
    }

    for index, choice in enumerate(state.king_pong_opponent_choices[:4]):
        rect = king_pong_opponent_rects[index]
        difficulty_id = choice.get("difficulty_id", "medium")
        config = KING_PONG_DIFFICULTIES.get(
            difficulty_id,
            KING_PONG_DIFFICULTIES["medium"],
        )
        npc = choice.get("npc") or {}
        selected = index == state.king_pong_selected_opponent_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (255, 217, 108) if selected else ((102, 196, 225) if hovered else (111, 126, 145))
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(window.game_surface, border, rect, 4 if selected else 2, border_radius=14)

        difficulty_surface = fonts.option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        window.game_surface.blit(
            difficulty_surface,
            difficulty_surface.get_rect(center=(rect.centerx, rect.y + 32)),
        )

        portrait_rect = pygame.Rect(rect.centerx - 55, rect.y + 62, 110, 110)
        pygame.draw.ellipse(window.game_surface, (14, 23, 34), portrait_rect)
        try:
            portrait = game_portraits.get_npc_portrait_surface(npc, 110)
        except Exception:
            portrait = None
        if portrait is not None:
            portrait = pygame.transform.smoothscale(portrait, portrait_rect.size)
            mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
            pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
            clipped = portrait.copy()
            clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            window.game_surface.blit(clipped, portrait_rect.topleft)
        pygame.draw.ellipse(window.game_surface, (229, 197, 102), portrait_rect, 3)

        npc_name = str(npc.get("name") or "Arcade Rival")
        name_surface = fonts.option_label_font.render(npc_name, True, (242, 245, 248))
        if name_surface.get_width() > rect.width - 24:
            name_surface = fonts.difficulty_detail_font.render(npc_name, True, (242, 245, 248))
        window.game_surface.blit(
            name_surface,
            name_surface.get_rect(center=(rect.centerx, rect.y + 198)),
        )

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward_surface = fonts.option_label_font.render(
            f"x{multiplier:.2f} TICKETS",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        window.game_surface.blit(
            reward_surface,
            reward_surface.get_rect(center=(rect.centerx, rect.y + 238)),
        )

        description_rect = pygame.Rect(
            rect.x + 16,
            rect.y + 258,
            rect.width - 32,
            50,
        )
        ui_text.draw_wrapped_text_limited(
            difficulty_descriptions.get(difficulty_id, "Arcade opponent"),
            fonts.difficulty_detail_font,
            (185, 195, 207),
            description_rect,
            2,
            line_spacing=1,
        )

        select_note = fonts.difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        window.game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 30)),
        )

    hub_screens.draw_arcade_action_image_button(
        king_pong_opponent_back_rect,
        "back",
        "Back",
    )
    hub_screens.draw_arcade_action_image_button(
        king_pong_opponent_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
    )

    token_cost = get_machine_cost("king_pong")
    can_play = (
        get_selected_king_pong_choice() is not None
        and int(state.arcade_state.get("tokens", 0)) >= token_cost
    )
    hub_screens.draw_arcade_action_image_button(
        king_pong_opponent_play_rect,
        "play_tokens",
        f"Play - {token_cost} Tokens",
        enabled=can_play,
        badge_text=f"{token_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(
            state.arcade_status_message,
            True,
            (248, 242, 216),
        )
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 620)))


def draw_battle_bosses_opponent_select():
    hub_screens.draw_arcade_page_background(62)

    panel = pygame.Rect(72, 42, 1222, 690)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = images.get_event_ui_asset(
        str(paths.asset("arcade/battle_bosses/logo.png")),
        (390, 92),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 92)))
    else:
        title = fonts.options_title_font.render("BATTLE BOSSES", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 86)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a three-rival squad. Harder squads move faster and pay more tickets.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 139)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS: {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS: {int(state.arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY: {get_machine_cost('battle_bosses')} TOKENS",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 170)))

    battle_name_font = ui_text.get_font(None, 19)

    for index, choice in enumerate(state.battle_bosses_opponent_choices[:4]):
        rect = battle_bosses_choice_rects[index]
        difficulty_id = choice.get("difficulty_id", "standard")
        config = choice.get("config") or BATTLE_BOSSES_DIFFICULTIES.get(
            difficulty_id,
            BATTLE_BOSSES_DIFFICULTIES["standard"],
        )
        selected = index == state.battle_bosses_selected_choice_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (255, 217, 108) if selected else ((102, 196, 225) if hovered else (111, 126, 145))
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(window.game_surface, border, rect, 4 if selected else 2, border_radius=14)

        difficulty_surface = fonts.option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        window.game_surface.blit(
            difficulty_surface,
            difficulty_surface.get_rect(midleft=(rect.x + 18, rect.y + 27)),
        )

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward_surface = fonts.difficulty_detail_font.render(
            f"x{multiplier:.2f} tickets",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        window.game_surface.blit(
            reward_surface,
            reward_surface.get_rect(midright=(rect.right - 18, rect.y + 28)),
        )

        npcs = list(choice.get("npcs") or [])[:3]
        portrait_y = rect.y + 54
        portrait_size = 76
        portrait_gap = 28
        group_width = portrait_size * 3 + portrait_gap * 2
        group_x = rect.centerx - group_width // 2

        for npc_index, npc in enumerate(npcs):
            portrait_rect = pygame.Rect(
                group_x + npc_index * (portrait_size + portrait_gap),
                portrait_y,
                portrait_size,
                portrait_size,
            )
            pygame.draw.ellipse(window.game_surface, (14, 23, 34), portrait_rect)
            try:
                portrait = game_portraits.get_npc_portrait_surface(npc, portrait_size)
            except Exception:
                portrait = None
            if portrait is not None:
                portrait = pygame.transform.smoothscale(portrait, portrait_rect.size)
                mask = pygame.Surface(portrait_rect.size, pygame.SRCALPHA)
                pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
                clipped = portrait.copy()
                clipped.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                window.game_surface.blit(clipped, portrait_rect.topleft)
            pygame.draw.ellipse(window.game_surface, (229, 197, 102), portrait_rect, 2)

            npc_name = str(npc.get("name") or f"Rival {npc_index + 1}")
            name_surface = battle_name_font.render(npc_name, True, (232, 236, 240))
            max_name_width = 92
            if name_surface.get_width() > max_name_width:
                scale = max_name_width / max(1, name_surface.get_width())
                name_surface = pygame.transform.smoothscale(
                    name_surface,
                    (max_name_width, max(1, int(name_surface.get_height() * scale))),
                )
            window.game_surface.blit(
                name_surface,
                name_surface.get_rect(center=(portrait_rect.centerx, portrait_rect.bottom + 15)),
            )

        description = fonts.difficulty_detail_font.render(
            config.get("description", "Three-rival arcade squad."),
            True,
            (185, 195, 207),
        )
        window.game_surface.blit(
            description,
            description.get_rect(center=(rect.centerx, rect.bottom - 20)),
        )

    hub_screens.draw_arcade_action_image_button(
        battle_bosses_back_rect,
        "back",
        "Back",
    )
    hub_screens.draw_arcade_action_image_button(
        battle_bosses_refresh_rect,
        "reroll_rivals",
        "Reroll Rivals",
    )
    battle_cost = get_machine_cost("battle_bosses")
    can_play = get_selected_battle_bosses_choice() is not None
    hub_screens.draw_arcade_action_image_button(
        battle_bosses_future_play_rect,
        "play_tokens",
        f"Play - {battle_cost} Tokens",
        enabled=can_play,
        badge_text=f"{battle_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(state.arcade_status_message, True, (248, 242, 216))
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 625)))


def draw_ace_invaders_difficulty_select():
    hub_screens.draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = images.get_event_ui_asset(
        str(paths.asset("arcade/ace_invaders/logo.png")),
        (360, 96),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 96)))
    else:
        title = fonts.options_title_font.render("ACE INVADERS", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 90)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a difficulty. Survive consecutive waves to earn tickets.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 157)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS {int(state.arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY {get_machine_cost('ace_invaders')}    |    "
        f"HIGH {int(state.arcade_state.get('stats', {}).get('ace_invaders_high_score', 0) or 0):,}",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 185)))

    difficulty_ids = list(ACE_INVADERS_DIFFICULTIES)
    for index, difficulty_id in enumerate(difficulty_ids[:4]):
        rect = ace_invaders_difficulty_rects[index]
        config = ACE_INVADERS_DIFFICULTIES[difficulty_id]
        selected = index == state.ace_invaders_selected_difficulty_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (
            (255, 217, 108)
            if selected
            else ((102, 196, 225) if hovered else (111, 126, 145))
        )
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            window.game_surface,
            border,
            rect,
            4 if selected else 2,
            border_radius=14,
        )

        label = fonts.option_label_font.render(
            config.get("label", difficulty_id.upper()),
            True,
            (255, 234, 141),
        )
        window.game_surface.blit(label, label.get_rect(center=(rect.centerx, rect.y + 35)))

        multiplier = float(config.get("ticket_multiplier", 1.0))
        reward = fonts.option_label_font.render(
            f"x{multiplier:.2f} TICKETS",
            True,
            (132, 222, 169) if multiplier >= 1.0 else (214, 201, 150),
        )
        window.game_surface.blit(reward, reward.get_rect(center=(rect.centerx, rect.y + 78)))

        rows = int(config.get("rows", 3))
        columns = int(config.get("columns", 8))
        enemy_count = rows * columns
        stat_lines = (
            f"Starts at {enemy_count} Aces",
            f"Formation speed: {int(config.get('formation_speed', 68))}",
            f"Enemy fire: {int(config.get('enemy_fire_ms', 1125))} ms",
            f"Shot speed: {int(config.get('enemy_bullet_speed', 220))}",
        )
        for line_index, line in enumerate(stat_lines):
            rendered = fonts.difficulty_detail_font.render(
                line,
                True,
                (219, 224, 230),
            )
            window.game_surface.blit(
                rendered,
                rendered.get_rect(center=(rect.centerx, rect.y + 126 + line_index * 30)),
            )

        description_rect = pygame.Rect(
            rect.x + 18,
            rect.y + 235,
            rect.width - 36,
            48,
        )
        ui_text.draw_wrapped_text_limited(
            config.get("description", "Arcade shooter difficulty."),
            fonts.difficulty_detail_font,
            (178, 190, 204),
            description_rect,
            2,
            line_spacing=3,
        )

        select_note = fonts.difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        window.game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 24)),
        )

    hub_screens.draw_arcade_action_image_button(
        ace_invaders_back_rect,
        "back",
        "Back",
    )
    hub_screens.draw_arcade_action_image_button(
        ace_invaders_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
    )

    token_cost = get_machine_cost("ace_invaders")
    can_play = (
        get_selected_ace_invaders_difficulty() is not None
        and int(state.arcade_state.get("tokens", 0)) >= token_cost
    )
    hub_screens.draw_arcade_action_image_button(
        ace_invaders_play_rect,
        "play_tokens",
        f"Play - {token_cost} Tokens",
        enabled=can_play,
        badge_text=f"{token_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.difficulty_detail_font.render(
            state.arcade_status_message,
            True,
            (248, 242, 216),
        )
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 620)))



def draw_suit_snake_difficulty_select():
    hub_screens.draw_arcade_page_background(62)

    panel = pygame.Rect(72, 44, 1222, 688)
    panel_surface = pygame.Surface(panel.size, pygame.SRCALPHA)
    panel_surface.fill((8, 15, 25, 238))
    window.game_surface.blit(panel_surface, panel.topleft)
    pygame.draw.rect(window.game_surface, (229, 197, 102), panel, 3, border_radius=16)

    logo = images.get_event_ui_asset(
        str(paths.asset("arcade/suit_snake/logo.png")),
        (360, 96),
    )
    if logo is not None:
        window.game_surface.blit(logo, logo.get_rect(center=(BASE_WIDTH // 2, 96)))
    else:
        title = fonts.options_title_font.render("SUIT SNAKE", True, (250, 249, 244))
        window.game_surface.blit(title, title.get_rect(center=(BASE_WIDTH // 2, 90)))

    subtitle = fonts.difficulty_detail_font.render(
        "Choose a mode, then choose Step or Smooth Movement.",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(subtitle, subtitle.get_rect(center=(BASE_WIDTH // 2, 157)))

    wallet = fonts.difficulty_detail_font.render(
        f"TOKENS {int(state.arcade_state.get('tokens', 0)):,}    |    "
        f"TICKETS {int(state.arcade_state.get('tickets', 0)):,}    |    "
        f"ENTRY {get_machine_cost('suit_snake')}    |    "
        f"HIGH {int(state.arcade_state.get('stats', {}).get('suit_snake_high_score', 0) or 0):,}",
        True,
        (255, 235, 145),
    )
    window.game_surface.blit(wallet, wallet.get_rect(center=(BASE_WIDTH // 2, 184)))

    mode_ids = list(SUIT_SNAKE_MODES)
    for index, mode_id in enumerate(mode_ids[:4]):
        rect = suit_snake_mode_rects[index]
        config = SUIT_SNAKE_MODES[mode_id]
        selected = index == state.suit_snake_selected_mode_index
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)

        fill = (34, 48, 64) if selected or hovered else (22, 31, 44)
        border = (
            (255, 217, 108)
            if selected
            else ((102, 196, 225) if hovered else (111, 126, 145))
        )
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=14)
        pygame.draw.rect(
            window.game_surface,
            border,
            rect,
            4 if selected else 2,
            border_radius=14,
        )

        label_lines = config.get("label_lines", (config.get("label", mode_id.upper()),))
        label_start_y = rect.y + 30
        for line_index, label_text in enumerate(label_lines[:2]):
            label = ui_text.render_text_fit(
                str(label_text),
                fonts.option_label_font,
                rect.width - 28,
                color=(255, 234, 141),
                minimum_size=16,
            )
            window.game_surface.blit(
                label,
                label.get_rect(center=(rect.centerx, label_start_y + line_index * 27)),
            )

        columns = int(config.get("grid_columns", 24))
        rows = int(config.get("grid_rows", 13))
        wraparound = bool(config.get("wraparound", False))
        stat_lines = (
            f"Grid: {columns} x {rows}",
            "Borders: WRAPAROUND" if wraparound else "Borders: DEADLY",
            "Self collision: Game Over",
        )
        for line_index, line in enumerate(stat_lines):
            rendered = fonts.difficulty_detail_font.render(
                line,
                True,
                (132, 222, 169) if wraparound and line_index == 1 else (219, 224, 230),
            )
            window.game_surface.blit(
                rendered,
                rendered.get_rect(center=(rect.centerx, rect.y + 105 + line_index * 30)),
            )

        description_rect = pygame.Rect(
            rect.x + 18,
            rect.y + 198,
            rect.width - 36,
            54,
        )
        ui_text.draw_wrapped_text_limited(
            config.get("description", "Suit Snake cabinet mode."),
            fonts.difficulty_detail_font,
            (178, 190, 204),
            description_rect,
            2,
            line_spacing=3,
        )

        select_note = fonts.difficulty_detail_font.render(
            "SELECTED" if selected else "Click to select",
            True,
            (255, 231, 143) if selected else (148, 161, 176),
        )
        window.game_surface.blit(
            select_note,
            select_note.get_rect(center=(rect.centerx, rect.bottom - 22)),
        )

    movement_label = fonts.difficulty_detail_font.render(
        "MOVEMENT STYLE",
        True,
        (213, 220, 228),
    )
    window.game_surface.blit(
        movement_label,
        movement_label.get_rect(center=(BASE_WIDTH // 2, 530)),
    )

    movement_options = (
        ("step", suit_snake_step_movement_rect),
        ("smooth", suit_snake_smooth_movement_rect),
    )
    for movement_id, rect in movement_options:
        selected = state.suit_snake_selected_movement_style == movement_id
        hovered = state.game_mouse_pos is not None and rect.collidepoint(state.game_mouse_pos)
        fill = (34, 48, 64) if selected or hovered else (20, 29, 41)
        border = (
            (255, 217, 108)
            if selected
            else ((102, 196, 225) if hovered else (111, 126, 145))
        )
        pygame.draw.rect(window.game_surface, fill, rect, border_radius=10)
        pygame.draw.rect(
            window.game_surface,
            border,
            rect,
            3 if selected else 2,
            border_radius=10,
        )
        movement_text = SUIT_SNAKE_MOVEMENT_STYLES[movement_id]["label"]
        rendered = ui_text.render_text_fit(
            movement_text,
            fonts.difficulty_detail_font,
            rect.width - 24,
            color=(255, 234, 141) if selected else (218, 225, 232),
            minimum_size=14,
        )
        window.game_surface.blit(rendered, rendered.get_rect(center=rect.center))

    movement_description = SUIT_SNAKE_MOVEMENT_STYLES[
        state.suit_snake_selected_movement_style
    ]["description"]
    description = fonts.ui_small_font.render(
        movement_description,
        True,
        (168, 181, 194),
    )
    window.game_surface.blit(
        description,
        description.get_rect(center=(BASE_WIDTH // 2, 614)),
    )

    hub_screens.draw_arcade_action_image_button(
        suit_snake_back_rect,
        "back",
        "Back",
    )
    hub_screens.draw_arcade_action_image_button(
        suit_snake_tokens_rect,
        "buy_tokens",
        "Buy Tokens",
    )

    token_cost = get_machine_cost("suit_snake")
    can_play = (
        get_selected_suit_snake_mode() is not None
        and int(state.arcade_state.get("tokens", 0)) >= token_cost
    )
    hub_screens.draw_arcade_action_image_button(
        suit_snake_play_rect,
        "play_tokens",
        f"Play - {token_cost} Token",
        enabled=can_play,
        badge_text=f"{token_cost} TOKEN" if token_cost == 1 else f"{token_cost} TOKENS",
    )

    if state.arcade_status_message and pygame.time.get_ticks() <= state.arcade_status_message_expires:
        info = fonts.ui_small_font.render(
            state.arcade_status_message,
            True,
            (248, 242, 216),
        )
        window.game_surface.blit(info, info.get_rect(center=(BASE_WIDTH // 2, 638)))


def loop_event_king_pong_opponent_select(event):
    """Old main-loop event branch for STATE_KING_PONG_OPPONENT_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        opponent_clicked = False

        for opponent_index, opponent_rect in enumerate(king_pong_opponent_rects):
            if (
                    opponent_index < len(state.king_pong_opponent_choices)
                    and opponent_rect.collidepoint(state.menu_mouse_pos)
            ):
                state.king_pong_selected_opponent_index = opponent_index
                sounds.audio.play_sound("button_click")
                opponent_clicked = True
                break

        if not opponent_clicked:
            if king_pong_opponent_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif king_pong_opponent_tokens_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                hub_screens.open_arcade_token_exchange("king_pong")

            elif king_pong_opponent_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_king_pong_choice() is None:
                    hub_screens.set_arcade_status_message("Choose a rival first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("king_pong"):
                    hub_screens.set_arcade_status_message("Not enough tokens. Buy more to play.")
                    hub_screens.open_arcade_token_exchange("king_pong")
                else:
                    sounds.audio.play_sound("button_click")
                    machine_screens.start_king_pong_session()


def loop_event_battle_bosses_opponent_select(event):
    """Old main-loop event branch for STATE_BATTLE_BOSSES_OPPONENT_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        choice_clicked = False
        for choice_index, choice_rect in enumerate(battle_bosses_choice_rects):
            if (
                    choice_index < len(state.battle_bosses_opponent_choices)
                    and choice_rect.collidepoint(state.menu_mouse_pos)
            ):
                state.battle_bosses_selected_choice_index = choice_index
                sounds.audio.play_sound("button_click")
                choice_clicked = True
                break

        if not choice_clicked:
            if battle_bosses_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT
            elif battle_bosses_refresh_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                open_battle_bosses_opponent_select(refresh=True)
                hub_screens.set_arcade_status_message("Battle Bosses rival squads rerolled.")
            elif battle_bosses_future_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_battle_bosses_choice() is None:
                    hub_screens.set_arcade_status_message("Choose a rival squad first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("battle_bosses"):
                    hub_screens.set_arcade_status_message("Not enough tokens. Buy more to enter the arena.")
                    hub_screens.open_arcade_token_exchange("battle_bosses")
                else:
                    sounds.audio.play_sound("button_click")
                    machine_screens.start_battle_bosses_session()


def loop_event_ace_invaders_difficulty_select(event):
    """Old main-loop event branch for STATE_ACE_INVADERS_DIFFICULTY_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        difficulty_clicked = False
        difficulty_ids = list(ACE_INVADERS_DIFFICULTIES)

        for difficulty_index, difficulty_rect in enumerate(ace_invaders_difficulty_rects):
            if (
                    difficulty_index < len(difficulty_ids)
                    and difficulty_rect.collidepoint(state.menu_mouse_pos)
            ):
                state.ace_invaders_selected_difficulty_index = difficulty_index
                sounds.audio.play_sound("button_click")
                difficulty_clicked = True
                break

        if not difficulty_clicked:
            if ace_invaders_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif ace_invaders_tokens_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                hub_screens.open_arcade_token_exchange("ace_invaders")

            elif ace_invaders_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_ace_invaders_difficulty() is None:
                    hub_screens.set_arcade_status_message("Choose an Ace Invaders difficulty first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("ace_invaders"):
                    hub_screens.set_arcade_status_message("Not enough tokens. Buy more to play.")
                    hub_screens.open_arcade_token_exchange("ace_invaders")
                else:
                    sounds.audio.play_sound("button_click")
                    machine_screens.start_ace_invaders_session()


def loop_event_suit_snake_difficulty_select(event):
    """Old main-loop event branch for STATE_SUIT_SNAKE_DIFFICULTY_SELECT."""

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        sounds.audio.play_sound("button_click")
        state.current_state = state_names.STATE_CAREER_EVENT_SELECT

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and state.menu_mouse_pos is not None:
        setup_clicked = False
        mode_ids = list(SUIT_SNAKE_MODES)

        for mode_index, mode_rect in enumerate(suit_snake_mode_rects):
            if (
                    mode_index < len(mode_ids)
                    and mode_rect.collidepoint(state.menu_mouse_pos)
            ):
                state.suit_snake_selected_mode_index = mode_index
                sounds.audio.play_sound("button_click")
                setup_clicked = True
                break

        if not setup_clicked and suit_snake_step_movement_rect.collidepoint(state.menu_mouse_pos):
            state.suit_snake_selected_movement_style = "step"
            sounds.audio.play_sound("button_click")
            setup_clicked = True

        if not setup_clicked and suit_snake_smooth_movement_rect.collidepoint(state.menu_mouse_pos):
            state.suit_snake_selected_movement_style = "smooth"
            sounds.audio.play_sound("button_click")
            setup_clicked = True

        if not setup_clicked:
            if suit_snake_back_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                state.current_state = state_names.STATE_CAREER_EVENT_SELECT

            elif suit_snake_tokens_rect.collidepoint(state.menu_mouse_pos):
                sounds.audio.play_sound("button_click")
                hub_screens.open_arcade_token_exchange("suit_snake")

            elif suit_snake_play_rect.collidepoint(state.menu_mouse_pos):
                if get_selected_suit_snake_mode() is None:
                    hub_screens.set_arcade_status_message("Choose a Suit Snake mode first.")
                elif int(state.arcade_state.get("tokens", 0)) < get_machine_cost("suit_snake"):
                    hub_screens.set_arcade_status_message("Not enough tokens. Buy more to play.")
                    hub_screens.open_arcade_token_exchange("suit_snake")
                else:
                    sounds.audio.play_sound("button_click")
                    machine_screens.start_suit_snake_session()


def loop_draw_king_pong_opponent_select():
    """Old draw-chain branch for STATE_KING_PONG_OPPONENT_SELECT."""

    draw_king_pong_opponent_select()


def loop_draw_battle_bosses_opponent_select():
    """Old draw-chain branch for STATE_BATTLE_BOSSES_OPPONENT_SELECT."""

    draw_battle_bosses_opponent_select()


def loop_draw_ace_invaders_difficulty_select():
    """Old draw-chain branch for STATE_ACE_INVADERS_DIFFICULTY_SELECT."""

    draw_ace_invaders_difficulty_select()


def loop_draw_suit_snake_difficulty_select():
    """Old draw-chain branch for STATE_SUIT_SNAKE_DIFFICULTY_SELECT."""

    draw_suit_snake_difficulty_select()
