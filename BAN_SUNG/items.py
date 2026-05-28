import pygame
import math
import random
from constants import *


class Item:
    RADIUS = 10
    BOB_SPEED = 0.08

    def __init__(self, x, y, item_type):
        self.x, self.y = x, y
        self.type = item_type
        self.alive = True
        self._bob = random.uniform(0, math.pi*2)
        self._age = 0

    def update(self):
        self._age += 1
        self._bob += self.BOB_SPEED

    def draw(self, screen, cam_x, cam_y):
        bob_y = int(3 * math.sin(self._bob))
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y) + bob_y

        # Glow ring
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        glow_col, inner_col, symbol = self._visuals()
        pulse = int(40 + 30 * abs(math.sin(self._bob * 0.5)))
        pygame.draw.circle(surf, (*glow_col, pulse), (20, 20), 16)
        screen.blit(surf, (sx-20, sy-20))

        # Body
        pygame.draw.circle(screen, glow_col, (sx, sy), self.RADIUS)
        pygame.draw.circle(screen, WHITE, (sx, sy), self.RADIUS, 2)

        # Symbol (simple shapes)
        self._draw_symbol(screen, sx, sy, inner_col, symbol)

    def _visuals(self):
        if self.type == ITEM_HEALTH:
            return RED, WHITE, "+"
        elif self.type == ITEM_AMMO:
            return YELLOW, DARK_BG, "A"
        elif self.type == ITEM_ARMOR:
            return CYAN, DARK_BG, "V"
        elif self.type == ITEM_GRENADE:
            return ORANGE, DARK_BG, "G"
        elif self.type == ITEM_RADAR:
            return PURPLE, WHITE, "R"
        elif self.type == ITEM_GOLD:
            return GOLD, WHITE, "$"
        return GRAY, WHITE, "?"

    def _draw_symbol(self, screen, sx, sy, col, sym):
        if sym == "+":
            pygame.draw.rect(screen, col, (sx-5, sy-2, 10, 4))
            pygame.draw.rect(screen, col, (sx-2, sy-5, 4, 10))
        elif sym == "A":
            pts = [(sx, sy-6), (sx+5, sy+4), (sx-5, sy+4)]
            pygame.draw.polygon(screen, col, pts, 2)
            pygame.draw.line(screen, col, (sx-3, sy+1), (sx+3, sy+1), 2)
        elif sym == "V":
            pts = [(sx-5, sy-4), (sx+5, sy-4), (sx, sy+5)]
            pygame.draw.polygon(screen, col, pts, 2)
        elif sym == "G":
            pygame.draw.circle(screen, col, (sx, sy), 4, 2)
            pygame.draw.line(screen, col, (sx, sy-4), (sx, sy-7), 2)
        elif sym == "R":
            for r in [3, 6]:
                pygame.draw.circle(screen, col, (sx, sy), r, 1)
        elif sym == "$":
            # Vẽ ký hiệu $ đơn giản
            pygame.draw.circle(screen, col, (sx, sy), 6, 2)
            pygame.draw.line(screen, col, (sx, sy-8), (sx, sy+8), 2)

    def get_effect(self):
        """Returns (heal, ammo, armor, grenades, gold) to apply to player."""
        if self.type == ITEM_HEALTH:
            return (40, 0, 0, 0, 0)
        elif self.type == ITEM_AMMO:
            return (0, 60, 0, 0, 0)
        elif self.type == ITEM_ARMOR:
            return (0, 0, 30, 0, 0)
        elif self.type == ITEM_GRENADE:
            return (0, 0, 0, 2, 0)
        elif self.type == ITEM_RADAR:
            return (0, 0, 0, 0, 0)  # handled separately
        elif self.type == ITEM_GOLD:
            return (0, 0, 0, 0, random.randint(15, 30)) # Vàng ngẫu nhiên
        return (0, 0, 0, 0, 0)


class ItemManager:
    def __init__(self, spawn_list, level=1):
        import random
        self.items = []
        item_types = [ITEM_HEALTH, ITEM_AMMO, ITEM_ARMOR, ITEM_GRENADE, ITEM_RADAR]
        weights    = [0.35, 0.30, 0.15, 0.15, 0.05]

        for (tx, ty) in spawn_list:
            itype = random.choices(item_types, weights=weights)[0]
            x = tx * TILE_SIZE + TILE_SIZE // 2
            y = ty * TILE_SIZE + TILE_SIZE // 2
            self.items.append(Item(x, y, itype))

    def update(self, player=None):
        for item in self.items:
            item.update()
            # Tự động hút vàng về phía người chơi sau 0.5 giây (age > 30)
            if player and item.type == ITEM_GOLD and item._age > 30:
                dist = math.hypot(player.x - item.x, player.y - item.y)
                if dist > 0:
                    speed = 18 + min(item._age - 30, 60) * 0.5 # Tăng tốc dần
                    item.x += (player.x - item.x) / dist * speed
                    item.y += (player.y - item.y) / dist * speed
                    
        self.items = [i for i in self.items if i.alive]

    def check_pickup(self, player):
        """Check if player picks up any item. Returns list of picked items."""
        picked = []
        for item in self.items:
            dist = math.hypot(player.x - item.x, player.y - item.y)
            if dist < 22:
                item.alive = False
                picked.append(item)
        return picked

    def draw(self, screen, cam_x, cam_y):
        for item in self.items:
            item.draw(screen, cam_x, cam_y)
