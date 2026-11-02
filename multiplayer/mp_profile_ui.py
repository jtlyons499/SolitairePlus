"""Multiplayer profile editor using the same layered avatar builder as single-player."""
import pygame
from mp_widgets import TextInput, wooden_button


class ProfileScreen:
    def __init__(self, profile, appearance):
        self.profile = profile
        self.appearance = appearance
        self.open = False
        self.buttons = []
        self.field = None
        self.text_input = TextInput()
        self.message = ""
        self.page = {"background": 0, "felt": 0, "back": 0}
        self.font = pygame.font.Font(None, 30)
        self.small = pygame.font.Font(None, 23)
        self.large = pygame.font.Font(None, 44)
        self.selector_keys = ("base", "eyes", "hair", "glasses", "top")

    def text(self, surface, value, pos, font=None, color=(244, 236, 211)):
        surface.blit((font or self.font).render(str(value), True, color), pos)

    def panel(self, surface, rect, fill=(14, 37, 29, 232), border=(205, 218, 210), width=2):
        rect = pygame.Rect(rect)
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=14)
        surface.blit(layer, rect)
        pygame.draw.rect(surface, border, rect, width, border_radius=14)

    def button(self, surface, label, rect, action, enabled=True):
        rect = pygame.Rect(rect)
        wooden_button(surface, self.appearance, rect, label, self.small, enabled)
        if enabled:
            self.buttons.append((rect, action))

    def draw_avatar_preview(self, surface):
        frame = pygame.Rect(118, 210, 250, 300)
        self.panel(surface, frame, (20, 55, 42, 235), (232, 236, 230), 3)
        avatar = self.profile.render_avatar_surface()
        target = frame.inflate(-24, -24)
        scale = min(target.w / avatar.get_width(), target.h / avatar.get_height())
        preview = pygame.transform.smoothscale(
            avatar,
            (max(1, int(avatar.get_width() * scale)), max(1, int(avatar.get_height() * scale))),
        )
        surface.blit(preview, preview.get_rect(center=frame.center))
        self.text(surface, "Same layered avatar builder as your single-player profile", (102, 528), self.small, (205, 216, 208))

    def draw(self, surface, table=None):
        self.appearance.background(surface)
        self.buttons = []
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 65))
        surface.blit(shade, (0, 0))
        self.panel(surface, (58, 42, 1250, 686), (10, 29, 23, 238), (221, 226, 221), 2)

        self.text(surface, "MULTIPLAYER PROFILE", (92, 68), self.large, (255, 220, 110))
        self.text(surface, f"Level {self.profile.level}  •  {self.profile.data['xp']} XP  •  {self.profile.data['wins']} winning hands", (94, 118), self.small)
        self.button(surface, "Done", (1152, 65, 112, 42), "close")

        # Profile slots remain independent from single-player save slots.
        for i in range(1, 4):
            self.button(
                surface,
                f"Profile {i}" + (" • Active" if i == self.profile.slot else ""),
                (92 + (i - 1) * 180, 150, 165, 40),
                ("slot", i),
                table is None,
            )

        self.draw_avatar_preview(surface)

        # Name field.
        self.text(surface, "Name", (430, 205), self.small)
        name_rect = pygame.Rect(430, 233, 430, 46)
        self.panel(surface, name_rect, (18, 52, 38, 225), (255, 215, 85) if self.field == "name" else (215, 226, 219), 2)
        shown = self.profile.data["name"] + ("|" if self.field == "name" else "")
        clip = surface.get_clip(); surface.set_clip(name_rect.inflate(-12, -4))
        self.text(surface, shown, (444, 244), self.font)
        surface.set_clip(clip)
        self.buttons.append((name_rect, "name"))

        # Avatar selectors mirror the single-player Base / Eyes / Hair / Glasses / Top rows.
        self.text(surface, "AVATAR", (430, 310), self.font, (255, 220, 110))
        _banks, choices = self.profile.avatar_choices()
        labels = {"base":"Base", "eyes":"Eyes", "hair":"Hair", "glasses":"Glasses", "top":"Top"}
        parts = self.profile.data.setdefault("avatar_parts", {})
        for index, key in enumerate(self.selector_keys):
            y = 352 + index * 52
            self.text(surface, labels[key], (430, y + 9), self.small)
            self.button(surface, "‹", (560, y, 48, 40), ("avatar", key, -1))
            self.button(surface, "›", (748, y, 48, 40), ("avatar", key, 1))
            options = choices[key]
            current = parts.get(key)
            if current is None:
                value = "None"
            else:
                try: value = f"{options.index(current) + 1}/{len(options)}"
                except ValueError: value = "1/" + str(max(1, len(options)))
            value_rect = pygame.Rect(617, y, 122, 40)
            self.panel(surface, value_rect, (17, 45, 34, 220), (130, 151, 143), 1)
            label = self.small.render(value, True, (255, 220, 110))
            surface.blit(label, label.get_rect(center=value_rect.center))

        # Cosmetic choices on the right, kept separate from avatar construction.
        self.panel(surface, (900, 198, 350, 418), (12, 34, 27, 220), (150, 169, 160), 1)
        self.text(surface, "MULTIPLAYER COSMETICS", (928, 220), self.font, (255, 220, 110))
        for row, category in enumerate(("background", "felt", "back")):
            y = 286 + row * 96
            keys = list(self.profile.catalog[category])
            self.page[category] %= len(keys)
            key = keys[self.page[category]]
            item = self.profile.catalog[category][key]
            required = self.profile.unlock_level(category, key)
            self.text(surface, category.title(), (928, y), self.small)
            self.button(surface, "‹", (928, y + 29, 44, 38), ("cycle", category, -1))
            self.button(surface, "›", (1178, y + 29, 44, 38), ("cycle", category, 1))
            name_rect = pygame.Rect(980, y + 29, 190, 38)
            self.panel(surface, name_rect, (17, 45, 34, 220), (130, 151, 143), 1)
            name = self.small.render(item["name"], True, (244, 236, 211))
            if name.get_width() > name_rect.w - 12:
                name = pygame.transform.smoothscale(name, (name_rect.w - 12, name.get_height()))
            surface.blit(name, name.get_rect(center=name_rect.center))
            selected = self.profile.data["selected"][category] == key
            text = "Selected" if selected else "Select" if required <= self.profile.level else f"Level {required}"
            self.button(surface, text, (1015, y + 70, 160, 34), ("select", category, key), required <= self.profile.level)

        message = self.message or self.profile.notice or "Avatar parts are stored locally; only the finished portrait is shared with the room."
        self.text(surface, message[:120], (94, 682), self.small, (205, 216, 208))

    def event(self, event, mouse, table=None):
        changed = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.open = False; self.field = None; self.text_input = TextInput(); self.profile.save(); pygame.key.stop_text_input(); return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, action in self.buttons:
                if not rect.collidepoint(mouse):
                    continue
                self.message = ""
                if action == "close":
                    self.open = False; self.field = None; self.text_input = TextInput(); self.profile.save(); pygame.key.stop_text_input()
                elif action == "name":
                    self.field = "name"; self.text_input.selected = False; pygame.key.start_text_input()
                elif isinstance(action, tuple):
                    if action[0] == "slot":
                        self.profile.save(); self.profile.load(action[1]); self.profile.rebuild_avatar(); changed = True
                    elif action[0] == "avatar":
                        self.profile.cycle_avatar_part(action[1], action[2]); changed = True
                    elif action[0] == "cycle":
                        self.page[action[1]] += action[2]
                    elif action[0] == "select":
                        self.profile.select(action[1], action[2]); changed = True
                break

        if self.field == "name" and event.type in (pygame.TEXTINPUT, pygame.KEYDOWN):
            value = self.text_input.event(event, self.profile.data["name"], 32)
            self.profile.data["name"] = "".join(c for c in value if c.isprintable())[:32]
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.profile.save(); self.field = None; pygame.key.stop_text_input(); changed = True

        if changed and table:
            table.refresh_profile()
        return True
