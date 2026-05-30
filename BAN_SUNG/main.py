import pygame

# ──────────────────────────────────────────────────────────────────────────────
# VIRTUAL RESOLUTION WRAPPER (Stretches display to fit window/screen, no black bars)
# ──────────────────────────────────────────────────────────────────────────────
_virtual_screen = pygame.Surface((1200, 800))
_real_screen = None
_is_fullscreen = False

_orig_display_set_mode = pygame.display.set_mode
def custom_set_mode(size, flags=0, depth=0, display=0, vsync=0):
    global _real_screen
    real_flags = flags & ~pygame.SCALED
    if real_flags & pygame.FULLSCREEN:
        _real_screen = _orig_display_set_mode((0, 0), real_flags, depth, display, vsync)
    else:
        _real_screen = _orig_display_set_mode(size, real_flags, depth, display, vsync)
    return _virtual_screen

pygame.display.set_mode = custom_set_mode
pygame.display.get_surface = lambda: _virtual_screen

_orig_display_flip = pygame.display.flip
_orig_display_update = pygame.display.update

def custom_display_flip():
    if _real_screen and _virtual_screen:
        pygame.transform.scale(_virtual_screen, _real_screen.get_size(), _real_screen)
    _orig_display_flip()

def custom_display_update(*args, **kwargs):
    if _real_screen and _virtual_screen:
        pygame.transform.scale(_virtual_screen, _real_screen.get_size(), _real_screen)
    _orig_display_update(*args, **kwargs)

pygame.display.flip = custom_display_flip
pygame.display.update = custom_display_update

_orig_mouse_get_pos = pygame.mouse.get_pos
def get_virtual_mouse_pos():
    real_mx, real_my = _orig_mouse_get_pos()
    if _real_screen:
        display_w, display_h = _real_screen.get_size()
        virtual_mx = int(real_mx * 1200 / display_w)
        virtual_my = int(real_my * 800 / display_h)
        return (virtual_mx, virtual_my)
    return (real_mx, real_my)

pygame.mouse.get_pos = get_virtual_mouse_pos

def toggle_fullscreen_global():
    global _is_fullscreen, _real_screen
    _is_fullscreen = not _is_fullscreen
    if _is_fullscreen:
        _real_screen = _orig_display_set_mode((0, 0), pygame.FULLSCREEN)
    else:
        _real_screen = _orig_display_set_mode((1200, 800), pygame.RESIZABLE)

_orig_event_get = pygame.event.get
def custom_event_get(*args, **kwargs):
    global _real_screen
    events = _orig_event_get(*args, **kwargs)
    filtered_events = []
    if _real_screen:
        display_w, display_h = _real_screen.get_size()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                _real_screen = _orig_display_set_mode(event.size, pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                toggle_fullscreen_global()
                continue
            if hasattr(event, "pos"):
                vx = int(event.pos[0] * 1200 / display_w)
                vy = int(event.pos[1] * 800 / display_h)
                event.pos = (vx, vy)
                if hasattr(event, "rel"):
                    vdx = int(event.rel[0] * 1200 / display_w)
                    vdy = int(event.rel[1] * 800 / display_h)
                    event.rel = (vdx, vdy)
                if "pos" in event.dict:
                    event.dict["pos"] = (vx, vy)
                if "rel" in event.dict:
                    event.dict["rel"] = (vdx, vdy)
            filtered_events.append(event)
        return filtered_events
    return events

pygame.event.get = custom_event_get
# ──────────────────────────────────────────────────────────────────────────────

import sys
import math
import random
import json
import os
from constants import *
from map_gen import GameMap
from player import Player
from enemy import EnemyManager
from bullet import BulletManager
from effects import EffectManager, Particle
from items import ItemManager, Item
from sound_manager import sound_manager
from hud import HUD
from upgrade_menu import UpgradeMenu
from menu import MainMenu
from in_game_menu import InGameSettings
from video_player import play_video
from dialogue import run_dialogue, LEVEL5_DIALOGUE, LEVEL1_DIALOGUE, LEVEL6_DIALOGUE, run_boss_cutscene


class GameApp:
    def __init__(self):
        pygame.init()
        # Cửa sổ game 1200x800, hỗ trợ tự động thu phóng (SCALED)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.SCALED | pygame.RESIZABLE)
        self.is_fullscreen = False
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # Fonts
        pygame.font.init()
        # Dùng font segoe ui hoặc arial để hỗ trợ tốt tiếng Việt
        self.font_large = pygame.font.SysFont("segoeui", 32, bold=True)
        self.font_title = pygame.font.SysFont("segoeui", 64, bold=True)
        self.font_normal = pygame.font.SysFont("segoeui", 24, bold=True)
        self.font_small = pygame.font.SysFont("segoeui", 16, bold=True)
        
        # Systems
        self.menu = MainMenu(self.font_title, self.font_normal, self.font_small)
        self.upgrade_menu = UpgradeMenu(self.font_title, self.font_normal, self.font_small)
        self.hud = HUD(self.font_large, self.font_small)
        self.in_game_settings = InGameSettings(self.font_title, self.font_normal)
        
        self.state = "MENU" # MENU, GAME, UPGRADE, GAMEOVER, WIN
        self.level = 1
        
        # Save System
        self.save_file = "save_data.json"
        self.gold = 0
        self.unlocked_weapons = ["AK-47", "PAN", "FRAG"]
        self.saved_equipped_weapons = ["AK-47"]
        self.saved_equipped_melee = "PAN"
        self.saved_equipped_grenade = "FRAG"
        self.perm_upgrades = {"hp": 0, "armor": 0, "damage": 0, "speed": 0, "dash": 0}
        self.inventory = {}
        self.load_save()
        
        # Đồng bộ với menu
        self.menu.gold = self.gold
        self.menu.unlocked_weapons = self.unlocked_weapons
        self.menu.equipped_weapons = list(self.saved_equipped_weapons)
        self.menu.equipped_melee = self.saved_equipped_melee
        self.menu.equipped_grenade = self.saved_equipped_grenade
        self.menu.perm_upgrades = self.perm_upgrades
        self.menu.inventory = dict(self.inventory)
        self.menu.save_callback = self.save_game
        
        # Game objects
        self.player = None
        self.game_map = None
        self.enemy_manager = None
        self.bullet_manager = None
        self.effect_manager = None
        self.item_manager = None
        
        # Raw scancode tracking (bypass Unikey)
        self.raw_keys = {
            "W": False, "A": False, "S": False, "D": False,
            "Q": False, "R": False, "G": False, "LShift": False
        }
        self.ai_mode = False  # AI tự chơi (bấm P để bật/tắt)
        
        # Fog of War Setup (Balanced Darkness)
        self.view_radius = 280
        # Tạo fog gradient mượt hơn — không có viền cứng, không tạo ô vuông sáng
        self.fog_gradient = pygame.Surface((self.view_radius * 2, self.view_radius * 2), pygame.SRCALPHA)
        for r in range(self.view_radius, 0, -2):
            alpha = int(225 * (r / self.view_radius)**1.4)
            pygame.draw.circle(self.fog_gradient, (0, 0, 0, alpha), (self.view_radius, self.view_radius), r)
            
        # Camera
        self.cam_x, self.cam_y = 0, 0
        
        # CRT Overlay Surface
        self.crt_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for y in range(0, SCREEN_H, 2):
            pygame.draw.line(self.crt_surf, (0, 0, 0, 40), (0, y), (SCREEN_W, y))

        # ── Pre-allocated Surfaces (tránh tạo Surface mỗi frame gây lag) ────
        self.fog_surf    = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.path_surf   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.overlay_surf= pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.warn_surf   = pygame.Surface((480, 54), pygame.SRCALPHA)
        self.alert_surf  = pygame.Surface((660, 54), pygame.SRCALPHA)
        self.ai_banner_surf = pygame.Surface((560, 64), pygame.SRCALPHA)
        self.flash_surf  = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.lobby_dark  = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.lobby_dark.fill((10, 12, 14, 180))
        self.lobby_psurf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Pre-compute ambient gradient cho Fog of War — gradient mượt, không viền cứng
        # Dùng radius lớn hơn và power thấp hơn để tránh ô vuông sáng
        _ar = 200
        self.fog_ambient_grad = pygame.Surface((_ar * 2, _ar * 2), pygame.SRCALPHA)
        for _r in range(_ar, 0, -2):
            # Power 2.5 → gradient rất mượt, fade dần từ trong ra ngoài
            _a = int(255 * (_r / _ar) ** 2.5)
            pygame.draw.circle(self.fog_ambient_grad, (0, 0, 0, _a), (_ar, _ar), _r)
        self._fog_ambient_radius = _ar
        self.alarm_active = False
        self.alarm_timer = 0
        self.siren_channel = None

            
    def load_save(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.gold = data.get("gold", 0)
                    self.unlocked_weapons = data.get("unlocked_weapons", ["AK-47", "PAN", "FRAG"])
                    self.perm_upgrades = data.get("perm_upgrades", {"hp": 0, "armor": 0, "damage": 0, "speed": 0, "dash": 0})
                    
                    # Load equipped weapons if present
                    eq_w = data.get("equipped_weapons", ["AK-47"])
                    eq_m = data.get("equipped_melee", "PAN")
                    eq_g = data.get("equipped_grenade", "FRAG")
                    
                    # Filter: only keep those that are actually unlocked
                    eq_w = [w for w in eq_w if w in self.unlocked_weapons]
                    if not eq_w:
                        eq_w = ["AK-47"]
                    if eq_m not in self.unlocked_weapons:
                        eq_m = "PAN"
                    if eq_g not in self.unlocked_weapons:
                        eq_g = "FRAG"
                        
                    self.saved_equipped_weapons = eq_w
                    self.saved_equipped_melee = eq_m
                    self.saved_equipped_grenade = eq_g
                    self.inventory = data.get("inventory", {})
            except Exception as e:
                print("Lỗi load save:", e)

    def save_game(self, new_gold=None, new_unlocked=None):
        if new_gold is not None:
            self.gold = new_gold
        if new_unlocked is not None:
            self.unlocked_weapons = new_unlocked
            
        # Get equipped lists from the menu
        eq_w = getattr(self, "menu", None) and self.menu.equipped_weapons or ["AK-47"]
        eq_m = getattr(self, "menu", None) and self.menu.equipped_melee or "PAN"
        eq_g = getattr(self, "menu", None) and self.menu.equipped_grenade or "FRAG"
        inv = getattr(self, "menu", None) and self.menu.inventory or {}
        
        # Filter just in case
        eq_w = [w for w in eq_w if w in self.unlocked_weapons]
        if not eq_w:
            eq_w = ["AK-47"]
        if eq_m not in self.unlocked_weapons:
            eq_m = "PAN"
        if eq_g not in self.unlocked_weapons:
            eq_g = "FRAG"
            
        self.perm_upgrades = getattr(self, "menu", None) and self.menu.perm_upgrades or {"hp": 0, "armor": 0, "damage": 0, "speed": 0, "dash": 0}
        self.inventory = dict(inv)
        
        data = {
            "gold": self.gold,
            "unlocked_weapons": self.unlocked_weapons,
            "equipped_weapons": eq_w,
            "equipped_melee": eq_m,
            "equipped_grenade": eq_g,
            "perm_upgrades": self.perm_upgrades,
            "inventory": self.inventory
        }
        try:
            with open(self.save_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            # Cập nhật lại vào menu
            self.menu.gold = self.gold
            self.menu.unlocked_weapons = self.unlocked_weapons
            self.menu.equipped_weapons = list(eq_w)
            self.menu.equipped_melee = eq_m
            self.menu.equipped_grenade = eq_g
            self.menu.perm_upgrades = self.perm_upgrades
            self.menu.inventory = dict(self.inventory)
        except Exception as e:
            print("Lỗi lưu save:", e)

    def start_game(self, new_campaign=True, is_training=False):
        self.is_training = is_training
        if new_campaign:
            if self.is_training:
                self.level = 0
            else:
                self.level = self.menu.selected_mission + 1
            # Initial player
            self.player = Player(0, 0)
            
            # Apply permanent upgrades
            hp_lvl = self.menu.perm_upgrades.get("hp", 0)
            armor_lvl = self.menu.perm_upgrades.get("armor", 0)
            damage_lvl = self.menu.perm_upgrades.get("damage", 0)
            speed_lvl = self.menu.perm_upgrades.get("speed", 0)
            dash_lvl = self.menu.perm_upgrades.get("dash", 0)

            self.player.max_hp = PLAYER_HP_MAX + hp_lvl * 10
            self.player.hp = self.player.max_hp
            self.player.max_armor = PLAYER_ARMOR_MAX + armor_lvl * 15
            self.player.armor = self.player.max_armor
            self.player.damage_mult = 1.0 + damage_lvl * 0.05
            self.player.speed = PLAYER_SPEED + speed_lvl * 0.16
            self.player.max_dash_cooldown = int(DASH_COOLDOWN * (1.0 - dash_lvl * 0.08))

            # Áp dụng trang bị đã chọn
            if self.is_training:
                self.player.equipped_weapons = ["AK-47", "SHOTGUN", "SMG", "FLAMETHROWER", "SNIPER", "MINIGUN", "LASER_RIFLE", "PLASMA_GUN"]
                self.player.ammo = 9999
                self.player.max_ammo = 9999
                self.player.grenades = 99
            else:
                self.player.equipped_weapons = list(self.menu.equipped_weapons)
            self.player.weapon = self.player.equipped_weapons[0] if self.player.equipped_weapons else "AK-47"
            self.player.equipped_grenade = self.menu.equipped_grenade
            self.player.equipped_melee = self.menu.equipped_melee
            
            # Áp dụng kho đồ & kích hoạt drone
            self.player.inventory = dict(self.menu.inventory)
            if self.player.inventory.get("Drone Hỗ Trợ", 0) > 0:
                from player import SupportDrone
                self.player.support_drone = SupportDrone(self.player)
            else:
                self.player.support_drone = None
            
        # Init level
        self.game_map = GameMap(self.level)
        self.alarm_active = False
        self.alarm_timer = 0
        if self.siren_channel:
            sound_manager.stop_channel(self.siren_channel)
            self.siren_channel = None
        self.game_map.alarm_active = False
        self.game_map.parse_laser_lines()
        self.player.x, self.player.y = self.game_map.player_spawn
        
        self.bullet_manager = BulletManager()
        self.effect_manager = EffectManager()
        self.item_manager = ItemManager(self.game_map.item_spawns, self.level)
        self.enemy_manager = EnemyManager(self.game_map.enemy_spawns, self.level, self.game_map)
        self.hud.bake_minimap(self.game_map)
        
        self.state = "GAME"
        sound_manager.play_bg_music(track="combat")
        
        # ── Hiệu ứng đặc biệt khi vào Màn 6 (Hang Boss cuối) ────────────────
        if self.level == 6:
            # Tắt báo động cũ từ màn 5 nếu còn
            self.alarm_active = False
            if self.siren_channel:
                sound_manager.stop_channel(self.siren_channel)
                self.siren_channel = None
            # Hiệu ứng xuất hiện boss tại vị trí player
            import time
            boss_list = [e for e in self.enemy_manager.enemies if e.type == "boss"]
            if boss_list:
                b = boss_list[0]
                self.effect_manager.add_explosion(b.x, b.y, radius=180)
                self.effect_manager.add_floating_text(b.x, b.y - 60,
                    "☠ TRÙM CUỐI ĐÃ XUẤT HIỆN — CHIẾN ĐẤU ĐẾN HƠI THỞ CUỐI CÙNG! ☠", (255, 50, 50))
            self.effect_manager.add_floating_text(
                self.player.x, self.player.y - 60,
                "HANG TRÙM CUỐI — KHÔNG CÓ LỐI THOÁT!", (255, 200, 0))
            sound_manager.play('hurt')

        # ── Kích hoạt các màn hình điện ảnh trước màn chơi ─────────────────
        if new_campaign and self.level == 6:
            # Cutscene kịch tính + hội thoại trước trận boss cuối
            run_boss_cutscene(self.screen, self.clock)
            run_dialogue(self.screen, self.clock, LEVEL6_DIALOGUE, boss_name="KỶ NGUYÊN HỦY DIỆT")

        elif new_campaign and self.level == 5:
            run_dialogue(self.screen, self.clock, LEVEL5_DIALOGUE)

        elif new_campaign and self.level == 1:
            run_dialogue(self.screen, self.clock, LEVEL1_DIALOGUE)

    def run(self):
        # 1. Video intro (chỉ phát nếu file thực sự tồn tại để tránh lag)
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(base_dir, "ANH", "video_intro.mp4")
        if os.path.exists(video_path):
            play_video(self.screen, video_path)

        # Bật nhạc nền sảnh chờ (lobby) ngay sau intro video để phát xuyên suốt
        sound_manager.play_bg_music(track="lobby")

        # 2. Chữ chạy kiểu terminal (câu chuyện / nhiệm vụ)
        self.play_story_intro()

        # 3. Hội thoại điện ảnh giữa Ghost & Boss
        run_dialogue(self.screen, self.clock, LEVEL1_DIALOGUE)

        # 4. Màn hình chờ (Lobby) - ảnh nền + nhấp nháy chờ nhấn phím
        self.play_lobby_wait()

        # 5. Đảm bảo nhạc sảnh tiếp tục chạy mượt mà (không bị reset gián đoạn)
        sound_manager.play_bg_music(track="lobby")

        # 6. Vào vòng lặp chính của game
        while True:
            self.handle_events()
            self.update()
            self.draw()


    def play_story_intro(self):
        story_text = [
            "SYSTEM BOOT SEQUENCE INITIATED...",
            "CONNECTING TO SECURE MILITARY NETWORK... [OK]",
            "DECRYPTING MISSION BRIEFING... [OK]",
            "===========================================================",
            "",
            "ĐẶC NHIỆM — CHIẾN DỊCH ĐEN / OPERATION BLACK",
            "Tọa độ: KHÔNG XÁC ĐỊNH (Tối mật).",
            "",
            "TÌNH TRẠNG:",
            "> Ngươi là lính đặc nhiệm duy nhất còn sống sót sau trận phục kích.",
            "> Căn cứ chỉ huy đã bị phá hủy hoàn toàn.",
            "> Kẻ thù đang phong tỏa và lùng sục mọi lối thoát.",
            "",
            "MỤC TIÊU NHIỆM VỤ:",
            "1. Xâm nhập vào sâu trong sào huyệt của phe địch.",
            "2. Tiêu diệt toàn bộ các chỉ huy đầu sỏ.",
            "3. Thu thập nhu yếu phẩm để sinh tồn.",
            "",
            "LƯU Ý QUAN TRỌNG:",
            "- Không có viện binh. Không có đường lui.",
            "- Sử dụng kỹ năng Tập Trung (Q) và Lướt (SPACE) để sống sót.",
            "",
            "Sẵn sàng nạp đạn chưa, hỡi bóng ma?",
            "==========================================================="
        ]
        
        # Thử lấy font Consolas cho giống Terminal, nếu không có dùng font mặc định
        font = pygame.font.match_font("consolas")
        if font:
            term_font = pygame.font.Font(font, 22)
        else:
            term_font = pygame.font.SysFont("courier", 22, bold=True)
            
        running = True
        displayed_lines = []
        current_line_idx = 0
        current_char_idx = 0
        frame_count = 0
        
        last_typing_time = pygame.time.get_ticks()
        typing_speed = 35  # Tốc độ gõ (ms mỗi ký tự)
        
        # --- Hiệu ứng nền động ---
        radar_angle = 0.0
        particles = [{"x": random.randint(0, SCREEN_W), "y": random.randint(0, SCREEN_H), "speed": random.uniform(0.5, 2.0), "size": random.randint(1, 3)} for _ in range(80)]
        radar_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        # -------------------------
        
        while running:
            now = pygame.time.get_ticks()
            frame_count += 1
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                        running = False
                        
            # Kiểm tra nếu giữ phím mũi tên thì chạy nhanh hơn
            keys = pygame.key.get_pressed()
            is_speed_up = keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
            
            current_typing_speed = 5 if is_speed_up else typing_speed
            line_delay = 20 if is_speed_up else 150
            chars_per_step = 5 if is_speed_up else 1
            
            # Cập nhật logic gõ chữ
            if current_line_idx < len(story_text):
                line = story_text[current_line_idx]
                if now - last_typing_time > current_typing_speed:
                    current_char_idx = min(current_char_idx + chars_per_step, len(line))
                    
                    # Âm thanh gõ phím cơ học / bíp terminal nhạy bén (bỏ qua khoảng trắng)
                    # Giảm tần suất phát âm thanh khi tua nhanh để tránh ồn
                    sound_check = True
                    if is_speed_up:
                        sound_check = (frame_count % 4 == 0)
                    
                    if sound_check:
                        try:
                            # Phát âm thanh nếu ký tự hiện tại không phải khoảng trắng
                            if current_char_idx <= len(line):
                                char = line[current_char_idx - 1]
                                if char.strip():
                                    sound_manager.play("typing")
                        except: pass
                    
                    if current_char_idx >= len(line):
                        displayed_lines.append(line)
                        current_line_idx += 1
                        current_char_idx = 0
                        last_typing_time = now + line_delay # Dừng một chút giữa các dòng
                    else:
                        last_typing_time = now
                        
            # VẼ NỀN ĐỘNG
            self.screen.fill((4, 8, 4)) # Nền xanh tối
            
            # 2. Vòng quét Radar (Radar sweep)
            radar_surf.fill((0, 0, 0, 0))
            
            # 1. Hạt dữ liệu trôi nổi (Data particles)
            for p in particles:
                p["y"] -= p["speed"]
                if p["y"] < 0:
                    p["y"] = SCREEN_H + 10
                    p["x"] = random.randint(0, SCREEN_W)
                alpha = max(0, min(255, int(150 * math.sin(max(0, p["y"]) / SCREEN_H * math.pi))))
                pygame.draw.circle(radar_surf, (0, 180, 80, alpha), (int(p["x"]), int(p["y"])), p["size"])
                
            center_x, center_y = SCREEN_W // 2, SCREEN_H // 2
            r_max = 500
            
            # Vẽ các lưới vòng tròn mờ
            for r in (150, 300, 450):
                pygame.draw.circle(radar_surf, (0, 100, 40, 60), (center_x, center_y), r, 1)
            # Tia chữ thập mờ
            pygame.draw.line(radar_surf, (0, 100, 40, 40), (0, center_y), (SCREEN_W, center_y), 1)
            pygame.draw.line(radar_surf, (0, 100, 40, 40), (center_x, 0), (center_x, SCREEN_H), 1)
            
            # Tia quét xoay
            radar_angle += 0.02
            sweep_length = 0.6 # Độ dài vệt sáng (radian)
            for a in range(40):
                angle = radar_angle - (a/40.0) * sweep_length
                px = center_x + r_max * math.cos(angle)
                py = center_y + r_max * math.sin(angle)
                alpha = int(100 * (1 - a/40.0))
                pygame.draw.line(radar_surf, (0, 255, 100, alpha), (center_x, center_y), (px, py), 2)
                
            self.screen.blit(radar_surf, (0, 0))
            
            # Vẽ nền đen mờ đè lên để chữ hiển thị rõ ràng
            dark_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            dark_overlay.fill((0, 0, 0, 100))
            self.screen.blit(dark_overlay, (0, 0))
            # KẾT THÚC VẼ NỀN ĐỘNG
            
            start_y = 50
            margin_x = 60
            
            # Vẽ các dòng đã hoàn thành
            for i, dl in enumerate(displayed_lines):
                s = term_font.render(dl, True, (0, 255, 100))
                self.screen.blit(s, (margin_x, start_y + i * 26))
                
            # Vẽ dòng đang gõ
            if current_line_idx < len(story_text):
                current_text = story_text[current_line_idx][:current_char_idx]
                s = term_font.render(current_text, True, (0, 255, 100))
                self.screen.blit(s, (margin_x, start_y + current_line_idx * 26))
                
                # Con trỏ nhấp nháy
                if (now // 200) % 2 == 0:
                    cursor_x = margin_x + s.get_width() + 2
                    cursor_y = start_y + current_line_idx * 26 + 2
                    pygame.draw.rect(self.screen, (0, 255, 100), (cursor_x, cursor_y, 10, 20))
            else:
                # Xong chữ, hiển thị yêu cầu Enter nhấp nháy
                if (now // 500) % 2 == 0:
                    blink = term_font.render(">> NHẤN [ENTER] ĐỂ TRUY CẬP HỆ THỐNG VÀ VÀO SẢNH CHỜ...", True, (255, 255, 100))
                    self.screen.blit(blink, (margin_x, start_y + (len(story_text) + 2) * 26))
                    

            # Phủ hiệu ứng CRT màn hình cũ
            self.screen.blit(self.crt_surf, (0, 0))

            # Hiệu ứng Glitch (chớp sọc ngang)
            if random.random() < 0.05:
                glitch_y = random.randint(0, SCREEN_H)
                glitch_h = random.randint(2, 8)
                glitch_surf = pygame.Surface((SCREEN_W, glitch_h), pygame.SRCALPHA)
                glitch_surf.fill((0, 255, 100, 30))
                self.screen.blit(glitch_surf, (0, glitch_y))

            pygame.display.flip()
            self.clock.tick(60)

    def play_lobby_wait(self):
        """Màn hình chờ (Lobby) sau hội thoại - hiển thị ảnh nền + chữ nhấp nháy."""
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Thử load ảnh nền lobby
        bg_surf = None
        for fname in ["anhnen.png", "lobby_bg.png", "lobby_bg.jpg", "background.jpg", "background.png"]:
            p = os.path.join(base_dir, "ANH", fname)
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert()
                    bg_surf = pygame.transform.scale(img, (SCREEN_W + 60, SCREEN_H + 40))
                    break
                except: pass

        # Nếu không có ảnh thì vẽ nền gradient tối
        if bg_surf is None:
            bg_surf = pygame.Surface((SCREEN_W + 60, SCREEN_H + 40))
            for y in range(SCREEN_H + 40):
                t = y / (SCREEN_H + 40)
                r = int(10 + 10 * t)
                g = int(12 + 12 * t)
                b = int(15 + 15 * t)
                pygame.draw.line(bg_surf, (r, g, b), (0, y), (SCREEN_W + 60, y))

        # Fonts quân sự tối giản/sạch sẽ
        f_big   = pygame.font.SysFont("segoeui", 60, bold=True)
        f_mid   = pygame.font.SysFont("segoeui", 22, bold=True)
        f_small = pygame.font.SysFont("consolas", 14, bold=True)

        # 3D Parallax camera offsets
        bg_dx = 0.0
        bg_dy = 0.0

        # Muted Embers (Tàn lửa rất nhỏ và chậm)
        embers_3d = []
        for _ in range(60):
            embers_3d.append({
                "x": random.uniform(-SCREEN_W / 2, SCREEN_W / 2),
                "y": random.uniform(-SCREEN_H / 2, SCREEN_H / 2),
                "z": random.uniform(10, 800),
                "speed": random.uniform(1.0, 2.5),
                "color": (245, 165, 30), # Đồng bộ màu vàng cam cát ấm
                "size": random.uniform(1.0, 2.0)
            })

        running = True
        t0 = pygame.time.get_ticks()
        while running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

            # Camera Parallax
            mx, my = pygame.mouse.get_pos()
            target_dx = (mx - SCREEN_W / 2) * -0.04
            target_dy = (my - SCREEN_H / 2) * -0.04
            bg_dx += (target_dx - bg_dx) * 0.1
            bg_dy += (target_dy - bg_dy) * 0.1

            self.screen.blit(bg_surf, (-30 + bg_dx, -20 + bg_dy))

            # Overlay tối và dịu mắt (dùng surface pre-alloc)
            self.screen.blit(self.lobby_dark, (0, 0))

            # 2. Lưới Perspective 3D cực kỳ chìm (Muted Grid)
            grid_scroll = (pygame.time.get_ticks() / 20) % 1.0
            horizon_y = 520
            
            vanishing_x = SCREEN_W // 2 + int(bg_dx * 1.5)
            num_v_lines = 16
            for i in range(-num_v_lines // 2, num_v_lines // 2 + 1):
                start_x = vanishing_x
                start_y = horizon_y
                end_x = vanishing_x + i * 180
                end_y = SCREEN_H
                pygame.draw.line(self.screen, (30, 33, 35), (start_x, start_y), (end_x, end_y), 1)

            num_h_lines = 8
            for i in range(num_h_lines):
                y_pct = ((i - grid_scroll) / num_h_lines)
                if y_pct < 0:
                    y_pct += 1.0
                y_pos = horizon_y + (SCREEN_H - horizon_y) * (y_pct ** 2.5)
                brightness = y_pct * 0.25
                line_color = (int(150 * brightness), int(160 * brightness), int(170 * brightness))
                pygame.draw.line(self.screen, line_color, (0, int(y_pos)), (SCREEN_W, int(y_pos)), 1)

            # 3. Embers trôi nhẹ nhàng
            cx = SCREEN_W // 2
            cy = SCREEN_H // 2
            fov = 450
            
            # Dùng lobby_psurf pre-alloc, xóa mỗi frame bằng fill
            self.lobby_psurf.fill((0, 0, 0, 0))
            for p in embers_3d:
                p["z"] -= p["speed"]
                if p["z"] <= 10:
                    p["z"] = 800
                    p["x"] = random.uniform(-SCREEN_W / 2, SCREEN_W / 2)
                    p["y"] = random.uniform(-SCREEN_H / 2, SCREEN_H / 2)

                px = cx + (p["x"] / p["z"]) * fov + bg_dx * 0.2
                py = cy + (p["y"] / p["z"]) * fov + bg_dy * 0.2

                size = max(1, int(p["size"] * (800 / p["z"])))
                if size > 4:
                    size = 4

                if 0 <= px < SCREEN_W and 0 <= py < SCREEN_H:
                    # Vẽ trực tiếp, không cần alpha (đã có lobby_psurf làm buffer)
                    pygame.draw.circle(self.screen, p["color"], (int(px), int(py)), size)

            # Calculate dynamic 3D tilt offset
            tilt_x = int((mx - SCREEN_W / 2) / (SCREEN_W / 2) * 12)
            tilt_y = int((my - SCREEN_H / 2) / (SCREEN_H / 2) * 12)

            # 4. HUD Corner Brackets tối giản (1px)
            margin = 35
            blen = 20
            hud_col = (150, 160, 170)
            
            pygame.draw.line(self.screen, hud_col, (margin, margin), (margin + blen, margin), 1)
            pygame.draw.line(self.screen, hud_col, (margin, margin), (margin, margin + blen), 1)
            
            pygame.draw.line(self.screen, hud_col, (SCREEN_W - margin, margin), (SCREEN_W - margin - blen, margin), 1)
            pygame.draw.line(self.screen, hud_col, (SCREEN_W - margin, margin), (SCREEN_W - margin, margin + blen), 1)
            
            pygame.draw.line(self.screen, hud_col, (margin, SCREEN_H - margin), (margin + blen, SCREEN_H - margin), 1)
            pygame.draw.line(self.screen, hud_col, (margin, SCREEN_H - margin), (margin, SCREEN_H - margin - blen), 1)
            
            pygame.draw.line(self.screen, hud_col, (SCREEN_W - margin, SCREEN_H - margin), (SCREEN_W - margin - blen, SCREEN_H - margin), 1)
            pygame.draw.line(self.screen, hud_col, (SCREEN_W - margin, SCREEN_H - margin), (SCREEN_W - margin, SCREEN_H - margin - blen), 1)

            # 5. Draw 3D shadows and perspective lines for the floating telemetry panels directly to screen
            col_connect = (40, 52, 66)
            
            # Left panel shadow & lines
            sh_left_x, sh_left_y = margin + 10 - int(tilt_x * 0.5), margin + 30 - int(tilt_y * 0.5)
            fr_left_x, fr_left_y = margin + 10 + tilt_x, margin + 30 + tilt_y
            pygame.draw.rect(self.screen, (10, 15, 22, 100), (sh_left_x, sh_left_y, 250, 150), border_radius=2)
            pygame.draw.rect(self.screen, (40, 52, 70), (sh_left_x, sh_left_y, 250, 150), 1, border_radius=2)
            pygame.draw.line(self.screen, col_connect, (sh_left_x, sh_left_y), (fr_left_x, fr_left_y), 1)
            pygame.draw.line(self.screen, col_connect, (sh_left_x + 250, sh_left_y), (fr_left_x + 250, fr_left_y), 1)
            pygame.draw.line(self.screen, col_connect, (sh_left_x, sh_left_y + 150), (fr_left_x, fr_left_y + 150), 1)
            pygame.draw.line(self.screen, col_connect, (sh_left_x + 250, sh_left_y + 150), (fr_left_x + 250, fr_left_y + 150), 1)
            
            # Right panel shadow & lines
            sh_right_x, sh_right_y = SCREEN_W - margin - 260 - int(tilt_x * 0.5), margin + 30 - int(tilt_y * 0.5)
            fr_right_x, fr_right_y = SCREEN_W - margin - 260 + tilt_x, margin + 30 + tilt_y
            pygame.draw.rect(self.screen, (10, 15, 22, 100), (sh_right_x, sh_right_y, 250, 150), border_radius=2)
            pygame.draw.rect(self.screen, (40, 52, 70), (sh_right_x, sh_right_y, 250, 150), 1, border_radius=2)
            pygame.draw.line(self.screen, col_connect, (sh_right_x, sh_right_y), (fr_right_x, fr_right_y), 1)
            pygame.draw.line(self.screen, col_connect, (sh_right_x + 250, sh_right_y), (fr_right_x + 250, fr_right_y), 1)
            pygame.draw.line(self.screen, col_connect, (sh_right_x, sh_right_y + 150), (fr_right_x, fr_right_y + 150), 1)
            pygame.draw.line(self.screen, col_connect, (sh_right_x + 250, sh_right_y + 150), (fr_right_x + 250, fr_right_y + 150), 1)

            # 6. Create transparent surface for the 3D floating interface elements
            wait_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

            # Draw Left Telemetry Panel
            left_data = [
                "SYS.STATUS: SECURE CONNECT",
                "LOC: 10.7626 N / 106.6602 E",
                "SECTOR: ALPHA-5 (TACTICAL)",
                "ALTITUDE: 104M MSL",
                "SYS.RADAR: OPERATIONAL",
                "COMM LINK: ACTIVE"
            ]
            pygame.draw.rect(wait_surf, (10, 12, 14, 200), (margin + 10, margin + 30, 250, 150), border_radius=2)
            pygame.draw.rect(wait_surf, (150, 160, 170), (margin + 10, margin + 30, 250, 150), 1, border_radius=2)
            
            # Corner accents on Left panel
            size = 8
            pygame.draw.line(wait_surf, (245, 165, 30), (margin + 10, margin + 30), (margin + 10 + size, margin + 30), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (margin + 10, margin + 30), (margin + 10, margin + 30 + size), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (margin + 260, margin + 30), (margin + 260 - size, margin + 30), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (margin + 260, margin + 30), (margin + 260, margin + 30 + size), 1)
            
            for idx, text in enumerate(left_data):
                txt_surf = f_small.render(text, True, (150, 160, 170))
                wait_surf.blit(txt_surf, (margin + 20, margin + 40 + idx * 22))

            # Draw Right Telemetry Panel
            right_data = [
                "UNIT: GHOST OPERATIVE",
                "TACTICAL LOADOUT: ACTIVE",
                "BATTERY: 100% SECURE",
                "THREAT LEVEL: MODERATE",
                "SECURITY: EYES ONLY",
                "SYSTEMS: ONLINE"
            ]
            pygame.draw.rect(wait_surf, (10, 12, 14, 200), (SCREEN_W - margin - 260, margin + 30, 250, 150), border_radius=2)
            pygame.draw.rect(wait_surf, (150, 160, 170), (SCREEN_W - margin - 260, margin + 30, 250, 150), 1, border_radius=2)
            
            # Corner accents on Right panel
            pygame.draw.line(wait_surf, (245, 165, 30), (SCREEN_W - margin - 260, margin + 30), (SCREEN_W - margin - 260 + size, margin + 30), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (SCREEN_W - margin - 260, margin + 30), (SCREEN_W - margin - 260, margin + 30 + size), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (SCREEN_W - margin - 10, margin + 30), (SCREEN_W - margin - 10 - size, margin + 30), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (SCREEN_W - margin - 10, margin + 30), (SCREEN_W - margin - 10, margin + 30 + size), 1)
            
            for idx, text in enumerate(right_data):
                txt_col = (240, 70, 70) if "EYES ONLY" in text or "MODERATE" in text else (150, 160, 170)
                txt_surf = f_small.render(text, True, txt_col)
                wait_surf.blit(txt_surf, (SCREEN_W - margin - 250, margin + 40 + idx * 22))

            # ── 6. TIÊU ĐỀ CHÍNH — FLOAT + MULTI-LAYER GLOW ──────────────────
            elapsed = (now - t0) / 1000.0

            # Float animation: tiêu đề nổi lên/xuống nhẹ nhàng
            float_offset = math.sin(elapsed * 1.2) * 6
            ty_base = SCREEN_H // 2 - 100
            ty = int(ty_base + float_offset)
            title_text = "ĐẶC NHIỆM — CHIẾN DỊCH ĐEN"
            title_surf = f_big.render(title_text, True, (245, 165, 30))
            tx = SCREEN_W // 2 - title_surf.get_width() // 2

            # Glitch layer offset for Chromatic Aberration
            glitch_offset = 0
            if random.random() < 0.08:  # 8% chance to glitch/flicker
                glitch_offset = random.randint(-4, 4)
                
            pulse_val = math.sin(elapsed * 5) * 2
            cyan_offset = (int(pulse_val + glitch_offset), int(-pulse_val // 2))
            red_offset = (int(-pulse_val - glitch_offset), int(pulse_val // 2))

            # Draw Cyan Title Shadow
            cyan_title = f_big.render(title_text, True, (0, 240, 255))
            cyan_title.set_alpha(150)
            wait_surf.blit(cyan_title, (tx + cyan_offset[0], ty + cyan_offset[1]))

            # Draw Red Title Shadow
            red_title = f_big.render(title_text, True, (255, 30, 80))
            red_title.set_alpha(150)
            wait_surf.blit(red_title, (tx + red_offset[0], ty + red_offset[1]))

            # Glow layer 1 — hào quang rộng (blur effect bằng alpha)
            glow_pulse = 0.4 + 0.6 * abs(math.sin(elapsed * 1.8))
            for gx_off, gy_off, g_alpha in [
                (-4, -4, 18), (4, -4, 18), (-4, 4, 18), (4, 4, 18),
                (-2, 0, 30), (2, 0, 30), (0, -2, 30), (0, 2, 30)
            ]:
                g_col = (int(245 * glow_pulse), int(165 * glow_pulse * 0.7), 0)
                g_surf = f_big.render(title_text, True, g_col)
                g_surf.set_alpha(int(g_alpha * glow_pulse))
                wait_surf.blit(g_surf, (tx + gx_off, ty + gy_off))

            # Glow layer 2 — viền sắc nét hơn
            for gx_off, gy_off in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                g2 = f_big.render(title_text, True, (255, 200, 80))
                g2.set_alpha(int(60 * glow_pulse))
                wait_surf.blit(g2, (tx + gx_off, ty + gy_off))

            # Bóng tối
            shadow_s = f_big.render(title_text, True, (5, 5, 5))
            wait_surf.blit(shadow_s, (tx + 3, ty + 3))

            # Chữ chính
            wait_surf.blit(title_surf, (tx, ty))

            # ── 6b. PHỤ ĐỀ — WAVE COLOR (từng chữ đổi màu lần lượt) ──────────
            sub_text = "B A N   S Ú N G  //  TACTICAL SHOOTER"
            sub_y = ty + title_surf.get_height() + 8

            # Render từng ký tự với màu sóng
            char_surf_list = []
            total_w = 0
            for ci, ch in enumerate(sub_text):
                wave = math.sin(elapsed * 2.5 - ci * 0.3)
                r = int(120 + 80 * wave)
                g = int(140 + 60 * wave)
                b = int(170 + 50 * wave)
                r, g, b = max(60, min(255, r)), max(60, min(255, g)), max(60, min(255, b))
                ch_s = f_mid.render(ch, True, (r, g, b))
                char_surf_list.append(ch_s)
                total_w += ch_s.get_width()

            # Vẽ subtitle căn giữa
            cx_sub = SCREEN_W // 2 - total_w // 2
            for ci, cs in enumerate(char_surf_list):
                cy_wave = math.sin(elapsed * 3.0 - ci * 0.4) * 2
                sh = f_mid.render(sub_text[ci], True, (5, 5, 5))
                wait_surf.blit(sh, (cx_sub + 1, sub_y + cy_wave + 1))
                wait_surf.blit(cs, (cx_sub, sub_y + cy_wave))
                cx_sub += cs.get_width()

            # ── 6c. ĐƯỜNG PHÂN CÁCH — ĐỘ DÀI MẠCH ĐỔI ──────────────────────
            line_y = sub_y + f_mid.get_height() + 18
            line_w_max = 520
            line_w_anim = int(line_w_max * (0.7 + 0.3 * abs(math.sin(elapsed * 0.8))))
            lx = SCREEN_W // 2 - line_w_anim // 2
            # Glow line
            line_col_glow = (int(245 * glow_pulse * 0.5), int(165 * glow_pulse * 0.3), 0)
            pygame.draw.line(wait_surf, line_col_glow, (lx - 3, line_y), (lx + line_w_anim + 3, line_y), 3)
            pygame.draw.line(wait_surf, (245, 165, 30), (lx, line_y), (lx + line_w_anim, line_y), 1)
            pygame.draw.line(wait_surf, (245, 165, 30), (lx, line_y - 5), (lx, line_y + 5), 2)
            pygame.draw.line(wait_surf, (245, 165, 30), (lx + line_w_anim, line_y - 5), (lx + line_w_anim, line_y + 5), 2)
            
            # Hình thoi ở giữa đường
            mid_x = SCREEN_W // 2
            pts = [(mid_x, line_y - 5), (mid_x + 6, line_y), (mid_x, line_y + 5), (mid_x - 6, line_y)]
            pygame.draw.polygon(wait_surf, (245, 165, 30), pts)

            # ── 7. CHỮ HINT — BREATHING SCALE + GLOW ────────────────────────
            hint_pulse = 0.5 + 0.5 * math.sin(elapsed * 2.0)
            hint_txt = "[ NHẤN PHÍM BẤT KỲ ĐỂ BẮT ĐẦU ]"

            # Màu nhấp nháy: từ vàng đậm sang trắng vàng
            hr = int(200 + 55 * hint_pulse)
            hg = int(140 + 65 * hint_pulse)
            hb = int(10 + 40 * hint_pulse)
            hint_color = (hr, hg, hb)

            hint_surf = f_mid.render(hint_txt, True, hint_color)
            hx = SCREEN_W // 2 - hint_surf.get_width() // 2
            hy = int(line_y + 30)

            # Glow hint
            hint_glow = f_mid.render(hint_txt, True, (255, 200, 60))
            hint_glow.set_alpha(int(60 * hint_pulse))
            wait_surf.blit(hint_glow, (hx - 1, hy - 1))
            wait_surf.blit(hint_glow, (hx + 1, hy + 1))

            # Bóng chữ
            h_sh = f_mid.render(hint_txt, True, (5, 5, 5))
            wait_surf.blit(h_sh, (hx + 2, hy + 2))
            wait_surf.blit(hint_surf, (hx, hy))

            # ── 8. FOOTER — NHẤP NHÁY VÀ SÓNG ──────────────────────────────
            footer_txt = "PHÂN LOẠI: TỐI MẬT  ·  CHIẾN DỊCH ALPHA V2"
            f_blink = 0.5 + 0.5 * math.sin(elapsed * 3.5)
            fr = int(160 + 80 * f_blink)
            fg = int(40 * (1 - f_blink))
            fb = int(40 * (1 - f_blink))
            footer_surf = f_small.render(footer_txt, True, (fr, fg, fb))
            fx = SCREEN_W // 2 - footer_surf.get_width() // 2
            fy = SCREEN_H - 72
            # Glow đỏ
            f_glow = f_small.render(footer_txt, True, (200, 0, 0))
            f_glow.set_alpha(int(40 * f_blink))
            wait_surf.blit(f_glow, (fx - 1, fy))
            wait_surf.blit(f_glow, (fx + 1, fy))
            wait_surf.blit(footer_surf, (fx, fy))

            # Dòng version mờ
            ver_surf = f_small.render("v2.0  //  SPEC-OPS ENGINE", True, (80, 90, 100))
            wait_surf.blit(ver_surf, (SCREEN_W // 2 - ver_surf.get_width() // 2, SCREEN_H - 50))

            # Blit wait_surf with 3D tilt offset
            self.screen.blit(wait_surf, (tilt_x, tilt_y))

            # CRT Overlay
            self.screen.blit(self.crt_surf, (0, 0))

            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            # Track raw scancodes for WASD (bypass Unikey)
            if event.type == pygame.KEYDOWN:
                scancode = getattr(event, 'scancode', None)
                # Scancode-based (bypass Unikey)
                if scancode == 26: self.raw_keys["W"] = True
                elif scancode == 4: self.raw_keys["A"] = True
                elif scancode == 22: self.raw_keys["S"] = True
                elif scancode == 7: self.raw_keys["D"] = True
                elif scancode == 20: self.raw_keys["Q"] = True
                elif scancode == 21: self.raw_keys["R"] = True
                elif scancode == 10: self.raw_keys["G"] = True
                elif scancode in [225, 229]: self.raw_keys["LShift"] = True
                # Fallback: also track via event.key
                if event.key == pygame.K_w: self.raw_keys["W"] = True
                elif event.key == pygame.K_a: self.raw_keys["A"] = True
                elif event.key == pygame.K_s: self.raw_keys["S"] = True
                elif event.key == pygame.K_d: self.raw_keys["D"] = True
                elif event.key == pygame.K_q: self.raw_keys["Q"] = True
                elif event.key == pygame.K_r: self.raw_keys["R"] = True
                elif event.key == pygame.K_g: self.raw_keys["G"] = True
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT): self.raw_keys["LShift"] = True
                
            elif event.type == pygame.KEYUP:
                scancode = getattr(event, 'scancode', None)
                if scancode == 26: self.raw_keys["W"] = False
                elif scancode == 4: self.raw_keys["A"] = False
                elif scancode == 22: self.raw_keys["S"] = False
                elif scancode == 7: self.raw_keys["D"] = False
                elif scancode == 20: self.raw_keys["Q"] = False
                elif scancode == 21: self.raw_keys["R"] = False
                elif scancode == 10: self.raw_keys["G"] = False
                elif scancode in [225, 229]: self.raw_keys["LShift"] = False
                if event.key == pygame.K_w: self.raw_keys["W"] = False
                elif event.key == pygame.K_a: self.raw_keys["A"] = False
                elif event.key == pygame.K_s: self.raw_keys["S"] = False
                elif event.key == pygame.K_d: self.raw_keys["D"] = False
                elif event.key == pygame.K_q: self.raw_keys["Q"] = False
                elif event.key == pygame.K_r: self.raw_keys["R"] = False
                elif event.key == pygame.K_g: self.raw_keys["G"] = False
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT): self.raw_keys["LShift"] = False
                
            if self.state == "GAME":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    self.state = "PAUSE_SETTINGS"
                    if self.player:
                        self.in_game_settings.sync_with_player(self.player)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                    self.menu.state = "MAIN"
                    self.is_training = False
                    if self.siren_channel:
                        sound_manager.stop_channel(self.siren_channel)
                        self.siren_channel = None
                    sound_manager.play_bg_music(track="lobby")
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.ai_mode = not self.ai_mode
                    sound_manager.play('pickup')
                if self.ai_mode and event.type == pygame.KEYDOWN and (event.key == pygame.K_c or getattr(event, 'scancode', None) == 6):
                    # Cycle pathfinding algorithm: A* -> BFS -> DFS -> HEURISTIC -> A*
                    algos = ["A*", "BFS", "DFS", "HEURISTIC"]
                    curr = getattr(self.player, 'ai_algorithm', 'A*')
                    if curr not in algos:
                        curr = "A*"
                    next_idx = (algos.index(curr) + 1) % len(algos)
                    self.player.ai_algorithm = algos[next_idx]
                    sound_manager.play('pickup')
                    self.player.ai_bfs_timer = 0  # Recompute path immediately

            elif self.state == "PAUSE_SETTINGS":
                action = self.in_game_settings.handle_input(event, self.player, sound_manager)
                if action == "RESUME":
                    self.state = "GAME"
            elif self.state == "MENU":
                action = self.menu.handle_input(event)
                if action == "QUIT":
                    pygame.quit()
                    sys.exit()
                elif action == "START":
                    self.start_game(new_campaign=True)
                elif action == "TRAINING":
                    self.start_game(new_campaign=True, is_training=True)
                    
            elif self.state == "UPGRADE":
                done = self.upgrade_menu.handle_input(event, self.player)
                if done:
                    self.level += 1
                    if self.level > MAX_LEVEL:
                        self.state = "WIN"
                    else:
                        self.start_game(new_campaign=False)
                        
            elif self.state == "WIN":
                if (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    self.state = "MENU"
                    self.menu.state = "MAIN"
                    sound_manager.play_bg_music(track="lobby")
                    
            elif self.state == "GAMEOVER":
                # Nhấn Space/Click để chơi lại màn hiện tại, ESC để về Menu
                if (event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN)) or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    self.player.hp = self.player.max_hp
                    self.player.alive = True
                    self.start_game(new_campaign=False)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "MENU"
                    self.menu.state = "MAIN"
                    sound_manager.play_bg_music(track="lobby")

    def update(self):
        if self.state not in ["GAME", "PAUSE_SETTINGS"]:
            self.clock.tick(FPS)
            
        if self.state == "GAME":
            self.frame_counter = getattr(self, 'frame_counter', 0) + 1
            if hasattr(self, "_boss_alert_timer") and self._boss_alert_timer > 0:
                self._boss_alert_timer -= 1

            # Sync global alarm state
            if getattr(self, 'game_map', None) and getattr(self.game_map, 'alarm_active', False):
                self.alarm_active = True
            elif getattr(self, 'game_map', None):
                self.game_map.alarm_active = self.alarm_active

            # Check laser intersections
            if not self.alarm_active and getattr(self, 'game_map', None) and hasattr(self.game_map, 'laser_lines'):
                for laser in self.game_map.laser_lines:
                    if laser["active"]:
                        x1, y1 = laser["p1"]
                        x2, y2 = laser["p2"]
                        dx_l = x2 - x1
                        dy_l = y2 - y1
                        seg_len_sq = dx_l * dx_l + dy_l * dy_l
                        if seg_len_sq > 0:
                            t = max(0.0, min(1.0, ((self.player.x - x1) * dx_l + (self.player.y - y1) * dy_l) / seg_len_sq))
                            proj_x = x1 + t * dx_l
                            proj_y = y1 + t * dy_l
                            dist = math.hypot(self.player.x - proj_x, self.player.y - proj_y)
                            if dist < self.player.radius + 3:
                                if not getattr(self.player, 'is_dashing', False):
                                    self.alarm_active = True
                                    self.game_map.alarm_active = True

            # Alarm behavior and spawning reinforcements
            if self.alarm_active:
                if not self.siren_channel:
                    self.siren_channel = sound_manager.play_loop('siren')
                self.alarm_timer += 1
                if self.alarm_timer % ALARM_SPAWN_INTERVAL == 0:
                    W, H = self.game_map.width, self.game_map.height
                    spawn_tiles = []
                    for y in range(2, H - 2):
                        for x in (2, W - 3):
                            if self.game_map.grid[y][x] == TILE_EMPTY:
                                spawn_tiles.append((x, y))
                    for x in range(2, W - 2):
                        for y in (2, H - 3):
                            if self.game_map.grid[y][x] == TILE_EMPTY:
                                spawn_tiles.append((x, y))
                    
                    if spawn_tiles:
                        from enemy import Enemy
                        tx, ty = random.choice(spawn_tiles)
                        px = tx * TILE_SIZE + TILE_SIZE // 2
                        py = ty * TILE_SIZE + TILE_SIZE // 2
                        reinforcement = Enemy(px, py, "assault", self.level)
                        reinforcement.state = "HUNT"
                        reinforcement.last_player_pos = (self.player.x, self.player.y)
                        self.enemy_manager.enemies.append(reinforcement)
                        self.effect_manager.add_sparks(px, py, count=8)
            # Input
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            
            # Pass raw_keys to player instead of just keys
            keys_dict = {"pygame_keys": keys, "raw_keys": self.raw_keys}
            
            # Update systems
            if self.ai_mode and self.player:
                # Ở chế độ AI thì Boss và AI tự tìm nhau
                for e in self.enemy_manager.enemies:
                    if e.alive and e.type == "boss":
                        e.force_hunt = True
                self.player.ai_update(
                    self.enemy_manager.enemies,
                    self.item_manager.items,
                    self.game_map,
                    self.bullet_manager,
                    self.effect_manager,
                    sound_manager,
                    self.bullet_manager.bullets
                )
            else:
                self.player.update(keys_dict, mouse_pos, self.cam_x, self.cam_y,
                                   self.game_map, self.bullet_manager,
                                   self.effect_manager, sound_manager,
                                   self.enemy_manager.enemies)

            
            # Clear noises at start of frame
            self.game_map.active_noises.clear()
            
            # Update game map ticking leaking barrels
            exploded_barrels = self.game_map.update(self.effect_manager, sound_manager)
            
            self.enemy_manager.update(self.player, self.game_map, 
                                      self.bullet_manager, self.effect_manager, 
                                      sound_manager)
            
            exploded_grenades = self.bullet_manager.update(self.game_map, self.effect_manager, sound_manager)
            
            # Append exploded barrels to exploded_grenades list
            for bx, by in exploded_barrels:
                exploded_grenades.append((bx, by, "FRAG"))
                sound_manager.play('explosion')
                self.effect_manager.add_explosion(bx, by, radius=120)
                self.game_map.add_noise(bx, by, 800)
                
            # Process chain reaction for barrels in range of FRAG explosions
            queue = list(exploded_grenades)
            detonated_barrels = set()
            processed_explosions = []
            while queue:
                ex_x, ex_y, g_type = queue.pop(0)
                processed_explosions.append((ex_x, ex_y, g_type))
                
                if g_type == "FRAG":
                    for ty in range(self.game_map.height):
                        for tx in range(self.game_map.width):
                            if self.game_map.grid[ty][tx] == TILE_BARREL:
                                if (tx, ty) not in detonated_barrels:
                                    bx = tx * TILE_SIZE + TILE_SIZE // 2
                                    by = ty * TILE_SIZE + TILE_SIZE // 2
                                    if math.hypot(ex_x - bx, ex_y - by) < GRENADE_RADIUS:
                                        detonated_barrels.add((tx, ty))
                                        self.game_map.grid[ty][tx] = TILE_EMPTY
                                        self.game_map.cover_hp.pop((tx, ty), None)
                                        self.game_map.leaking_barrels.pop((tx, ty), None)
                                        self.game_map.redraw_tile_floor(tx, ty)
                                        self.game_map.minimap_dirty = True
                                        
                                        queue.append((bx, by, "FRAG"))
                                        sound_manager.play('explosion')
                                        self.effect_manager.add_explosion(bx, by, radius=120)
                                        self.game_map.add_noise(bx, by, 800)
            exploded_grenades = processed_explosions
            self.item_manager.update(self.player)
            self.effect_manager.update()
            self.effect_manager.update_ambient(self.cam_x, self.cam_y, self.level)
            
            if self.game_map.minimap_dirty:
                self.hud.bake_minimap(self.game_map)
                self.game_map.minimap_dirty = False
            
            # ── Slow Motion Update ──────────────────────────────────────────
            if self.player.is_focusing:
                self.clock.tick(int(FPS * TIME_SLOW_FACTOR))
            else:
                self.clock.tick(FPS)
            # Override standard tick at end of loop, so we remove it from there
            
            # Check bullet collisions with entities
            for b in self.bullet_manager.bullets:
                if b.is_enemy:
                    # Check player
                    dist = math.hypot(b.x - self.player.x, b.y - self.player.y)
                    if dist < self.player.radius + 2:
                        self.player.take_damage(b.damage, self.effect_manager, sound_manager)
                        b.alive = False
                else:
                    # Check enemies
                    for e in self.enemy_manager.enemies:
                        dist = math.hypot(b.x - e.x, b.y - e.y)
                        if dist < e.radius + 2:
                            old_alive = e.alive
                            e.take_damage(b.damage, self.effect_manager, sound_manager)
                            if old_alive and not e.alive and not getattr(self, 'is_training', False):
                                self.item_manager.items.append(Item(e.x, e.y, ITEM_GOLD))
                            b.alive = False
                            break
                            
                    if b.alive and hasattr(self.enemy_manager, 'cameras'):
                        for c in self.enemy_manager.cameras:
                            dist = math.hypot(b.x - c.x, b.y - c.y)
                            if dist < c.radius + 2:
                                c.take_damage(b.damage, self.effect_manager, sound_manager)
                                b.alive = False
                                break
                            
            # Check explosion damage
            for ex_x, ex_y, g_type in exploded_grenades:
                if g_type == "FRAG":
                    # Player
                    dist = math.hypot(ex_x - self.player.x, ex_y - self.player.y)
                    if dist < GRENADE_RADIUS:
                        dmg = int(GRENADE_DAMAGE * (1 - dist/GRENADE_RADIUS))
                        self.player.take_damage(dmg, self.effect_manager, sound_manager)
                    # Enemies
                    for e in self.enemy_manager.enemies:
                        dist = math.hypot(ex_x - e.x, ex_y - e.y)
                        if dist < GRENADE_RADIUS:
                            dmg = int(GRENADE_DAMAGE * (1 - dist/GRENADE_RADIUS))
                            old_alive = e.alive
                            e.take_damage(dmg, self.effect_manager, sound_manager)
                            if old_alive and not e.alive and not getattr(self, 'is_training', False):
                                self.item_manager.items.append(Item(e.x, e.y, ITEM_GOLD))
                elif g_type == "FLASH":
                    # Player screen shake
                    dist = math.hypot(ex_x - self.player.x, ex_y - self.player.y)
                    if dist < GRENADE_RADIUS * 1.5:
                        self.effect_manager.shake.trigger(12, 15)
                    # Stun enemies
                    for e in self.enemy_manager.enemies:
                        dist = math.hypot(ex_x - e.x, ex_y - e.y)
                        if dist < GRENADE_RADIUS * 1.5:
                            e.stun_timer = 240 # 4 giây choáng
                            for _ in range(8):
                                angle = random.uniform(0, math.pi*2)
                                spd = random.uniform(1, 3)
                                self.effect_manager.particles.append(Particle(
                                    e.x, e.y, math.cos(angle)*spd, math.sin(angle)*spd,
                                    (0, 180, 255), random.randint(2, 4), 30))

            # Sát thương từ các vùng lửa trên mặt đất
            for fp in self.effect_manager.fire_pools:
                if fp.lifetime % 10 == 0:
                    # Player
                    dist = math.hypot(fp.x - self.player.x, fp.y - self.player.y)
                    if dist < fp.radius:
                        self.player.take_damage(3, self.effect_manager, sound_manager)
                    # Enemies
                    for e in self.enemy_manager.enemies:
                        dist = math.hypot(fp.x - e.x, fp.y - e.y)
                        if dist < fp.radius:
                            old_alive = e.alive
                            e.take_damage(5, self.effect_manager, sound_manager)
                            if old_alive and not e.alive and not getattr(self, 'is_training', False):
                                self.item_manager.items.append(Item(e.x, e.y, ITEM_GOLD))
                            
            # Sát thương từ các thùng rò rỉ (leaking barrels)
            if self.frame_counter % 10 == 0:
                for (tx, ty) in list(self.game_map.leaking_barrels.keys()):
                    bx = tx * TILE_SIZE + TILE_SIZE // 2
                    by = ty * TILE_SIZE + TILE_SIZE // 2
                    # Player
                    if math.hypot(bx - self.player.x, by - self.player.y) < 64:
                        self.player.take_damage(3, self.effect_manager, sound_manager)
                    # Enemies
                    for e in self.enemy_manager.enemies:
                        if math.hypot(bx - e.x, by - e.y) < 64:
                            old_alive = e.alive
                            e.take_damage(5, self.effect_manager, sound_manager)
                            if old_alive and not e.alive and not getattr(self, 'is_training', False):
                                self.item_manager.items.append(Item(e.x, e.y, ITEM_GOLD))

            # Check items
            picked = self.item_manager.check_pickup(self.player)
            for item in picked:
                sound_manager.play('pickup')
                heal, ammo, armor, gre, gold = item.get_effect()
                self.player.heal(heal)
                self.player.ammo += ammo
                self.player.max_armor += armor
                self.player.armor += armor
                self.player.grenades += gre
                self.gold += gold
                
            # Logic riêng cho Map 5: Thông báo lối thoát mở khi diệt sạch địch
            if self.level == 5:
                if len(self.enemy_manager.enemies) == 0:
                    if not getattr(self, 'exit_opened_notified', False):
                        self.exit_opened_notified = True
                        sound_manager.play('pickup')
                        self.effect_manager.add_floating_text(self.player.x, self.player.y - 40, "ĐÃ TIÊU DIỆT CÁC CHỈ HUY! HÃY TÌM LỐI THOÁT ĐỂ ĐẾN HANG TRÙM CUỐI!", (255, 200, 0))
                
            # Logic riêng cho Map 6: Solo Boss 5
            if self.level == 6:
                if len(self.enemy_manager.enemies) == 0:
                    if self.siren_channel:
                        sound_manager.stop_channel(self.siren_channel)
                        self.siren_channel = None
                    self.state = "WIN"
                    if hasattr(self, 'win_timer'):
                        delattr(self, 'win_timer')
                
            # Update camera
            target_cx = self.player.x - SCREEN_W / 2
            target_cy = self.player.y - SCREEN_H / 2
            # Clamp to map bounds
            target_cx = max(0, min(target_cx, self.game_map.pixel_w - SCREEN_W))
            target_cy = max(0, min(target_cy, self.game_map.pixel_h - SCREEN_H))
            
            # Smooth follow
            self.cam_x += (target_cx - self.cam_x) * 0.1
            self.cam_y += (target_cy - self.cam_y) * 0.1
            
            # Check level complete (Touch exit door)
            px, py = int(self.player.x // TILE_SIZE), int(self.player.y // TILE_SIZE)
            if self.game_map.get_tile(px, py) == TILE_EXIT:
                if getattr(self, 'is_training', False):
                    # Trong chế độ tập huấn, thoát cửa = về menu
                    sound_manager.play('pickup')
                    self.state = "MENU"
                    self.menu.state = "MAIN"
                    self.is_training = False
                    sound_manager.play_bg_music(track="lobby")
                else:
                    boss_alive = any(e.type == "boss" for e in self.enemy_manager.enemies)
                    if boss_alive:
                        if not hasattr(self, "_boss_alert_timer") or self._boss_alert_timer <= 0:
                            self._boss_alert_timer = 90  # 1.5 giây cảnh báo
                            sound_manager.play('hurt')
                        for e in self.enemy_manager.enemies:
                            if e.alive and e.type == "boss":
                                e.force_hunt = True
                    else:
                        sound_manager.play('pickup')
                        if self.siren_channel:
                            sound_manager.stop_channel(self.siren_channel)
                            self.siren_channel = None
                        if self.level >= MAX_LEVEL:
                            self.state = "WIN"
                            if hasattr(self, 'win_timer'):
                                delattr(self, 'win_timer')
                        else:
                            self.upgrade_menu.roll_choices()
                            self.state = "UPGRADE"
                
            # Check game over
            if self.player.hp <= 0:
                if self.ai_mode or getattr(self, 'is_training', False):
                    # AI mode / Training: không bao giờ game over, hồi máu
                    self.player.hp = self.player.max_hp
                    self.player.alive = True
                    self.effect_manager.add_floating_text(self.player.x, self.player.y - 40, "BẤT TỬ!", (0, 255, 200))
                else:
                    self.state = "GAMEOVER"
                    if self.siren_channel:
                        sound_manager.stop_channel(self.siren_channel)
                        self.siren_channel = None

    def draw(self):
        if self.state == "MENU":
            self.menu.draw(self.screen)
            
        elif self.state in ("GAME", "UPGRADE", "GAMEOVER", "WIN", "PAUSE_SETTINGS"):
            self.screen.fill(BLACK)
            
            # Apply Screen Shake to Camera
            cam_draw_x, cam_draw_y = self.effect_manager.shake.apply(self.cam_x, self.cam_y)
            
            # Draw game objects
            self.game_map.draw(self.screen, cam_draw_x, cam_draw_y)
            
            # Draw Laser lines (Optimized & Glowing Neon)
            if hasattr(self.game_map, 'laser_lines'):
                self.overlay_surf.fill((0, 0, 0, 0))
                pulse = int(140 + 80 * math.sin(pygame.time.get_ticks() / 80.0))
                has_active_lasers = False
                
                for laser in self.game_map.laser_lines:
                    if laser["active"]:
                        has_active_lasers = True
                        p1_x, p1_y = laser["p1"]
                        p2_x, p2_y = laser["p2"]
                        draw_p1 = (int(p1_x - cam_draw_x), int(p1_y - cam_draw_y))
                        draw_p2 = (int(p2_x - cam_draw_x), int(p2_y - cam_draw_y))
                        
                        # Neon glow outer beam (thick, translucent)
                        pygame.draw.line(self.overlay_surf, (255, 0, 0, pulse // 3), draw_p1, draw_p2, 10)
                        # Neon glow mid beam
                        pygame.draw.line(self.overlay_surf, (255, 30, 30, pulse // 2), draw_p1, draw_p2, 6)
                        # Intense core beam (thin, more solid)
                        pygame.draw.line(self.overlay_surf, (255, 80, 80, pulse), draw_p1, draw_p2, 3)
                
                if has_active_lasers:
                    self.screen.blit(self.overlay_surf, (0, 0))
                    
                # Draw the fine inner white-hot filament on main screen directly
                for laser in self.game_map.laser_lines:
                    if laser["active"]:
                        p1_x, p1_y = laser["p1"]
                        p2_x, p2_y = laser["p2"]
                        draw_p1 = (int(p1_x - cam_draw_x), int(p1_y - cam_draw_y))
                        draw_p2 = (int(p2_x - cam_draw_x), int(p2_y - cam_draw_y))
                        pygame.draw.line(self.screen, (255, 220, 220), draw_p1, draw_p2, 1)
            self.item_manager.draw(self.screen, cam_draw_x, cam_draw_y)
            self.enemy_manager.draw(self.screen, cam_draw_x, cam_draw_y)
            self.player.draw(self.screen, cam_draw_x, cam_draw_y)
            self.bullet_manager.draw(self.screen, cam_draw_x, cam_draw_y)
            self.effect_manager.draw(self.screen, cam_draw_x, cam_draw_y, self.level)
            
            # ── BFS Pathfinding Line (The Quest Path) ──────────────────────────
            # Target the boss if alive, otherwise target the exit
            path = None
            bosses = [e for e in self.enemy_manager.enemies if getattr(e, 'type', '') == 'boss' and e.alive]
            if bosses:
                boss_targets = [(int(e.x), int(e.y)) for e in bosses]
                if hasattr(self.game_map, 'find_path_to_point_list'):
                    path = self.game_map.find_path_to_point_list(self.player.x, self.player.y, boss_targets, algorithm="BFS")
            else:
                path = self.game_map.find_path_bfs(self.player.x, self.player.y, TILE_EXIT)
            if path and len(path) > 1:
                points = []
                for tx, ty in path:
                    px = tx * TILE_SIZE + TILE_SIZE // 2 - cam_draw_x
                    py = ty * TILE_SIZE + TILE_SIZE // 2 - cam_draw_y
                    points.append((px, py))
                
                # Draw neon path line with pulse effect
                pulse = int(100 + 50 * math.sin(pygame.time.get_ticks() / 200))
                color = (0, 255, 255, pulse) # Cyan neon
                
                if len(points) >= 2:
                    # Dùng self.path_surf pre-alloc
                    self.path_surf.fill((0, 0, 0, 0))
                    pygame.draw.lines(self.path_surf, color, False, points, 3)
                    self.screen.blit(self.path_surf, (0, 0))
            
            # ── Emergency Paths (Health/Ammo) ──────────────────────────────────
            emergency_paths = []
            
            # 1. Health Path (if < 50%)
            if self.player.hp < self.player.max_hp * 0.5:
                h_targets = [(item.x, item.y) for item in self.item_manager.items if item.type == ITEM_HEALTH]
                if h_targets:
                    h_path = self.game_map.find_path_to_point_list(self.player.x, self.player.y, h_targets)
                    if h_path: emergency_paths.append((h_path, (255, 50, 50))) # Bright Red
            
            # 2. Ammo Path (if 0 ammo)
            if self.player.ammo <= 0:
                a_targets = [(item.x, item.y) for item in self.item_manager.items if item.type == ITEM_AMMO]
                if a_targets:
                    a_path = self.game_map.find_path_to_point_list(self.player.x, self.player.y, a_targets)
                    if a_path: emergency_paths.append((a_path, (255, 200, 0))) # Bright Orange/Yellow
                    
            for path, color in emergency_paths:
                if path and len(path) > 1:
                    pts = []
                    for tx, ty in path:
                        pts.append((tx * TILE_SIZE + TILE_SIZE // 2 - cam_draw_x, 
                                    ty * TILE_SIZE + TILE_SIZE // 2 - cam_draw_y))
                    
                    # Vẽ đường trực tiếp (không cần alpha surface)
                    pygame.draw.lines(self.screen, color, False, pts, 5)
                    pygame.draw.lines(self.screen, (255,255,255), False, pts, 2)
            # ──────────────────────────────────────────────────────────────────
            
            # ── Fog of War with Flashlight Effect (dùng pre-alloc surfaces) ──
            if self.level not in (3,):
                base_alpha = 110 if self.level == 5 else (130 if self.level == 2 else 160)
                self.fog_surf.fill((0, 0, 0, base_alpha))

                player_screen_x = int(self.player.x - cam_draw_x)
                player_screen_y = int(self.player.y - cam_draw_y)

                # 1. Ambient circle — dùng pre-computed gradient
                ar = self._fog_ambient_radius
                self.fog_surf.blit(self.fog_ambient_grad,
                    (player_screen_x - ar, player_screen_y - ar),
                    special_flags=pygame.BLEND_RGBA_MIN)

                # 2. Flashlight Cone
                if self.ai_mode and self.player:
                    angle = self.player.angle
                else:
                    mx, my = pygame.mouse.get_pos()
                    angle = math.atan2(my - player_screen_y, mx - player_screen_x)

                cone_length = 500
                cone_spread = 0.5
                cone_points = [
                    (player_screen_x, player_screen_y),
                    (player_screen_x + math.cos(angle - cone_spread) * cone_length,
                     player_screen_y + math.sin(angle - cone_spread) * cone_length),
                    (player_screen_x + math.cos(angle) * cone_length * 1.1,
                     player_screen_y + math.sin(angle) * cone_length * 1.1),
                    (player_screen_x + math.cos(angle + cone_spread) * cone_length,
                     player_screen_y + math.sin(angle + cone_spread) * cone_length)
                ]
                pygame.draw.polygon(self.fog_surf, (0, 0, 0, 0), cone_points, 0)

                # Re-blit ambient để đảm bảo vùng trung tâm sáng
                self.fog_surf.blit(self.fog_ambient_grad,
                    (player_screen_x - ar, player_screen_y - ar),
                    special_flags=pygame.BLEND_RGBA_MIN)

                self.screen.blit(self.fog_surf, (0, 0))
            # ──────────────────────────────────────────────────────────────────────
            
            # ── Red Alert Vignette Overlay ──────────────────────────────────────
            if self.alarm_active:
                pulse = abs(math.sin(pygame.time.get_ticks() / 150.0))
                overlay_alpha = int(40 + 45 * pulse)
                vignette_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                for thick in range(1, 20, 2):
                    alpha = int(overlay_alpha * (1 - thick / 20.0))
                    pygame.draw.rect(vignette_surf, (255, 0, 0, alpha), (thick, thick, SCREEN_W - thick*2, SCREEN_H - thick*2), 2)
                self.screen.blit(vignette_surf, (0, 0))

            # Draw HUD
            self.hud.draw(self.screen, self.player, self.level, self.game_map, self.enemy_manager.enemies, self.item_manager.items)
            
            # ── Boss HUD lớn (Màn 6) ─────────────────────────────────────────
            if self.level == 6 and self.enemy_manager:
                for e in self.enemy_manager.enemies:
                    if e.alive and e.type == "boss":
                        self.hud.draw_boss_hud(self.screen, e)
                        break

            # ── WARNING BANNER IF BOSS IS HUNTING ────────────────────────────
            boss_hunting = False
            boss_fast_hunting = False
            if self.enemy_manager:
                for e in self.enemy_manager.enemies:
                    if e.alive and e.type == "boss":
                        if getattr(e, 'boss_state', 'PATROL') == 'HUNT':
                            boss_hunting = True
                        if getattr(e, 'force_hunt', False):
                            boss_fast_hunting = True
            
            # Màn 6 không cần banner boss hunting (đã có Boss HUD riêng ở trên)
            if boss_hunting and self.level != 6:
                pulse = abs(math.sin(pygame.time.get_ticks() / 150))
                # Red flashing warning box at the top
                warn_w = 480
                warn_h = 52
                self.warn_surf.fill((0, 0, 0, 0)) # clear
                pygame.draw.rect(self.warn_surf, (20, 5, 5, 200), (0, 0, warn_w, warn_h), border_radius=8)
                pygame.draw.rect(self.warn_surf, (255, 30, 30, int(150 + 105 * pulse)), (0, 0, warn_w, warn_h), 2, border_radius=8)
                self.screen.blit(self.warn_surf, (SCREEN_W // 2 - warn_w // 2, 60))
                
                # Flashing text
                msg = "CẢNH BÁO: BOSS ĐANG TRUY KÍCH SIÊU TỐC!" if boss_fast_hunting else "CẢNH BÁO: BOSS ĐANG TRUY KÍCH BẠN!"
                warn_text = self.font_normal.render(msg, True, (255, 255, 255))
                self.screen.blit(warn_text, (SCREEN_W // 2 - warn_text.get_width() // 2, 60 + (warn_h - warn_text.get_height()) // 2))

            # ── CẢNH BÁO LỐI THOÁT BỊ KHOÁ ──────────────────────────────────────
            if getattr(self, "_boss_alert_timer", 0) > 0:
                pulse = abs(math.sin(pygame.time.get_ticks() / 80))
                alert_w = 660
                alert_h = 52
                self.alert_surf.fill((0, 0, 0, 0)) # clear
                pygame.draw.rect(self.alert_surf, (20, 5, 5, 200), (0, 0, alert_w, alert_h), border_radius=8)
                pygame.draw.rect(self.alert_surf, (255, 30, 30, int(150 + 105 * pulse)), (0, 0, alert_w, alert_h), 2, border_radius=8)
                self.screen.blit(self.alert_surf, (SCREEN_W // 2 - alert_w // 2, 120))
                
                alert_text = self.font_normal.render("LỐI THOÁT KHÓA! TIÊU DIỆT BOSS ĐỂ MỞ KHOÁ QUA MÀN!", True, (255, 255, 255))
                self.screen.blit(alert_text, (SCREEN_W // 2 - alert_text.get_width() // 2, 120 + (alert_h - alert_text.get_height()) // 2))

            # ── ĐÈ VÒNG CẢNH BÁO KHÓA LÊN LỐI THOÁT ──────────────────────────────
            boss_alive = any(e.type == "boss" for e in self.enemy_manager.enemies) if self.enemy_manager else False
            if boss_alive and hasattr(self.game_map, "exit_px"):
                ex = self.game_map.exit_px - cam_draw_x
                ey = self.game_map.exit_py - cam_draw_y
                
                # Vẽ vòng đỏ nhấp nháy
                pygame.draw.circle(self.screen, (255, 0, 0), (int(ex), int(ey)), 28, 3)
                
                # Vẽ chữ LOCKED nhỏ màu đỏ
                font_exit = pygame.font.SysFont("arial", 12, bold=True)
                exit_lbl = font_exit.render("LOCKED", True, (255, 80, 80))
                self.screen.blit(exit_lbl, (int(ex - exit_lbl.get_width()//2), int(ey + 22)))

            # ── AI MODE INDICATOR + PATH DRAW ──────────────────────────────────
            if self.ai_mode:
                import time as _time
                pulse = abs(math.sin(_time.time() * 4))

                # Draw AI BFS path on screen
                ai_path = getattr(self.player, 'ai_bfs_path', [])
                mode    = getattr(self.player, 'ai_mode_label', 'GREEN')
                path_colors = {"RED":(255,60,60), "YELLOW":(255,200,0),
                               "GREEN":(0,255,100), "CYAN":(0,220,255)}
                pcol = path_colors.get(mode, (0,255,100))
                if ai_path:
                    pts = [(self.player.x - cam_draw_x, self.player.y - cam_draw_y)] + [
                        (px - cam_draw_x, py - cam_draw_y) for px, py in ai_path
                    ]
                    # Vẽ AI path trực tiếp, không cần Surface
                    pygame.draw.lines(self.screen, pcol, False, pts, 5)
                    pygame.draw.lines(self.screen, (255, 255, 255), False, pts, 2)
                    # Circle at next waypoint
                    wpx, wpy = ai_path[0]
                    wpx -= cam_draw_x
                    wpy -= cam_draw_y
                    pygame.draw.circle(self.screen, pcol, (int(wpx), int(wpy)), 8, 3)

                # Banner layout using pre-allocated Surface for true alpha transparency
                bar_w, bar_h = 560, 64
                self.ai_banner_surf.fill((0, 0, 0, 0))
                
                # Semi-transparent dark background for readability
                pygame.draw.rect(self.ai_banner_surf, (10, 15, 20, 200), (0, 0, bar_w, bar_h), border_radius=8)
                
                # Pulse glow border
                border_glow_alpha = int(140 + 70 * pulse)
                pygame.draw.rect(self.ai_banner_surf, (*pcol, border_glow_alpha), (0, 0, bar_w, bar_h), 2, border_radius=8)
                
                # Corner HUD brackets in state color (pcol)
                cl = 12 # bracket length
                # Top-Left
                pygame.draw.line(self.ai_banner_surf, pcol, (0, 0), (cl, 0), 4)
                pygame.draw.line(self.ai_banner_surf, pcol, (0, 0), (0, cl), 4)
                # Top-Right
                pygame.draw.line(self.ai_banner_surf, pcol, (bar_w, 0), (bar_w - cl, 0), 4)
                pygame.draw.line(self.ai_banner_surf, pcol, (bar_w, 0), (bar_w, cl), 4)
                # Bottom-Left
                pygame.draw.line(self.ai_banner_surf, pcol, (0, bar_h), (cl, bar_h), 4)
                pygame.draw.line(self.ai_banner_surf, pcol, (0, bar_h), (0, bar_h - cl), 4)
                # Bottom-Right
                pygame.draw.line(self.ai_banner_surf, pcol, (bar_w, bar_h), (bar_w - cl, bar_h), 4)
                pygame.draw.line(self.ai_banner_surf, pcol, (bar_w, bar_h), (bar_w, bar_h - cl), 4)
                
                # Pulse status dot
                dot_col = pcol if pulse > 0.4 else (60, 60, 60)
                pygame.draw.circle(self.ai_banner_surf, dot_col, (24, 20), 6)
                
                # Mode label mapping (Vietnamese with rich details)
                mode_labels = {"RED": "TÌM MÁU CẤP CỨU", "YELLOW": "TÌM ĐẠN DỰ TRỮ",
                               "GREEN": "TẤN CÔNG TRUY SÁT", "CYAN": "DI CHUYỂN QUA MÀN"}
                mode_str = mode_labels.get(mode, "TỰ ĐỘNG CHƠI")
                
                # Get current algorithm
                algo = getattr(self.player, 'ai_algorithm', 'A*')
                algo_desc = {
                    "BFS": "BFS (Đường Đi Ngắn Nhất)",
                    "DFS": "DFS (Tìm Kiếm Chiều Sâu)",
                    "A*": "A* (Tối Ưu Hóa Chi Phí)",
                    "HEURISTIC": "Greedy Best-First (Ước Lượng)"
                }.get(algo, algo)
                
                # Render text in high-contrast colors (white and state color)
                # Title text
                title_txt = self.font_small.render("HỆ THỐNG AI TỰ ĐỘNG", True, (200, 220, 255))
                self.ai_banner_surf.blit(title_txt, (40, 10))
                
                # State Text
                state_lbl = self.font_small.render("MỤC TIÊU: ", True, (150, 150, 150))
                self.ai_banner_surf.blit(state_lbl, (40, 30))
                state_val = self.font_small.render(mode_str, True, pcol)
                self.ai_banner_surf.blit(state_val, (40 + state_lbl.get_width(), 30))
                
                # Algorithm Text
                algo_lbl = self.font_small.render("THUẬT TOÁN: ", True, (150, 150, 150))
                self.ai_banner_surf.blit(algo_lbl, (290, 10))
                algo_val = self.font_small.render(algo_desc, True, (255, 215, 0)) # Gold/Yellow
                self.ai_banner_surf.blit(algo_val, (290 + algo_lbl.get_width(), 10))
                
                # Control Helper text
                control_txt = self.font_small.render("[C] ĐỔI THUẬT TOÁN  |  [SPACE] TẮT AI", True, (220, 220, 220))
                self.ai_banner_surf.blit(control_txt, (290, 32))
                
                # Blit the banner surface to the center top of screen
                self.screen.blit(self.ai_banner_surf, (SCREEN_W // 2 - bar_w // 2, 8))
            else:
                hint = self.font_small.render("[SPACE] BẬT AI TỰ CHƠI", True, (100, 100, 100))
                self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 14))

            if self.state == "UPGRADE":
                self.upgrade_menu.draw(self.screen)
                
            elif self.state == "GAMEOVER":
                # Dark overlay (pre-alloc)
                self.overlay_surf.fill((100, 0, 0, 150))
                self.screen.blit(self.overlay_surf, (0, 0))
                
                txt = self.font_title.render("NHIỆM VỤ THẤT BẠI", True, WHITE)
                sub1 = self.font_normal.render("Nhấn SPACE / Click Chuột để CHƠI LẠI MÀN HIỆN TẠI", True, YELLOW)
                sub2 = self.font_normal.render("Nhấn ESC để Thoát Về Menu", True, (200, 200, 200))
                self.screen.blit(txt, (SCREEN_W//2 - txt.get_width()//2, SCREEN_H//2 - 60))
                self.screen.blit(sub1, (SCREEN_W//2 - sub1.get_width()//2, SCREEN_H//2 + 10))
                self.screen.blit(sub2, (SCREEN_W//2 - sub2.get_width()//2, SCREEN_H//2 + 50))
                
            elif self.state == "WIN":
                import random as _rnd
                if not hasattr(self, 'win_timer'):
                    self.win_timer = 0
                    # Khởi tạo ngôi sao nền
                    self.win_stars = [(_rnd.randint(0, SCREEN_W), _rnd.randint(0, SCREEN_H),
                                       _rnd.uniform(0.3, 1.0), _rnd.randint(1, 3)) for _ in range(180)]
                    # Danh sách pháo hoa [x, y, vx, vy, color, life]
                    self.win_fireworks = []
                    self.win_fw_timer = 0
                self.win_timer += 1
                self.win_fw_timer -= 1

                # ── Nền đêm gradient ──
                for row in range(SCREEN_H):
                    t = row / SCREEN_H
                    r = int(0 + 5 * t)
                    g = int(0 + 8 * t)
                    b = int(12 + 30 * t)
                    pygame.draw.line(self.screen, (r, g, b), (0, row), (SCREEN_W, row))

                # ── Ngôi sao lấp lánh ──
                for sx, sy, bright, sz in self.win_stars:
                    twinkle = abs(math.sin(pygame.time.get_ticks() / 800 + sx))
                    alpha = int(bright * twinkle * 255)
                    c = (alpha, alpha, int(alpha * 0.9))
                    pygame.draw.circle(self.screen, c, (sx, sy), sz)

                # ── Bắn pháo hoa mỗi 60 frame đầu ──
                if self.win_fw_timer <= 0:
                    self.win_fw_timer = _rnd.randint(30, 70)
                    fx = _rnd.randint(SCREEN_W // 5, SCREEN_W * 4 // 5)
                    fy = _rnd.randint(SCREEN_H // 6, SCREEN_H * 2 // 3)
                    fw_colors = [
                        (255, 220, 50), (255, 80, 80), (80, 200, 255),
                        (160, 255, 100), (255, 130, 255), (255, 180, 50)
                    ]
                    col = _rnd.choice(fw_colors)
                    for _ in range(40):
                        angle = _rnd.uniform(0, math.pi * 2)
                        spd = _rnd.uniform(1.5, 5.0)
                        self.win_fireworks.append([fx, fy,
                                                    math.cos(angle) * spd,
                                                    math.sin(angle) * spd,
                                                    col, 60 + _rnd.randint(0, 30)])

                # ── Vẽ & cập nhật hạt pháo hoa ──
                new_fw = []
                for p in self.win_fireworks:
                    p[0] += p[2]; p[1] += p[3]
                    p[3] += 0.08  # trọng lực
                    p[5] -= 1
                    if p[5] > 0:
                        alpha = int(255 * p[5] / 90)
                        col = (min(255, p[4][0]), min(255, p[4][1]), min(255, p[4][2]))
                        sz = max(1, p[5] // 20)
                        pygame.draw.circle(self.screen, col, (int(p[0]), int(p[1])), sz)
                        new_fw.append(p)
                self.win_fireworks = new_fw

                # ── Câu chuyện cuộn từ dưới lên ──
                story_lines = [
                    ("CHIẾN THẮNG CHIẾN DỊCH!", "title", GOLD),
                    ("", "gap", WHITE),
                    ("Tiếng nổ rúng động cuối cùng vang lên...", "normal", (200, 220, 255)),
                    ("Siêu vũ khí 'Chiến Hạm Hủy Diệt' đã hoàn toàn sụp đổ.", "normal", (255, 100, 100)),
                    ("Bầu trời Địa ngục dần tan biến dưới làn khói súng.", "normal", WHITE),
                    ("Bạn đứng trên tàn tích của tổng hành dinh địch,", "normal", WHITE),
                    ("lau vệt máu và thuốc súng trên mặt.", "normal", (255, 200, 100)),
                    ("", "gap", WHITE),
                    ("Kế hoạch hủy diệt thế giới của Tổ Chức Hắc Ám đã bị đập tan.", "normal", WHITE),
                    ("Hàng vạn sinh mạng vô tội đã được cứu vớt trong gang tấc.", "normal", (150, 255, 150)),
                    ("Tuy nhiên, một bóng đen bí ẩn vừa thoát khỏi căn cứ...", "normal", (200, 200, 200)),
                    ("", "gap", WHITE),
                    ("Trận chiến này đã kết thúc, nhưng chiến tranh thì chưa.", "normal", (255, 120, 120)),
                    ("Hãy nghỉ ngơi đi, chiến binh.", "normal", (255, 200, 200)),
                    ("Thế giới sẽ lại cần đến bạn.", "normal", (255, 200, 200)),
                    ("", "gap", WHITE),
                    ("CẢM ƠN BẠN ĐÃ CHƠI GAME!", "title", CYAN),
                    ("", "gap", WHITE),
                    ("Sản phẩm được phát triển bởi:", "normal", (200, 240, 255)),
                    ("~ NHÓM 11 ~", "title", GOLD),
                ]

                y_offset = SCREEN_H - (self.win_timer * 0.9)

                for i, (line, style, color) in enumerate(story_lines):
                    if not line:
                        continue
                    if style == "title":
                        surf_txt = self.font_title.render(line, True, color)
                    else:
                        surf_txt = self.font_normal.render(line, True, color)

                    txt_y = y_offset + i * 52
                    if -80 < txt_y < SCREEN_H + 80:
                        # Glow cho title
                        if style == "title":
                            glow = self.font_title.render(line, True, (color[0]//3, color[1]//3, color[2]//3))
                            for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                                self.screen.blit(glow, (SCREEN_W//2 - glow.get_width()//2 + dx, txt_y + dy))
                        self.screen.blit(surf_txt, (SCREEN_W//2 - surf_txt.get_width()//2, txt_y))

                # ── Nút thoát nhấp nháy khi cuộn xong ──
                last_y = y_offset + len(story_lines) * 52
                if last_y < SCREEN_H * 0.6:
                    if (self.win_timer // 25) % 2 == 0:
                        hint = self.font_normal.render("Nhấn SPACE hoặc Click Chuột để về Menu", True, YELLOW)
                        self.screen.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 80))

                # ── Đường viền vàng rung nhẹ ──
                border_pulse = int(180 + 60 * math.sin(self.win_timer / 20))
                pygame.draw.rect(self.screen, (border_pulse, border_pulse // 2, 0),
                                 (4, 4, SCREEN_W - 8, SCREEN_H - 8), 3)
                
            # ── Screen Flash (Flashbang) ──────────────────────────────────────
            if getattr(self.effect_manager, 'screen_flash', 0) > 0:
                self.flash_surf.fill((255, 255, 255, int(self.effect_manager.screen_flash)))
                self.screen.blit(self.flash_surf, (0, 0))

        # ── Hậu xử lý toàn cục (Menu và Game) ───────────────────────────────
        # 1. Độ sáng màn hình (Brightness)
        brightness = getattr(self.menu, 'brightness', 1.0)
        if brightness < 0.99 or brightness > 1.01:
            if brightness < 1.0:
                alpha = int((1.0 - brightness) * 255)
                self.overlay_surf.fill((0, 0, 0, alpha))
            else:
                alpha = int((brightness - 1.0) * 128)
                self.overlay_surf.fill((255, 255, 255, alpha))
            self.screen.blit(self.overlay_surf, (0, 0))

        # 2. Hiệu ứng CRT Scanlines
        if getattr(self.menu, 'crt_scanlines', True):
            self.screen.blit(self.crt_surf, (0, 0))
                

        # Draw PAUSE_SETTINGS overlay
        if self.state == "PAUSE_SETTINGS":
            self.in_game_settings.draw(self.screen)
            
        # Global Brightness
        if hasattr(self, 'in_game_settings'):
            b = self.in_game_settings.brightness
            if b < 10:
                alpha = int(255 * (10 - b) / 10.0)
                self.overlay_surf.fill((0, 0, 0, alpha))
                self.screen.blit(self.overlay_surf, (0, 0))
        pygame.display.flip()

if __name__ == "__main__":
    try:
        app = GameApp()
        app.run()
    except Exception as e:
        import traceback
        with open("crash_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        raise
