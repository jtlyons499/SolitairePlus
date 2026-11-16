"""How to Play screen (moved out of legacy.py)."""
import pygame
from solitaireplus.app import state
from solitaireplus.app import state_names
from solitaireplus.menus import help_content   # builds the help pages when the help screen loads
from solitaireplus.app.lazy import lazy
window = lazy("solitaireplus.app.window")
sounds = lazy("solitaireplus.app.sounds")
panels = lazy("solitaireplus.ui.panels")
fonts = lazy("solitaireplus.app.fonts")
buttons = lazy("solitaireplus.ui.buttons")


# ==================================================
# HELP MENU
# ==================================================

help_expanded_categories = {
    "solitaire": True,
    "poker": False,
    "casual_cards": False,
    "score_four": False,
    "blackjack": False,
    "roulette": False,
    "horse_races": False,
    "niche_games": False,
    "career": False,
}

help_category_rects = {}
help_page_rects = {}

HELP_NAV_PANEL_RECT = pygame.Rect(40, 110, 280, 570)
HELP_CONTENT_RECT = pygame.Rect(345, 110, 980, 570)
HELP_NAV_SCROLL_STEP = 48
HELP_CONTENT_SCROLL_STEP = 42
help_history_image_cache = {}

how_to_play_back_rect = pygame.Rect(
    533,
    690,
    300,
    50
)


def draw_solitaire_help_diagram(panel_rect):

    # ------------------------------------------
    # Diagram container
    # ------------------------------------------

    diagram_rect = pygame.Rect(
        panel_rect.x + panel_rect.width - 470,
        panel_rect.y + 60,
        440,
        280
    )

    pygame.draw.rect(
        window.game_surface,
        (245, 245, 240),
        diagram_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (0, 0, 0),
        diagram_rect,
        2
    )

    # ------------------------------------------
    # Title
    # ------------------------------------------

    title_surface = fonts.option_label_font.render(
        "BOARD LAYOUT",
        True,
        (0, 0, 0)
    )

    window.game_surface.blit(
        title_surface,
        (
            diagram_rect.x + 15,
            diagram_rect.y + 4
        )
    )

    # ------------------------------------------
    # Mini card sizes
    # ------------------------------------------

    card_w = 42
    card_h = 58

    top_y = diagram_rect.y + 50
    left_x = diagram_rect.x + 20

    # ------------------------------------------
    # Stock
    # ------------------------------------------

    stock_rect = pygame.Rect(
        left_x,
        top_y,
        card_w,
        card_h
    )

    pygame.draw.rect(
        window.game_surface,
        (220, 220, 220),
        stock_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (0, 0, 0),
        stock_rect,
        2
    )

    stock_label = fonts.difficulty_detail_font.render(
        "Stock",
        True,
        (0, 0, 0)
    )

    window.game_surface.blit(
        stock_label,
        (
            stock_rect.x - 2,
            stock_rect.y - 22
        )
    )

    # ------------------------------------------
    # Waste
    # ------------------------------------------

    waste_rect = pygame.Rect(
        left_x + 65,
        top_y,
        card_w,
        card_h
    )

    pygame.draw.rect(
        window.game_surface,
        (255, 255, 255),
        waste_rect
    )

    pygame.draw.rect(
        window.game_surface,
        (0, 0, 0),
        waste_rect,
        2
    )

    waste_label = fonts.difficulty_detail_font.render(
        "Waste",
        True,
        (0, 0, 0)
    )

    window.game_surface.blit(
        waste_label,
        (
            waste_rect.x - 3,
            waste_rect.y - 22
        )
    )

    # ------------------------------------------
    # Foundations
    # ------------------------------------------

    foundation_label = fonts.difficulty_detail_font.render(
        "Foundations",
        True,
        (0, 0, 0)
    )

    window.game_surface.blit(
        foundation_label,
        (
            diagram_rect.x + 245,
            top_y - 22
        )
    )

    foundation_start_x = diagram_rect.x + 230

    for i in range(4):
        foundation_rect = pygame.Rect(
            foundation_start_x + i * 48,
            top_y,
            card_w,
            card_h
        )

        pygame.draw.rect(
            window.game_surface,
            (255, 255, 255),
            foundation_rect
        )

        pygame.draw.rect(
            window.game_surface,
            (0, 0, 0),
            foundation_rect,
            2
        )

    # ------------------------------------------
    # Tableau
    # ------------------------------------------

    tableau_label = fonts.difficulty_detail_font.render(
        "Tableau",
        True,
        (0, 0, 0)
    )

    window.game_surface.blit(
        tableau_label,
        (
            diagram_rect.x + 15,
            top_y + 85
        )
    )

    tableau_y = top_y + 110

    for col in range(7):

        col_x = diagram_rect.x + 15 + col * 58

        # top card
        base_rect = pygame.Rect(
            col_x,
            tableau_y,
            card_w,
            card_h
        )

        pygame.draw.rect(
            window.game_surface,
            (255, 255, 255),
            base_rect
        )

        pygame.draw.rect(
            window.game_surface,
            (0, 0, 0),
            base_rect,
            2
        )

        # a couple stacked cards
        for offset in range(1, 3):
            stacked_rect = pygame.Rect(
                col_x,
                tableau_y + offset * 14,
                card_w,
                card_h
            )

            pygame.draw.rect(
                window.game_surface,
                (245, 245, 245),
                stacked_rect
            )

            pygame.draw.rect(
                window.game_surface,
                (0, 0, 0),
                stacked_rect,
                2
            )

def draw_how_to_play():

    panels.draw_submenu_background(
        overlay_alpha=135
    )

    help_category_rects.clear()
    help_page_rects.clear()

    panels.draw_submenu_title(
        "HELP",
        y=60,
        width=300
    )

    nav_panel = HELP_NAV_PANEL_RECT
    content_rect = HELP_CONTENT_RECT

    nav_surface = pygame.Surface(
        (nav_panel.width, nav_panel.height),
        pygame.SRCALPHA
    )
    nav_surface.fill((15, 35, 25, 220))
    window.game_surface.blit(nav_surface, nav_panel.topleft)
    pygame.draw.rect(window.game_surface, (255, 255, 255), nav_panel, 2)

    content_surface = pygame.Surface(
        (content_rect.width, content_rect.height),
        pygame.SRCALPHA
    )
    content_surface.fill((245, 245, 238, 250))
    window.game_surface.blit(content_surface, content_rect.topleft)
    pygame.draw.rect(window.game_surface, (255, 255, 255), content_rect, 2)

    # ==================================================
    # Scrollable navigation index
    # ==================================================

    old_clip = window.game_surface.get_clip()
    window.game_surface.set_clip(nav_panel.inflate(-2, -2))

    current_y = nav_panel.y + 20 - state.help_nav_scroll
    unscrolled_y = nav_panel.y + 20

    for category_id, category_data in help_content.HELP_NAVIGATION.items():
        category_rect = pygame.Rect(
            nav_panel.x + 15,
            current_y,
            nav_panel.width - 30,
            46
        )

        if category_rect.bottom >= nav_panel.top and category_rect.top <= nav_panel.bottom:
            help_category_rects[category_id] = category_rect

            expanded = help_expanded_categories.get(category_id, False)
            arrow = "-" if expanded else "+"
            buttons.draw_menu_button(
                category_rect,
                f"{arrow}  {category_data['name']}",
                state.game_mouse_pos,
                font=fonts.difficulty_detail_font
            )

        expanded = help_expanded_categories.get(category_id, False)
        current_y += 52
        unscrolled_y += 52

        if expanded:
            for page_id, page_name in category_data["pages"]:
                page_rect = pygame.Rect(
                    nav_panel.x + 35,
                    current_y,
                    nav_panel.width - 55,
                    38
                )

                if page_rect.bottom >= nav_panel.top and page_rect.top <= nav_panel.bottom:
                    help_page_rects[page_id] = page_rect
                    buttons.draw_menu_button(
                        page_rect,
                        page_name,
                        state.game_mouse_pos,
                        selected=(state.help_current_page == page_id),
                        font=fonts.difficulty_detail_font
                    )

                current_y += 42
                unscrolled_y += 42

        current_y += 6
        unscrolled_y += 6

    window.game_surface.set_clip(old_clip)

    state.help_nav_max_scroll = max(
        0,
        unscrolled_y - (nav_panel.bottom - 12)
    )
    state.help_nav_scroll = max(0, min(state.help_nav_scroll, state.help_nav_max_scroll))

    if state.help_nav_max_scroll > 0:
        track = pygame.Rect(nav_panel.right - 9, nav_panel.y + 8, 4, nav_panel.height - 16)
        pygame.draw.rect(window.game_surface, (70, 92, 80), track, border_radius=2)
        ratio = nav_panel.height / max(nav_panel.height, nav_panel.height + state.help_nav_max_scroll)
        thumb_h = max(36, int(track.height * ratio))
        travel = max(1, track.height - thumb_h)
        position = 0 if state.help_nav_max_scroll <= 0 else int(
            travel * min(1.0, state.help_nav_scroll / state.help_nav_max_scroll)
        )
        thumb = pygame.Rect(track.x, track.y + position, track.width, thumb_h)
        pygame.draw.rect(window.game_surface, (220, 224, 218), thumb, border_radius=2)

    # ==================================================
    # Content page
    # ==================================================

    content = help_content.HELP_CONTENT.get(
        state.help_current_page,
        help_content.HELP_CONTENT["solitaire_basics"]
    )

    section_title = fonts.option_label_font.render(
        content["title"],
        True,
        (20, 20, 20)
    )
    window.game_surface.blit(
        section_title,
        (content_rect.x + 35, content_rect.y + 30)
    )

    history_image = None
    image_path = content.get("image")
    if image_path:
        if image_path not in help_history_image_cache:
            try:
                help_history_image_cache[image_path] = pygame.image.load(
                    image_path
                ).convert_alpha()
            except (pygame.error, FileNotFoundError):
                help_history_image_cache[image_path] = None
        history_image = help_history_image_cache.get(image_path)

    if state.help_current_page == "solitaire_basics":
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            455,
            content_rect.height - 125
        )
    elif history_image is not None:
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            505,
            content_rect.height - 125
        )
    else:
        text_rect = pygame.Rect(
            content_rect.x + 35,
            content_rect.y + 90,
            content_rect.width - 70,
            content_rect.height - 125
        )

    # Wrap first so we know the scrollable content height.
    wrapped_entries = []
    logical_height = 0

    for line in content.get("lines", []):
        if not line:
            wrapped_entries.append(("", True))
            logical_height += 14
            continue

        words = str(line).split()
        wrapped_lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            test_surface = fonts.difficulty_detail_font.render(
                test_line,
                True,
                (20, 20, 20)
            )
            if test_surface.get_width() <= text_rect.width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word

        if current_line:
            wrapped_lines.append(current_line)

        for wrapped_line in wrapped_lines:
            wrapped_entries.append((wrapped_line, False))
            logical_height += 26
        logical_height += 10

    state.help_content_max_scroll = max(
        0,
        logical_height - text_rect.height
    )
    state.help_content_scroll = max(
        0,
        min(state.help_content_scroll, state.help_content_max_scroll)
    )

    text_clip = text_rect.copy()
    old_clip = window.game_surface.get_clip()
    window.game_surface.set_clip(text_clip)

    current_y = text_rect.y - state.help_content_scroll
    for line, blank in wrapped_entries:
        if blank:
            current_y += 14
            continue

        if current_y + 24 >= text_rect.top and current_y <= text_rect.bottom:
            line_surface = fonts.difficulty_detail_font.render(
                line,
                True,
                (20, 20, 20)
            )
            window.game_surface.blit(line_surface, (text_rect.x, current_y))
        current_y += 26

        # Paragraph spacing is represented by the 10 pixels added to the
        # logical height after the final wrapped line. Apply it whenever the
        # next entry is blank or this line closes a source paragraph.
        # A small uniform gap keeps histories readable without special markup.
        current_y += 2

    window.game_surface.set_clip(old_clip)

    if state.help_content_max_scroll > 0:
        track = pygame.Rect(text_rect.right - 5, text_rect.y, 3, text_rect.height)
        pygame.draw.rect(window.game_surface, (195, 198, 192), track)
        ratio = text_rect.height / max(text_rect.height, logical_height)
        thumb_h = max(30, int(track.height * ratio))
        travel = max(1, track.height - thumb_h)
        position = int(
            travel * min(1.0, state.help_content_scroll / state.help_content_max_scroll)
        )
        pygame.draw.rect(
            window.game_surface,
            (80, 88, 83),
            pygame.Rect(track.x, track.y + position, track.width, thumb_h)
        )

    if history_image is not None:
        image_panel = pygame.Rect(
            content_rect.right - 400,
            content_rect.y + 104,
            350,
            350
        )
        pygame.draw.rect(
            window.game_surface,
            (225, 225, 218),
            image_panel,
            border_radius=8
        )
        pygame.draw.rect(
            window.game_surface,
            (90, 90, 86),
            image_panel,
            2,
            border_radius=8
        )

        source_w, source_h = history_image.get_size()
        scale = min(
            (image_panel.width - 18) / max(1, source_w),
            (image_panel.height - 18) / max(1, source_h)
        )
        image_size = (
            max(1, int(source_w * scale)),
            max(1, int(source_h * scale))
        )
        scaled = pygame.transform.smoothscale(history_image, image_size)
        window.game_surface.blit(scaled, scaled.get_rect(center=image_panel.center))

        caption = str(content.get("caption", "") or "").strip()
        if caption:
            caption_rect = pygame.Rect(
                image_panel.x,
                image_panel.bottom + 12,
                image_panel.width,
                72
            )
            words = caption.split()
            line = ""
            lines = []
            for word in words:
                test = f"{line} {word}".strip()
                if fonts.difficulty_detail_font.size(test)[0] <= caption_rect.width:
                    line = test
                else:
                    if line:
                        lines.append(line)
                    line = word
            if line:
                lines.append(line)
            for index, caption_line in enumerate(lines[:3]):
                surf = fonts.difficulty_detail_font.render(
                    caption_line,
                    True,
                    (70, 70, 68)
                )
                window.game_surface.blit(
                    surf,
                    surf.get_rect(
                        center=(caption_rect.centerx, caption_rect.y + 12 + index * 20)
                    )
                )

    if state.help_current_page == "solitaire_basics":
        draw_solitaire_help_diagram(content_rect)

    buttons.draw_menu_button(
        how_to_play_back_rect,
        "Return",
        state.game_mouse_pos,
        font=fonts.difficulty_detail_font
    )


def handle_event(event):
    """Old main-loop event branch for STATE_HOW_TO_PLAY."""

    if event.type == pygame.MOUSEWHEEL:
        if state.game_mouse_pos is not None and HELP_NAV_PANEL_RECT.collidepoint(state.game_mouse_pos):
            state.help_nav_scroll = max(
                0,
                min(
                    state.help_nav_max_scroll,
                    state.help_nav_scroll - event.y * HELP_NAV_SCROLL_STEP
                )
            )
        elif state.game_mouse_pos is not None and HELP_CONTENT_RECT.collidepoint(state.game_mouse_pos):
            state.help_content_scroll = max(
                0,
                min(
                    state.help_content_max_scroll,
                    state.help_content_scroll - event.y * HELP_CONTENT_SCROLL_STEP
                )
            )

    elif (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and state.game_mouse_pos is not None
    ):

        click_handled = False

        for category_id, category_rect in help_category_rects.items():
            if category_rect.collidepoint(state.game_mouse_pos):
                sounds.audio.play_sound("button_click")

                was_expanded = help_expanded_categories.get(
                    category_id,
                    False
                )

                for other_category_id in help_expanded_categories:
                    help_expanded_categories[other_category_id] = False

                if not was_expanded:
                    help_expanded_categories[category_id] = True

                click_handled = True
                break

        if not click_handled:
            for page_id, page_rect in help_page_rects.items():
                if page_rect.collidepoint(state.game_mouse_pos):
                    sounds.audio.play_sound("button_click")
                    state.help_current_page = page_id
                    state.help_content_scroll = 0
                    click_handled = True
                    break

        if (
                not click_handled
                and how_to_play_back_rect.collidepoint(state.game_mouse_pos)
        ):
            sounds.audio.play_sound("button_click")
            state.current_state = state_names.STATE_MENU


def draw():
    """Old draw-chain branch for STATE_HOW_TO_PLAY."""

    draw_how_to_play()
