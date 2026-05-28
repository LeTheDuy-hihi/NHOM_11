# menu.py — Cyberpunk Neon Menu
import pygame, math, random, time, os
from constants import *
from ui_framework import Panel, ScanLine, ParticleField, Button
from sound_manager import sound_manager

def hue_rgb(h):
    h = h % 1.0
    i = int(h * 6); f = h*6-i
    p,q,t = 0, int(255*(1-f)), int(255*f)
    if i%6==0: return (255,t,p)
    if i%6==1: return (int(255*q/255),255,p)
    if i%6==2: return (p,255,t)
    if i%6==3: return (p,int(255*q/255),255)
    if i%6==4: return (t,p,255)
    return (255,p,int(255*q/255))

class MainMenu:
    def __init__(self, font_title, font_normal, font_small):
        # Load font quân sự đặc thù sạch sẽ sắc nét - bold=True để chữ đậm rõ ràng
        title_path = pygame.font.match_font("segoeui", bold=True) or pygame.font.match_font("arial", bold=True)
        small_path = pygame.font.match_font("consolas") or pygame.font.match_font("couriernew")
        
        if title_path:
            self.font_title_mil  = pygame.font.Font(title_path, 56)
            self.font_normal_mil = pygame.font.Font(title_path, 24)
        else:
            self.font_title_mil  = font_title
            self.font_normal_mil = font_normal

        if small_path:
            self.font_small_mil = pygame.font.Font(small_path, 14)
        else:
            self.font_small_mil = font_small

        self.font_title  = self.font_title_mil
        self.font_normal = self.font_normal_mil
        self.font_small  = self.font_small_mil
        self.state    = "MAIN"
        self.selected = 0
        self._pulse   = 0.0
        self.tilt_x   = 0
        self.tilt_y   = 0

        # Phối màu quân đội / chiến thuật tối giản
        self.menu_items = [
            {"text": "VÀO GAME",   "action": "START",     "color": (150, 160, 170),  "glow": (245, 165, 30)},
            {"text": "TRANG BỊ",   "action": "LOADOUT",   "color": (150, 160, 170),  "glow": (245, 165, 30)},
            {"text": "KHO ĐỒ",     "action": "INVENTORY", "color": (150, 160, 170),  "glow": (245, 165, 30)},
            {"text": "NÂNG CẤP",   "action": "UPGRADES",  "color": (150, 160, 170),  "glow": (245, 165, 30)},
            {"text": "TẬP HUẤN",   "action": "TRAINING",  "color": (150, 160, 170),  "glow": (100, 220, 80)},
            {"text": "NHIỆM VỤ",   "action": "MISSIONS",  "color": (150, 160, 170),  "glow": (245, 165, 30)},
            {"text": "CÀI ĐẶT",     "action": "SETTINGS",  "color": (150, 160, 170),  "glow": (245, 165, 30)},
            {"text": "THOÁT",      "action": "QUIT",       "color": (240, 70, 70),    "glow": (240, 70, 70)},
        ]
        self.selected_weapon  = 0
        self.loadout_tab = 0  # 0: SÚNG CHÍNH, 1: CẬN CHIẾN, 2: LỰU ĐẠN
        self.loadout_focus = "ITEMS"  # "TABS" hoặc "ITEMS"
        self.loadout_selected_index = 0  # Chỉ mục đang được chọn trong tab hiện tại
        self.weapons  = ["AK-47", "SHOTGUN", "SMG", "FLAMETHROWER"]
        self.equipped_weapons = ["AK-47"]   # tối đa 3 súng
        self._weapon_rects = {}             # dùng để detect click
 
        self.grenades_list = ["FRAG", "FLASH", "SMOKE"]
        self.equipped_grenade = "FRAG"
        self._grenade_rects = {}
 
        self.melee_list = ["PAN", "SABER", "BAT", "SWORD", "SCYTHE"]
        self.equipped_melee = "PAN"
        self._melee_rects = {}
 
        self.selected_mission = 0
        self.missions = [1, 2, 3, 4, 5]
        self._mission_rects = {}
        self._mission_start_rect = None
        
        # Cài đặt (Settings)
        self.settings_selected_idx = 0
        self.brightness = 1.0
        self.crt_scanlines = True
        self._settings_rects = []
        
        # Shop & Economy
        self.gold = 0
        self.unlocked_weapons = ["AK-47", "PAN", "FRAG"]
        self.inventory = {}  # item_name -> quantity owned
        self.save_callback = None
        self.perm_upgrades = {"hp": 0, "armor": 0, "damage": 0, "speed": 0, "dash": 0}
        self.upgrades_selected_idx = 0
        self._upgrade_rects = []
        
        self.upgrades_catalog = [
            {
                "id": "hp",
                "name": "Thể Lực Đặc Nhiệm",
                "desc": "Tăng giới hạn sinh mệnh tối đa (+10 HP mỗi cấp).",
                "max_level": 5,
                "bonus": 10,
                "costs": [150, 250, 400, 600, 900],
                "color": (220, 60, 80) # Red
            },
            {
                "id": "armor",
                "name": "Giáp Chiến Thuật",
                "desc": "Cường hóa lớp giáp chống đạn Kevlar (+15 Giáp mỗi cấp).",
                "max_level": 5,
                "bonus": 15,
                "costs": [150, 250, 400, 600, 900],
                "color": (80, 160, 220) # Blue/Cyan
            },
            {
                "id": "damage",
                "name": "Sát Thương Thực Chiến",
                "desc": "Gia tăng sát thương súng đạn (+5% sát thương mỗi cấp).",
                "max_level": 5,
                "bonus": 0.05,
                "costs": [200, 350, 500, 800, 1200],
                "color": (235, 120, 0) # Orange
            },
            {
                "id": "speed",
                "name": "Tốc Độ Tác Chiến",
                "desc": "Tăng tốc độ di chuyển linh hoạt (+5% tốc chạy mỗi cấp).",
                "max_level": 5,
                "bonus": 0.16,
                "costs": [200, 300, 450, 700, 1000],
                "color": (100, 180, 80) # Olive Green
            },
            {
                "id": "dash",
                "name": "Phản Xạ Linh Hoạt",
                "desc": "Giảm thời gian hồi chiêu kỹ năng lướt (Dash) (-8% CD mỗi cấp).",
                "max_level": 5,
                "bonus": 0.08,
                "costs": [250, 400, 600, 900, 1300],
                "color": (180, 80, 220) # Purple
            }
        ]

        # Load operative avatar for lobby
        self.avatar_img = None
        self.ghost_portrait = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        avatar_path = os.path.join(base_dir, "ANH", "nha-vat_chinh.jpg")
        ghost_path = os.path.join(base_dir, "ANH", "ghost_portrait.png")
        
        if os.path.exists(ghost_path):
            try:
                img = pygame.image.load(ghost_path).convert_alpha()
                self.ghost_portrait = pygame.transform.smoothscale(img, (220, 240))
            except Exception as e:
                print("Lỗi load ghost_portrait.png:", e)
                
        if os.path.exists(avatar_path):
            try:
                img = pygame.image.load(avatar_path).convert_alpha()
                bg_color = img.get_at((0, 0))
                img.lock()
                w, h = img.get_size()
                for x in range(w):
                    for y in range(h):
                        c = img.get_at((x, y))
                        if abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2]) < 50:
                            img.set_at((x, y), (0, 0, 0, 0))
                img.unlock()
                self.avatar_img = pygame.transform.smoothscale(img, (110, 110))
            except:
                pass
        self.prices = {
            "AK-47": 0, "SHOTGUN": 150, "SMG": 300, "FLAMETHROWER": 600,
            "PAN": 0, "SABER": 100, "BAT": 150, "SWORD": 400, "SCYTHE": 800,
            "FRAG": 0, "FLASH": 80, "SMOKE": 80,
            # New inventory items
            "Túi Cứu Thương": 200, "Tiêm Adrenaline": 150, "Giáp Titan Cấp III": 500,
            "Mặt Nạ Chống Khói": 120, "Lựu Đạn Frag": 100, "Kính Nhìn Đêm": 140,
            # Additional items
            "Nước Uống Năng Lượng": 80, "Bộ Dò Radar": 300, "Thuốc Hồi Phục": 120, "Áp Lực Cường Hóa": 250, "Bảo Vệ Năng Lượng": 180, "Thẻ Thảo Dược": 90
        }
        # Define catalog for inventory UI
        self.inventory_catalog = [
            ("VẬT TƯ Y TẾ", (220, 60, 80), [
                {"name": "Túi Cứu Thương",    "desc": "Hồi phục 50 HP tức thì",       "qty": 3, "effect": "+50 HP",    "rarity": "THƯỜNG"},
                {"name": "Tiêm Adrenaline",   "desc": "Tăng tốc di chuyển 30% / 10s", "qty": 1, "effect": "+SPD",      "rarity": "HIẾM"},
                {"name": "Nước Uống Năng Lượng", "desc": "Hồi phục 20 HP và tăng tốc 10% trong 5s", "qty": 2, "effect": "+HP & SPD", "rarity": "THƯỜNG"},
                {"name": "Thuốc Hồi Phục", "desc": "Hồi phục 100 HP nhanh chóng", "qty": 1, "effect": "+100 HP", "rarity": "HIẾM"}
            ]),
            ("GIÁP & BẢO VỆ", (80, 160, 220), [
                {"name": "Giáp Titan Cấp III","desc": "Hấp thụ 50 điểm sát thương",   "qty": 1, "effect": "+50 ARMOR", "rarity": "SỬ THI"},
                {"name": "Mặt Nạ Chống Khói","desc": "Miễn nhiễm lựu đạn khói",       "qty": 1, "effect": "IMMUNE",    "rarity": "HIẾM"},
                {"name": "Bảo Vệ Năng Lượng","desc": "Tạo lá chắn năng lượng giảm sát thương 20%", "qty": 1, "effect": "SHIELD", "rarity": "HIẾM"},
                {"name": "Áp Lực Cường Hóa","desc": "Tăng sức chịu đựng của giáp 15%", "qty": 1, "effect": "+DEF", "rarity": "SỬ THI"}
            ]),
            ("VŨ TRANG ĐẶC BIỆT", (235, 120, 0), [
                {"name": "Lựu Đạn Frag",      "desc": "Nổ diện rộng, sát thương cao", "qty": 3, "effect": "AOE DMG",   "rarity": "THƯỜNG"},
                {"name": "Kính Nhìn Đêm",     "desc": "Tăng tầm nhìn trong bóng tối", "qty": 1, "effect": "+VISION",   "rarity": "HIẾM"},
                {"name": "Bộ Dò Radar", "desc": "Phát hiện kẻ thù trong phạm vi rộng", "qty": 1, "effect": "DETECT", "rarity": "HIẾM"},
                {"name": "Thẻ Thảo Dược", "desc": "Tăng khả năng hồi sức trong trận", "qty": 2, "effect": "+RECOVERY", "rarity": "THƯỜNG"}
            ]),
            ("CÔNG NGHỆ", (100, 200, 255), [
                {"name": "Radar Siêu Cấp", "desc": "Phát hiện mục tiêu trong bán kính 200m", "price": 800, "rarity": "SIÊU HIẾM"},
                {"name": "Drone Hỗ Trợ", "desc": "Cung cấp hỗ trợ hỏa lực nhỏ", "price": 1200, "rarity": "HIẾM"},
                {"name": "Thẻ Truy Cập", "desc": "Mở khóa khu vực đặc biệt", "price": 500, "rarity": "THƯỜNG"}
            ]),

        ]
 
        # 3D Parallax camera offsets
        self.bg_dx = 0.0
        self.bg_dy = 0.0
 
        # 3D Embers (Tàn lửa chiến trường bay 3D rất nhỏ và chậm)
        self.stars_3d = []
        for _ in range(60):
            self.stars_3d.append({
                "x": random.uniform(-SCREEN_W / 2, SCREEN_W / 2),
                "y": random.uniform(-SCREEN_H / 2, SCREEN_H / 2),
                "z": random.uniform(10, 800),
                "speed": random.uniform(1.0, 2.5),
                "color": (245, 165, 30),
                "size": random.uniform(1.0, 2.0)
            })

        # Meteors
        self.meteors = []
        self._meteor_timer = 0

        self.scan = ScanLine(0,0,SCREEN_W,SCREEN_H,speed=1,color=UI_BORDER)
        self.controls_text = [
            "W A S D — Di chuyển",
            "Chuột trái — Bắn súng",
            "V hoặc 4 — Chém cận chiến",
            "G — Ném lựu đạn",
            "1, 2, 3 — Đổi súng (Slot 1-3)",
            "Chuột phải — Ngắm bắn (ADS)",
            "SHIFT — Chạy nhanh",
            "Q — Tập trung (Slow-Mo)",
            "TAB — Hồi Máu khẩn cấp",
            "R — Nạp đạn",
            "SPACE — Lướt (Dash)",
        ]
        
        self.bg_image = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path_png = os.path.join(base_dir, "ANH", "anhnen.png")
        bg_path_jpg = os.path.join(base_dir, "ANH", "anhnen.jpg")
        try:
            if os.path.exists(bg_path_png):
                self.bg_image = pygame.transform.scale(pygame.image.load(bg_path_png).convert(), (SCREEN_W + 60, SCREEN_H + 40))
            elif os.path.exists(bg_path_jpg):
                self.bg_image = pygame.transform.scale(pygame.image.load(bg_path_jpg).convert(), (SCREEN_W + 60, SCREEN_H + 40))
        except:
            pass
            
        # Load weapon images
        self.weapon_images = {}
        for w_id, f_name in [("AK-47", "AK.jpg"), ("SHOTGUN", "shotgun.jpg"), ("SMG", "MP.jpg"), ("FLAMETHROWER", "súng lửa.png")]:
            w_path = os.path.join(base_dir, "ANH", f_name)
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
                    img = pygame.transform.smoothscale(img, (140, 90)) # Fit inside 170x200 box
                    self.weapon_images[w_id] = img
                except Exception as e:
                    pass

        # Load melee weapon images
        self.melee_images = {}
        for m_id, f_name in [
            ("PAN", "chảo.png"),
            ("SABER", "đao.jpg"),
            ("BAT", "gậy bóng chày.jpg"),
            ("SWORD", "kiếm.jpg"),
            ("SCYTHE", "lưỡi hái.jpg")
        ]:
            m_path = os.path.join(base_dir, "ANH", f_name)
            if os.path.exists(m_path):
                try:
                    img = pygame.image.load(m_path).convert_alpha()
                    # Xóa nền
                    bg_color = img.get_at((0, 0))
                    img.lock()
                    w, h = img.get_size()
                    for x in range(w):
                        for y in range(h):
                            c = img.get_at((x, y))
                            # Lọc nền trắng/xám
                            if abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2]) < 60 or (c[0] > 230 and c[1] > 230 and c[2] > 230):
                                img.set_at((x, y), (0,0,0,0))
                    img.unlock()
                    img = pygame.transform.flip(img, True, False)
                    img = pygame.transform.smoothscale(img, (110, 60))
                    self.melee_images[m_id] = img
                except Exception as e:
                    print(f"Lỗi load ảnh cận chiến {m_id}:", e)

        # Load grenade images
        self.grenade_images = {}
        for g_id, f_name in [
            ("FRAG", "lựu đạn.jpg"),
            ("FLASH", "lựu choáng.jpg"),
            ("SMOKE", "lựu khói.jpg")
        ]:
            g_path = os.path.join(base_dir, "ANH", f_name)
            if os.path.exists(g_path):
                try:
                    img = pygame.image.load(g_path).convert_alpha()
                    bg_color = img.get_at((0, 0))
                    img.lock()
                    w, h = img.get_size()
                    for x in range(w):
                        for y in range(h):
                            c = img.get_at((x, y))
                            if abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2]) < 60 or (c[0] > 230 and c[1] > 230 and c[2] > 230):
                                img.set_at((x, y), (0,0,0,0))
                    img.unlock()
                    img = pygame.transform.smoothscale(img, (100, 100))
                    self.grenade_images[g_id] = img
                except Exception as e:
                    print(f"Lỗi load ảnh lựu đạn {g_id}:", e)

        # Load inventory item images
        self.inventory_images = {}
        item_img_files = {
            "Túi Cứu Thương": "medkit.png",
            "Tiêm Adrenaline": "adrenaline.png",
            "Nước Uống Năng Lượng": "energy_drink.png",
            "Thuốc Hồi Phục": "potion.png",
            "Giáp Titan Cấp III": "titan_armor.png",
            "Mặt Nạ Chống Khói": "gas_mask.png",
            "Bảo Vệ Năng Lượng": "energy_shield.png",
            "Áp Lực Cường Hóa": "titan_armor.png",
            "Lựu Đạn Frag": "lựu đạn.jpg",
            "Kính Nhìn Đêm": "nvg.png",
            "Bộ Dò Radar": "radar_detector.png",
            "Thẻ Thảo Dược": "herbal_card.png",
            "Radar Siêu Cấp": "radar_detector.png",
            "Drone Hỗ Trợ": "drone.png",
            "Thẻ Truy Cập": "access_card.png"
        }
        for item_name, f_name in item_img_files.items():
            img_path = os.path.join(base_dir, "ANH", f_name)
            if os.path.exists(img_path):
                try:
                    img = pygame.image.load(img_path).convert_alpha()
                    bg_color = img.get_at((0, 0))
                    img.lock()
                    w, h = img.get_size()
                    for x in range(w):
                        for y in range(h):
                            c = img.get_at((x, y))
                            if abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2]) < 45 or (c[0] < 15 and c[1] < 15 and c[2] < 15):
                                img.set_at((x, y), (0,0,0,0))
                    img.unlock()
                    img = pygame.transform.smoothscale(img, (96, 96))
                    self.inventory_images[item_name] = img
                except Exception as e:
                    print(f"Lỗi load ảnh vật phẩm {item_name}:", e)

        # Initialize menu items slide-right offsets
        self.menu_offsets = [0.0] * len(self.menu_items)
        
        self.inventory_tab = 0
        self.inventory_focus = "TABS"
        self.inventory_selected_index = 0
        self._close_btn_rect = None

    # ── INPUT ───────────────────────────────────────────────────────────────
    def handle_input(self, event):
        # Tính tilt offset tức thời từ vị trí chuột hiện tại (đồng bộ với draw)
        mx_cur, my_cur = pygame.mouse.get_pos()
        cur_tilt_x = int((mx_cur - SCREEN_W / 2) / (SCREEN_W / 2) * 12)
        cur_tilt_y = int((my_cur - SCREEN_H / 2) / (SCREEN_H / 2) * 12)

        mpos = (0, 0)
        if hasattr(event, 'pos'):
            # Trừ tilt để chuyển tọa độ màn hình thực → tọa độ menu_surf
            mpos = (event.pos[0] - cur_tilt_x, event.pos[1] - cur_tilt_y)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state != "MAIN":
                    self.state = "MAIN"
                    return None

            if self.state == "MAIN":
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected-1) % len(self.menu_items)
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected+1) % len(self.menu_items)
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return self._activate()
            
            elif self.state == "UPGRADES":
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    self.upgrades_selected_idx = (self.upgrades_selected_idx - 1) % 5
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                    self.upgrades_selected_idx = (self.upgrades_selected_idx + 1) % 5
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._buy_upgrade(self.upgrades_selected_idx)
            
            elif self.state == "LOADOUT":
                # Điều hướng phím khi đang focus vào TAB BAR
                if self.loadout_focus == "TABS":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.loadout_tab = (self.loadout_tab - 1) % 3
                        self.loadout_selected_index = 0
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.loadout_tab = (self.loadout_tab + 1) % 3
                        self.loadout_selected_index = 0
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.loadout_focus = "ITEMS"
                        self.loadout_selected_index = 0
                        sound_manager.play('menu_select')
                
                # Điều hướng phím khi đang focus vào ITEMS GRID/LIST
                elif self.loadout_focus == "ITEMS":
                    if self.loadout_tab == 0:  # Súng chính (4 súng, lưới 2x2)
                        idx = self.loadout_selected_index
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.loadout_selected_index = (idx - 1) % 4
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.loadout_selected_index = (idx + 1) % 4
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            if idx < 2:  # Ở dòng đầu -> Di chuyển lên Tab Bar
                                self.loadout_focus = "TABS"
                            else:
                                self.loadout_selected_index = idx - 2
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            if idx < 2:
                                self.loadout_selected_index = idx + 2
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            w = self.weapons[idx]
                            if w in self.unlocked_weapons:
                                if w in self.equipped_weapons:
                                    if len(self.equipped_weapons) > 1:
                                        self.equipped_weapons.remove(w)
                                        sound_manager.play('menu_select')
                                        if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                                elif len(self.equipped_weapons) < 3:
                                    self.equipped_weapons.append(w)
                                    sound_manager.play('menu_select')
                                    if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                            else:
                                if self._buy_item(w): sound_manager.play('pickup')
                                else: sound_manager.play('error')
                                
                    elif self.loadout_tab == 1:  # Cận chiến (5 vũ khí, lưới 3x2)
                        idx = self.loadout_selected_index
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.loadout_selected_index = (idx - 1) % 5
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.loadout_selected_index = (idx + 1) % 5
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            if idx < 3:  # Dòng đầu -> Lên Tab Bar
                                self.loadout_focus = "TABS"
                            else:
                                self.loadout_selected_index = idx - 3
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            if idx < 3:
                                self.loadout_selected_index = min(4, idx + 3)
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            m = self.melee_list[idx]
                            if m in self.unlocked_weapons:
                                self.equipped_melee = m
                                sound_manager.play('menu_select')
                                if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                            else:
                                if self._buy_item(m): sound_manager.play('pickup')
                                else: sound_manager.play('error')
                            
                    elif self.loadout_tab == 2:  # Lựu đạn (3 lựu đạn, hàng ngang 1x3)
                        idx = self.loadout_selected_index
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self.loadout_selected_index = (idx - 1) % 3
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self.loadout_selected_index = (idx + 1) % 3
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            self.loadout_focus = "TABS"
                            sound_manager.play('menu_select')
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            g = self.grenades_list[idx]
                            if g in self.unlocked_weapons:
                                self.equipped_grenade = g
                                sound_manager.play('menu_select')
                                if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                            else:
                                if self._buy_item(g): sound_manager.play('pickup')
                                else: sound_manager.play('error')

            elif self.state == "INVENTORY":
                if self.inventory_focus == "TABS":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.inventory_tab = (self.inventory_tab - 1) % len(self.inventory_catalog)
                        self.inventory_selected_index = 0
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.inventory_tab = (self.inventory_tab + 1) % len(self.inventory_catalog)
                        self.inventory_selected_index = 0
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.inventory_focus = "ITEMS"
                        self.inventory_selected_index = 0
                        sound_manager.play('menu_select')
                elif self.inventory_focus == "ITEMS":
                    items = self.inventory_catalog[self.inventory_tab][2]
                    idx = self.inventory_selected_index
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.inventory_selected_index = (idx - 1) % len(items)
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.inventory_selected_index = (idx + 1) % len(items)
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if idx < 2:
                            self.inventory_focus = "TABS"
                        else:
                            self.inventory_selected_index = idx - 2
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if idx + 2 < len(items):
                            self.inventory_selected_index = idx + 2
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        item = items[idx]
                        if self._buy_item(item["name"]):
                            sound_manager.play('pickup')
                        else:
                            sound_manager.play('error')

            elif self.state == "MISSIONS":
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                    self.selected_mission = (self.selected_mission-1) % len(self.missions)
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                    self.selected_mission = (self.selected_mission+1) % len(self.missions)
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return "START"

            elif self.state == "CONTROLS":
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.settings_selected_idx = (self.settings_selected_idx - 1) % 4
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.settings_selected_idx = (self.settings_selected_idx + 1) % 4
                    sound_manager.play('menu_select')
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust_setting(self.settings_selected_idx, -1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust_setting(self.settings_selected_idx, 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._adjust_setting(self.settings_selected_idx, 0, toggle=True)

        elif event.type == pygame.MOUSEMOTION:
            if self.state == "MAIN":
                for i in range(len(self.menu_items)):
                    if self._item_rect(i).collidepoint(mpos):
                        self.selected = i
            elif self.state == "UPGRADES":
                if hasattr(self, "_upgrade_rects") and self._upgrade_rects:
                    for ui, rect in enumerate(self._upgrade_rects):
                        if rect.collidepoint(mpos):
                            self.upgrades_selected_idx = ui
            elif self.state == "MISSIONS":
                if hasattr(self, "_mission_rects"):
                    for mi, rect in self._mission_rects.items():
                        if rect.collidepoint(mpos):
                            self.selected_mission = mi
            elif self.state == "CONTROLS":
                if hasattr(self, "_settings_rects") and self._settings_rects:
                    for si, rect in enumerate(self._settings_rects):
                        if rect.collidepoint(mpos):
                            self.settings_selected_idx = si
                            if event.buttons[0] == 1:
                                self._handle_settings_mouse(si, mpos)
            elif self.state == "LOADOUT":
                if hasattr(self, "_tab_rects"):
                    for ti, rect in enumerate(self._tab_rects):
                        if rect.collidepoint(mpos):
                            self.loadout_focus = "TABS"
                            self.loadout_tab = ti
                            
                if self.loadout_tab == 0:
                    for wi, w in enumerate(self.weapons):
                        if w in self._weapon_rects and self._weapon_rects[w].collidepoint(mpos):
                            self.loadout_focus = "ITEMS"
                            self.loadout_selected_index = wi
                elif self.loadout_tab == 1:
                    for mi, m in enumerate(self.melee_list):
                        if m in self._melee_rects and self._melee_rects[m].collidepoint(mpos):
                            self.loadout_focus = "ITEMS"
                            self.loadout_selected_index = mi
                elif self.loadout_tab == 2:
                    for gi, g in enumerate(self.grenades_list):
                        if g in self._grenade_rects and self._grenade_rects[g].collidepoint(mpos):
                            self.loadout_focus = "ITEMS"
                            self.loadout_selected_index = gi

            elif self.state == "INVENTORY":
                if hasattr(self, "_inv_tab_rects"):
                    for ti, rect in enumerate(self._inv_tab_rects):
                        if rect.collidepoint(mpos):
                            self.inventory_focus = "TABS"
                            self.inventory_tab = ti
                if hasattr(self, "_inventory_rects"):
                    for name, rect in self._inventory_rects.items():
                        if rect.collidepoint(mpos):
                            self.inventory_focus = "ITEMS"
                            items = self.inventory_catalog[self.inventory_tab][2]
                            for ii, it in enumerate(items):
                                if it["name"] == name:
                                    self.inventory_selected_index = ii
                                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state != "MAIN" and hasattr(self, "_close_btn_rect") and self._close_btn_rect:
                if self._close_btn_rect.collidepoint(mpos):
                    self.state = "MAIN"
                    sound_manager.play('menu_select')
                    return None

            if self.state == "MAIN":
                for i in range(len(self.menu_items)):
                    r = self._item_rect(i)
                    if r.collidepoint(mpos):
                        self.selected = i
                        return self._activate()
            elif self.state == "UPGRADES":
                clicked = False
                if hasattr(self, "_upgrade_rects") and self._upgrade_rects:
                    for ui, rect in enumerate(self._upgrade_rects):
                        if rect.collidepoint(mpos):
                            self.upgrades_selected_idx = ui
                            self._buy_upgrade(ui)
                            clicked = True
                            break
                if not clicked:
                    panel_rect = pygame.Rect(SCREEN_W//2-500, 45, 1000, 710)
                    if not panel_rect.collidepoint(mpos):
                        self.state = "MAIN"
            elif self.state == "INVENTORY":
                clicked = False
                if hasattr(self, "_inv_tab_rects"):
                    for ti, rect in enumerate(self._inv_tab_rects):
                        if rect.collidepoint(mpos):
                            self.inventory_tab = ti
                            self.inventory_focus = "ITEMS"
                            self.inventory_selected_index = 0
                            clicked = True
                            break
                if not clicked and hasattr(self, "_inventory_rects"):
                    for name, rect in self._inventory_rects.items():
                        if rect.collidepoint(mpos):
                            self.inventory_focus = "ITEMS"
                            items = self.inventory_catalog[self.inventory_tab][2]
                            for ii, it in enumerate(items):
                                if it["name"] == name:
                                    self.inventory_selected_index = ii
                                    break
                            if self._buy_item(name):
                                sound_manager.play('pickup')
                            else:
                                sound_manager.play('error')
                            clicked = True
                            break
                panel_rect = pygame.Rect(SCREEN_W//2-480, 45, 960, 710)
                if not clicked and not panel_rect.collidepoint(mpos):
                    self.state = "MAIN"
            elif self.state == "CONTROLS":
                clicked = False
                if hasattr(self, "_settings_rects") and self._settings_rects:
                    for si, rect in enumerate(self._settings_rects):
                        if rect.collidepoint(mpos):
                            self.settings_selected_idx = si
                            clicked = True
                            if si == 3:
                                self.crt_scanlines = not self.crt_scanlines
                            else:
                                self._handle_settings_mouse(si, mpos)
                            break
                if not clicked:
                    panel_rect = pygame.Rect(SCREEN_W//2-500, 60, 1000, 620)
                    if not panel_rect.collidepoint(mpos):
                        self.state = "MAIN"
            elif self.state == "LOADOUT":
                clicked = False
                if hasattr(self, "_tab_rects"):
                    for ti, rect in enumerate(self._tab_rects):
                        if rect.collidepoint(mpos):
                            self.loadout_tab = ti
                            self.loadout_focus = "ITEMS"
                            self.loadout_selected_index = 0
                            clicked = True
                            break
                
                if not clicked:
                    if self.loadout_tab == 0:
                        for wi, w in enumerate(self.weapons):
                            if w in self._weapon_rects and self._weapon_rects[w].collidepoint(mpos):
                                clicked = True
                                self.loadout_focus = "ITEMS"
                                self.loadout_selected_index = wi
                                if w in self.unlocked_weapons:
                                    if w in self.equipped_weapons:
                                        if len(self.equipped_weapons) > 1:
                                            self.equipped_weapons.remove(w)
                                            sound_manager.play('menu_select')
                                            if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                                    elif len(self.equipped_weapons) < 3:
                                        self.equipped_weapons.append(w)
                                        sound_manager.play('menu_select')
                                        if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                                else:
                                    if self._buy_item(w): sound_manager.play('pickup')
                                    else: sound_manager.play('error')
                                break
                    elif self.loadout_tab == 1:
                        for mi, m in enumerate(self.melee_list):
                            if m in self._melee_rects and self._melee_rects[m].collidepoint(mpos):
                                clicked = True
                                self.loadout_focus = "ITEMS"
                                self.loadout_selected_index = mi
                                if m in self.unlocked_weapons:
                                    self.equipped_melee = m
                                    sound_manager.play('menu_select')
                                    if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                                else:
                                    if self._buy_item(m): sound_manager.play('pickup')
                                    else: sound_manager.play('error')
                                break
                    elif self.loadout_tab == 2:
                        for gi, g in enumerate(self.grenades_list):
                            if g in self._grenade_rects and self._grenade_rects[g].collidepoint(mpos):
                                clicked = True
                                self.loadout_focus = "ITEMS"
                                self.loadout_selected_index = gi
                                if g in self.unlocked_weapons:
                                    self.equipped_grenade = g
                                    sound_manager.play('menu_select')
                                    if self.save_callback: self.save_callback(self.gold, self.unlocked_weapons)
                                else:
                                    if self._buy_item(g): sound_manager.play('pickup')
                                    else: sound_manager.play('error')
                                break
                
                if not clicked:
                    panel_rect = pygame.Rect(SCREEN_W//2-530, 45, 1060, 705)
                    if not panel_rect.collidepoint(mpos):
                        self.state = "MAIN"
            elif self.state == "MISSIONS":
                clicked = False
                if hasattr(self, "_mission_rects"):
                    for mi, rect in self._mission_rects.items():
                        if rect.collidepoint(mpos):
                            if self.selected_mission == mi:
                                # Click lần 2 vào map đã chọn → bắt đầu game
                                sound_manager.play('menu_select')
                                return "START"
                            else:
                                # Click lần đầu → chọn map
                                self.selected_mission = mi
                                sound_manager.play('menu_select')
                            clicked = True
                            break
                # Click vào nút START ở dưới
                if not clicked and hasattr(self, "_mission_start_rect") and self._mission_start_rect:
                    if self._mission_start_rect.collidepoint(mpos):
                        sound_manager.play('menu_select')
                        return "START"
                        clicked = True
                if not clicked:
                    # Panel thực tế: Panel(SCREEN_W//2-480, 45, 960, 710)
                    panel_rect = pygame.Rect(SCREEN_W//2-480, 45, 960, 710)
                    if not panel_rect.collidepoint(mpos):
                        self.state = "MAIN"
            else:
                self.state = "MAIN"
        return None

    def _buy_item(self, item_name):
        # Unified purchase logic for weapons and inventory items
        if item_name in self.unlocked_weapons:
            return True
        price = self.prices.get(item_name, 0)
        if self.gold >= price:
            self.gold -= price
            # If item is a weapon/melee/grenade, add to unlocked list
            if item_name in self.weapons + self.melee_list + self.grenades_list:
                self.unlocked_weapons.append(item_name)
            else:
                # Otherwise treat as consumable inventory item
                self.inventory[item_name] = self.inventory.get(item_name, 0) + 1
            if self.save_callback:
                self.save_callback(self.gold, self.unlocked_weapons)
            return True
        return False

    def _activate(self):
        a = self.menu_items[self.selected]["action"]
        if a=="START":    self.state="MISSIONS"; return None  # Vào màn chọn map trước
        if a=="QUIT":     return "QUIT"
        if a=="SETTINGS": self.state="CONTROLS"
        if a=="LOADOUT":  self.state="LOADOUT"
        if a=="INVENTORY":self.state="INVENTORY"
        if a=="MISSIONS": self.state="MISSIONS"
        if a=="UPGRADES": self.state="UPGRADES"
        if a=="TRAINING": return "TRAINING"
        return None

    def _item_rect(self, idx):
        offset = self.menu_offsets[idx] if (hasattr(self, 'menu_offsets') and idx < len(self.menu_offsets)) else 0.0
        base_x = 40 + 12 + int(offset)   # lx=40, card offset=12
        ry     = 115 + 54 + idx * 60      # panel_top=115, items_top offset=54, item_h=60
        return pygame.Rect(base_x, ry, 256, 52)  # iw=lw-24=256, ih=52

    def _draw_close_button(self, screen, x, y, size=30):
        # x, y is the top-left of the 30x30 button area
        btn_rect = pygame.Rect(x, y, size, size)
        
        # Check mouse hover
        mx, my = pygame.mouse.get_pos()
        mpos = (mx - getattr(self, 'tilt_x', 0), my - getattr(self, 'tilt_y', 0))
        is_hov = btn_rect.collidepoint(mpos)
        
        # Color based on hover (Red neon glow when hovered, standard dim red when idle)
        color = (255, 60, 60) if is_hov else (180, 50, 50)
        
        # Draw background and outline
        bg_a = 40 if is_hov else 15
        btn_bg = pygame.Surface((size, size), pygame.SRCALPHA)
        btn_bg.fill((*color, bg_a))
        screen.blit(btn_bg, (x, y))
        pygame.draw.rect(screen, color, btn_rect, 1, border_radius=3)
        
        if is_hov:
            # Add simple glow
            for thick in range(1, 3):
                pygame.draw.rect(screen, (*color, 40 // thick), (x - thick, y - thick, size + thick*2, size + thick*2), 1, border_radius=4)
                
        # Draw X lines inside button (offset by 8px)
        offset = 8
        pygame.draw.line(screen, color, (x + offset, y + offset), (x + size - offset, y + size - offset), 2)
        pygame.draw.line(screen, color, (x + size - offset, y + offset), (x + offset, y + size - offset), 2)
        
        return btn_rect

    # ── DRAW ────────────────────────────────────────────────────────────────
    def draw(self, screen):
        self._pulse += 0.025
        
        # Calculate dynamic 3D tilt offset
        mx, my = pygame.mouse.get_pos()
        self.tilt_x = int((mx - SCREEN_W / 2) / (SCREEN_W / 2) * 12)
        self.tilt_y = int((my - SCREEN_H / 2) / (SCREEN_H / 2) * 12)
        
        # 1. Draw the background layers directly to screen (flat/deep layers)
        self._draw_bg(screen)
        
        # 2. Render all menu screens onto a separate transparent surface
        menu_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        
        self.scan.update()
        if   self.state=="MAIN":      self._draw_main(menu_surf)
        elif self.state=="CONTROLS":  self._draw_controls(menu_surf)
        elif self.state=="LOADOUT":   self._draw_loadout(menu_surf)
        elif self.state=="INVENTORY": self._draw_inventory(menu_surf)
        elif self.state=="MISSIONS":  self._draw_missions(menu_surf)
        elif self.state=="UPGRADES":  self._draw_upgrades(menu_surf)
        
        # 3. Blit the menu surface with 3D tilt offset
        screen.blit(menu_surf, (self.tilt_x, self.tilt_y))
        
        # 4. Draw the scanlines on top of everything
        self.scan.draw(screen)

    def _draw_bg(self, screen):
        # 1. Camera Parallax shift based on mouse position
        mx, my = pygame.mouse.get_pos()
        target_dx = (mx - SCREEN_W / 2) * -0.05
        target_dy = (my - SCREEN_H / 2) * -0.05
        self.bg_dx += (target_dx - self.bg_dx) * 0.1
        self.bg_dy += (target_dy - self.bg_dy) * 0.1

        if hasattr(self, 'bg_image') and self.bg_image:
            screen.blit(self.bg_image, (-30 + self.bg_dx, -20 + self.bg_dy))
            # Dark overlay for readability (slightly darker to enhance text contrast)
            fade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            fade.fill((0, 0, 0, 110))
            screen.blit(fade, (0, 0))
        else:
            screen.fill((12, 16, 12)) # Nền rêu xanh quân đội rất tối

        # 2. Scrolling 3D perspective grid floor at the bottom - Màu xám / cam đất cực kỳ chìm (Muted Grid)
        grid_scroll = (pygame.time.get_ticks() / 15) % 1.0
        horizon_y = 520
        
        # Draw horizontal lines with exponential spacing
        num_h_lines = 10
        for i in range(num_h_lines):
            y_pct = ((i - grid_scroll) / num_h_lines)
            if y_pct < 0:
                y_pct += 1.0
            y_pos = horizon_y + (SCREEN_H - horizon_y) * (y_pct ** 2.5)
            brightness = y_pct * 0.25
            line_color = (int(150 * brightness), int(160 * brightness), int(170 * brightness))
            pygame.draw.line(screen, line_color, (0, int(y_pos)), (SCREEN_W, int(y_pos)), 1)
            
        # Draw vertical radiating lines from vanishing point
        vanishing_x = SCREEN_W // 2 + int(self.bg_dx * 1.5) # Shift vanishing point for 3D pivot
        num_v_lines = 22
        for i in range(-num_v_lines // 2, num_v_lines // 2 + 1):
            start_x = vanishing_x
            start_y = horizon_y
            end_x = vanishing_x + i * 140
            end_y = SCREEN_H
            pygame.draw.line(screen, (30, 33, 35), (start_x, start_y), (end_x, end_y), 1)

        # 3. 3D Stars/Dust Particles flowing toward screen -> Bây giờ là tàn lửa cam rất nhỏ và chậm
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        fov = 400
        for p in self.stars_3d:
            p["z"] -= p["speed"]
            if p["z"] <= 10:
                p["z"] = 800
                p["x"] = random.uniform(-SCREEN_W / 2, SCREEN_W / 2)
                p["y"] = random.uniform(-SCREEN_H / 2, SCREEN_H / 2)
            
            # Perspective projection with parallax layer offset (moving slightly slower than bg)
            px = cx + (p["x"] / p["z"]) * fov + self.bg_dx * 0.3
            py = cy + (p["y"] / p["z"]) * fov + self.bg_dy * 0.3
            
            size = max(1, int(p["size"] * (800 / p["z"])))
            if size > 4:
                size = 4
            
            if 0 <= px < SCREEN_W and 0 <= py < SCREEN_H:
                # Brightness based on depth (z)
                brightness = 1.0 - (p["z"] / 800)
                brightness = max(0.1, min(1.0, brightness))
                color = (int(p["color"][0] * brightness), 
                         int(p["color"][1] * brightness), 
                         int(p["color"][2] * brightness))
                pygame.draw.circle(screen, color, (int(px), int(py)), size)

        # 4. Meteors with parallax -> Đạn vạch đường (Tracer rounds) màu cam đỏ rực
        self._meteor_timer += 1
        if self._meteor_timer > 80 and random.random() > 0.7:
            self._meteor_timer = 0
            self.meteors.append({"x":random.randint(0,SCREEN_W),"y":-10,
                                  "dx":random.uniform(2,4),"dy":random.uniform(5,9),
                                  "len":random.randint(40,100),"hue":random.uniform(0.0, 0.1),"life":60})
        for m in self.meteors[:]:
            # Đạn vạch đường màu lửa cam
            col = (255, 100, 10)
            px1 = int(m["x"] + self.bg_dx)
            py1 = int(m["y"] + self.bg_dy)
            px2 = int(m["x"] + m["dx"] + self.bg_dx)
            py2 = int(m["y"] + m["dy"] + self.bg_dy)
            pygame.draw.line(screen, col, (px1, py1), (px2, py2), 2)
            
            fade_surf = pygame.Surface((abs(m["len"]), 4), pygame.SRCALPHA)
            pygame.draw.line(fade_surf, (*col, 60), (0, 2), (m["len"], 2), 2)
            screen.blit(fade_surf, (px1 - m["len"], py1))
            
            m["x"] += m["dx"]
            m["y"] += m["dy"]
            m["life"] -= 1
            if m["life"] <= 0 or m["y"] > SCREEN_H: 
                self.meteors.remove(m)

        # 5. Clean 1px lines and ticks instead of warning stripes
        for xi in [35, SCREEN_W - 35]:
            pygame.draw.line(screen, (150, 160, 170), (xi, 35), (xi, SCREEN_H - 35), 1)
            for sy in range(50, SCREEN_H - 35, 50):
                tick_len = 5
                if xi < SCREEN_W // 2:
                    pygame.draw.line(screen, (150, 160, 170), (xi, sy), (xi + tick_len, sy), 1)
                else:
                    pygame.draw.line(screen, (150, 160, 170), (xi, sy), (xi - tick_len, sy), 1)

    def _rainbow_text(self, screen, font, text, x, y, speed=0.05, spacing=0.07, base_color=(245, 165, 30)):
        # Render clean solid text with simple 1px black shadow
        shadow = font.render(text, True, (10, 12, 14))
        screen.blit(shadow, (x + 1, y + 1))
        
        main_surf = font.render(text, True, base_color)
        screen.blit(main_surf, (x, y))
        return x + main_surf.get_width()

    def _draw_main(self, screen):
        t = time.time()

        # ═══════════════════════════════════════════════════════════
        # HEADER  (y 0–112)
        # ═══════════════════════════════════════════════════════════
        hdr = pygame.Surface((SCREEN_W, 112), pygame.SRCALPHA)
        for hy in range(112):
            a = int(200 * (1 - hy / 112) ** 0.5)
            hdr.fill((4, 7, 14, a), (0, hy, SCREEN_W, 1))
        screen.blit(hdr, (0, 0))

        # Glitch title
        title_text = "\u0110\u1eb6C NHI\u1ec6M \u2014 CHI\u1ebeN D\u1ecaCH \u0110EN"
        tx, ty = 40, 16
        g_off = random.randint(-3, 3) if random.random() < 0.06 else 0
        pv    = math.sin(t * 6) * 2
        for col, alpha, ox in [(( 0,230,255), 120, int(pv)+g_off),
                                ((255,20, 70), 120, -int(pv)-g_off)]:
            s = self.font_title.render(title_text, True, col)
            s.set_alpha(alpha)
            screen.blit(s, (tx+ox, ty))
        self._rainbow_text(screen, self.font_title, title_text, tx, ty,
                           base_color=(245, 165, 30))

        # Subtitle strip
        sub_y = 88
        pygame.draw.line(screen, (28, 40, 55), (40, sub_y), (SCREEN_W-40, sub_y), 1)

        # Left: build tag
        bt = self.font_small.render("SPEC-OPS  v2.4  //  CLASSIFIED", True, (60, 78, 96))
        screen.blit(bt, (42, sub_y+8))

        # Centre: blinking status
        blink = int(t*2)%2 == 0
        dot   = (75, 215, 75) if blink else (35, 110, 35)
        dcx   = SCREEN_W//2 - 105
        gs = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*dot, 50), (11,11), 9)
        screen.blit(gs, (dcx-11, sub_y+4))
        pygame.draw.circle(screen, dot, (dcx, sub_y+14), 4)
        ss2 = self.font_small.render("CHI\u1ebeN D\u1ecaCH: S\u1eb4N S\u00c0NG", True, (150, 210, 130))
        screen.blit(ss2, (dcx+11, sub_y+8))

        # Right: clock
        ck = self.font_small.render(time.strftime("%H:%M:%S  %d/%m/%Y"), True, (85, 112, 148))
        screen.blit(ck, (SCREEN_W-ck.get_width()-42, sub_y+8))

        # Menu items — clean, spacious
        _MICON = {
            "START":   ">>",
            "LOADOUT": "[W]",
            "INVENTORY": "[B]",
            "UPGRADES": "[+]",
            "TRAINING": "[T]",
            "MISSIONS": "[M]",
            "MAP":     "[#]",
            "CONTROLS": "[C]",
            "QUIT":    "[X]",
        }

        item_h    = 60
        items_top = 115 + 54  # = 169)
        # ═══════════════════════════════════════════════════════════
        panel_top = 115
        panel_h   = 640

        # ── LEFT: MAIN MENU ────────────────────────────────────────
        lx = 40
        lw = 280

        lp = pygame.Surface((lw, panel_h), pygame.SRCALPHA)
        lp.fill((5, 8, 15, 160))
        screen.blit(lp, (lx, panel_top))
        pygame.draw.rect(screen, (30, 42, 56), (lx, panel_top, lw, panel_h), 1, border_radius=4)

        # Corner accent marks
        for ddx, ddy in [(1,1),(-1,1),(1,-1),(-1,-1)]:
            ex = lx if ddx==1 else lx+lw
            ey = panel_top if ddy==1 else panel_top+panel_h
            pygame.draw.line(screen,(245,165,30),(ex,ey),(ex+14*ddx,ey),1)
            pygame.draw.line(screen,(245,165,30),(ex,ey),(ex,ey+14*ddy),1)

        # Panel header
        lhdr = self.font_normal.render("MENU CH\u00cdNH", True, (245,165,30))
        screen.blit(lhdr, (lx+lw//2-lhdr.get_width()//2, panel_top+12))
        pygame.draw.line(screen,(50,65,82),(lx+16,panel_top+40),(lx+lw-16,panel_top+40),1)

        if not hasattr(self,'menu_offsets') or len(self.menu_offsets)!=len(self.menu_items):
            self.menu_offsets = [0.0]*len(self.menu_items)

        for i, item in enumerate(self.menu_items):
            is_sel  = (i == self.selected)
            tgt     = 10.0 if is_sel else 0.0
            self.menu_offsets[i] += (tgt - self.menu_offsets[i]) * 0.15

            ix  = lx + 12 + int(self.menu_offsets[i])
            iy  = items_top + i * item_h
            iw  = lw - 24
            ih  = 52         # card height
            act = item.get("action","")
            is_quit = (act == "QUIT")

            if is_sel:
                accent  = (240,70,70) if is_quit else (0, 255, 200) # Bright neon cyan
                tcol    = accent
                bg_a    = 50
            else:
                accent  = (145,45,45) if is_quit else (40,56,74)
                tcol    = (185,60,60) if is_quit else (115,132,150)
                bg_a    = 8

            # Background
            cs = pygame.Surface((iw,ih), pygame.SRCALPHA)
            cs.fill((*accent, bg_a))
            screen.blit(cs, (ix, iy))

            # Left accent stripe (Thick and glowing)
            sw = 6 if is_sel else 2
            pygame.draw.rect(screen, accent, (ix, iy+2, sw, ih-4), border_radius=2)

            # Border
            pygame.draw.rect(screen, accent, (ix, iy, iw, ih), 1, border_radius=3)

            # Glow halo for selected
            if is_sel:
                gh = pygame.Surface((iw+16, ih+16), pygame.SRCALPHA)
                pygame.draw.rect(gh, (*accent, 120), (0,0,iw+16,ih+16), 4, border_radius=6)
                pygame.draw.rect(gh, (*accent, 60), (0,0,iw+16,ih+16), 8, border_radius=8)
                screen.blit(gh, (ix-8, iy-8))

            # Icon
            ico = _MICON.get(act, "\u2022")
            ic  = self.font_normal.render(ico, True, accent)
            screen.blit(ic, (ix+16, iy+ih//2-ic.get_height()//2))

            # Label
            lbl = item["text"]
            if is_sel:
                for coff,ccol,calp in [(-1,(0,215,255),80),(1,(255,35,75),80)]:
                    s2 = self.font_normal.render(lbl, True, ccol)
                    s2.set_alpha(calp)
                    screen.blit(s2, (ix+50+coff, iy+ih//2-s2.get_height()//2))
            ls = self.font_normal.render(lbl, True, tcol)
            screen.blit(ls, (ix+50, iy+ih//2-ls.get_height()//2))

            # Right chevron on selected
            if is_sel:
                ch = self.font_normal.render("\u203a", True, accent)
                screen.blit(ch, (ix+iw-ch.get_width()-14, iy+ih//2-ch.get_height()//2))

        # ── RIGHT: OPERATOR HUD (GLASS STYLE) ─────────────────────
        rp_y = panel_top
        
        right_col_x = SCREEN_W - 440
        right_col_w = 400

        # Gold badge top right
        gdb = pygame.Surface((150,24), pygame.SRCALPHA)
        gdb.fill((255,215,0,18))
        screen.blit(gdb, (right_col_x + right_col_w - 150, rp_y))
        pygame.draw.rect(screen,(180,148,0),(right_col_x + right_col_w - 150, rp_y, 150, 24),1,border_radius=2)
        gdt = self.font_small.render(f"V\u00c0NG: {self.gold} $", True, (255,215,0))
        screen.blit(gdt, (right_col_x + right_col_w - 150 + 75 - gdt.get_width()//2, rp_y + 5))

        # Avatar (Centered in right column)
        av = self.ghost_portrait or self.avatar_img
        img_w = right_col_w
        img_h = 220
        img_x = right_col_x
        img_y = rp_y + 35

        if av:
            sav = pygame.transform.smoothscale(av, (img_w, img_h))
            pygame.draw.rect(screen,(5,8,12),(img_x,img_y,img_w,img_h))
            screen.blit(sav, (img_x, img_y))
            pygame.draw.rect(screen,(0,255,200, 150),(img_x,img_y,img_w,img_h),1)
            # Corner lock marks
            for ddx,ddy in [(1,1),(-1,1),(1,-1),(-1,-1)]:
                cx2 = img_x if ddx==1 else img_x+img_w
                cy2 = img_y if ddy==1 else img_y+img_h
                pygame.draw.line(screen,(0,255,200),(cx2,cy2),(cx2+15*ddx,cy2),2)
                pygame.draw.line(screen,(0,255,200),(cx2,cy2),(cx2,cy2+15*ddy),2)
        else:
            pygame.draw.rect(screen,(5,8,12,150),(img_x,img_y,img_w,img_h))
            pygame.draw.rect(screen,(0,255,200,150),(img_x,img_y,img_w,img_h),1)
            ft = self.font_small.render("NO DATA", True,(240,70,70))
            screen.blit(ft,(img_x+img_w//2-ft.get_width()//2, img_y+img_h//2-ft.get_height()//2))

        # Info block (below avatar)
        iy2 = img_y + img_h + 15
        nm = self.font_normal.render("M\u1eacT DANH: GHOST", True, (0,255,200))
        screen.blit(nm, (right_col_x, iy2))
        rk = self.font_small.render("BI\u1ec6T K\u00cdCH L\u1eacP I  \u2014  SPEC-OPS", True, (120,142,165))
        screen.blit(rk, (right_col_x, iy2+24))
        
        # Stats block container
        sy = iy2 + 55
        stats_w = right_col_w
        stats_h = 135
        stats_bg = pygame.Surface((stats_w, stats_h), pygame.SRCALPHA)
        stats_bg.fill((5, 10, 18, 180))
        screen.blit(stats_bg, (right_col_x, sy))
        pygame.draw.rect(screen, (30, 45, 60), (right_col_x, sy, stats_w, stats_h), 1, border_radius=4)
        
        bw2 = 200
        r_stats = [
            ("M\u00c1U",       100+self.perm_upgrades.get("hp",0)*10,    150, (215,55,75)),
            ("GI\u00c1P",      100+self.perm_upgrades.get("armor",0)*15, 175, (65,152,215)),
            ("S\u00c1T TH\u01af\u1ee2NG",100+int(self.perm_upgrades.get("damage",0)*5),125,(232,118,0)),
            ("T\u1ed0C \u0110\u1ed8",  100+int(self.perm_upgrades.get("speed",0)*16), 180, (95,182,75)),
        ]
        for i2,(lb,vl,mx,co) in enumerate(r_stats):
            sy3 = sy + i2*28 + 10
            ls4 = self.font_small.render(lb, True, (130,150,170))
            # Right-align the labels
            screen.blit(ls4, (right_col_x + 100 - ls4.get_width(), sy3))
            
            bx3=right_col_x+120; by5=sy3+6; bh=8
            
            # Dark track for the bar
            pygame.draw.rect(screen,(15,22,32),(bx3,by5,bw2,bh),border_radius=2)
            pygame.draw.rect(screen,(45,60,80),(bx3,by5,bw2,bh),1,border_radius=2)
            
            fw=int(bw2*min(vl/mx,1.0))
            if fw>0:
                pygame.draw.rect(screen,co,(bx3,by5,fw,bh),border_radius=2)
                # Bright tip
                pygame.draw.rect(screen,(255,255,255),(bx3+fw-2,by5,2,bh),border_radius=1)
                
            vt = f"{vl}%" if ("TH\u01af\u1ee2NG" in lb or "T\u1ed0C" in lb) else f"{vl}"
            vs4=self.font_small.render(vt,True,co)
            screen.blit(vs4,(bx3+bw2+12,sy3-1))

        # Weapons
        wdy = sy + stats_h + 15
        
        # Weapon glass panel
        w_bg = pygame.Surface((stats_w, 85), pygame.SRCALPHA)
        w_bg.fill((5, 10, 18, 180))
        screen.blit(w_bg, (right_col_x, wdy))
        pygame.draw.rect(screen, (30, 45, 60), (right_col_x, wdy, stats_w, 85), 1, border_radius=4)
        
        wlb = self.font_small.render("TRANG BỊ CHIẾN ĐẤU:", True, (160,180,200))
        screen.blit(wlb, (right_col_x + 15, wdy + 10))
        
        wy3=wdy+35; ww3=100; wh3=40
        eq3=list(self.equipped_weapons)[:3]
        for wi in range(3):
            wx3=right_col_x + 15 + wi*115
            wr3=pygame.Rect(wx3,wy3,ww3,wh3)
            pygame.draw.rect(screen,(15,22,32),wr3,border_radius=3)
            pygame.draw.rect(screen,(0,255,200, 100),wr3,1,border_radius=3)
            if wi<len(eq3):
                wid3=eq3[wi]
                if wid3 in self.weapon_images:
                    wi3=pygame.transform.smoothscale(self.weapon_images[wid3],(ww3-6,wh3-6))
                    screen.blit(wi3,(wx3+3,wy3+3))
                else:
                    wt3=self.font_small.render(wid3[:6],True,(245,165,30))
                    screen.blit(wt3,(wx3+ww3//2-wt3.get_width()//2,wy3+wh3//2-wt3.get_height()//2))
            else:
                et3=self.font_small.render("TRỐNG",True,(60,80,100))
                screen.blit(et3,(wx3+ww3//2-et3.get_width()//2,wy3+wh3//2-et3.get_height()//2))

        # Status
        sfy=wdy+100
        s1=self.font_small.render("ĐẶC NHIỆM: GHOST  [ ACTIVE ]",True,(85,205,75))
        screen.blit(s1,(right_col_x,sfy))
        s2=self.font_small.render("KẾT NỐI MẠNG: ĐÃ LIÊN KẾT",True,(0,210,245))
        screen.blit(s2,(right_col_x,sfy+22))

        # ═══════════════════════════════════════════════════════════
        # BOTTOM BAR  (y = SCREEN_H - 34)
        # ═══════════════════════════════════════════════════════════
        bby = SCREEN_H - 34
        btm = pygame.Surface((SCREEN_W, 34), pygame.SRCALPHA)
        btm.fill((3, 6, 12, 175))
        screen.blit(btm, (0, bby))
        pygame.draw.line(screen,(32,44,58),(0,bby),(SCREEN_W,bby),1)
        ht2=self.font_small.render("\u2191\u2193 Di chuy\u1ec3n   ENTER Ch\u1ecdn   ESC Quay l\u1ea1i",True,(70,88,108))
        screen.blit(ht2,(42,bby+10))
        vt2=self.font_small.render("\u0110\u1eb6C NHI\u1ec6M: CHI\u1ebeN D\u1ecaCH \u0110EN  \u00a9  TACTICAL ENGINE",True,(42,56,72))
        screen.blit(vt2,(SCREEN_W//2-vt2.get_width()//2,bby+10))
        fs2=self.font_small.render("SYS: ONLINE",True,(52,138,52))
        screen.blit(fs2,(SCREEN_W-fs2.get_width()-42,bby+10))


    def _draw_controls(self, screen):
        panel = Panel(SCREEN_W//2-500, 60, 1000, 620, "ĐIỀU KHIỂN & CÀI ĐẶT HỆ THỐNG")
        panel.draw(screen, self.font_normal)
        self._close_btn_rect = self._draw_close_button(screen, SCREEN_W//2 + 500 - 45, 68, 30)

        # Vertical Divider Line
        bc = (50, 60, 80)
        pygame.draw.line(screen, bc, (SCREEN_W//2, 110), (SCREEN_W//2, 650), 1)

        # ── LEFT SIDE: CONTROLS ───────────────────────────────────────────────
        hc_left = (235, 120, 0) # Tactical amber
        lbl_left = self.font_normal.render("HỆ THỐNG ĐIỀU KHIỂN", True, hc_left)
        screen.blit(lbl_left, (SCREEN_W//2 - 470, 105))

        for i, ln in enumerate(self.controls_text):
            cy = 150 + i * 42
            if "—" in ln:
                p = ln.split("—")
                key_txt = p[0].strip()
                act_txt = p[1].strip()
                kc = (120, 160, 100) # Olive green keys
                
                # Render key with box background
                key_surf = self.font_small.render(key_txt, True, kc)
                box_w = max(100, key_surf.get_width() + 16)
                pygame.draw.rect(screen, (15, 20, 15), (SCREEN_W//2 - 470, cy - 4, box_w, 30), border_radius=4)
                pygame.draw.rect(screen, kc, (SCREEN_W//2 - 470, cy - 4, box_w, 30), 1, border_radius=4)
                screen.blit(key_surf, (SCREEN_W//2 - 470 + (box_w - key_surf.get_width())//2, cy + 1))
                
                # Render action text
                act_surf = self.font_normal.render(act_txt, True, (200, 210, 200))
                screen.blit(act_surf, (SCREEN_W//2 - 350, cy))
            else:
                desc_surf = self.font_small.render(ln, True, (130, 140, 130))
                screen.blit(desc_surf, (SCREEN_W//2 - 470, cy + 4))

        # ── RIGHT SIDE: SETTINGS ──────────────────────────────────────────────
        hc_right = (235, 120, 0) # Tactical amber
        lbl_right = self.font_normal.render("CÀI ĐẶT HỆ THỐNG", True, hc_right)
        screen.blit(lbl_right, (SCREEN_W//2 + 30, 105))

        # Cập nhật rects của settings để tính toán va chạm chuột
        self._settings_rects = []
        settings_data = [
            {"label": "ÂM LƯỢNG NHẠC", "type": "slider", "val": sound_manager.music_volume},
            {"label": "ÂM LƯỢNG HIỆU ỨNG", "type": "slider", "val": sound_manager.sfx_volume},
            {"label": "ĐỘ SÁNG MÀN HÌNH", "type": "slider", "val": (self.brightness - 0.5) / 1.0}, # maps 0.5-1.5 to 0-1
            {"label": "HIỆU ỨNG CRT SCANLINES", "type": "toggle", "val": self.crt_scanlines}
        ]

        for i, opt in enumerate(settings_data):
            ry = 150 + i * 110
            r_card = pygame.Rect(SCREEN_W//2 + 30, ry, 440, 95)
            self._settings_rects.append(r_card)
            
            is_sel = (self.settings_selected_idx == i)
            
            # Card Background - Charcoal green tint
            bg_alpha = 55 if is_sel else 20
            bg_col = (235, 120, 0) if is_sel else (25, 30, 25)
            card_surf = pygame.Surface((440, 95), pygame.SRCALPHA)
            card_surf.fill((*bg_col, bg_alpha))
            screen.blit(card_surf, (SCREEN_W//2 + 30, ry))
            
            # Border - thin 1px flat
            border_w = 2 if is_sel else 1
            border_col = (245, 165, 30) if is_sel else (150, 160, 170)
            pygame.draw.rect(screen, border_col, r_card, border_w, border_radius=2)
                
            # Option Label
            lbl_color = (245, 165, 30) if is_sel else (150, 160, 170)
            lbl_surf = self.font_small.render(opt["label"], True, lbl_color)
            screen.blit(lbl_surf, (SCREEN_W//2 + 45, ry + 12))
            
            # Draw Values and Controls
            if opt["type"] == "slider":
                val = opt["val"]
                # Slider Track
                track_y = ry + 52
                track_x = SCREEN_W//2 + 55
                track_w = 320
                pygame.draw.rect(screen, (10, 12, 14), (track_x, track_y, track_w, 8), border_radius=2)
                pygame.draw.rect(screen, (150, 160, 170), (track_x, track_y, track_w, 8), 1, border_radius=2)
                
                # Slider Fill
                fill_w = int(track_w * val)
                if fill_w > 0:
                    fill_col = (245, 165, 30) if is_sel else (150, 160, 170)
                    pygame.draw.rect(screen, fill_col, (track_x, track_y, fill_w, 8), border_radius=2)
                
                # Slider Handle (solid rect, no glow)
                handle_x = track_x + fill_w
                handle_col = (245, 165, 30) if is_sel else (150, 160, 170)
                pygame.draw.rect(screen, handle_col, (handle_x - 4, track_y - 3, 8, 14), border_radius=2)
                    
                # Percentage Display
                pct_str = f"{int(val * 100)}%"
                if i == 2: # Brightness multiplier text
                    pct_str = f"{self.brightness:.2f}x"
                val_surf = self.font_small.render(pct_str, True, lbl_color)
                screen.blit(val_surf, (SCREEN_W//2 + 390, ry + 12))
                
            elif opt["type"] == "toggle":
                val = opt["val"]
                toggle_x = SCREEN_W//2 + 55
                toggle_y = ry + 42
                
                # Draw switch container
                switch_w = 70
                switch_h = 24
                pygame.draw.rect(screen, (10, 12, 14), (toggle_x, toggle_y, switch_w, switch_h), border_radius=2)
                
                # Draw toggle fill and knob
                if val:
                    fill_col = (245, 165, 30)
                    pygame.draw.rect(screen, fill_col, (toggle_x, toggle_y, switch_w, switch_h), border_radius=2)
                    pygame.draw.rect(screen, (255, 200, 80), (toggle_x, toggle_y, switch_w, switch_h), 1, border_radius=2)
                    pygame.draw.rect(screen, (255, 255, 255), (toggle_x + switch_w - 20, toggle_y + 3, 14, switch_h - 6), border_radius=2)
                    txt_state = self.font_small.render("BẬT (ON)", True, fill_col)
                else:
                    pygame.draw.rect(screen, (150, 160, 170), (toggle_x, toggle_y, switch_w, switch_h), 1, border_radius=2)
                    pygame.draw.rect(screen, (150, 160, 170), (toggle_x + 6, toggle_y + 3, 14, switch_h - 6), border_radius=2)
                    txt_state = self.font_small.render("TẮT (OFF)", True, (150, 160, 170))
                    
                screen.blit(txt_state, (toggle_x + switch_w + 12, toggle_y + 3))

        # Bottom Hints for Settings Page - static, no pulsing
        bt = self.font_small.render("↑↓ Chọn mục   ←→ Thay đổi   SPACE/ENTER Bật/Tắt   ESC Quay lại", True, (150, 160, 170))
        screen.blit(bt, (SCREEN_W//2 + 250 - bt.get_width()//2, ry + 115))

    def _draw_loadout(self, screen):
        panel = Panel(SCREEN_W//2-530, 45, 1060, 705, "TRANG BỊ VŨ KHÍ & TRANG BỊ PHỤ")
        panel.draw(screen, self.font_normal)
        self._close_btn_rect = self._draw_close_button(screen, SCREEN_W//2 + 530 - 45, 53, 30)

        # Hiển thị số Vàng
        gold_txt = self.font_normal.render(f"VÀNG: {self.gold} $", True, (255, 215, 0))
        screen.blit(gold_txt, (SCREEN_W//2 + 530 - gold_txt.get_width() - 60, 55))

        dnames = {
            "AK-47": "AK-47", "SHOTGUN": "SHOTGUN", "SMG": "TIỂU LIÊN SMG", "FLAMETHROWER": "SÚNG LỬA",
            "FRAG": "Lựu Đạn Nổ", "FLASH": "Lựu Đạn Choáng", "SMOKE": "Lựu Đạn Khói",
            "PAN": "Chảo", "SABER": "Đao", "BAT": "Gậy Bóng Chày", "SWORD": "Kiếm", "SCYTHE": "Lưỡi Hái"
        }
        
        short_names = {
            "AK-47": "AK-47", "SHOTGUN": "Shotgun", "SMG": "Tiểu Liên", "FLAMETHROWER": "Súng Lửa",
            "FRAG": "L.Đ Nổ", "FLASH": "L.Đ Choáng", "SMOKE": "L.Đ Khói",
            "PAN": "Chảo", "SABER": "Đao", "BAT": "Gậy", "SWORD": "Kiếm", "SCYTHE": "Lưỡi Hái"
        }
        
        details_db = {
            "AK-47": {
                "title": "AK-47", "cat": "Vũ Khí Chính", 
                "desc": "Súng trường tấn công huyền thoại. Sát thương cao, tầm bắn xa và ổn định.",
                "l1": "SÁT THƯƠNG", "v1": 6.5, "l2": "TỐC ĐỘ BẮN", "v2": 6.0
            },
            "SHOTGUN": {
                "title": "SHOTGUN", "cat": "Vũ Khí Chính",
                "desc": "Vũ khí cận chiến tầm gần hủy diệt. Bắn ra chùm đạn nhiều viên cùng lúc.",
                "l1": "SÁT THƯƠNG", "v1": 9.0, "l2": "TỐC ĐỘ BẮN", "v2": 2.0
            },
            "SMG": {
                "title": "TIỂU LIÊN SMG", "cat": "Vũ Khí Chính",
                "desc": "Tốc độ bắn cực nhanh và độ linh hoạt cao. Thích hợp vừa chạy vừa bắn.",
                "l1": "SÁT THƯƠNG", "v1": 4.5, "l2": "TỐC ĐỘ BẮN", "v2": 8.5
            },
            "FLAMETHROWER": {
                "title": "SÚNG PHUN LỬA", "cat": "Vũ Khí Chính",
                "desc": "Thiêu rụi kẻ địch trong phạm vi hình nón phía trước. Gây sát thương liên tục.",
                "l1": "SÁT THƯƠNG", "v1": 5.5, "l2": "TỐC ĐỘ BẮN", "v2": 9.5
            },
            "FRAG": {
                "title": "LỰU ĐẠN NỔ", "cat": "Trang Bị Phụ",
                "desc": "Ném ra sau 1.5s sẽ kích nổ, gây sát thương cực lớn lên mọi kẻ địch xung quanh.",
                "l1": "SÁT THƯƠNG", "v1": 9.5, "l2": "BÁN KÍNH NỔ", "v2": 7.0
            },
            "FLASH": {
                "title": "LỰU CHOÁNG", "cat": "Trang Bị Phụ",
                "desc": "Gây mù toàn diện kẻ địch trong tầm ảnh hưởng, khiến chúng đứng bất động.",
                "l1": "TẦM CHOÁNG", "v1": 8.5, "l2": "THỜI GIAN", "v2": 8.0
            },
            "SMOKE": {
                "title": "LỰU ĐẠN KHÓI", "cat": "Trang Bị Phụ",
                "desc": "Tạo một đám mây khói lớn che mắt kẻ địch. Địch không thể nhìn thấy hay bắn xuyên qua.",
                "l1": "BÁN KÍNH KHÓI", "v1": 9.0, "l2": "THỜI GIAN KHÓI", "v2": 9.5
            },
            "PAN": {
                "title": "CHẢO CHIÊN", "cat": "Vũ Khí Cận Chiến",
                "desc": "Món bảo bối cận chiến có khả năng đẩy lùi kẻ địch cực mạnh khi đánh trúng.",
                "l1": "SÁT THƯƠNG", "v1": 4.5, "l2": "ĐẨY LÙI", "v2": 8.0
            },
            "SABER": {
                "title": "ĐAO SẮC BÉN", "cat": "Vũ Khí Cận Chiến",
                "desc": "Lưỡi đao nặng nề chém ra những nhát cực kỳ uy lực, sát thương chí mạng.",
                "l1": "SÁT THƯƠNG", "v1": 8.5, "l2": "TẦM ĐÁNH", "v2": 6.0
            },
            "BAT": {
                "title": "GẬY BÓNG CHÀY", "cat": "Vũ Khí Cận Chiến",
                "desc": "Gậy bóng chày hợp kim cứng cáp, vụt bay kẻ địch ra xa và làm choáng nhẹ.",
                "l1": "SÁT THƯƠNG", "v1": 5.5, "l2": "ĐẨY LÙI", "v2": 9.0
            },
            "SWORD": {
                "title": "KIẾM KATANA", "cat": "Vũ Khí Cận Chiến",
                "desc": "Đường kiếm thanh thoát, tốc độ chém nhanh và phản ứng linh hoạt trong thực chiến.",
                "l1": "SÁT THƯƠNG", "v1": 6.5, "l2": "TẦM ĐÁNH", "v2": 5.5
            },
            "SCYTHE": {
                "title": "LƯỠI HÁI TỬ THẦN", "cat": "Vũ Khí Cận Chiến",
                "desc": "Vũ khí quét diện rộng góc cực đại (1.6 radian), tiêu diệt hàng loạt địch đứng gần.",
                "l1": "SÁT THƯƠNG", "v1": 7.5, "l2": "TẦM ĐÁNH", "v2": 8.5
            }
        }

        grid_y = 125
        self._weapon_rects = {}
        self._grenade_rects = {}
        self._melee_rects = {}
        self._tab_rects = []

        mx, my = pygame.mouse.get_pos()
        mouse_pos = (mx - getattr(self, 'tilt_x', 0), my - getattr(self, 'tilt_y', 0))
        hovered_item = None
        hovered_type = None

        # ── VẼ TAB BAR NGANG ──────────────────────────────────────────────────
        tabs_info = ["1. SÚNG CHÍNH", "2. CẬN CHIẾN", "3. LỰU ĐẠN"]
        tab_w, tab_h = 200, 40
        tab_gap = 15
        tab_start_x = 90
        
        for ti, label in enumerate(tabs_info):
            tx = tab_start_x + ti * (tab_w + tab_gap)
            tr = pygame.Rect(tx, grid_y, tab_w, tab_h)
            self._tab_rects.append(tr)
            
            is_active = (self.loadout_tab == ti)
            is_hov = tr.collidepoint(mouse_pos)
            is_focused = (self.loadout_focus == "TABS" and self.loadout_tab == ti)
            
            tbg = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            if is_focused:
                tbg.fill((235, 120, 0, 40))
                tc = (235, 120, 0)
                border_w = 3
            elif is_active:
                tbg.fill((80, 160, 70, 30))
                tc = (80, 160, 70)
                border_w = 2
            elif is_hov:
                tbg.fill((255, 255, 255, 15))
                tc = WHITE
                border_w = 1
            else:
                tbg.fill((10, 15, 10, 180))
                tc = (130, 140, 130)
                border_w = 1
                
            screen.blit(tbg, (tx, grid_y))
            pygame.draw.rect(screen, tc, tr, border_w, border_radius=2)
            
            txt_surf = self.font_normal.render(label, True, tc)
            screen.blit(txt_surf, (tx + (tab_w - txt_surf.get_width()) // 2, grid_y + (tab_h - txt_surf.get_height()) // 2))
  
        # Khung chứa nội dung bên trái (Expanded Content Box to 340px height)
        content_box = pygame.Rect(80, 185, 650, 340)
        pygame.draw.rect(screen, (10, 12, 14), content_box)
        pygame.draw.rect(screen, (150, 160, 170), content_box, 1, border_radius=2)
  
        # ── VẼ NỘI DUNG TỪNG TRANG (TABS) ──────────────────────────────────────
        if self.loadout_tab == 0:
            # TRANG 1: KHO SÚNG CHÍNH (Larger cards)
            card_w, card_h = 300, 135
            w_gap = 20
            for wi, w in enumerate(self.weapons):
                col = wi % 2; row = wi // 2
                bx = 95 + col * (card_w + w_gap)
                by = 200 + row * (card_h + w_gap)
  
                pr = pygame.Rect(bx, by, card_w, card_h)
                self._weapon_rects[w] = pr
                
                is_equipped = w in self.equipped_weapons
                slot_num = (self.equipped_weapons.index(w)+1) if is_equipped else None
                is_hov = pr.collidepoint(mouse_pos)
                is_focused = (self.loadout_focus == "ITEMS" and self.loadout_selected_index == wi)
                
                if is_hov:
                    self.loadout_focus = "ITEMS"
                    self.loadout_selected_index = wi
                    is_focused = True
  
                if is_focused:
                    hovered_item = w
                    hovered_type = "WEAPON"
  
                if is_focused:    wc = (235, 120, 0)
                elif w not in self.unlocked_weapons: wc = (90, 95, 100)
                elif is_equipped: wc = (100, 180, 80)
                elif is_hov:      wc = WHITE
                else:             wc = (130, 140, 130)
  
                bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                if is_focused:   bg.fill((235, 120, 0, 30))
                elif is_equipped: bg.fill((80, 160, 70, 20))
                elif is_hov:      bg.fill((255, 255, 255, 15))
                else:             bg.fill((10, 15, 10, 180))
                screen.blit(bg, (bx, by))
  
                # Accent corner details for card
                for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                    cx_c = bx if dx==1 else bx+card_w
                    cy_c = by if dy==1 else by+card_h
                    pygame.draw.line(screen, wc, (cx_c, cy_c), (cx_c+6*dx, cy_c), 1)
                    pygame.draw.line(screen, wc, (cx_c, cy_c), (cx_c, cy_c+6*dy), 1)

                # Ảnh súng bên trái (Dịch chuyển cân đối)
                if w in self.weapon_images:
                    img_scaled = pygame.transform.smoothscale(self.weapon_images[w], (120, 60))
                    # Nền mờ cho ảnh súng
                    img_bg = pygame.Surface((126, 66), pygame.SRCALPHA)
                    img_bg.fill((20, 25, 30, 120))
                    screen.blit(img_bg, (bx + 8, by + (card_h - 66)//2))
                    pygame.draw.rect(screen, (50, 60, 75), (bx + 8, by + (card_h - 66)//2, 126, 66), 1)
                    screen.blit(img_scaled, (bx + 11, by + (card_h - 60)//2))
  
                # Tên và trạng thái bên phải
                wn = self.font_normal.render(dnames[w], True, wc)
                screen.blit(wn, (bx + 145, by + 30))
  
                if w not in self.unlocked_weapons:
                    price = self.prices.get(w, 0)
                    if is_focused:
                        status_str = f"MUA: {price} $"
                        sc = (255, 80, 80) if self.gold < price else (255, 215, 0)
                    else:
                        status_str = f"KHÓA - {price} $"
                        sc = (120, 120, 120)
                else:
                    if is_equipped:
                        status_str = f"ĐANG DÙNG (KHE {slot_num})"
                        sc = (255, 100, 100) if is_focused else (100, 180, 80)
                    else:
                        status_str = "SẴN SÀNG"
                        sc = (100, 220, 80) if is_focused else (130, 140, 130)
                
                st_txt = self.font_small.render(status_str, True, sc)
                screen.blit(st_txt, (bx + 145, by + 65))
  
                pygame.draw.rect(screen, wc, pr, 2 if is_focused else 1, border_radius=2)
  
        elif self.loadout_tab == 1:
            # TRANG 2: VŨ KHÍ CẬN CHIẾN (Spacious Melee Cards)
            card_w, card_h = 195, 135
            for mi, m in enumerate(self.melee_list):
                col = mi % 3; row = mi // 3
                bx = 95 + col * (card_w + 20)
                by = 200 + row * (card_h + 20)
  
                pr = pygame.Rect(bx, by, card_w, card_h)
                self._melee_rects[m] = pr
                
                is_equipped = (self.equipped_melee == m)
                is_hov = pr.collidepoint(mouse_pos)
                is_focused = (self.loadout_focus == "ITEMS" and self.loadout_selected_index == mi)
                
                if is_hov:
                    self.loadout_focus = "ITEMS"
                    self.loadout_selected_index = mi
                    is_focused = True
  
                if is_focused:
                    hovered_item = m
                    hovered_type = "MELEE"
  
                if is_focused:    wc = (235, 120, 0)
                elif m not in self.unlocked_weapons: wc = (90, 95, 100)
                elif is_equipped: wc = (100, 180, 80)
                elif is_hov:      wc = WHITE
                else:             wc = (130, 140, 130)
  
                bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                if is_focused:   bg.fill((235, 120, 0, 30))
                elif is_equipped: bg.fill((80, 160, 70, 20))
                elif is_hov:      bg.fill((255, 255, 255, 15))
                else:             bg.fill((10, 15, 10, 180))
                screen.blit(bg, (bx, by))

                # Corner accent lines
                for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                    cx_c = bx if dx==1 else bx+card_w
                    cy_c = by if dy==1 else by+card_h
                    pygame.draw.line(screen, wc, (cx_c, cy_c), (cx_c+6*dx, cy_c), 1)
                    pygame.draw.line(screen, wc, (cx_c, cy_c), (cx_c, cy_c+6*dy), 1)
 
                # Ảnh ở giữa trên
                if m in self.melee_images:
                    img_scaled = pygame.transform.smoothscale(self.melee_images[m], (100, 50))
                    screen.blit(img_scaled, (bx + (card_w - 100)//2, by + 25))
 
                # Tên ở dưới
                mn = self.font_small.render(dnames[m], True, wc)
                screen.blit(mn, (bx + card_w//2 - mn.get_width()//2, by + card_h - 26))
 
                pygame.draw.rect(screen, wc, pr, 2 if is_focused else 1, border_radius=2)
 
                if m not in self.unlocked_weapons:
                    price = self.prices.get(m, 0)
                    color_bg = (200, 50, 50) if self.gold < price else (255, 215, 0)
                    pygame.draw.rect(screen, color_bg, (bx, by, card_w, 18), border_radius=2)
                    bt_txt = self.font_small.render(f"MUA: {price} $", True, (10, 12, 14))
                    screen.blit(bt_txt, (bx+card_w//2-bt_txt.get_width()//2, by+1))
                else:
                    if is_equipped:
                        pygame.draw.rect(screen, (100, 180, 80), (bx, by, card_w, 18), border_radius=2)
                        bt_txt = self.font_small.render("ĐANG TRANG BỊ", True, (10, 12, 14))
                        screen.blit(bt_txt, (bx+card_w//2-bt_txt.get_width()//2, by+1))
                    elif is_focused:
                        pygame.draw.rect(screen, (245, 165, 30), (bx, by, card_w, 18), border_radius=2)
                        bt_txt = self.font_small.render("ENTER: CHỌN", True, (10, 12, 14))
                        screen.blit(bt_txt, (bx+card_w//2-bt_txt.get_width()//2, by+1))
 
        elif self.loadout_tab == 2:
            # TRANG 3: LỰU ĐẠN (Expanded cards height)
            card_w, card_h = 195, 290
            for gi, g in enumerate(self.grenades_list):
                bx = 95 + gi * (card_w + 20)
                by = 210
 
                pr = pygame.Rect(bx, by, card_w, card_h)
                self._grenade_rects[g] = pr
                
                is_equipped = (self.equipped_grenade == g)
                is_hov = pr.collidepoint(mouse_pos)
                is_focused = (self.loadout_focus == "ITEMS" and self.loadout_selected_index == gi)
                
                if is_hov:
                    self.loadout_focus = "ITEMS"
                    self.loadout_selected_index = gi
                    is_focused = True
 
                if is_focused:
                    hovered_item = g
                    hovered_type = "GRENADE"
 
                if is_focused:    wc = (235, 120, 0)
                elif g not in self.unlocked_weapons: wc = (90, 95, 100)
                elif is_equipped: wc = (220, 60, 50)
                elif is_hov:      wc = WHITE
                else:             wc = (130, 140, 130)
 
                bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                if is_focused:   bg.fill((235, 120, 0, 30))
                elif is_equipped: bg.fill((220, 60, 50, 20))
                elif is_hov:      bg.fill((255, 255, 255, 15))
                else:             bg.fill((10, 15, 10, 180))
                screen.blit(bg, (bx, by))
 
                # Corner accents
                for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                    cx_c = bx if dx==1 else bx+card_w
                    cy_c = by if dy==1 else by+card_h
                    pygame.draw.line(screen, wc, (cx_c, cy_c), (cx_c+6*dx, cy_c), 1)
                    pygame.draw.line(screen, wc, (cx_c, cy_c), (cx_c, cy_c+6*dy), 1)

                # Ảnh lựu đạn lớn ở trên
                if g in self.grenade_images:
                    img_scaled = pygame.transform.smoothscale(self.grenade_images[g], (110, 110))
                    # Frame for image
                    img_bg = pygame.Surface((116, 116), pygame.SRCALPHA)
                    img_bg.fill((20, 25, 30, 120))
                    screen.blit(img_bg, (bx + (card_w - 116)//2, by + 20))
                    pygame.draw.rect(screen, (50, 60, 75), (bx + (card_w - 116)//2, by + 20, 116, 116), 1)
                    screen.blit(img_scaled, (bx + (card_w - 110)//2, by + 23))
 
                # Tên ở giữa
                gn = self.font_normal.render(dnames[g], True, wc)
                screen.blit(gn, (bx + card_w//2 - gn.get_width()//2, by + 165))
 
                pygame.draw.rect(screen, wc, pr, 2 if is_focused else 1, border_radius=2)
 
                if g not in self.unlocked_weapons:
                    price = self.prices.get(g, 0)
                    if is_focused:
                        status_str = f"MUA: {price} $"
                        sc = (255, 80, 80) if self.gold < price else (255, 215, 0)
                    else:
                        status_str = f"KHÓA - {price} $"
                        sc = (120, 120, 120)
                else:
                    if is_equipped:
                        status_str = "ĐANG CHỌN"
                        sc = (220, 60, 50)
                    elif is_focused:
                        status_str = "ENTER: CHỌN"
                        sc = (235, 120, 0)
                    elif is_hov:
                        status_str = "CLICK ĐỂ CHỌN"
                        sc = WHITE
                    else:
                        status_str = "SẴN SÀNG"
                        sc = (130, 140, 130)
                st_txt = self.font_small.render(status_str, True, sc)
                screen.blit(st_txt, (bx + card_w//2 - st_txt.get_width()//2, by + 235))
 
        # ── 4. PANEL CHI TIẾT (Bên phải - D_H expanded to 340px) ──────────────────
        D_X = 752; D_Y = 185; D_W = 368; D_H = 340
        d_box = pygame.Rect(D_X, D_Y, D_W, D_H)
 
        # Nền card
        d_bg = pygame.Surface((D_W, D_H), pygame.SRCALPHA)
        d_bg.fill((8, 11, 16, 235))
        screen.blit(d_bg, (D_X, D_Y))
        pygame.draw.rect(screen, (52, 62, 78), d_box, 1, border_radius=3)
 
        # Header bar
        hdr_s = pygame.Surface((D_W, 32), pygame.SRCALPHA)
        hdr_s.fill((235, 120, 0, 32))
        screen.blit(hdr_s, (D_X, D_Y))
        pygame.draw.line(screen, (235, 120, 0), (D_X, D_Y + 32), (D_X + D_W, D_Y + 32), 1)
        pygame.draw.rect(screen, (235, 120, 0), (D_X, D_Y, 4, 32), border_radius=1)
        lbl_d = self.font_normal.render("CHI TIẾT TRANG BỊ", True, (235, 120, 0))
        screen.blit(lbl_d, (D_X + 14, D_Y + 7))
 
        # Fallback hovered item
        if not hovered_item:
            if self.loadout_tab == 0:
                hovered_item = self.weapons[self.loadout_selected_index] if self.loadout_focus == "ITEMS" else (self.equipped_weapons[0] if self.equipped_weapons else "AK-47")
                hovered_type = "WEAPON"
            elif self.loadout_tab == 1:
                hovered_item = self.melee_list[self.loadout_selected_index] if self.loadout_focus == "ITEMS" else self.equipped_melee
                hovered_type = "MELEE"
            else:
                hovered_item = self.grenades_list[self.loadout_selected_index] if self.loadout_focus == "ITEMS" else self.equipped_grenade
                hovered_type = "GRENADE"
 
        if hovered_item in details_db:
            info    = details_db[hovered_item]
            cat_col = (235, 120, 0) if hovered_type == "WEAPON" else ((220, 60, 50) if hovered_type == "GRENADE" else (100, 180, 80))
 
            # ── Preview image (căn giữa, khung viền) ──
            preview_img = None
            if hovered_item in self.weapon_images:
                preview_img = pygame.transform.smoothscale(self.weapon_images[hovered_item], (142, 68))
            elif hovered_item in self.grenade_images:
                preview_img = pygame.transform.smoothscale(self.grenade_images[hovered_item], (72, 72))
            elif hovered_item in self.melee_images:
                preview_img = pygame.transform.smoothscale(self.melee_images[hovered_item], (120, 58))
 
            if preview_img:
                pw, ph = preview_img.get_width(), preview_img.get_height()
                px = D_X + (D_W - pw) // 2
                py = D_Y + 42
                frm = pygame.Rect(px-5, py-5, pw+10, ph+10)
                frm_bg = pygame.Surface((pw+10, ph+10), pygame.SRCALPHA)
                frm_bg.fill((16, 20, 28, 230))
                screen.blit(frm_bg, (px-5, py-5))
                pygame.draw.rect(screen, (48, 58, 72), frm, 1, border_radius=2)
                screen.blit(preview_img, (px, py))

                # ── HOLOGRAPHIC SCANNER LINE ANIMATION ──
                elapsed_time = pygame.time.get_ticks() / 1000.0
                scan_y_pct = 0.5 + 0.5 * math.sin(elapsed_time * 4.0)
                scan_line_y = py + int(ph * scan_y_pct)
                
                # Draw neon scanner line across the preview image
                pygame.draw.line(screen, (245, 165, 30), (px, scan_line_y), (px + pw, scan_line_y), 2)
                # Neon glow buffer
                scan_glow = pygame.Surface((pw, 6), pygame.SRCALPHA)
                scan_glow.fill((245, 165, 30, 50))
                screen.blit(scan_glow, (px, scan_line_y - 3))

                # Corner accents
                for ax,ay,adx,ady in [(px-5,py-5,1,1),(px+pw+5,py-5,-1,1),(px-5,py+ph+5,1,-1),(px+pw+5,py+ph+5,-1,-1)]:
                    pygame.draw.line(screen, cat_col, (ax,ay), (ax+adx*8, ay), 2)
                    pygame.draw.line(screen, cat_col, (ax,ay), (ax, ay+ady*8), 2)
                content_y = py + ph + 16
            else:
                content_y = D_Y + 42
 
            # ── Category badge + Name ──
            cat_s = self.font_small.render(info["cat"].upper(), True, cat_col)
            cat_bw = cat_s.get_width() + 14
            cat_bb = pygame.Surface((cat_bw, 20), pygame.SRCALPHA)
            cat_bb.fill((*cat_col, 32))
            screen.blit(cat_bb, (D_X+12, content_y))
            pygame.draw.rect(screen, cat_col, pygame.Rect(D_X+12, content_y, cat_bw, 20), 1, border_radius=2)
            screen.blit(cat_s, (D_X+19, content_y+3))
 
            title_s = self.font_normal.render(info["title"], True, (232, 238, 248))
            screen.blit(title_s, (D_X+12, content_y+26))
 
            pygame.draw.line(screen, (38, 48, 60), (D_X+12, content_y+52), (D_X+D_W-12, content_y+52), 1)
 
            # ── Mô tả xuống dòng (tối đa 2 dòng) ──
            d_words = info["desc"].split(' '); d_lns = []; d_cur = ""
            for dw in d_words:
                t = d_cur + dw + " "
                if self.font_small.size(t)[0] > D_W-28: d_lns.append(d_cur.strip()); d_cur = dw + " "
                else: d_cur = t
            d_lns.append(d_cur.strip())
            for dli, dl in enumerate(d_lns[:2]):
                screen.blit(self.font_small.render(dl, True, (158, 168, 185)), (D_X+12, content_y+60+dli*17))
 
            # ── Segmented LED Stats bars (equalizer block style) ──
            stat_y_start = D_Y + D_H - 88
            pygame.draw.line(screen, (38, 48, 60), (D_X+12, stat_y_start-8), (D_X+D_W-12, stat_y_start-8), 1)
 
            def draw_stat_bar(scr, x, y, label, val):
                bar_w = D_W - 28
                lbl_s = self.font_small.render(label, True, (138, 148, 168))
                scr.blit(lbl_s, (x, y))
                pct_s = self.font_small.render(f"{int(val*10)}%", True, (212, 218, 228))
                scr.blit(pct_s, (x + bar_w - pct_s.get_width(), y))
                by2 = y + 16
                
                # Background track
                pygame.draw.rect(scr, (16, 20, 28), (x, by2, bar_w, 8), border_radius=2)
                pygame.draw.rect(scr, (42, 52, 66), (x, by2, bar_w, 8), 1, border_radius=2)
                
                # Segmented LED drawing (10 segments)
                seg_w = (bar_w - 9) // 10
                for bi in range(10):
                    bx2 = x + bi * (seg_w + 1)
                    is_filled = (val >= bi + 0.5)
                    if is_filled:
                        # Draw neon LED block
                        pygame.draw.rect(scr, cat_col, (bx2, by2 + 1, seg_w, 6))
                        # Draw thin high-brightness highlight line on top
                        pygame.draw.line(scr, (255, 255, 255, 140), (bx2, by2 + 1), (bx2 + seg_w - 1, by2 + 1), 1)
 
            draw_stat_bar(screen, D_X+12, stat_y_start,    info["l1"], info["v1"])
            draw_stat_bar(screen, D_X+12, stat_y_start+32, info["l2"], info["v2"])
 
        # ── 5. LOADOUT SUMMARY (Spacious bottom dashboard) ──────────────────────────────
        summary_y = 540
        SUM_W = 1040; SUM_H = 150
        sum_rect = pygame.Rect(80, summary_y, SUM_W, SUM_H)
 
        sum_bg = pygame.Surface((SUM_W, SUM_H), pygame.SRCALPHA)
        sum_bg.fill((8, 11, 16, 235))
        screen.blit(sum_bg, (80, summary_y))
        pygame.draw.rect(screen, (52, 62, 78), sum_rect, 1, border_radius=3)
 
        # Summary header accent
        sh_bg = pygame.Surface((SUM_W, 30), pygame.SRCALPHA)
        sh_bg.fill((235, 120, 0, 28))
        screen.blit(sh_bg, (80, summary_y))
        pygame.draw.line(screen, (235, 120, 0), (80, summary_y+30), (80+SUM_W, summary_y+30), 1)
        pygame.draw.rect(screen, (235, 120, 0), (80, summary_y, 4, 30), border_radius=1)
        lbl_sum = self.font_normal.render("》 HỆ THỐNG VŨ KHÍ TÁC CHIẾN RA TRẬN", True, (235, 120, 0))
        screen.blit(lbl_sum, (98, summary_y+6))
 
        # READY badge (top right)
        rdy_s = self.font_small.render("SẴN SÀNG CHIẾN ĐẤU (READY)", True, (80, 200, 100))
        pygame.draw.circle(screen, (80, 200, 100), (80+SUM_W-rdy_s.get_width()-24, summary_y+15), 4)
        screen.blit(rdy_s, (80+SUM_W-rdy_s.get_width()-12, summary_y+8))
 
        # Slot definitions
        slot_defs = []
        for si3 in range(3):
            if si3 < len(self.equipped_weapons):
                w_id = self.equipped_weapons[si3]
                slot_defs.append({"lbl": f"SÚNG KHE {si3+1}", "name": short_names[w_id], "col": (245,165,30),
                                   "img_k": w_id, "img_d": self.weapon_images, "img_sz": (44,28)})
            else:
                slot_defs.append({"lbl": f"KHE SÚNG {si3+1}", "name": "TRỐNG", "col": (55,65,80),
                                   "img_k": None, "img_d": {}, "img_sz": (44,28)})
        g_id = self.equipped_grenade
        slot_defs.append({"lbl": "LỰU ĐẠN", "name": short_names[g_id], "col": (220,60,50),
                          "img_k": g_id, "img_d": self.grenade_images, "img_sz": (30,30)})
        m_id = self.equipped_melee
        slot_defs.append({"lbl": "CẬN CHIẾN", "name": short_names[m_id], "col": (100,180,80),
                          "img_k": m_id, "img_d": self.melee_images, "img_sz": (40,26)})

        n_slots = len(slot_defs)
        sl_w = 178; sl_h = 64; sl_gap = 14
        sx0 = 100 + (SUM_W - (n_slots*sl_w + (n_slots-1)*sl_gap)) // 2
        sy0 = summary_y + 44

        for si4, sd in enumerate(slot_defs):
            sx = sx0 + si4*(sl_w+sl_gap)
            sr = pygame.Rect(sx, sy0, sl_w, sl_h)
            sc4 = sd["col"]
            # Card bg
            sl_bg = pygame.Surface((sl_w, sl_h), pygame.SRCALPHA)
            sl_bg.fill((*sc4, 14))
            screen.blit(sl_bg, (sx, sy0))
            pygame.draw.rect(screen, sc4, sr, 1, border_radius=2)
            # Slot label
            lbl_sl = self.font_small.render(sd["lbl"], True, sc4)
            screen.blit(lbl_sl, (sx+8, sy0+4))
            # Thumbnail + name
            if sd["img_k"] and sd["img_k"] in sd["img_d"]:
                iw, ih = sd["img_sz"]
                thumb = pygame.transform.smoothscale(sd["img_d"][sd["img_k"]], (iw,ih))
                screen.blit(thumb, (sx+8, sy0+sl_h-ih-6))
                nm_s = self.font_small.render(sd["name"], True, sc4)
                screen.blit(nm_s, (sx+iw+14, sy0+sl_h//2+4))
            else:
                nm_s = self.font_small.render(sd["name"], True, sc4)
                screen.blit(nm_s, (sx+8, sy0+sl_h//2+4))
            # Ready dot
            dc2 = sc4 if sd["name"] not in ("TRỐNG", "EMPTY") else (45,52,65)
            pygame.draw.circle(screen, dc2, (sx+sl_w-10, sy0+sl_h-10), 4)

        # Help hint
        ct = self.font_small.render("Click hoặc phím mũi tên để chọn trang bị  •  ESC để lưu và quay lại", True, (88,98,115))
        screen.blit(ct, (SCREEN_W//2-ct.get_width()//2, summary_y+SUM_H+10))

    def _draw_item_icon(self, screen, name, rect, color):
        rx, ry, rw, rh = rect
        # Khung viền mờ của icon
        pygame.draw.rect(screen, (35, 45, 55), rect, 1, border_radius=2)
        
        # Nền icon phát sáng nhẹ
        glow_s = pygame.Surface((rw, rh), pygame.SRCALPHA)
        pygame.draw.rect(glow_s, (*color, 16), (0, 0, rw, rh), border_radius=2)
        screen.blit(glow_s, (rx, ry))
        
        cx, cy = rx + rw // 2, ry + rh // 2
        
        # Tải ảnh gốc nếu có sẵn
        if hasattr(self, 'inventory_images') and name in self.inventory_images:
            img = pygame.transform.smoothscale(self.inventory_images[name], (rw-4, rh-4))
            screen.blit(img, (rx+2, ry+2))
            return

        # Vẽ vector/wireframe kĩ thuật số cho từng loại vật phẩm
        if name in ("Túi Cứu Thương", "Thuốc Hồi Phục"):
            # Vali/Hộp cứu thương
            pygame.draw.rect(screen, color, (cx - 13, cy - 7, 26, 17), 1, border_radius=2)
            pygame.draw.rect(screen, color, (cx - 5, cy - 11, 10, 4), 1)
            # Chữ thập y tế
            pygame.draw.line(screen, color, (cx - 5, cy + 1), (cx + 5, cy + 1), 2)
            pygame.draw.line(screen, color, (cx, cy - 4), (cx, cy + 6), 2)
            
        elif name == "Tiêm Adrenaline":
            # Ống tiêm Adrenaline
            pygame.draw.line(screen, color, (cx - 10, cy + 10), (cx + 8, cy - 8), 2)
            pygame.draw.line(screen, color, (cx + 8, cy - 8), (cx + 13, cy - 13), 1) # Kim tiêm
            pygame.draw.line(screen, color, (cx - 10, cy + 10), (cx - 13, cy + 13), 3) # Pit-tông
            # Thuốc phát sáng
            pygame.draw.circle(screen, (80, 220, 100), (cx - 1, cy + 1), 3)
            
        elif name == "Nước Uống Năng Lượng":
            # Lon nước tăng lực
            pygame.draw.rect(screen, color, (cx - 8, cy - 12, 16, 24), 1, border_radius=2)
            # Tia sét vàng
            pygame.draw.lines(screen, (255, 215, 0), False, [(cx-2, cy-7), (cx+2, cy-2), (cx-2, cy+1), (cx+2, cy+6)], 2)
            
        elif name in ("Giáp Titan Cấp III", "Áp Lực Cường Hóa"):
            # Tấm giáp chống đạn / Khiên
            pts = [(cx, cy - 13), (cx + 11, cy - 7), (cx + 9, cy + 6), (cx, cy + 13), (cx - 9, cy + 6), (cx - 11, cy - 7)]
            pygame.draw.polygon(screen, color, pts, 1)
            pygame.draw.line(screen, color, (cx, cy - 7), (cx, cy + 9), 1)
            
        elif name == "Mặt Nạ Chống Khói":
            # Mặt nạ phòng độc
            pygame.draw.circle(screen, color, (cx, cy - 2), 9, 1)
            pygame.draw.circle(screen, color, (cx - 9, cy + 3), 4, 1) # Filter trái
            pygame.draw.circle(screen, color, (cx + 9, cy + 3), 4, 1) # Filter phải
            pygame.draw.rect(screen, color, (cx - 2, cy + 1, 4, 7), 1)
            
        elif name in ("Bảo Vệ Năng Lượng", "Radar Siêu Cấp"):
            # Khiên năng lượng / Radar quét
            pygame.draw.circle(screen, color, (cx, cy), 12, 1)
            pygame.draw.circle(screen, color, (cx, cy), 6, 2)
            # Vạch chia
            for angle in [0, 90, 180, 270]:
                rad = math.radians(angle)
                pygame.draw.line(screen, color, (cx + int(math.cos(rad)*12), cy + int(math.sin(rad)*12)), 
                                 (cx + int(math.cos(rad)*15), cy + int(math.sin(rad)*15)), 1)
                                 
        elif name == "Kính Nhìn Đêm":
            # Kính hồng ngoại
            pygame.draw.rect(screen, color, (cx - 14, cy - 5, 28, 10), 1, border_radius=2)
            pygame.draw.circle(screen, (80, 220, 100), (cx - 6, cy), 4, 1)
            pygame.draw.circle(screen, (80, 220, 100), (cx + 6, cy), 4, 1)
            
        elif name == "Bộ Dò Radar":
            # Màn hình radar quét xoay
            pygame.draw.circle(screen, color, (cx, cy), 13, 1)
            angle = (pygame.time.get_ticks() / 120.0) % (2 * math.pi)
            pygame.draw.line(screen, color, (cx, cy), (cx + int(math.cos(angle)*13), cy + int(math.sin(angle)*13)), 2)
            
        elif name in ("Thẻ Thảo Dược", "Thẻ Truy Cập"):
            # Thẻ chip / Thẻ truy cập
            pygame.draw.rect(screen, color, (cx - 13, cy - 9, 26, 18), 1, border_radius=1)
            pygame.draw.rect(screen, color, (cx - 5, cy - 3, 10, 6), 1) # Con chip
            
        elif name == "Drone Hỗ Trợ":
            # Drone 4 cánh
            pygame.draw.circle(screen, color, (cx, cy), 4, 1)
            pygame.draw.line(screen, color, (cx - 4, cy - 4), (cx - 11, cy - 11), 1)
            pygame.draw.line(screen, color, (cx + 4, cy - 4), (cx + 11, cy - 11), 1)
            pygame.draw.line(screen, color, (cx - 4, cy + 4), (cx - 11, cy + 11), 1)
            pygame.draw.line(screen, color, (cx + 4, cy + 4), (cx + 11, cy + 11), 1)
            for rx2, ry2 in [(cx - 11, cy - 11), (cx + 11, cy - 11), (cx - 11, cy + 11), (cx + 11, cy + 11)]:
                pygame.draw.line(screen, color, (rx2 - 3, ry2), (rx2 + 3, ry2), 1)
        else:
            pygame.draw.rect(screen, color, (cx - 9, cy - 9, 18, 18), 1)

    def _draw_inventory(self, screen):
        panel = Panel(SCREEN_W//2-480, 45, 960, 710, "KHO ĐỒ — INVENTORY VAULT")
        panel.draw(screen, self.font_normal)
        self._close_btn_rect = self._draw_close_button(screen, SCREEN_W//2 + 480 - 45, 53, 30)

        gold_txt = self.font_normal.render(f"VÀNG: {self.gold} $", True, (255, 215, 0))
        screen.blit(gold_txt, (SCREEN_W//2 + 480 - gold_txt.get_width() - 60, 55))

        rarity_col = {
            "THƯỜNG": (110, 120, 130), "HIẾM": (60, 140, 200),
            "SỬ THI": (160, 90, 210), "HUYỀN THOẠI": (210, 140, 20), "SIÊU HIẾM": (200, 80, 200)
        }

        mouse_pos = pygame.mouse.get_pos()
        mx_cur, my_cur = mouse_pos
        cur_tilt_x = int((mx_cur - SCREEN_W / 2) / (SCREEN_W / 2) * 12)
        cur_tilt_y = int((my_cur - SCREEN_H / 2) / (SCREEN_H / 2) * 12)
        mpos = (mx_cur - cur_tilt_x, my_cur - cur_tilt_y)

        # ── TABS ──
        self._inv_tab_rects = []
        tab_w = 210
        tab_h = 40
        tab_gap = 15
        num_tabs = len(self.inventory_catalog)
        total_tab_w = num_tabs * tab_w + (num_tabs - 1) * tab_gap
        tab_start_x = SCREEN_W // 2 - total_tab_w // 2
        grid_y = 110

        for ti, (cat_name, cc, items) in enumerate(self.inventory_catalog):
            tx = tab_start_x + ti * (tab_w + tab_gap)
            tr = pygame.Rect(tx, grid_y, tab_w, tab_h)
            self._inv_tab_rects.append(tr)
            
            is_active = (self.inventory_tab == ti)
            is_hov = tr.collidepoint(mpos)
            is_focused = (self.inventory_focus == "TABS" and self.inventory_tab == ti)
            
            tbg = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            if is_focused:
                tbg.fill((*cc, 80)); tc = cc; border_w = 3
            elif is_active:
                tbg.fill((*cc, 40)); tc = cc; border_w = 2
            elif is_hov:
                tbg.fill((255, 255, 255, 15)); tc = WHITE; border_w = 1
            else:
                tbg.fill((10, 15, 10, 180)); tc = (130, 140, 130); border_w = 1
                
            screen.blit(tbg, (tx, grid_y))
            pygame.draw.rect(screen, tc, tr, border_w, border_radius=2)
            
            txt_surf = self.font_small.render(cat_name, True, tc)
            screen.blit(txt_surf, (tx + (tab_w - txt_surf.get_width()) // 2, grid_y + (tab_h - txt_surf.get_height()) // 2))

        # ── ITEMS GRID ──
        self._inventory_rects = {}
        cat_name, cc, items = self.inventory_catalog[self.inventory_tab]
        
        card_w, card_h = 420, 220
        w_gap, h_gap = 25, 20
        grid_x0 = SCREEN_W // 2 - (card_w * 2 + w_gap) // 2
        grid_y0 = 175

        for ii, item in enumerate(items):
            col = ii % 2
            row = ii // 2
            ix = grid_x0 + col * (card_w + w_gap)
            iy = grid_y0 + row * (card_h + h_gap)
            
            ir = pygame.Rect(ix, iy, card_w, card_h)
            self._inventory_rects[item["name"]] = ir
            
            is_hov = ir.collidepoint(mpos)
            is_focused = (self.inventory_focus == "ITEMS" and self.inventory_selected_index == ii)
            
            rc = rarity_col.get(item["rarity"], (130, 145, 160))
            if is_focused: wc = (235, 120, 0)
            elif is_hov: wc = WHITE
            else: wc = rc
            
            cb = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            if is_focused: cb.fill((235, 120, 0, 30))
            elif is_hov: cb.fill((255, 255, 255, 15))
            else: 
                cb.fill((8, 10, 12, 235))
                tint = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                tint.fill((*rc, 6))
                cb.blit(tint, (0, 0))
            
            screen.blit(cb, (ix, iy))
            pygame.draw.rect(screen, wc, ir, 2 if is_focused else 1, border_radius=2)
            
            for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                c_x = ix if dx==1 else ix+card_w
                c_y = iy if dy==1 else iy+card_h
                pygame.draw.line(screen, wc, (c_x, c_y), (c_x+8*dx, c_y), 1)
                pygame.draw.line(screen, wc, (c_x, c_y), (c_x, c_y+8*dy), 1)

            name_s = self.font_normal.render(item["name"], True, wc)
            screen.blit(name_s, (ix + 130, iy + 20))
            
            # Big Icon Area
            self._draw_item_icon(screen, item["name"], pygame.Rect(ix + 15, iy + 55, 96, 96), rc)
            
            desc_words = item["desc"].split(" ")
            desc_lines = []
            cur_line = ""
            for dw in desc_words:
                test_t = cur_line + dw + " "
                if self.font_small.size(test_t)[0] > card_w - 140:
                    desc_lines.append(cur_line.strip())
                    cur_line = dw + " "
                else: cur_line = test_t
            desc_lines.append(cur_line.strip())
            
            for dli, dl in enumerate(desc_lines[:3]):
                dl_s = self.font_small.render(dl, True, (160, 170, 180))
                screen.blit(dl_s, (ix + 130, iy + 65 + dli * 18))
                
            if "effect" in item:
                eff_s = self.font_small.render(f"Hiệu ứng: {item['effect']}", True, (245, 165, 30))
                screen.blit(eff_s, (ix + 130, iy + 130))
                
            qty = self.inventory.get(item["name"], 0)
            qty_s = self.font_small.render(f"SỞ HỮU: {qty}", True, (100, 180, 80) if qty > 0 else (130, 140, 150))
            screen.blit(qty_s, (ix + 15, iy + 165))
            
            price = item.get("price", self.prices.get(item["name"], 0))
            btn_txt = f"{price} $"
            btn_color = (220, 60, 50) if self.gold < price else (245, 165, 30)
            if is_focused and self.gold >= price: btn_color = (255, 255, 100)
            
            btn_s = self.font_small.render(btn_txt, True, btn_color)
            btn_w = btn_s.get_width() + 16
            pygame.draw.rect(screen, btn_color, (ix + card_w - btn_w - 15, iy + card_h - 40, btn_w, 24), 1, border_radius=2)
            screen.blit(btn_s, (ix + card_w - btn_w - 7, iy + card_h - 38))

        ty = SCREEN_H - 80
        pygame.draw.line(screen, (42, 52, 65), (SCREEN_W//2-455, ty), (SCREEN_W//2+455, ty), 1)
        tip = self.font_small.render("CLICK hoặc MŨI TÊN/ENTER để chọn vật phẩm  •  ESC Quay lại sảnh chờ", True, (88, 98, 115))
        screen.blit(tip, (SCREEN_W//2-tip.get_width()//2, ty+12))

    def _draw_missions(self, screen):
        panel = Panel(SCREEN_W//2-480, 45, 960, 710, "BẢN ĐỒ TÁC CHIẾN — CHỌN CHIẾN DỊCH")
        panel.draw(screen, self.font_normal)
        self._close_btn_rect = self._draw_close_button(screen, SCREEN_W//2 + 480 - 45, 53, 30)

        now = pygame.time.get_ticks()
        elapsed = now / 1000.0

        diff      = ["DỄ", "BÌNH THƯỜNG", "KHÓ", "RẤT KHÓ", "ÁC MỘNG"]
        dcol      = [(100,200,80),(235,180,0),(220,120,20),(220,60,50),(180,30,30)]
        lvl_names = ["RỪNG RẬM NHIỆT ĐỚI","SA MẠC TỬ THẦN","BĂNG CỰC HOANG VU","CĂN CỨ PHÒNG THỦ","CHIẾN HẠM HUỶ DIỆT"]
        objectives = [
            ["Xâm nhập khu vực rừng rậm","Tiêu diệt đội tuần tra địch","Vô hiệu hóa trạm thông tin"],
            ["Vượt qua sa mạc không có nước","Phá hủy xe thiết giáp địch","Bảo vệ điểm trích xuất"],
            ["Sống sót trong bão tuyết","Tấn công căn cứ băng giá","Tiêu diệt chỉ huy địch"],
            ["Xâm nhập căn cứ kiên cố","Vô hiệu hóa hệ thống phòng thủ","Thoát khỏi vòng vây"],
            ["Lên tàu chiến địch","Phá hủy lò phản ứng hạt nhân","Tiêu diệt Đô Đốc địch"],
        ]
        threat_txt= ["THẤP","TRUNG BÌNH","CAO","RẤT CAO","CỰC ĐỘ"]

        self._mission_rects = {}
        lvl = self.selected_mission
        dc  = dcol[lvl]

        # ── LEFT: Danh sách chiến dịch (vertical list of dossiers) ──
        LX = SCREEN_W//2 - 460
        CW = 252; CH = 100; CG = 10
        ly0 = 108

        for mi in range(5):
            is_sel = (mi == lvl)
            my0 = ly0 + mi*(CH+CG)
            mr  = pygame.Rect(LX, my0, CW, CH)
            self._mission_rects[mi] = mr
            mc  = dcol[mi]

            # Dossier card bg
            cb = pygame.Surface((CW, CH), pygame.SRCALPHA)
            cb.fill((*mc, 24) if is_sel else (8,11,15,225))
            screen.blit(cb, (LX, my0))
            pygame.draw.rect(screen, mc, mr, 2 if is_sel else 1, border_radius=3)

            # Tactical corner bracket details
            for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                cx_c = LX if dx==1 else LX+CW
                cy_c = my0 if dy==1 else my0+CH
                pygame.draw.line(screen, mc, (cx_c, cy_c), (cx_c+6*dx, cy_c), 1)
                pygame.draw.line(screen, mc, (cx_c, cy_c), (cx_c, cy_c+6*dy), 1)

            if is_sel:
                pygame.draw.rect(screen, mc, (LX, my0, 5, CH), border_radius=1)
                arr = [(LX+CW+1, my0+CH//2-9),(LX+CW+11, my0+CH//2),(LX+CW+1, my0+CH//2+9)]
                pygame.draw.polygon(screen, mc, arr)

            # Mission number index
            num_s = self.font_title.render(str(mi+1), True, mc if is_sel else (45,55,70))
            screen.blit(num_s, (LX+12, my0+CH//2-num_s.get_height()//2))

            # Name + difficulty
            nm_col = (230,236,245) if is_sel else (120,130,145)
            nm_s   = self.font_small.render(lvl_names[mi], True, nm_col)
            screen.blit(nm_s, (LX+68, my0+12))

            df_s = self.font_small.render(diff[mi], True, mc)
            df_w = df_s.get_width()+12
            df_bg = pygame.Surface((df_w, 20), pygame.SRCALPHA)
            df_bg.fill((*mc, 28))
            screen.blit(df_bg, (LX+68, my0+38))
            pygame.draw.rect(screen, mc, pygame.Rect(LX+68, my0+38, df_w, 20), 1, border_radius=2)
            screen.blit(df_s, (LX+74, my0+40))

            # Threat dots (5 levels)
            for ti in range(5):
                dot_c2 = mc if ti <= mi else (25,32,42)
                pygame.draw.circle(screen, dot_c2, (LX+68+ti*14, my0+76), 4)

        # Vertical divider
        DV_X = LX + CW + 20
        pygame.draw.line(screen, (44,54,68), (DV_X, 100), (DV_X, SCREEN_H-86), 1)

        # ── RIGHT: Dossier details ──
        RX = DV_X + 18
        RW = SCREEN_W//2 + 460 - RX

        # Big number index
        pulse2 = 0.55 + 0.45*abs(math.sin(elapsed*1.6))
        num_big = self.font_title.render(f"0{lvl+1}", True, dc)
        for gx2,gy2 in [(-3,-3),(3,-3),(-3,3),(3,3)]:
            gs = self.font_title.render(f"0{lvl+1}", True, dc)
            gs.set_alpha(int(55*pulse2))
            screen.blit(gs, (RX+gx2, 108+gy2))
        screen.blit(num_big, (RX, 108))

        # Title text
        title_lbl = self.font_small.render(f"CHIẾN DỊCH {lvl+1}:", True, (155,165,180))
        screen.blit(title_lbl, (RX+num_big.get_width()+14, 118))
        name_big = self.font_normal.render(lvl_names[lvl], True, (228,235,246))
        screen.blit(name_big, (RX+num_big.get_width()+14, 148))

        # Underline division with diamonds
        div_y2 = 186
        pygame.draw.line(screen, dc, (RX, div_y2), (RX+RW, div_y2), 1)
        mid2 = RX + RW//2
        pygame.draw.polygon(screen, dc, [(mid2,div_y2-5),(mid2+5,div_y2),(mid2,div_y2+5),(mid2-5,div_y2)])
        pygame.draw.circle(screen, dc, (RX, div_y2), 3)
        pygame.draw.circle(screen, dc, (RX+RW, div_y2), 3)

        # Map simulation + stats
        MAP_SZ = 192
        self._draw_map_simulation(screen, RX, 200, MAP_SZ, lvl)

        # Stats column
        SX2 = RX + MAP_SZ + 22
        SY2 = 200

        diff_lbl2 = self.font_small.render("ĐỘ KHÓ:", True, (100,110,128))
        screen.blit(diff_lbl2, (SX2, SY2))
        diff_val2 = self.font_normal.render(diff[lvl], True, dc)
        screen.blit(diff_val2, (SX2, SY2+18))

        pygame.draw.line(screen, (38,48,60), (SX2, SY2+50), (SX2+RW-MAP_SZ-26, SY2+50), 1)

        thr_lbl = self.font_small.render("ĐE DỌA:", True, (100,110,128))
        screen.blit(thr_lbl, (SX2, SY2+58))
        thr_val = self.font_small.render(threat_txt[lvl], True, dc)
        screen.blit(thr_val, (SX2, SY2+74))

        # Threat dots
        for ti2 in range(5):
            tc = dc if ti2 <= lvl else (25,32,42)
            cx3 = SX2 + 8 + ti2*22
            pygame.draw.circle(screen, tc, (cx3, SY2+106), 8)
            if ti2 <= lvl:
                pygame.draw.circle(screen, (255,255,255), (cx3, SY2+106), 3)

        # ── Objectives ──
        OBJ_Y = 200 + MAP_SZ + 18
        obj_hdr = self.font_normal.render("MỤC TIÊU NHIỆM VỤ:", True, (245,165,30))
        screen.blit(obj_hdr, (RX, OBJ_Y))
        pygame.draw.line(screen, (38,48,60), (RX, OBJ_Y+28), (RX+RW, OBJ_Y+28), 1)

        for oi, obj in enumerate(objectives[lvl]):
            oy2 = OBJ_Y + 38 + oi*34
            # Diamond bullets
            pts2 = [(RX+6,oy2+9),(RX+12,oy2+3),(RX+18,oy2+9),(RX+12,oy2+15)]
            pygame.draw.polygon(screen, dc, pts2)
            obj_s = self.font_small.render(obj, True, (182,192,210))
            screen.blit(obj_s, (RX+28, oy2+2))
            
            # Digital Status checkbox badge
            cb_x = RX+RW-64
            cb_bg2 = pygame.Surface((58,18), pygame.SRCALPHA)
            cb_bg2.fill((*dc, 22))
            screen.blit(cb_bg2, (cb_x, oy2+3))
            pygame.draw.rect(screen, dc, pygame.Rect(cb_x, oy2+3, 58, 18), 1, border_radius=2)
            todo_s = self.font_small.render("CHƯA", True, dc)
            screen.blit(todo_s, (cb_x+29-todo_s.get_width()//2, oy2+4))

        # ── Bottom CTA ──
        cta_y = SCREEN_H - 86
        pygame.draw.line(screen, (44,54,68), (SCREEN_W//2-460, cta_y), (SCREEN_W//2+460, cta_y), 1)

        hint_m = self.font_small.render("◄ ▲▼ ► Chọn chiến dịch  •  ENTER hoặc CLICK bắt đầu  •  ESC Quay lại", True, (88,98,115))
        screen.blit(hint_m, (SCREEN_W//2-hint_m.get_width()//2, cta_y+8))

        # Animated START prompt button — có thể click
        bp2 = 0.5+0.5*math.sin(elapsed*2.5)
        bc2 = (int(dc[0]*(0.65+0.35*bp2)), int(dc[1]*(0.65+0.35*bp2)), int(dc[2]*(0.65+0.35*bp2)))
        btn_t = f"[ ENTER — KÍCH HOẠT: {lvl_names[lvl]} ]"
        btn_s = self.font_normal.render(btn_t, True, bc2)
        bx3   = SCREEN_W//2-btn_s.get_width()//2
        by3   = cta_y+30
        
        # Lưu rect nút START để xử lý click
        btn_pad_x, btn_pad_y = 18, 8
        self._mission_start_rect = pygame.Rect(bx3 - btn_pad_x, by3 - btn_pad_y,
                                                btn_s.get_width() + btn_pad_x*2,
                                                btn_s.get_height() + btn_pad_y*2)
        
        # Vẽ nền nút
        mx_now, my_now = pygame.mouse.get_pos()
        mpos_now = (mx_now - getattr(self, 'tilt_x', 0), my_now - getattr(self, 'tilt_y', 0))
        btn_hovered = self._mission_start_rect.collidepoint(mpos_now)
        btn_bg = pygame.Surface((self._mission_start_rect.width, self._mission_start_rect.height), pygame.SRCALPHA)
        if btn_hovered:
            btn_bg.fill((*dc, 60))
        else:
            btn_bg.fill((*dc, int(28 * bp2)))
        screen.blit(btn_bg, self._mission_start_rect.topleft)
        pygame.draw.rect(screen, bc2, self._mission_start_rect, 2, border_radius=4)
        
        gls   = self.font_normal.render(btn_t, True, dc)
        gls.set_alpha(int(72*bp2))
        screen.blit(gls, (bx3-1, by3-1))
        screen.blit(gls, (bx3+1, by3+1))
        screen.blit(btn_s, (bx3, by3))

    def _draw_map_simulation(self, screen, x, y, size, level):
        """Vẽ bản đồ mô phỏng độc đáo dạng màn hình Radar chiến thuật cao cấp."""
        # Khung nền tối tối xanh quân sự
        pygame.draw.rect(screen, (8, 10, 15), (x, y, size, size))
        pygame.draw.rect(screen, (50, 75, 55), (x, y, size, size), 2)
        
        center_x = x + size // 2
        center_y = y + size // 2
        
        # 1. Đường lưới radar kĩ thuật (Technic Grid Coordinates)
        grid_space = size // 6
        for i in range(1, 6):
            # Dọc
            pygame.draw.line(screen, (15, 32, 20), (x + i * grid_space, y), (x + i * grid_space, y + size), 1)
            # Ngang
            pygame.draw.line(screen, (15, 32, 20), (x, y + i * grid_space), (x + size, y + i * grid_space), 1)
            
        # 2. Các vòng tròn quét đồng tâm mờ
        for r_factor in [0.25, 0.5, 0.75, 0.95]:
            pygame.draw.circle(screen, (22, 52, 28), (center_x, center_y), int((size//2) * r_factor), 1)

        # 3. Rotating Sweeping Radar Line with gradient trail
        radar_angle = (pygame.time.get_ticks() / 1000.0) * 1.6 # speed
        end_x = center_x + int((size//2) * math.cos(radar_angle))
        end_y = center_y + int((size//2) * math.sin(radar_angle))
        
        # Draw fading trails (gradient sweep)
        trail_steps = 12
        for ti in range(trail_steps):
            angle_offset = radar_angle - (ti / float(trail_steps)) * 0.35
            tx = center_x + int((size//2) * math.cos(angle_offset))
            ty = center_y + int((size//2) * math.sin(angle_offset))
            alpha = int(120 * (1.0 - ti / float(trail_steps)))
            
            trail_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.line(trail_surf, (0, 200, 80, alpha), (size//2, size//2), (tx - x, ty - y), 1)
            screen.blit(trail_surf, (x, y))
            
        # Draw primary sweep line
        pygame.draw.line(screen, (0, 255, 100), (center_x, center_y), (end_x, end_y), 2)
        
        pulse_fast = abs(math.sin(pygame.time.get_ticks() / 120))
        
        # 4. Địa hình chiến thuật đặc trưng từng màn
        if level == 0: # Màn 1: Rừng rậm nhiệt đới
            river_pts = [
                (x, y + size//4),
                (x + size//3, y + size//3),
                (x + size//2, y + size//2),
                (x + size*2//3, y + size*3//4),
                (x + size, y + size*5//6)
            ]
            pygame.draw.lines(screen, (30, 90, 180), False, river_pts, 3)
            random.seed(1234)
            for _ in range(8):
                tx = x + random.randint(15, size-15)
                ty = y + random.randint(15, size-15)
                pygame.draw.circle(screen, (10, 120, 45, 60), (tx, ty), random.randint(8, 14))
                pygame.draw.circle(screen, (30, 180, 70), (tx, ty), random.randint(4, 7), 1)
                
        elif level == 1: # Màn 2: Sa mạc tử thần
            random.seed(5678)
            for i in range(3):
                dy = y + 40 + i * 40
                points = []
                for dx in range(0, size + 10, 10):
                    px = x + dx
                    py = dy + math.sin(dx * 0.05 + i) * 6
                    points.append((px, py))
                pygame.draw.lines(screen, (170, 120, 25), False, points, 2)
            pygame.draw.ellipse(screen, (25, 100, 140), (x + 35, y + 55, 30, 18))
            pygame.draw.circle(screen, (0, 180, 50), (x + 38, y + 52), 3)
 
        elif level == 2: # Màn 3: Băng cực hoang vu
            random.seed(999)
            for _ in range(4):
                ix = x + random.randint(15, size - 45)
                iy = y + random.randint(15, size - 45)
                w, h = random.randint(20, 30), random.randint(20, 30)
                pygame.draw.rect(screen, (60, 180, 220, 50), (ix, iy, w, h), border_radius=4)
                pygame.draw.rect(screen, (130, 210, 240), (ix, iy, w, h), 1, border_radius=4)
            t = pygame.time.get_ticks() * 0.04
            for i in range(10):
                px = x + (i * 19 + t * 1.5) % size
                py = y + (i * 29 + t) % size
                pygame.draw.line(screen, (210, 220, 240, 80), (px, py), (px + 3, py + 1.5), 1)
 
        elif level == 3: # Màn 4: Căn cứ phòng thủ
            walls = [
                pygame.Rect(x + 15, y + 15, 35, 35),
                pygame.Rect(x + size - 50, y + 15, 35, 35),
                pygame.Rect(x + 15, y + size - 50, 35, 35),
                pygame.Rect(x + size - 50, y + size - 50, 35, 35),
                pygame.Rect(x + size//2 - 18, y + size//2 - 18, 36, 36)
            ]
            for r in walls:
                pygame.draw.rect(screen, (30, 40, 55), r)
                pygame.draw.rect(screen, (70, 100, 150), r, 1)
            pygame.draw.circle(screen, (200, 50, 50), (x + 32, y + 32), 3)
            pygame.draw.circle(screen, (200, 50, 50), (x + size - 32, y + size - 32), 3)
 
        elif level == 4: # Màn 5: Chiến hạm huỷ diệt
            random.seed(111)
            for i in range(2):
                points = []
                for dy_val in range(0, size + 10, 10):
                    px = x + 35 + i * 55 + math.sin(dy_val * 0.07 + i) * 10
                    py = y + dy_val
                    points.append((px, py))
                pygame.draw.lines(screen, (200, 45, 18), False, points, 3)
            pygame.draw.circle(screen, (160, 18, 0), (x + 22, y + 35), 10)
            pygame.draw.circle(screen, (160, 18, 0), (x + size - 22, y + size - 35), 10)
            t = pygame.time.get_ticks() * 0.015
            for i in range(8):
                px = x + (i * 23) % size
                py = y + (size - (i * 19 + t) % size)
                pygame.draw.circle(screen, (240, 80, 0), (int(px), int(py)), random.randint(1, 2))
 
        # 5. Các vị trí mục tiêu chiến thuật
        sp_x, sp_y = x + 25, y + size - 25
        pygame.draw.circle(screen, (0, 255, 0), (sp_x, sp_y), 5)
        pygame.draw.circle(screen, (0, 255, 0), (sp_x, sp_y), int(5 + 4 * pulse_fast), 1)
        
        ex_x, ex_y = x + size - 25, y + 25
        pygame.draw.rect(screen, (80, 180, 255), (ex_x - 5, ex_y - 5, 10, 10))
        pygame.draw.rect(screen, (80, 180, 255), (ex_x - 5, ex_y - 5, 10, 10), 1)
        
        bs_x, bs_y = x + size - 40, y + 40
        if level == 4:
            bs_x, bs_y = center_x, center_y
        pygame.draw.circle(screen, (220, 50, 50), (bs_x, bs_y), 5)
        pygame.draw.circle(screen, (255, 50, 50), (bs_x, bs_y), int(5 + 6 * pulse_fast), 1)
        
        bs_size = 12 + int(3 * pulse_fast)
        pygame.draw.rect(screen, (220, 50, 50), (bs_x - bs_size//2, bs_y - bs_size//2, bs_size, bs_size), 1)

        # Labels
        font_map = pygame.font.SysFont("arial", 11, bold=True)
        lbl_spawn = font_map.render("SPAWN", True, (0, 255, 0))
        screen.blit(lbl_spawn, (sp_x + 8, sp_y - 6))
        
        lbl_exit = font_map.render("EXIT", True, (80, 180, 255))
        screen.blit(lbl_exit, (ex_x - 38, ex_y - 6))
        
        lbl_boss = font_map.render("BOSS", True, (220, 50, 50))
        screen.blit(lbl_boss, (bs_x - 16, bs_y - 17))
        
        # Overlay map details text
        lbl_title = font_map.render("SƠ ĐỒ BẢN ĐỒ MÔ PHỎNG", True, (130, 140, 130))
        screen.blit(lbl_title, (x + size//2 - lbl_title.get_width()//2, y - 16))

        # Telemetry corner coordinates overlays
        tele_col = (50, 75, 55)
        lbl_c1 = font_map.render("SYS: ACTV", True, tele_col)
        screen.blit(lbl_c1, (x + 6, y + 6))
        lbl_c2 = font_map.render("SEC: A5", True, tele_col)
        screen.blit(lbl_c2, (x + size - lbl_c2.get_width() - 6, y + 6))
        lbl_c3 = font_map.render("10.76 N", True, tele_col)
        screen.blit(lbl_c3, (x + 6, y + size - 17))
        lbl_c4 = font_map.render("106.66 E", True, tele_col)
        screen.blit(lbl_c4, (x + size - lbl_c4.get_width() - 6, y + size - 17))


    def _adjust_setting(self, idx, direction, toggle=False):
        if idx == 0:  # Music Volume
            val = sound_manager.music_volume
            if toggle:
                val = 0.0 if val > 0.0 else 0.5
            else:
                val = max(0.0, min(1.0, val + direction * 0.05))
            sound_manager.set_music_volume(val)
        elif idx == 1:  # SFX Volume
            val = sound_manager.sfx_volume
            if toggle:
                val = 0.0 if val > 0.0 else 0.5
            else:
                val = max(0.0, min(1.0, val + direction * 0.05))
            sound_manager.set_sfx_volume(val)
            # Phát âm thanh click ngắn để người chơi test âm lượng
            sound_manager.play('pickup')
        elif idx == 2:  # Brightness
            if toggle:
                self.brightness = 1.0
            else:
                self.brightness = max(0.5, min(1.5, self.brightness + direction * 0.05))
        elif idx == 3:  # CRT Scanlines
            self.crt_scanlines = not self.crt_scanlines

    def _handle_settings_mouse(self, idx, pos):
        mx, my = pos
        if idx in (0, 1, 2):
            slider_x = SCREEN_W//2 + 55
            slider_w = 320
            pct = (mx - slider_x) / slider_w
            pct = max(0.0, min(1.0, pct))
            
            if idx == 0:
                sound_manager.set_music_volume(pct)
            elif idx == 1:
                sound_manager.set_sfx_volume(pct)
            elif idx == 2:
                self.brightness = 0.5 + pct * 1.0
        elif idx == 3:
            pass # Toggled separately on click down

    def _buy_upgrade(self, idx):
        upg = self.upgrades_catalog[idx]
        uid = upg["id"]
        curr_lvl = self.perm_upgrades.get(uid, 0)
        
        if curr_lvl < upg["max_level"]:
            cost = upg["costs"][curr_lvl]
            if self.gold >= cost:
                self.gold -= cost
                self.perm_upgrades[uid] = curr_lvl + 1
                sound_manager.play('pickup')
                if self.save_callback:
                    self.save_callback(self.gold, self.unlocked_weapons)
                return True
            else:
                sound_manager.play('error')
        else:
            sound_manager.play('error')
        return False

    def _draw_upgrades(self, screen):
        panel = Panel(SCREEN_W//2-500, 45, 1000, 710, "TRUNG TÂM HUẤN LUYỆN ĐẶC NHIỆM — UPGRADES")
        panel.draw(screen, self.font_normal)
        self._close_btn_rect = self._draw_close_button(screen, SCREEN_W//2 + 500 - 45, 53, 30)

        # Hiển thị số Vàng
        gold_txt = self.font_normal.render(f"VÀNG: {self.gold} $", True, (255, 215, 0))
        screen.blit(gold_txt, (SCREEN_W//2 + 500 - gold_txt.get_width() - 60, 55))

        row_w, row_h = 900, 90
        gap = 14
        start_x = SCREEN_W//2 - row_w//2
        start_y = 150

        self._upgrade_rects = []
        mx, my = pygame.mouse.get_pos()
        mpos = (mx - getattr(self, 'tilt_x', 0), my - getattr(self, 'tilt_y', 0))

        rarity_col = {
            "THƯỜNG": (110, 120, 130), "HIẾM": (60, 140, 200),
            "SỬ THI": (160, 90, 210), "HUYỀN THOẠI": (210, 140, 20), "SIÊU HIẾM": (200, 80, 200)
        }

        for idx, upg in enumerate(self.upgrades_catalog):
            ry = start_y + idx * (row_h + gap)
            rect = pygame.Rect(start_x, ry, row_w, row_h)
            self._upgrade_rects.append(rect)

            is_sel = (self.upgrades_selected_idx == idx)
            is_hov = rect.collidepoint(mpos)
            if is_hov:
                self.upgrades_selected_idx = idx
                is_sel = True

            uid = upg["id"]
            lvl = self.perm_upgrades.get(uid, 0)
            is_max = (lvl >= upg["max_level"])
            cost = upg["costs"][lvl] if not is_max else 0
            color = upg["color"]

            # Card background - Glassmorphic horizontal row look
            row_bg = pygame.Surface((row_w, row_h), pygame.SRCALPHA)
            if is_sel:
                row_bg.fill((*color, 24))
                border_col = color
                border_w = 2
            else:
                row_bg.fill((8, 11, 16, 220))
                border_col = (45, 55, 68)
                border_w = 1
            screen.blit(row_bg, (start_x, ry))
            
            # Glowing borders on selection
            if is_sel:
                for thick in range(1, 4):
                    pygame.draw.rect(screen, (*color, 50 // thick), (start_x - thick, ry - thick, row_w + thick*2, row_h + thick*2), 1, border_radius=4)
            pygame.draw.rect(screen, border_col, rect, border_w, border_radius=4)

            # Draw tactical corner crosses on selected cards
            if is_sel:
                for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                    ax = start_x if dx==1 else start_x+row_w
                    ay = ry if dy==1 else ry+row_h
                    pygame.draw.line(screen, (255, 255, 255), (ax, ay), (ax+8*dx, ay), 2)
                    pygame.draw.line(screen, (255, 255, 255), (ax, ay), (ax, ay+8*dy), 2)

            # ── LEFT: Name & Level blocks ──
            name_s = self.font_normal.render(upg["name"], True, color if is_sel else (220, 230, 240))
            screen.blit(name_s, (start_x + 20, ry + 16))

            # Draw level segments
            seg_w = 18
            seg_h = 10
            seg_gap = 4
            for step in range(upg["max_level"]):
                seg_x = start_x + 20 + step * (seg_w + seg_gap)
                seg_rect = pygame.Rect(seg_x, ry + 52, seg_w, seg_h)
                is_filled = step < lvl
                if is_filled:
                    pygame.draw.rect(screen, color, seg_rect, border_radius=2)
                    pygame.draw.rect(screen, (255, 255, 255, 120), (seg_x + 1, ry + 53, seg_w - 2, 2), border_radius=1)
                else:
                    pygame.draw.rect(screen, (25, 30, 35), seg_rect, border_radius=2)
                    pygame.draw.rect(screen, (45, 55, 65), seg_rect, 1, border_radius=2)

            # Current Level text
            lbl_lvl = self.font_small.render(f"CẤP {lvl}/{upg['max_level']}", True, color if is_sel else (150, 160, 170))
            screen.blit(lbl_lvl, (start_x + 20 + upg["max_level"] * (seg_w + seg_gap) + 8, ry + 49))

            # ── CENTER: Description & Stat comparison ──
            desc_s = self.font_small.render(upg["desc"], True, (160, 175, 195))
            screen.blit(desc_s, (start_x + 230, ry + 18))

            if uid == "hp":
                curr_val = f"{PLAYER_HP_MAX + lvl * 10} HP"
                next_val = f"{PLAYER_HP_MAX + (lvl + 1) * 10} HP" if not is_max else "MAX"
            elif uid == "armor":
                curr_val = f"{PLAYER_ARMOR_MAX + lvl * 15} AP"
                next_val = f"{PLAYER_ARMOR_MAX + (lvl + 1) * 15} AP" if not is_max else "MAX"
            elif uid == "damage":
                curr_val = f"+{lvl * 5}%"
                next_val = f"+{(lvl + 1) * 5}%" if not is_max else "MAX"
            elif uid == "speed":
                curr_val = f"+{lvl * 5}%"
                next_val = f"+{(lvl + 1) * 5}%" if not is_max else "MAX"
            elif uid == "dash":
                curr_val = f"-{lvl * 8}% CD"
                next_val = f"-{(lvl + 1) * 8}% CD" if not is_max else "MAX"

            comp_txt = f"Hiện tại: {curr_val}   ──►   Kế tiếp: {next_val}" if not is_max else f"Chỉ số: {curr_val} (ĐÃ ĐẠT TỐI ĐA)"
            comp_color = color if not is_max else (100, 180, 120)
            comp_s = self.font_small.render(comp_txt, True, comp_color)
            screen.blit(comp_s, (start_x + 230, ry + 48))

            # ── RIGHT: Purchase button ──
            btn_w, btn_h = 220, 44
            btn_x = start_x + row_w - btn_w - 20
            btn_y = ry + 23
            btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

            if is_max:
                btn_bg_col = (20, 30, 25)
                btn_border_col = (100, 180, 120)
                btn_txt = "ĐÃ CỰC ĐẠI"
                txt_col = (100, 180, 120)
            elif self.gold >= cost:
                btn_bg_col = color if is_sel else (20, 25, 30)
                btn_border_col = (255, 200, 50) if is_sel else color
                btn_txt = f"NÂNG CẤP: {cost} $"
                txt_col = (10, 12, 14) if is_sel else WHITE
            else:
                btn_bg_col = (20, 20, 20)
                btn_border_col = (100, 100, 100)
                btn_txt = f"THIẾU: {cost} $"
                txt_col = (130, 130, 130)

            pygame.draw.rect(screen, btn_bg_col, btn_rect, border_radius=3)
            pygame.draw.rect(screen, btn_border_col, btn_rect, 1, border_radius=3)
            btn_s = self.font_small.render(btn_txt, True, txt_col)
            screen.blit(btn_s, (btn_x + (btn_w - btn_s.get_width())//2, btn_y + (btn_h - btn_s.get_height())//2))

        # Bottom tip
        ty = SCREEN_H - 80
        pygame.draw.line(screen, (42, 52, 65), (SCREEN_W//2-455, ty), (SCREEN_W//2+455, ty), 1)
        tip = self.font_small.render("▲ ▼ Chọn chỉ số  •  ENTER / CLICK để nâng cấp  •  ESC Quay lại sảnh chờ", True, (88, 98, 115))
        screen.blit(tip, (SCREEN_W//2-tip.get_width()//2, ty+12))

