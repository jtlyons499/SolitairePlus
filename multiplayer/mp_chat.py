"""Small reusable freeform chat composer for multiplayer card/casino rooms."""
from __future__ import annotations

import pygame

from mp_widgets import TextInput


MAX_CHAT_LENGTH = 160


class MultiplayerChat:
    def __init__(self):
        self.text = ""
        self.active = False
        self.scroll = 0
        self.input = TextInput()
        self.last_seen_seq = 0

    @property
    def editing(self):
        return self.active

    def close(self):
        self.active = False
        self.input.selected = False
        pygame.key.stop_text_input()

    def activate(self):
        self.active = True
        pygame.key.start_text_input()

    def submit(self, table):
        message = " ".join(str(self.text or "").split())[:MAX_CHAT_LENGTH]
        if not message:
            return False
        ok = table.act("chat", message)
        if ok:
            self.text = ""
            self.input.selected = False
            self.scroll = 0
        return ok

    def event(self, event, mouse, table, input_rect, send_rect):
        input_rect = pygame.Rect(input_rect)
        send_rect = pygame.Rect(send_rect)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if input_rect.collidepoint(mouse):
                self.activate()
                return True
            if send_rect.collidepoint(mouse):
                if self.submit(table):
                    self.activate()
                return True
            if self.active:
                self.close()

        if event.type == pygame.MOUSEWHEEL:
            messages = table.message.get("chat_messages", [])
            max_scroll = max(0, len(messages) - 5)
            self.scroll = max(0, min(max_scroll, self.scroll - event.y))
            return True

        if not self.active:
            return False

        if event.type == pygame.TEXTINPUT:
            self.text = self.input.event(event, self.text, MAX_CHAT_LENGTH)
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.submit(table)
                self.activate()
                return True
            self.text = self.input.event(event, self.text, MAX_CHAT_LENGTH)
            return True

        return False

    def sync_unread(self, messages, visible):
        if not messages:
            return False
        seq = int(messages[-1].get("seq", 0) or 0)
        unread = seq > self.last_seen_seq
        if visible:
            self.last_seen_seq = max(self.last_seen_seq, seq)
            return False
        return unread

    @staticmethod
    def _fit(font, text, width):
        text = str(text)
        if font.size(text)[0] <= width:
            return text
        suffix = "…"
        while text and font.size(text + suffix)[0] > width:
            text = text[:-1]
        return text.rstrip() + suffix

    def draw_messages(self, surface, messages, rect, font, muted, accent, max_lines=5):
        rect = pygame.Rect(rect)
        messages = list(messages or [])
        maximum_scroll = max(0, len(messages) - max_lines)
        self.scroll = max(0, min(self.scroll, maximum_scroll))
        end = max(0, len(messages) - self.scroll)
        start = max(0, end - max_lines)
        visible = messages[start:end]
        line_height = max(18, font.get_linesize())
        y = rect.y
        for row in visible:
            name = str(row.get("name", "Player"))[:24]
            message = str(row.get("text", ""))
            prefix = f"{name}: "
            prefix_surface = font.render(prefix, True, accent)
            surface.blit(prefix_surface, (rect.x, y))
            remaining = max(30, rect.width - prefix_surface.get_width())
            fitted = self._fit(font, message, remaining)
            surface.blit(font.render(fitted, True, muted), (rect.x + prefix_surface.get_width(), y))
            y += line_height

    def draw_input(self, surface, input_rect, send_rect, font, button_drawer, panel_drawer, mouse, enabled=True):
        input_rect = pygame.Rect(input_rect)
        send_rect = pygame.Rect(send_rect)
        border = (242, 202, 79) if self.active else (126, 148, 140)
        panel_drawer(input_rect, (8, 20, 18, 238), border, 2 if self.active else 1, 8)
        placeholder = "Type a message…" if not self.text else self.text
        color = (246, 239, 216) if self.text else (155, 170, 164)
        fitted = self._fit(font, placeholder + ("|" if self.active else ""), input_rect.width - 18)
        surface.blit(font.render(fitted, True, color), (input_rect.x + 9, input_rect.y + 8))
        button_drawer("SEND", send_rect, "chat_send", enabled and bool(self.text.strip()))
