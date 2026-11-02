"""Shared Quick Chat overlay and small presentation polish for non-Hold'em poker."""
from __future__ import annotations

import pygame

from poker_quick_chat import (
    QUICK_CHAT_LABELS,
    TARGETED_QUICK_CHAT,
    quick_chat_options_for_game,
    quick_chat_target_options,
    submit_holdem_quick_chat,
)
from poker_quick_chat_adapter import adapt_quick_chat_game

WHITE = (245, 245, 245)
MUTED = (182, 188, 192)
GOLD = (235, 190, 70)


def _font(size=15, bold=True):
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.font.SysFont("cambria", size, bold=bold)


def _panel(surface, rect, fill=(12, 16, 20, 238), border=(145, 154, 164), radius=10, width=2):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=radius)
    gloss = pygame.Rect(3, 3, max(1, rect.width - 6), max(7, rect.height // 2 - 3))
    pygame.draw.rect(layer, (255, 255, 255, 18), gloss, border_radius=max(4, radius - 2))
    pygame.draw.rect(layer, (*border, 245), layer.get_rect(), width, border_radius=radius)
    surface.blit(layer, rect.topleft)


def _button(surface, rect, label, mouse_pos, selected=False):
    hover = mouse_pos is not None and rect.collidepoint(mouse_pos)
    fill = (72, 98, 126, 235) if selected else (72, 78, 86, 230) if hover else (54, 59, 66, 225)
    border = (190, 220, 250) if selected else (158, 166, 176)
    _panel(surface, rect, fill, border, radius=9)
    font = _font(13)
    text = font.render(str(label), True, WHITE)
    if text.get_width() > rect.width - 12:
        smaller = _font(11)
        text = smaller.render(str(label), True, WHITE)
    surface.blit(text, text.get_rect(center=rect.center))


def _fit(font, text, max_width, color=WHITE):
    text = str(text)
    if font.size(text)[0] <= max_width:
        return font.render(text, True, color)
    clipped = text
    while clipped and font.size(clipped + "…")[0] > max_width:
        clipped = clipped[:-1]
    return font.render(clipped.rstrip() + "…", True, color)


class VariantQuickChatController:
    def __init__(self, game_id):
        self.game_id = game_id
        self.game = None
        self.adapter = None
        self.open = False
        self.target_key = None
        self.pending = []
        self.local_history = []
        self.button_rect = pygame.Rect(0, 0, 110, 28)
        self.popup_rect = pygame.Rect(0, 0, 330, 100)
        self._option_rects = []
        self._target_rects = []

    def bind(self, game):
        if game is not self.game:
            self.game = game
            self.adapter = adapt_quick_chat_game(game, self.game_id) if game is not None else None
            self.open = False
            self.target_key = None
            self.pending.clear()
        if self.adapter is not None:
            self.adapter.sync()
        return self.adapter

    def _post(self, speaker, message, post_message=None):
        if post_message is not None:
            post_message(speaker, message)
        else:
            text = f"{speaker}: {message}" if speaker else str(message)
            self.local_history.append(text)
            del self.local_history[:-30]

    def _flush(self, post_message=None):
        now = pygame.time.get_ticks()
        remaining = []
        for due, speaker, message in self.pending:
            if due <= now:
                self._post(speaker, message, post_message)
            else:
                remaining.append((due, speaker, message))
        self.pending = remaining

    def _options(self):
        return tuple(quick_chat_options_for_game(self.adapter)) if self.adapter is not None else ()

    def _layout(self, anchor_rect, five_o=False):
        button_x = anchor_rect.x + (12 if five_o else 202)
        self.button_rect = pygame.Rect(button_x, anchor_rect.y + 10, 110, 28)
        options = self._options()
        rows = quick_chat_target_options(self.adapter, self.target_key) if self.target_key else options
        count = max(1, len(rows))
        height = 18 + count * 31 + 12
        popup_y = (self.button_rect.bottom + 8) if five_o else (anchor_rect.y - height - 8)
        popup_x = anchor_rect.x if not five_o else max(12, self.button_rect.x - 210)
        self.popup_rect = pygame.Rect(popup_x, popup_y, 330, height)
        rects = []
        for index in range(count):
            rects.append(pygame.Rect(self.popup_rect.x + 10, self.popup_rect.y + 10 + index * 31, self.popup_rect.width - 20, 27))
        if self.target_key:
            self._target_rects = list(zip(rows, rects))
            self._option_rects = []
        else:
            self._option_rects = list(zip(options, rects))
            self._target_rects = []

    def draw(self, surface, mouse_pos, game, anchor_rect, post_message=None, five_o=False, history_rect=None):
        adapter = self.bind(game)
        self._flush(post_message)
        options = self._options()
        if not options:
            self.open = False
            self.target_key = None
            return
        self._layout(anchor_rect, five_o=five_o)
        _button(surface, self.button_rect, "QUICK CHAT", mouse_pos, selected=self.open)

        if self.open:
            _panel(surface, self.popup_rect, (10, 14, 18, 246), (165, 173, 183), radius=12)
            if self.target_key:
                for (npc_index, name), rect in self._target_rects:
                    _button(surface, rect, name, mouse_pos)
            else:
                for (key, label), rect in self._option_rects:
                    _button(surface, rect, label, mouse_pos)

        if five_o and self.local_history:
            # Variants without a normal chat tab get a compact local history
            # strip. The caller can place it around that game's controls.
            chat_rect = history_rect or pygame.Rect(24, 618, 312, 38)
            _panel(surface, chat_rect, (8, 13, 18, 218), (104, 118, 130), radius=8, width=1)
            font = _font(11)
            y = chat_rect.y + 3
            for line in self.local_history[-2:]:
                rendered = _fit(font, line, chat_rect.width - 12, MUTED)
                surface.blit(rendered, (chat_rect.x + 6, y))
                y += 16

    def handle_click(self, mouse_pos, post_message=None):
        if self.adapter is None or mouse_pos is None:
            return False
        options = self._options()
        if not options:
            return False

        if self.button_rect.collidepoint(mouse_pos):
            self.open = not self.open
            self.target_key = None
            return True

        if not self.open:
            return False

        if self.target_key:
            for (npc_index, _name), rect in self._target_rects:
                if rect.collidepoint(mouse_pos):
                    self._submit(self.target_key, npc_index, post_message)
                    return True
            if self.popup_rect.collidepoint(mouse_pos):
                return True
            self.open = False
            self.target_key = None
            return False

        for (key, _label), rect in self._option_rects:
            if rect.collidepoint(mouse_pos):
                if key in TARGETED_QUICK_CHAT:
                    self.target_key = key
                    return True
                self._submit(key, None, post_message)
                return True

        if self.popup_rect.collidepoint(mouse_pos):
            return True
        self.open = False
        return False

    def _submit(self, key, target_index, post_message):
        result = submit_holdem_quick_chat(self.adapter, key, target_index=target_index)
        if not result.get("accepted"):
            return
        self._post("You", result.get("label", QUICK_CHAT_LABELS.get(key, key)), post_message)
        now = pygame.time.get_ticks()
        for response in result.get("responses", ()):
            self.pending.append((
                now + int(response.get("delay_ms", 0) or 0),
                str(response.get("speaker", "Opponent")),
                str(response.get("message", "")),
            ))
        self.open = False
        self.target_key = None

    def draw_status_ribbon(self, surface, game, rect=None):
        if game is None:
            return
        rect = rect or pygame.Rect(520, 72, 326, 34)
        hand_complete = bool(getattr(game, "hand_complete", False))
        if hand_complete:
            label = str(getattr(game, "result_text", "Hand complete") or "Hand complete")
            border = GOLD
        else:
            stage = str(getattr(game, "current_stage", None) or getattr(game, "phase", "Hand")).replace("_", " ").title()
            player_turn = False
            if hasattr(game, "current_actor"):
                player_turn = getattr(game, "current_actor", -1) == 0
                checker = getattr(game, "can_player_act_now", None)
                if callable(checker):
                    try: player_turn = player_turn and bool(checker())
                    except Exception: pass
            elif getattr(game, "phase", "") == "placement":
                player_turn = getattr(game, "player_drawn_card", None) is not None
            elif getattr(game, "phase", "") == "betting":
                getter = getattr(game, "get_player_actions", None)
                player_turn = bool(getter()) if callable(getter) else False
            label = f"YOUR TURN  •  {stage}" if player_turn else stage
            border = GOLD if player_turn else (145, 154, 164)
        _panel(surface, rect, (10, 14, 18, 220), border, radius=10, width=3 if "YOUR TURN" in label else 2)
        rendered = _fit(_font(14), label, rect.width - 18, WHITE)
        surface.blit(rendered, rendered.get_rect(center=rect.center))


_CONTROLLERS = {}


def controller_for(game_id):
    key = str(game_id)
    if key not in _CONTROLLERS:
        _CONTROLLERS[key] = VariantQuickChatController(key)
    return _CONTROLLERS[key]
