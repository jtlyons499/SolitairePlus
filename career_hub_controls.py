"""Career Hub selection and toolbar widgets, drawn at the game's base resolution.

Career progression and profile persistence stay in main.py. This module only
owns the Hub's temporary selection, messages, and shared click geometry.
"""

import pygame
from career_time_warp import WARP_OPTIONS


class CareerHubControls:
    def __init__(self):
        self.font = pygame.font.Font(None, 20)
        self.selected_day = None
        self.future_days = set()
        self.day_rects = {}
        self.fast_skip_rects = {}
        self.confirm_skip_day = None
        self.message = ""
        self.message_until = 0
        self.message_fade_ms = 700
        self.profile_cancel_rect = pygame.Rect(533, 660, 300, 46)
        self.warp_open = False
        self.warp_rect = pygame.Rect(0,0,0,0)
        self.warp_choices = {}
        self.toolbar_rects = {}
        x = 335
        for action, width in (
            ("save", 52), ("profile", 62), ("switch", 108),
            ("options", 68), ("customize", 86), ("skip_to_day", 140), ("cryptid",122), ("cases",132),
        ):
            self.toolbar_rects[action] = pygame.Rect(x, 733, width, 27)
            x += width + 8

    def reset(self):
        self.warp_open = False
        self.selected_day = None
        self.future_days.clear()
        self.day_rects.clear()
        self.fast_skip_rects.clear()
        self.confirm_skip_day = None
        self.message = ""
        self.message_until = 0

    def begin_calendar(self, schedule, current_day):
        page_start = 0 if current_day <= 15 else 15
        visible_entries = schedule[page_start:page_start + 15]
        self.future_days = {
            entry["day_number"] for entry in visible_entries
            if entry["day_number"] > current_day
        }
        self.day_rects.clear()
        self.fast_skip_rects.clear()
        if self.selected_day not in self.future_days:
            self.selected_day = None
        if self.confirm_skip_day not in self.future_days:
            self.confirm_skip_day = None

    def register_day(self, day, rect):
        if day in self.future_days:
            self.day_rects[day] = rect.copy()

    def register_fast_skip(self, day, rect):
        if day in self.future_days:
            self.fast_skip_rects[day] = rect.copy()

    def select_day_at(self, position):
        if position is None:
            return False
        for day, rect in self.day_rects.items():
            if rect.collidepoint(position):
                self.selected_day = day
                self.message = ""
                return True
        return False

    def request_fast_skip_at(self, position):
        if position is None:
            return None
        for day, rect in self.fast_skip_rects.items():
            if rect.collidepoint(position):
                self.confirm_skip_day = day
                self.selected_day = day
                self.message = ""
                return day
        return None

    def clear_skip_confirmation(self):
        self.confirm_skip_day = None

    def get_action(self, position):
        if position is None:
            return None
        if self.warp_rect.collidepoint(position):
            self.warp_open = not self.warp_open
            return "warp_menu"
        if self.warp_open:
            for months, rect in self.warp_choices.items():
                if rect.collidepoint(position):
                    self.warp_open = False
                    return "warp:" + str(months)
            self.warp_open = False
        for action, rect in self.toolbar_rects.items():
            if rect.collidepoint(position):
                if action == "skip_to_day" and self.selected_day not in self.future_days:
                    return None
                return action
        return None

    def days_to_skip(self, schedule, current_day):
        """Revalidate against live calendar data before any progression change."""
        page_start = 0 if current_day <= 15 else 15
        visible_days = {
            entry["day_number"]
            for entry in schedule[page_start:page_start + 15]
        }
        target = self.selected_day
        if target not in visible_days or target is None or target <= current_day:
            return 0
        # Do not allow a malformed save to roll over into a different schedule.
        if target > len(schedule):
            return 0
        return target - current_day

    def show_message(self, message, now, duration=2200, fade_ms=700):
        self.message = str(message or "")
        self.message_until = now + max(250, int(duration))
        self.message_fade_ms = max(150, min(int(fade_ms), int(duration)))

    def draw_toolbar(self, surface, draw_button, font, now):
        labels = {
            "save": "Save", "profile": "Profile", "switch": "Switch Profile",
            "options": "Options", "customize": "Customize",
            "cryptid": "Cryptid Cards", "cases": "Cases / trophies",
            "skip_to_day": (
                f"Skip to day: {self.selected_day}"
                if self.selected_day in self.future_days
                else "Select future day"
            ),
        }
        for action, rect in self.toolbar_rects.items():
            if action == "skip_to_day" and self.selected_day not in self.future_days:
                pygame.draw.rect(surface, (165, 175, 180), rect)
                pygame.draw.rect(surface, (255, 255, 255), rect, 2)
                text = font.render(labels[action], True, (35, 45, 50))
                surface.blit(text, text.get_rect(center=rect.center))
            else:
                draw_button(rect, labels[action], font=font)

        if self.message and now >= self.message_until:
            self.message = ""
            self.message_until = 0

        if self.message and now < self.message_until:
            # Brief feedback occupies the website-link row above the controls.
            status_rect = pygame.Rect(335, 703, 816, 26)
            remaining = max(0, self.message_until - now)
            fade_ms = max(1, self.message_fade_ms)
            alpha = 255 if remaining >= fade_ms else int(255 * (remaining / fade_ms))

            panel = pygame.Surface(status_rect.size, pygame.SRCALPHA)
            panel.fill((235, 245, 255, alpha))
            surface.blit(panel, status_rect.topleft)

            text = font.render(self.message, True, (25, 65, 100))
            text.set_alpha(alpha)
            surface.blit(text, text.get_rect(center=status_rect.center))

    def draw_time_warp(self,surface,header,draw_button,font):
        self.warp_rect=pygame.Rect(header.right-140,header.bottom-34,130,28)
        draw_button(self.warp_rect,'Time Warp',font=font)
        self.warp_choices={}
        if self.warp_open:
            for index,(months,label) in enumerate(WARP_OPTIONS):
                rect=pygame.Rect(header.right-200,header.bottom+4+index*36,190,34)
                self.warp_choices[months]=rect
                draw_button(rect,label,font=font)
