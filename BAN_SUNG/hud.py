import pygame
import math
from constants import *


class HUD:
    def __init__(self, font_large, font_small):
        self.font_large = font_large
        self.font_small = font_small
        
        # Minimap surface
        self.mm_size = 150
        self.mm_surf = pygame.Surface((self.mm_size, self.mm_size), pygame.SRCALPHA)
        
        # Load weapon images
        self.weapon_images = {}
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        debug_log_path = os.path.join(base_dir, "hud_debug.log")
        with open(debug_log_path, "w", encoding="utf-8") as log_f:
            log_f.write("HUD Init Debug Log\n")
            for w_id, f_name in [("AK-47", "AK.jpg"), ("SHOTGUN", "shotgun.jpg"), ("SMG", "MP.jpg"), ("FLAMETHROWER", "súng lửa.png")]:
                w_path = os.path.join(base_dir, "ANH", f_name)
                log_f.write(f"Checking {w_id} at {w_path}...\n")
                if os.path.exists(w_path):
                    try:
                        img = pygame.image.load(w_path).convert_alpha()
                        # Xóa nền
                        bg_color = img.get_at((0, 0))
                        img.lock()
                        w, h = img.get_size()
                        for x in range(w):
                            for y in range(h):
                                c = img.get_at((x, y))
                                if abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2]) < 60:
                                    img.set_at((x, y), (0,0,0,0))
                        img.unlock()
                        # Quay súng về bên phải (lật ngang)
                        img = pygame.transform.flip(img, True, False)
                        img = pygame.transform.smoothscale(img, (110, 60)) # Phù hợp với ô 120x75
                        self.weapon_images[w_id] = img
                        log_f.write(f"  Loaded {w_id} successfully! Keys in dict: {list(self.weapon_images.keys())}\n")
                    except Exception as e:
                        log_f.write(f"  Error loading {w_id}: {e}\n")
                else:
                    log_f.write(f"  File not found at: {w_path}\n")
        
        self.mm_background = None

    def bake_minimap(self, game_map):
        self.mm_background = pygame.Surface((self.mm_size, self.mm_size), pygame.SRCALPHA)
        self.mm_background.fill((10, 20, 10, 220)) # Deep tactical green
        
        scale_x = self.mm_size / game_map.pixel_w
        scale_y = self.mm_size / game_map.pixel_h
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                t = game_map.grid[y][x]
                dx = x * TILE_SIZE * scale_x
                dy = y * TILE_SIZE * scale_y
                if t == TILE_WALL:
                    pygame.draw.rect(self.mm_background, (30, 70, 30), (dx, dy, 2, 2))
                elif t == TILE_COVER:
                    pygame.draw.rect(self.mm_background, (70, 70, 60), (dx, dy, 2, 2))
                elif t == TILE_BARREL:
                    pygame.draw.rect(self.mm_background, (160, 45, 10), (dx, dy, 2, 2))
                elif t == TILE_ALARM_CONSOLE:
                    pygame.draw.rect(self.mm_background, (200, 200, 0), (dx, dy, 2, 2))
                elif t == TILE_LASER:
                    pygame.draw.rect(self.mm_background, (255, 0, 0), (dx, dy, 2, 2))
                elif game_map.detail_grid[y][x] == 1: # Path
                    pygame.draw.rect(self.mm_background, (50, 50, 30), (dx, dy, 1, 1))

    def draw(self, screen, player, level, game_map, enemies, items=None):
        # ── Bottom Left: Stats ──────────────────────────────────────────────
        margin = 20
        y_start = SCREEN_H - margin - 80
        
        # HP Bar (Rugged)
        hp_pct = max(0, player.hp / player.max_hp)
        self._draw_neon_bar(screen, margin, y_start, 200, 18, hp_pct, (180, 20, 20), "HP")
        
        # Armor Bar (Military Green)
        y_start += 28
        ar_pct = player.armor / player.max_armor if player.max_armor > 0 else 0
        self._draw_neon_bar(screen, margin, y_start, 200, 18, ar_pct, (80, 100, 60), "GIÁP")
        
        # Focus Bar (Amber)
        y_start += 28
        fc_pct = player.focus / FOCUS_MAX
        self._draw_neon_bar(screen, margin, y_start, 200, 12, fc_pct, (200, 150, 20), "TẬP TRUNG")
        
        # ── Bottom Right: Ammo & Grenades ───────────────────────────────────
        m_type = getattr(player, 'equipped_melee', 'PAN')
        m_name = {"PAN": "CHẢO", "SABER": "ĐAO", "BAT": "GẬY", "SWORD": "KIẾM", "SCYTHE": "LƯỠI HÁI"}.get(m_type, "CHẢO")
        
        if player.weapon == "MELEE":
            ammo_txt = self.font_large.render(f"CẬN CHIẾN: {m_name}", True, (255, 200, 50))
        else:
            ammo_txt = self.font_large.render(f"ĐẠN: {player.ammo}", True, YELLOW)
            
        g_type = getattr(player, 'equipped_grenade', 'FRAG')
        g_name = {"FRAG": "NỔ", "FLASH": "CHOÁNG", "SMOKE": "KHÓI"}.get(g_type, "NỔ")
        gre_txt = self.font_large.render(f"LỰU ĐẠN ({g_name}): {player.grenades}", True, ORANGE)
        
        melee_txt = self.font_small.render(f"CẬN CHIẾN: {m_name} [RIGHT CLICK / V]", True, (255, 200, 50))
        
        # Dash indicator
        dash_color = LIME if player.dash_cooldown <= 0 else GRAY
        dash_txt = self.font_small.render("LƯỚT: SẴN SÀNG" if player.dash_cooldown <= 0 else "LƯỚT: CHỜ", True, dash_color)
        
        screen.blit(ammo_txt, (SCREEN_W - margin - ammo_txt.get_width(), SCREEN_H - margin - 90))
        screen.blit(gre_txt, (SCREEN_W - margin - gre_txt.get_width(), SCREEN_H - margin - 60))
        screen.blit(melee_txt, (SCREEN_W - margin - melee_txt.get_width(), SCREEN_H - margin - 35))
        screen.blit(dash_txt, (SCREEN_W - margin - dash_txt.get_width(), SCREEN_H - margin - 15))
        
        # ── Top Left: Level Info ────────────────────────────────────────────
        if level == 6:
            lvl_txt = self.font_large.render("CHIẾN DỊCH CUỐI: HANG TRÙM CUỐI", True, (255, 60, 60))
        else:
            lvl_txt = self.font_large.render(f"MÀN CHƠI {level}", True, WHITE)
        en_txt = self.font_small.render(f"ĐỊCH: {len(enemies)}", True, RED)
        screen.blit(lvl_txt, (margin, margin))
        screen.blit(en_txt, (margin, margin + 35))
        
        # ── Top Right: Minimap ──────────────────────────────────────────────
        self.mm_surf.fill((0, 0, 0, 0))
        if self.mm_background:
            self.mm_surf.blit(self.mm_background, (0, 0))
        else:
            self.mm_surf.fill((10, 20, 10, 220))
        
        scale_x = self.mm_size / game_map.pixel_w
        scale_y = self.mm_size / game_map.pixel_h

        # 2. Radar scan line effect
        scan_y = (pygame.time.get_ticks() // 15) % self.mm_size
        scan_surf = pygame.Surface((self.mm_size, 2), pygame.SRCALPHA)
        scan_surf.fill((0, 255, 0, 40))
        self.mm_surf.blit(scan_surf, (0, scan_y))

        # 3. Draw entities
        # Draw player
        px = int(player.x * scale_x)
        py = int(player.y * scale_y)
        pygame.draw.circle(self.mm_surf, GREEN, (px, py), 3)
        pygame.draw.circle(self.mm_surf, WHITE, (px, py), 4, 1) # Ring
        
        # Draw enemies
        for e in enemies:
            ex = int(e.x * scale_x)
            ey = int(e.y * scale_y)
            if e.type == "boss":
                # Chấm màu vàng nhấp nháy cho Boss trên mini map
                pulse = int(150 + 105 * math.sin(pygame.time.get_ticks() / 150))
                pygame.draw.circle(self.mm_surf, (255, 255, 0), (ex, ey), 4)
                pygame.draw.circle(self.mm_surf, (255, 200, 0, pulse), (ex, ey), 6, 1)
            else:
                pygame.draw.circle(self.mm_surf, RED, (ex, ey), 2)
            
        # Draw exit
        pulse = int(128 + 127 * math.sin(pygame.time.get_ticks() / 200))
        for y in range(game_map.height):
            for x in range(game_map.width):
                if game_map.grid[y][x] == TILE_EXIT:
                    ex = int((x * TILE_SIZE + TILE_SIZE//2) * scale_x)
                    ey = int((y * TILE_SIZE + TILE_SIZE//2) * scale_y)
                    pygame.draw.circle(self.mm_surf, (*EXIT_COLOR, pulse), (ex, ey), 4)
                    pygame.draw.circle(self.mm_surf, WHITE, (ex, ey), 6, 1)

        # Tactical Grid and Border
        for i in range(1, 4):
            pos = i * (self.mm_size // 4)
            pygame.draw.line(self.mm_surf, (30, 50, 30), (pos, 0), (pos, self.mm_size), 1)
            pygame.draw.line(self.mm_surf, (30, 50, 30), (0, pos), (self.mm_size, pos), 1)
        pygame.draw.rect(self.mm_surf, (80, 120, 80), (0, 0, self.mm_size, self.mm_size), 2)
            
        screen.blit(self.mm_surf, (SCREEN_W - margin - self.mm_size, margin))

        # ── Bottom Center: Weapon Slots ──────────────────────────────────────
        equipped = getattr(player, 'equipped_weapons', ["AK-47"])
        dnames = {"AK-47": "AK-47", "SHOTGUN": "SHOTGUN", "SMG": "TIỂU LIÊN", "FLAMETHROWER": "SÚNG LỬA"}
        weapons_info = []
        for idx, w_id in enumerate(equipped):
            weapons_info.append({
                "key": str(idx + 1),
                "name": dnames.get(w_id, w_id),
                "id": w_id
            })
            
        slot_w = 120
        slot_h = 75
        gap = 15
        num_slots = len(weapons_info) if weapons_info else 1
        total_w = slot_w * num_slots + gap * (num_slots - 1)
        start_x = SCREEN_W // 2 - total_w // 2
        start_y = SCREEN_H - slot_h - 15
        
        active_weapon = getattr(player, 'weapon', 'AK-47')
        
        if not hasattr(self, 'debug_drawn'):
            self.debug_drawn = True
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            debug_log_path = os.path.join(base_dir, "hud_debug.log")
            with open(debug_log_path, "a", encoding="utf-8") as log_f:
                log_f.write(f"[draw] active_weapon: {active_weapon}\n")
                log_f.write(f"[draw] weapons_info: {weapons_info}\n")
                log_f.write(f"[draw] weapon_images keys: {list(self.weapon_images.keys())}\n")
        
        for idx, wpn in enumerate(weapons_info):
            x = start_x + idx * (slot_w + gap)
            y = start_y
            
            is_active = (active_weapon == wpn["id"])
            
            # Colors
            bg_color = (20, 35, 45, 220) if is_active else (10, 15, 20, 180)
            border_color = (0, 255, 220) if is_active else (60, 80, 90)
            text_color = WHITE if is_active else (120, 140, 150)
            key_color = (0, 255, 220) if is_active else (100, 110, 120)
            
            # Draw Slot Background
            slot_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            pygame.draw.rect(slot_surf, bg_color, (0, 0, slot_w, slot_h), border_radius=6)
            
            # Draw Weapon Image
            if wpn["id"] in self.weapon_images:
                img = self.weapon_images[wpn["id"]]
                img_x = (slot_w - img.get_width()) // 2
                img_y = (slot_h - img.get_height()) // 2
                # Draw slightly dark overlay over image if not active
                if not is_active:
                    img_copy = img.copy()
                    dark = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                    dark.fill((0, 0, 0, 90))
                    img_copy.blit(dark, (0, 0))
                    slot_surf.blit(img_copy, (img_x, img_y))
                else:
                    slot_surf.blit(img, (img_x, img_y))
            
            pygame.draw.rect(slot_surf, border_color, (0, 0, slot_w, slot_h), 2 if is_active else 1, border_radius=6)
            
            # Active indicator glow
            if is_active:
                pygame.draw.rect(slot_surf, (0, 255, 220, 45), (2, 2, slot_w-4, slot_h-4), border_radius=4)
                
            screen.blit(slot_surf, (x, y))
            
            # Draw Key Bind Indicator (e.g. "1")
            key_txt = self.font_small.render(wpn["key"], True, key_color)
            screen.blit(key_txt, (x + 6, y + 3))
            
            # Draw Weapon Name with shadow for readability
            name_txt = self.font_small.render(wpn["name"], True, text_color)
            shadow = self.font_small.render(wpn["name"], True, (0,0,0))
            screen.blit(shadow, (x + slot_w // 2 - name_txt.get_width() // 2 + 1, y + slot_h - name_txt.get_height() - 1))
            screen.blit(name_txt, (x + slot_w // 2 - name_txt.get_width() // 2, y + slot_h - name_txt.get_height() - 2))

    def _draw_neon_bar(self, screen, x, y, w, h, pct, color, label):
        # BG
        pygame.draw.rect(screen, (10, 10, 15), (x, y, w, h), border_radius=4)
        pygame.draw.rect(screen, (40, 40, 50), (x, y, w, h), 1, border_radius=4)
        
        if pct > 0:
            fill_w = int((w-4) * pct)
            if fill_w > 0:
                # Main fill
                pygame.draw.rect(screen, color, (x+2, y+2, fill_w, h-4), border_radius=2)
                # Gloss / Shine (Using a lighter version of the color instead of alpha)
                shine_color = tuple(min(255, c + 50) for c in color)
                pygame.draw.rect(screen, shine_color, (x+2, y+2, fill_w, (h-4)//2), border_radius=2)
                
                # Glow effect
                glow_surf = pygame.Surface((fill_w+10, h+10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*color, 60), (5, 5, fill_w, h), border_radius=4)
                screen.blit(glow_surf, (x-5, y-5), special_flags=pygame.BLEND_ADD)
                
        # Label
        txt = self.font_small.render(label, True, WHITE)
        screen.blit(txt, (x + 5, y - 18))
