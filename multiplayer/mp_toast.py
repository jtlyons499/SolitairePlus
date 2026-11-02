"""Small transient multiplayer notifications shared by all room views."""
import pygame


class LeaveToast:
    def __init__(self, duration_ms=2800):
        self.duration_ms = max(800, int(duration_ms))
        self.seen = 0
        self.text = ""
        self.started = 0

    def sync(self, table):
        try:
            sequence = int(getattr(table, "leave_notice_seq", 0) or 0)
        except (TypeError, ValueError):
            sequence = 0
        if sequence > self.seen:
            self.seen = sequence
            self.text = str(getattr(table, "leave_notice", "") or "A player left the game.")[:96]
            self.started = pygame.time.get_ticks()

    def draw(self, surface, font):
        if not self.text or not self.started:
            return
        age = pygame.time.get_ticks() - self.started
        if age >= self.duration_ms:
            return
        fade_start = self.duration_ms - 900
        alpha = 255 if age <= fade_start else max(0, round(255 * (self.duration_ms - age) / 900))
        text_image = font.render(self.text, True, (248, 241, 218))
        width = min(surface.get_width() - 48, max(300, text_image.get_width() + 54))
        panel = pygame.Surface((width, 46), pygame.SRCALPHA)
        pygame.draw.rect(panel, (13, 27, 25, min(235, alpha)), panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, (226, 191, 80, alpha), panel.get_rect(), 2, border_radius=12)
        text_image.set_alpha(alpha)
        panel.blit(text_image, text_image.get_rect(center=panel.get_rect().center))
        surface.blit(panel, panel.get_rect(midtop=(surface.get_width() // 2, 92)))
