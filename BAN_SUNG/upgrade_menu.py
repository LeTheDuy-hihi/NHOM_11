import pygame
import random
import math
from constants import *


class UpgradeMenu:
    def __init__(self, font_title, font_normal, font_small):
        self.font_title = font_title
        self.font_normal = font_normal
        self.font_small = font_small
        
        self.options = [
            {"id": "dmg", "name": "Sát Thương", "desc": "Tăng 20% sát thương AK", "color": RED},
            {"id": "spd", "name": "Tốc Độ", "desc": "Tăng tốc độ di chuyển", "color": CYAN},
            {"id": "arm", "name": "Giáp", "desc": "Tăng 50 giáp tối đa", "color": BLUE},
            {"id": "ammo", "name": "Đạn", "desc": "Nhận 100 viên đạn AK", "color": YELLOW},
            {"id": "gre", "name": "Lựu Đạn", "desc": "Nhận 3 lựu đạn", "color": ORANGE},
            {"id": "heal", "name": "Hồi Phục", "desc": "Hồi đầy HP", "color": GREEN}
        ]
        
        self.current_choices = []
        self.selected_idx = 0
        
    def roll_choices(self):
        self.current_choices = random.sample(self.options, 3)
        self.selected_idx = 0
        
    def handle_input(self, event, player):
        if event.type == pygame.KEYDOWN:
            scancode = getattr(event, 'scancode', None)
            if event.key == pygame.K_LEFT or event.key == pygame.K_a or scancode == 4:
                self.selected_idx = (self.selected_idx - 1) % 3
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d or scancode == 7:
                self.selected_idx = (self.selected_idx + 1) % 3
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.apply_upgrade(player)
                return True # Done
        
        elif event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONDOWN:
            card_w, card_h = 200, 250
            gap = 50
            total_w = 3 * card_w + 2 * gap
            start_x = SCREEN_W//2 - total_w//2
            y = 250
            
            for i in range(3):
                x = start_x + i * (card_w + gap)
                rect = pygame.Rect(x, y, card_w, card_h)
                if rect.collidepoint(event.pos):
                    self.selected_idx = i
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.apply_upgrade(player)
                        return True
                    break
        
        return False

    def apply_upgrade(self, player):
        choice = self.current_choices[self.selected_idx]
        cid = choice["id"]
        
        if cid == "dmg":
            player.damage_mult += 0.2
        elif cid == "spd":
            player.speed += 0.5
        elif cid == "arm":
            player.max_armor += 50
            player.armor = player.max_armor
        elif cid == "ammo":
            player.ammo += 100
        elif cid == "gre":
            player.grenades += 3
        elif cid == "heal":
            player.hp = player.max_hp

    def draw(self, screen):
        # Overlay
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 200))
        screen.blit(surf, (0, 0))
        
        # Title
        title = self.font_title.render("HOÀN THÀNH NHIỆM VỤ", True, GOLD)
        sub = self.font_normal.render("CHỌN 1 TRANG BỊ TIẾP VIỆN", True, WHITE)
        screen.blit(title, (SCREEN_W//2 - title.get_width()//2, 100))
        screen.blit(sub, (SCREEN_W//2 - sub.get_width()//2, 160))
        
        # Cards
        card_w, card_h = 200, 250
        gap = 50
        total_w = 3 * card_w + 2 * gap
        start_x = SCREEN_W//2 - total_w//2
        y = 250
        
        for i, choice in enumerate(self.current_choices):
            x = start_x + i * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            
            is_sel = (i == self.selected_idx)
            bg_col = (40, 40, 40) if not is_sel else (80, 80, 80)
            br_col = choice["color"] if is_sel else (100, 100, 100)
            
            pygame.draw.rect(screen, bg_col, rect)
            pygame.draw.rect(screen, br_col, rect, 4 if is_sel else 2)
            
            # Text
            ntxt = self.font_normal.render(choice["name"], True, choice["color"])
            dtxt = self.font_small.render(choice["desc"], True, WHITE)
            
            screen.blit(ntxt, (x + card_w//2 - ntxt.get_width()//2, y + 50))
            
            # Wrap desc
            words = choice["desc"].split()
            line1 = " ".join(words[:len(words)//2 + 1])
            line2 = " ".join(words[len(words)//2 + 1:])
            l1t = self.font_small.render(line1, True, WHITE)
            l2t = self.font_small.render(line2, True, WHITE)
            screen.blit(l1t, (x + card_w//2 - l1t.get_width()//2, y + 120))
            screen.blit(l2t, (x + card_w//2 - l2t.get_width()//2, y + 150))
            
            if is_sel:
                # Pulsing outline
                pulse = int(128 + 127 * math.sin(pygame.time.get_ticks() / 150))
                p_col = (*choice["color"], pulse)
                psurf = pygame.Surface((card_w+20, card_h+20), pygame.SRCALPHA)
                pygame.draw.rect(psurf, p_col, (0, 0, card_w+20, card_h+20), 4, border_radius=10)
                screen.blit(psurf, (x-10, y-10))
