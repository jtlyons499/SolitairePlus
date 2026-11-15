"""Career leaderboard biography screen (moved out of legacy.py)."""
from solitaireplus.games.solitaire.rules import BASE_WIDTH
from solitaireplus.npc.personality_ui import draw_npc_traits
from solitaireplus.career.fans import get_player_public_appeal_display_name
from solitaireplus.career.fans import get_public_appeal_display_name
from solitaireplus.npc.personality import personality_summary
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.career.world_flavor import strongest_rating_status
from solitaireplus.app.lazy import lazy
web_pages = lazy("solitaireplus.career.web_pages")
career_names = lazy("solitaireplus.career.career_names")
legacy = lazy("solitaireplus.legacy")
window = lazy("solitaireplus.app.window")
ui_text = lazy("solitaireplus.ui.text")
sounds = lazy("solitaireplus.app.sounds")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


def draw_career_leaderboard_bio():

    window.game_surface.fill((235, 235, 225))
    web_pages.draw_career_browser_header("https://www.cardrankings.net/bios")

    if state.selected_leaderboard_entry is None:
        title = fonts.menu_title_font.render("PLAYER BIO", True, (0, 0, 0))
        window.game_surface.blit(
            title,
            title.get_rect(center=(BASE_WIDTH // 2, 130))
        )
        buttons.draw_button(web_pages.career_subpage_back_rect, "Return to Rankings")
        return

    entry = state.selected_leaderboard_entry
    name = entry.get("name", "Unknown Player")
    rating = entry.get("rating", 1000)
    rating_label = entry.get("rating_label", "Global")
    personality = personality_summary(entry.get("npc") or entry)

    bio = entry.get("bio", "Professional card player.") or "Professional card player."
    country = entry.get("country", "Unknown") or "Unknown"
    age = entry.get("age", "Unknown") or "Unknown"
    hometown = entry.get("hometown", "Unknown") or "Unknown"
    favorite_suit = entry.get("favorite_suit", "Unknown") or "Unknown"
    fans = int(entry.get("fans", 0) or 0)
    appeal_key = entry.get("public_appeal", "steady")
    appeal = (
        get_player_public_appeal_display_name(state.career_fan_trend, state.career_fans)
        if entry.get("is_player")
        else get_public_appeal_display_name(appeal_key)
    )
    is_star = entry.get("is_star", False)
    is_player = entry.get("is_player", False)

    title = fonts.menu_title_font.render(name, True, (0, 0, 0))
    window.game_surface.blit(
        title,
        title.get_rect(center=(BASE_WIDTH // 2, 135))
    )

    rating_surface = fonts.option_label_font.render(
        f"{rating_label}: {rating:,}",
        True,
        (0, 0, 0)
    )
    window.game_surface.blit(
        rating_surface,
        rating_surface.get_rect(center=(BASE_WIDTH // 2, 190))
    )

    if entry.get("is_prospect"):
        joined_year, joined_zero_month = divmod(int(entry["joined_month"]), 12)
        label = "PRODIGY" if entry.get("is_prodigy") else "PROSPECT"
        joined = fonts.difficulty_detail_font.render(
            f"{label} · Joined {career_names.CAREER_MONTH_NAMES[joined_zero_month + 1]} {joined_year}"
            + (" · WORLD #1" if is_star else ""),
            True, (40, 95, 105),
        )
        window.game_surface.blit(joined, joined.get_rect(center=(BASE_WIDTH // 2, 220)))
    elif is_star:
        star_surface = fonts.option_label_font.render(
            "WORLD #1",
            True,
            (180, 120, 0)
        )
        window.game_surface.blit(
            star_surface,
            star_surface.get_rect(center=(BASE_WIDTH // 2, 220))
        )

    # The bio and portrait are treated as one centered composition.
    bio_panel_rect = pygame.Rect(218, 240, 665, 300)
    portrait_panel_rect = pygame.Rect(901, 240, 247, 300)

    for panel in (bio_panel_rect, portrait_panel_rect):
        pygame.draw.rect(window.game_surface, (250, 250, 250), panel)
        pygame.draw.rect(window.game_surface, (0, 0, 0), panel, 3)

    if is_player:
        personality = "Player"

    birthday_month = entry.get("birthday_month")
    birthday_text = (f"  |  Birthday: {career_names.CAREER_MONTH_NAMES[birthday_month][:3]}"
                     if isinstance(birthday_month, int) and 1 <= birthday_month <= 12 else "")
    details = [
        f"Country: {country}",
        f"Age: {age}" + birthday_text
        + (f"  |  {entry.get('career_stage', 'Established')}" if not is_player else ""),
        f"Personality: {personality}",
        f"Public Appeal: {appeal}",
        *([f"Rating Status: {strongest_rating_status(state.career_ratings)[0]}"] if is_player else []),
        f"Fans: {fans:,}",
        f"Hometown: {hometown}",
        f"Favorite Suit: {favorite_suit}",
    ]

    for index, detail in enumerate(details):
        detail_surface = ui_text.render_text_fit(
            detail,
            fonts.option_value_font,
            bio_panel_rect.width - 50,
            (0, 0, 0),
            minimum_size=20,
        )
        window.game_surface.blit(
            detail_surface,
            (bio_panel_rect.x + 25, bio_panel_rect.y + 20 + index * 24)
        )

    ui_text.draw_wrapped_text_limited(
        bio,
        fonts.option_label_font,
        (0, 0, 0),
        pygame.Rect(
            bio_panel_rect.x + 25,
            bio_panel_rect.y + 26 + len(details) * 24,
            bio_panel_rect.width - 50,
            max(36, bio_panel_rect.height - (38 + len(details) * 24))
        ),
        max_lines=3,
        line_spacing=4
    )

    npc = entry.get("npc")
    if is_player:
        portrait = legacy.get_profile_avatar()
    elif isinstance(npc, dict):
        portrait = legacy.get_npc_portrait_surface(npc, 260)
    else:
        portrait = None

    if portrait is not None:
        max_rect = portrait_panel_rect.inflate(-24, -24)
        src_w, src_h = portrait.get_size()
        scale = min(
            max_rect.width / max(1, src_w),
            max_rect.height / max(1, src_h)
        )
        draw_size = (
            max(1, int(src_w * scale)),
            max(1, int(src_h * scale))
        )
        portrait = pygame.transform.smoothscale(portrait, draw_size)
        window.game_surface.blit(
            portrait,
            portrait.get_rect(center=portrait_panel_rect.center)
        )
    else:
        placeholder = fonts.options_title_font.render(
            "PLAYER" if is_player else "NPC ICON",
            True,
            (20, 20, 20)
        )
        window.game_surface.blit(
            placeholder,
            placeholder.get_rect(center=portrait_panel_rect.center)
        )

    if not is_player:
        draw_npc_traits(window.game_surface, entry.get("npc") or entry,
                        pygame.Rect(218, 550, 930, 153), fonts.difficulty_detail_font)
    buttons.draw_button(web_pages.career_subpage_back_rect, "Return to Rankings")


def handle_event(event):
    """Old main-loop event branch for STATE_CAREER_LEADERBOARD_BIO."""

    if (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
    ):

        if web_pages.career_subpage_back_rect.collidepoint(
                state.game_mouse_pos
        ):
            sounds.audio.play_sound(
                "button_click"
            )

            state.current_state = state_names.STATE_CAREER_LEADERBOARDS


def draw():
    """Old draw-chain branch for STATE_CAREER_LEADERBOARD_BIO."""
    draw_career_leaderboard_bio()
