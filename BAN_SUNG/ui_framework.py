# ui_framework.py — Reusable Tactical UI Components
import pygame
import math
from constants import *


class UIColors:
    """Centralized UI color manager."""
    BG = UI_BG
    PANEL = UI_PANEL
    PANEL_LIGHT = UI_PANEL_LIGHT
    BORDER = UI_BORDER
    HIGHLIGHT = UI_HIGHLIGHT
    TEXT = UI_TEXT
    TEXT_DIM = UI_TEXT_DIM
    HP = UI_HP
    ARMOR = UI_ARMOR
    STAMINA = UI_STAMINA


class Button:
    """Tactical-style button with hover/click effects."""
    def __init__(self, x, y, w, h, text, font, color=None, icon=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color or UI_BORDER
        self.icon = icon
        self.hovered = False
        self.clicked = False
        self.disabled = False
        self._pulse = 0.0

    def update(self, mouse_pos, mouse_click=False):
        self.hovered = self.rect.collidepoint(mouse_pos) and not self.disabled
        self.clicked = self.hovered and mouse_click
        self._pulse += 0.08
        return self.clicked

    def draw(self, screen):
        # Background
        bg = UI_PANEL_LIGHT if self.hovered else UI_PANEL
        if self.disabled:
            bg = (10, 10, 15)
        pygame.draw.rect(screen, bg, self.rect, border_radius=4)

        # Border with glow on hover
        border_col = self.color
        border_w = 1
        if self.hovered:
            border_col = UI_HIGHLIGHT
            border_w = 2
            # Glow
            glow = pygame.Surface((self.rect.w + 12, self.rect.h + 12), pygame.SRCALPHA)
            pulse = int(30 + 20 * math.sin(self._pulse * 3))
            pygame.draw.rect(glow, (*UI_HIGHLIGHT, pulse), (0, 0, self.rect.w + 12, self.rect.h + 12), border_radius=8)
            screen.blit(glow, (self.rect.x - 6, self.rect.y - 6))

        pygame.draw.rect(screen, border_col, self.rect, border_w, border_radius=4)

        # Text
        txt_color = UI_HIGHLIGHT if self.hovered else UI_TEXT
        if self.disabled:
            txt_color = UI_TEXT_DIM
        txt_surf = self.font.render(self.text, True, txt_color)
        screen.blit(txt_surf, (self.rect.centerx - txt_surf.get_width() // 2,
                               self.rect.centery - txt_surf.get_height() // 2))

        # Left accent line
        if self.hovered:
            pygame.draw.line(screen, UI_HIGHLIGHT,
                             (self.rect.x, self.rect.y + 4),
                             (self.rect.x, self.rect.bottom - 4), 3)


class Panel:
    """Dark panel with border glow."""
    def __init__(self, x, y, w, h, title="", border_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.title = title
        self.border_color = border_color or (150, 160, 170)
        self._pulse = 0.0

    def draw(self, screen, font=None):
        self._pulse += 0.03
        
        # Calculate 3D tilt offset from screen center
        mx, my = pygame.mouse.get_pos()
        tilt_x = int((mx - SCREEN_W / 2) / (SCREEN_W / 2) * -12)
        tilt_y = int((my - SCREEN_H / 2) / (SCREEN_H / 2) * -12)
        
        # 1. Draw 3D depth shadow panel
        shadow_rect = pygame.Rect(self.rect.x + tilt_x, self.rect.y + tilt_y, self.rect.w, self.rect.h)
        shadow_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        shadow_surf.fill((10, 15, 22, 100)) # very dark translucent blue-grey
        screen.blit(shadow_surf, shadow_rect.topleft)
        pygame.draw.rect(screen, (40, 52, 70), shadow_rect, 1, border_radius=4)
        
        # 2. Draw connecting perspective lines at the corners to show depth
        col_connect = (40, 52, 66)
        pygame.draw.line(screen, col_connect, (self.rect.x + tilt_x, self.rect.y + tilt_y), (self.rect.x, self.rect.y), 1)
        pygame.draw.line(screen, col_connect, (self.rect.right + tilt_x, self.rect.y + tilt_y), (self.rect.right, self.rect.y), 1)
        pygame.draw.line(screen, col_connect, (self.rect.x + tilt_x, self.rect.bottom + tilt_y), (self.rect.x, self.rect.bottom), 1)
        pygame.draw.line(screen, col_connect, (self.rect.right + tilt_x, self.rect.bottom + tilt_y), (self.rect.right, self.rect.bottom), 1)
        
        # 3. Draw front panel background - dark tactical background with transparency
        bg_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg_surf.fill((10, 12, 14, 220))
        screen.blit(bg_surf, self.rect.topleft)
        
        # Border (1px slate gray)
        pygame.draw.rect(screen, self.border_color, self.rect, 1, border_radius=2)
        
        # Corner accents (1px gold/amber)
        size = 12
        for corner in [(self.rect.topleft, 1, 1), (self.rect.topright, -1, 1),
                        (self.rect.bottomleft, 1, -1), (self.rect.bottomright, -1, -1)]:
            pos, dx, dy = corner
            x, y = pos
            pygame.draw.line(screen, (245, 165, 30), (x, y), (x + size * dx, y), 1)
            pygame.draw.line(screen, (245, 165, 30), (x, y), (x, y + size * dy), 1)

        # Title
        if self.title and font:
            txt = font.render(self.title, True, (245, 165, 30))
            screen.blit(txt, (self.rect.x + 20, self.rect.y + 12))
            # Line under title
            pygame.draw.line(screen, (150, 160, 170),
                             (self.rect.x + 15, self.rect.y + 44),
                             (self.rect.right - 15, self.rect.y + 44), 1)


class TacticalBar:
    """Progress bar with military/tactical styling."""
    def __init__(self, x, y, w, h, color, label="", show_value=False):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.color = color
        self.label = label
        self.show_value = show_value
        self._pulse = 0.0

    def draw(self, screen, pct, font, current=None, maximum=None):
        self._pulse += 0.05
        pct = max(0, min(1, pct))

        # Background
        pygame.draw.rect(screen, (10, 12, 18), (self.x, self.y, self.w, self.h), border_radius=3)
        pygame.draw.rect(screen, (30, 35, 45), (self.x, self.y, self.w, self.h), 1, border_radius=3)

        # Fill
        if pct > 0:
            fill_w = int((self.w - 4) * pct)
            if fill_w > 0:
                # Main fill
                fill_rect = pygame.Rect(self.x + 2, self.y + 2, fill_w, self.h - 4)
                pygame.draw.rect(screen, self.color, fill_rect, border_radius=2)

                # Gloss (top half lighter)
                gloss_color = tuple(min(255, c + 40) for c in self.color)
                gloss_rect = pygame.Rect(self.x + 2, self.y + 2, fill_w, (self.h - 4) // 2)
                pygame.draw.rect(screen, gloss_color, gloss_rect, border_radius=2)

                # Pulsing end-cap when low
                if pct < 0.25:
                    pulse_alpha = int(100 + 80 * math.sin(self._pulse * 6))
                    pulse_surf = pygame.Surface((fill_w, self.h - 4), pygame.SRCALPHA)
                    pulse_surf.fill((*UI_DANGER, pulse_alpha))
                    screen.blit(pulse_surf, (self.x + 2, self.y + 2))

        # Label (left)
        if self.label:
            txt = font.render(self.label, True, UI_TEXT)
            screen.blit(txt, (self.x + 6, self.y + self.h // 2 - txt.get_height() // 2))

        # Value (right)
        if self.show_value and current is not None and maximum is not None:
            val_txt = font.render(f"{int(current)}/{int(maximum)}", True, WHITE)
            screen.blit(val_txt, (self.x + self.w - val_txt.get_width() - 6,
                                  self.y + self.h // 2 - val_txt.get_height() // 2))


class ScanLine:
    """Animated horizontal scan line effect for panels."""
    def __init__(self, x, y, w, h, speed=2, color=None):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.speed = speed
        self.color = color or UI_HIGHLIGHT
        self.pos = 0

    def update(self):
        self.pos = (self.pos + self.speed) % self.h

    def draw(self, screen):
        for i in range(3):
            alpha = int(40 - i * 12)
            if alpha > 0:
                line_y = self.y + (self.pos + i) % self.h
                surf = pygame.Surface((self.w, 1), pygame.SRCALPHA)
                surf.fill((*self.color, alpha))
                screen.blit(surf, (self.x, line_y))


class ParticleField:
    """Floating particles for menu backgrounds."""
    def __init__(self, count=60, bounds=(SCREEN_W, SCREEN_H)):
        import random
        self.particles = []
        self.bounds = bounds
        for _ in range(count):
            self.particles.append({
                'x': random.randint(0, bounds[0]),
                'y': random.randint(0, bounds[1]),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(-0.5, -0.1),
                'size': random.uniform(1, 3),
                'alpha': random.randint(30, 120),
                'color': random.choice([UI_BORDER, UI_HIGHLIGHT, (0, 100, 140)])
            })

    def update(self):
        import random
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['y'] < -10:
                p['y'] = self.bounds[1] + 10
                p['x'] = random.randint(0, self.bounds[0])
            if p['x'] < -10 or p['x'] > self.bounds[0] + 10:
                p['x'] = random.randint(0, self.bounds[0])

    def draw(self, screen):
        for p in self.particles:
            size = int(p['size'])
            if size < 1:
                continue
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['color'], p['alpha']), (size, size), size)
            screen.blit(surf, (int(p['x']) - size, int(p['y']) - size))
