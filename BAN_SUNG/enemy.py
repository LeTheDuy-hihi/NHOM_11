import pygame
import math
import random
import os
from constants import *
import ai_logic

_TANK_IMAGE = None
_TANK_LOADED = False

def get_tank_image():
    global _TANK_IMAGE, _TANK_LOADED
    if _TANK_LOADED:
        return _TANK_IMAGE
    _TANK_LOADED = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "ANH", "xe tăng đỏ.jpg")
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert_alpha()
            img.lock()
            w, h = img.get_size()
            for x in range(w):
                for y in range(h):
                    r, g, b, a = img.get_at((x, y))
                    # Lọc lấy màu đỏ của xe tăng hoặc màu xám/đen của bánh xích
                    is_bg = (r < 15 and g < 15 and b < 15)
                    if is_bg:
                        img.set_at((x, y), (0, 0, 0, 0))
            img.unlock()
            _TANK_IMAGE = pygame.transform.scale(img, (64, 64))
        except Exception as e:
            print("Lỗi load ảnh xe tăng:", e)
    return _TANK_IMAGE

_YELLOW_TANK_IMAGE = None
_YELLOW_TANK_LOADED = False

def get_yellow_tank_image():
    global _YELLOW_TANK_IMAGE, _YELLOW_TANK_LOADED
    if _YELLOW_TANK_LOADED:
        return _YELLOW_TANK_IMAGE
    _YELLOW_TANK_LOADED = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "ANH", "xe tăng vàng.jpg")
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert_alpha()
            img.lock()
            w, h = img.get_size()
            for x in range(w):
                for y in range(h):
                    r, g, b, a = img.get_at((x, y))
                    # Lọc màu vàng (Red và Green cao, Blue thấp)
                    is_bg = (r < 15 and g < 15 and b < 15)
                    if is_bg:
                        img.set_at((x, y), (0, 0, 0, 0))
            img.unlock()
            _YELLOW_TANK_IMAGE = pygame.transform.scale(img, (64, 64))
        except Exception as e:
            print("Lỗi load ảnh xe tăng vàng:", e)
    return _YELLOW_TANK_IMAGE

_GREEN_TANK_IMAGE = None
_GREEN_TANK_LOADED = False

def get_green_tank_image():
    global _GREEN_TANK_IMAGE, _GREEN_TANK_LOADED
    if _GREEN_TANK_LOADED:
        return _GREEN_TANK_IMAGE
    _GREEN_TANK_LOADED = True
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "ANH", "xe tăng xanh.jpg")
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert_alpha()
            img.lock()
            w, h = img.get_size()
            for x in range(w):
                for y in range(h):
                    r, g, b, a = img.get_at((x, y))
                    # Lọc màu xanh lá (Green cao, Red và Blue thấp)
                    is_bg = (r < 15 and g < 15 and b < 15)
                    if is_bg:
                        img.set_at((x, y), (0, 0, 0, 0))
            img.unlock()
            _GREEN_TANK_IMAGE = pygame.transform.scale(img, (64, 64))
        except Exception as e:
            print("Lỗi load ảnh xe tăng xanh:", e)
    return _GREEN_TANK_IMAGE

_BOSS_IMAGES = {}

def get_boss_image(level=1):
    global _BOSS_IMAGES
    if level in _BOSS_IMAGES:
        return _BOSS_IMAGES[level]
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_level = 5 if level == 6 else level
    # Thử load ảnh boss theo level trước (ví dụ: boss lv2.png, boss lv4.jpg, bosslv5.png)
    img_path = os.path.join(base_dir, "ANH", f"boss lv{img_level}.png")
    if not os.path.exists(img_path):
        img_path = os.path.join(base_dir, "ANH", f"boss lv{img_level}.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.join(base_dir, "ANH", f"bosslv{img_level}.png")
    if not os.path.exists(img_path):
        img_path = os.path.join(base_dir, "ANH", f"bosslv{img_level}.jpg")
    if not os.path.exists(img_path):
        img_path = os.path.join(base_dir, "ANH", "boss.png")
        
    if os.path.exists(img_path):
        try:
            img = pygame.image.load(img_path).convert_alpha()
            # Tách nền (remove background)
            bg_color = img.get_at((0, 0))
            if bg_color[3] != 0:
                img.lock()
                w, h = img.get_size()
                for x in range(w):
                    for y in range(h):
                        r, g, b, a = img.get_at((x, y))
                        is_bg = (abs(r - bg_color[0]) < 35 and abs(g - bg_color[1]) < 35 and abs(b - bg_color[2]) < 35)
                        is_white = (r > 215 and g > 215 and b > 215)
                        is_black = (r < 20 and g < 20 and b < 20)
                        if is_bg or is_white or is_black:
                            img.set_at((x, y), (0, 0, 0, 0))
                    img.unlock()
            if level == 6:
                size = (220, 220)
            elif level == 5:
                size = (150, 150)
            elif level == 4:
                size = (140, 140)
            else:
                size = (100, 100)
            _BOSS_IMAGES[level] = pygame.transform.scale(img, size)
            return _BOSS_IMAGES[level]
        except Exception as e:
            print(f"Lỗi load ảnh boss level {level}:", e)
            
    # Dự phòng load boss.png mặc định nếu có lỗi
    default_path = os.path.join(base_dir, "ANH", "boss.png")
    if os.path.exists(default_path):
        try:
            img = pygame.image.load(default_path).convert_alpha()
            # Tách nền (remove background)
            bg_color = img.get_at((0, 0))
            if bg_color[3] != 0:
                img.lock()
                w, h = img.get_size()
                for x in range(w):
                    for y in range(h):
                        r, g, b, a = img.get_at((x, y))
                        is_bg = (abs(r - bg_color[0]) < 35 and abs(g - bg_color[1]) < 35 and abs(b - bg_color[2]) < 35)
                        is_white = (r > 215 and g > 215 and b > 215)
                        is_black = (r < 20 and g < 20 and b < 20)
                        if is_bg or is_white or is_black:
                            img.set_at((x, y), (0, 0, 0, 0))
                img.unlock()
            _BOSS_IMAGES[level] = pygame.transform.scale(img, (75, 75))
            return _BOSS_IMAGES[level]
        except Exception as e:
            print("Lỗi load ảnh boss default:", e)
            
    return None

class SecurityCamera:
    def __init__(self, x, y, base_angle):
        self.x, self.y = float(x), float(y)
        self.base_angle = base_angle
        self.angle = base_angle
        self.sweep_range = math.pi / 3  # 60 degrees total sweep
        self.sweep_speed = 0.012
        self.direction = 1
        self.hp = CAMERA_HP
        self.max_hp = CAMERA_HP
        self.alive = True
        self.detection_progress = 0.0
        self.radius = 12

    def update(self, player, game_map, effect_manager):
        if not self.alive:
            return False

        # Oscillate angle
        self.angle += self.sweep_speed * self.direction
        diff = (self.angle - self.base_angle + math.pi) % (2 * math.pi) - math.pi
        if abs(diff) > self.sweep_range / 2:
            self.direction *= -1
            self.angle = self.base_angle + (self.sweep_range / 2 if diff > 0 else -self.sweep_range / 2)

        # Check detection
        dist = math.hypot(player.x - self.x, player.y - self.y)
        detected = False
        if dist < 240:
            angle_to_player = math.atan2(player.y - self.y, player.x - self.x)
            ang_diff = abs((angle_to_player - self.angle + math.pi) % (2 * math.pi) - math.pi)
            if ang_diff < 0.45:  # ~25 degrees half-angle spread
                if ai_logic.has_line_of_sight(self.x, self.y, player.x, player.y, game_map):
                    hiding = False
                    if hasattr(effect_manager, 'smoke_clouds'):
                        for sc in effect_manager.smoke_clouds:
                            dx = player.x - self.x
                            dy = player.y - self.y
                            seg_len_sq = dx*dx + dy*dy
                            if seg_len_sq > 0:
                                t = ((sc.x - self.x) * dx + (sc.y - self.y) * dy) / seg_len_sq
                                t = max(0.0, min(1.0, t))
                                proj_x = self.x + t * dx
                                proj_y = self.y + t * dy
                                if math.hypot(sc.x - proj_x, sc.y - proj_y) < getattr(sc, 'current_radius', sc.radius):
                                    hiding = True
                                    break
                    if getattr(player, 'is_dashing', False):
                        hiding = True

                    if not hiding:
                        detected = True

        if detected:
            self.detection_progress = min(100.0, self.detection_progress + 2.0)
            if random.random() < 0.15:
                effect_manager.add_sparks(self.x, self.y, count=1)
        else:
            self.detection_progress = max(0.0, self.detection_progress - 1.0)

        if self.detection_progress >= 100.0:
            return True # Trigger Alarm!
        return False

    def take_damage(self, amount, effect_manager, sound_manager):
        if not self.alive:
            return
        self.hp -= amount
        effect_manager.add_sparks(self.x, self.y, count=random.randint(4, 7))
        if self.hp <= 0:
            self.alive = False
            sound_manager.play('wood_break')
            effect_manager.add_cover_destruction(self.x, self.y)

    def draw(self, screen, cam_x, cam_y):
        if not self.alive:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Draw vision cone
        cone_len = 240
        spread = 0.45
        p1 = (sx, sy)
        p2 = (sx + int(math.cos(self.angle - spread) * cone_len), sy + int(math.sin(self.angle - spread) * cone_len))
        p3 = (sx + int(math.cos(self.angle + spread) * cone_len), sy + int(math.sin(self.angle + spread) * cone_len))
        
        alpha = int(40 + 80 * (self.detection_progress / 100.0))
        if self.detection_progress > 0:
            color = (255, 255 - int(255 * (self.detection_progress / 100.0)), 0, alpha)
        else:
            color = (0, 255, 100, 30)

        cone_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surf, color, [p1, p2, p3])
        screen.blit(cone_surf, (0, 0))

        # Camera body
        pygame.draw.circle(screen, (50, 50, 50), (sx, sy), 8)
        pygame.draw.circle(screen, (80, 85, 90), (sx, sy), 6)
        
        lx = sx + int(math.cos(self.angle) * 11)
        ly = sy + int(math.sin(self.angle) * 11)
        pygame.draw.line(screen, (30, 30, 30), (sx, sy), (lx, ly), 4)
        
        light_color = (255, 0, 0) if (self.detection_progress > 0 and (pygame.time.get_ticks() // 200) % 2 == 0) else (0, 255, 0)
        pygame.draw.circle(screen, light_color, (sx, sy), 2)


class Enemy:
    def __init__(self, x, y, enemy_type, level=1):
        self.x, self.y = float(x), float(y)
        self.type = enemy_type
        self.level = level
        
        # Difficulty scaling factors
        hp_scale = 1.0 + (level - 1) * 0.15
        dmg_scale = 1.0 + (level - 1) * 0.1
        spd_scale = 1.0 + (level - 1) * 0.05
        
        # Thiết lập thông số, màu sắc và thuật toán theo loại địch (loại địch tương ứng với từng Map)
        if enemy_type == "dummy":
            self.hp = 200
            self.max_hp = 200
            self.speed = 0
            self.damage = 0
            self.range = 0
            self.max_cooldown = 999999
            self.color = (0, 255, 255)
            self.current_algo = "BFS"
            self.patrol_algo = "BFS"
        elif enemy_type == "moving_dummy":
            self.hp = 200
            self.max_hp = 200
            self.speed = 1.5
            self.damage = 0
            self.range = 0
            self.max_cooldown = 999999
            self.color = (255, 100, 255)
            self.current_algo = "BFS"
            self.patrol_algo = "BFS"
        elif enemy_type == "combat_dummy":
            self.hp = 150
            self.max_hp = 150
            self.speed = 1.6
            self.damage = 6
            self.range = 350
            self.max_cooldown = 60
            self.color = (255, 150, 0)
            self.current_algo = "BFS"
            self.patrol_algo = "BFS"
        elif enemy_type == "assault": # Map 1 tank
            self.hp = 100 * hp_scale
            self.speed = 2.0 * spd_scale
            self.damage = 10 * dmg_scale
            self.range = 300
            self.max_cooldown = 45
            self.color = (220, 50, 50) # Đỏ
            self.current_algo = "BFS"
            self.patrol_algo = "BFS"
        elif enemy_type == "sniper": # Map 2 tank
            self.hp = 80 * hp_scale
            self.speed = 2.5 * spd_scale
            self.damage = 25 * dmg_scale
            self.range = 500
            self.max_cooldown = 90
            self.color = (220, 200, 50) # Vàng
            self.current_algo = "DFS"
            self.patrol_algo = "DFS"
        elif enemy_type == "patrol": # Map 3 tank
            self.hp = 120 * hp_scale
            self.speed = 1.8 * spd_scale
            self.damage = 15 * dmg_scale
            self.range = 350
            self.max_cooldown = 60
            self.color = (50, 220, 50) # Xanh lá
            self.current_algo = "ASTAR"
            self.patrol_algo = "ASTAR"
        elif enemy_type == "heavy": # Map 4 tank
            self.hp = 200 * hp_scale
            self.speed = 1.5 * spd_scale
            self.damage = 20 * dmg_scale
            self.range = 400
            self.max_cooldown = 75
            self.color = (50, 100, 255) # Xanh dương
            self.current_algo = "HEURISTIC"
            self.patrol_algo = "HEURISTIC"
        else: # boss
            # Bosses scale even harder
            if level == 6:
                # Boss Màn 6 (Solo Boss Cuối): Siêu to khổng lồ, siêu trâu bò
                self.hp = BOSS_HP * 35
                self.speed = BOSS_SPEED * 1.0
                self.damage = BOSS_DAMAGE * 1.8
                self.range = BOSS_RANGE + 200
                self.max_cooldown = 10
            elif level == 5:
                # Boss Màn 5: CHIẾN HẠM HUỶ DIỆT - Siêu mạnh
                self.hp = BOSS_HP * 3.5
                self.speed = BOSS_SPEED * 1.6
                self.damage = BOSS_DAMAGE * 2.0
                self.range = BOSS_RANGE + 150
                self.max_cooldown = 6  # Bắn cực nhanh
            else:
                self.hp = BOSS_HP * (1.0 + (level-1)*0.5)
                self.speed = BOSS_SPEED * (1.0 + (level-1)*0.08)
                self.damage = BOSS_DAMAGE * (1.0 + (level-1)*0.2)
                self.range = BOSS_RANGE + (level * 20)
                self.max_cooldown = max(20, BOSS_COOLDOWN - (level * 2))
            self.color = BOSS_COLOR
            
            # Signature skill based on level
            skills = {
                1: "JUNGLE SPREAD",
                2: "DESERT BURST",
                3: "SPIRAL BLIZZARD",
                4: "TÊN LỬA ĐỊNH VỊ",
                5: "CHIẾN HẠM HUỶ DIỆT",
                6: "KỶ NGUYÊN HỦY DIỆT"
            }
            self.skill_name = skills.get(self.level, "HEAVY ATTACK")
            self.skill_timer = 0
            
        self.max_hp = self.hp
        self.cooldown = random.randint(0, int(self.max_cooldown))
        self.alive = True
        self.radius = 12
        if self.type == "boss":
            # Boss Level 4 là máy bay (32), Boss Level 5 là chiến hạm (22), Boss Level 6 là siêu chiến hạm khổng lồ (55)
            if self.level == 6:
                self.radius = 55
            elif self.level == 4:
                self.radius = 32
            elif self.level == 5:
                self.radius = 22
            else:
                self.radius = 20
            self.boss_state = "PATROL"
            self.patrol_target = None
            self.patrol_algo = "BFS"
            self.current_algo = "BFS"
            
        self.angle = 0.0        # góc nòng pháo (hướng bắn / hướng nhìn)
        self.draw_angle = 0.0   # góc nòng pháo smooth (lerp)
        self.move_angle = 0.0   # góc thân xe (hướng di chuyển)
        self.draw_move_angle = 0.0  # góc thân xe smooth
        self.path = []
        self.path_timer = 0
        self.step_timer = 0
        self.is_moving = False
        
        # DFS specific
        self.visited_tiles = set()
        self.stun_timer = 0
        
        if self.type != "boss":
            self.state = "PATROL"
            self.suspicious_timer = 0
            self.suspicious_target = None
            self.cover_target = None
            self.last_player_pos = None
        
        # Assault (xe tăng đỏ) - Systematic Map Sweep
        if enemy_type == "assault":
            self.sweep_waypoints = []   # Danh sách waypoints phủ toàn bản đồ
            self.sweep_idx = 0          # Chỉ mục waypoint hiện tại
            self.sweep_initialized = False  # Chưa khởi tạo waypoints
            self.sweep_zone_size = 6    # Khoảng cách giữa các waypoints (tile)
            self.hunt_confirmed = False  # Đang trực tiếp truy đuổi

    def _init_sweep_waypoints(self, game_map):
        """Tạo lưới waypoints phủ toàn bản đồ cho chế độ quét hệ thống."""
        step = self.sweep_zone_size
        waypoints = []
        # Quét theo hàng rắn, xế hướng (boustrophedon) để phủ đều
        for row_idx, ty in enumerate(range(step, game_map.height - step, step)):
            # Hàng chẵn: trái → phải; Hàng lẻ: phải → trái
            col_range = range(step, game_map.width - step, step)
            if row_idx % 2 == 1:
                col_range = reversed(list(col_range))
            for tx in col_range:
                if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                    if game_map.grid[ty][tx] == TILE_EMPTY:
                        px = tx * TILE_SIZE + TILE_SIZE // 2
                        py = ty * TILE_SIZE + TILE_SIZE // 2
                        waypoints.append((px, py))
        self.sweep_waypoints = waypoints
        self.sweep_idx = 0
        self.sweep_initialized = True

    def _pick_sweep_target(self):
        """Trả về waypoint tiếp theo cần đến khi quét bản đồ."""
        if not self.sweep_waypoints:
            return None
        if self.sweep_idx >= len(self.sweep_waypoints):
            self.sweep_idx = 0  # Reset: quét lại từ đầu
        return self.sweep_waypoints[self.sweep_idx]

    def find_cover_tile(self, player, game_map):
        cx = int(self.x // TILE_SIZE)
        cy = int(self.y // TILE_SIZE)
        best_tile = None
        best_dist = 999999
        
        for dy in range(-6, 7):
            for dx in range(-6, 7):
                tx = cx + dx
                ty = cy + dy
                if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                    if game_map.grid[ty][tx] == TILE_EMPTY:
                        is_near_obstacle = False
                        for ny, nx in [(ty-1, tx), (ty+1, tx), (ty, tx-1), (ty, tx+1)]:
                            if 0 <= nx < game_map.width and 0 <= ny < game_map.height:
                                if game_map.grid[ny][nx] in (TILE_WALL, TILE_COVER, TILE_BARREL):
                                    is_near_obstacle = True
                                    break
                        if is_near_obstacle:
                            px = tx * TILE_SIZE + TILE_SIZE // 2
                            py = ty * TILE_SIZE + TILE_SIZE // 2
                            if not ai_logic.has_line_of_sight(px, py, player.x, player.y, game_map):
                                dist = math.hypot(px - self.x, py - self.y)
                                if dist < best_dist:
                                    best_dist = dist
                                    best_tile = (px, py)
        return best_tile

    def find_flanking_target(self, player, game_map):
        dx = self.x - player.x
        dy = self.y - player.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return player.x, player.y
            
        side = 1 if (id(self) % 2 == 0) else -1
        for offset in [160, 120, 80]:
            for s in [side, -side]:
                perp_x = -dy / dist * offset * s
                perp_y = dx / dist * offset * s
                tx = player.x + perp_x
                ty = player.y + perp_y
                tile_x = int(tx // TILE_SIZE)
                tile_y = int(ty // TILE_SIZE)
                if 0 <= tile_x < game_map.width and 0 <= tile_y < game_map.height:
                    if game_map.grid[tile_y][tile_x] == TILE_EMPTY:
                        return tx, ty
        return player.x, player.y

    def find_nearest_alarm_console(self, game_map):
        cx = int(self.x // TILE_SIZE)
        cy = int(self.y // TILE_SIZE)
        best_dist = 999999
        best_tile = None
        for dy in range(-12, 13):
            for dx in range(-12, 13):
                tx = cx + dx
                ty = cy + dy
                if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                    if game_map.grid[ty][tx] == TILE_ALARM_CONSOLE:
                        px = tx * TILE_SIZE + TILE_SIZE // 2
                        py = ty * TILE_SIZE + TILE_SIZE // 2
                        dist = math.hypot(px - self.x, py - self.y)
                        if dist < 350 and dist < best_dist:
                            best_dist = dist
                            best_tile = (px, py)
        return best_tile

    def get_avoidance_force(self, game_map, enemies, desired_vx, desired_vy):
        force_x = 0.0
        force_y = 0.0
        
        # Mutual repulsion from other active enemies to prevent clumping
        if enemies:
            for other in enemies:
                if other is self or not other.alive:
                    continue
                dx = self.x - other.x
                dy = self.y - other.y
                dist = math.hypot(dx, dy)
                
                min_dist = (self.radius + other.radius) * 1.15
                if dist < min_dist and dist > 0.1:
                    overlap = min_dist - dist
                    force_mag = (overlap / min_dist) * (self.speed if hasattr(self, 'speed') else 1.5) * 2.0
                    force_x += (dx / dist) * force_mag
                    force_y += (dy / dist) * force_mag
                    
        return force_x, force_y

    def resolve_wall_collision(self, game_map):
        cx = int(self.x // TILE_SIZE)
        cy = int(self.y // TILE_SIZE)
        radius = 14 if self.type != "boss" else 20
        net_push_x, net_push_y = 0.0, 0.0
        push_count = 0
        push_count = 0

        for dy in range(-1, 2):
            for dx in range(-1, 2):
                tx = cx + dx
                ty = cy + dy
                if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                    if game_map.is_wall(tx, ty):
                        tile_left = tx * TILE_SIZE
                        tile_right = tile_left + TILE_SIZE
                        tile_top = ty * TILE_SIZE
                        tile_bottom = tile_top + TILE_SIZE

                        closest_x = max(tile_left, min(self.x, tile_right))
                        closest_y = max(tile_top, min(self.y, tile_bottom))

                        dist_x = self.x - closest_x
                        dist_y = self.y - closest_y
                        dist = math.hypot(dist_x, dist_y)

                        if dist < radius:
                            if dist > 0.01:
                                overlap = radius - dist
                                self.x += (dist_x / dist) * overlap * 1.2
                                self.y += (dist_y / dist) * overlap * 1.2
                                net_push_x += dist_x / dist
                                net_push_y += dist_y / dist
                                push_count += 1
                            else:
                                tile_center_x = tile_left + TILE_SIZE / 2
                                tile_center_y = tile_top + TILE_SIZE / 2
                                vx = self.x - tile_center_x
                                vy = self.y - tile_center_y
                                v_len = math.hypot(vx, vy)
                                if v_len > 0.01:
                                    self.x += (vx / v_len) * radius
                                    self.y += (vy / v_len) * radius
                                    net_push_x += vx / v_len
                                    net_push_y += vy / v_len
                                else:
                                    self.x += radius
                                    net_push_x += 1.0
                                push_count += 1

        # Enhanced escape when push forces cancel out
        if push_count >= 2:
            net_len = math.hypot(net_push_x, net_push_y)
            if net_len < 0.2:
                escaped = False
                for angle_step in range(8):
                    a = angle_step * (math.pi / 4)
                    ex = math.cos(a) * (radius + 2)
                    ey = math.sin(a) * (radius + 2)
                    test_x = self.x + ex
                    test_y = self.y + ey
                    if not game_map.is_wall_pixel_radius(test_x, test_y, radius - 3):
                        self.x = test_x
                        self.y = test_y
                        escaped = True
                        break
                if not escaped:
                    # Teleport to a safe nearby spot
                    self.x = float(4 * TILE_SIZE + TILE_SIZE // 2 + random.randint(-30, 30))
                    self.y = float(4 * TILE_SIZE + TILE_SIZE // 2 + random.randint(-30, 30))
                    self.path = []
                    self.stuck_timer = 0


    def resolve_enemy_collisions(self, enemies):
        if not enemies:
            return
        for other in enemies:
            if other is self or not other.alive:
                continue
            dx = self.x - other.x
            dy = self.y - other.y
            dist = math.hypot(dx, dy)
            min_dist = self.radius + other.radius
            if dist < min_dist:
                is_self_static = (self.speed == 0)
                is_other_static = (other.speed == 0)
                
                if dist > 0.01:
                    overlap = min_dist - dist
                    if is_self_static and is_other_static:
                        continue
                    elif is_self_static:
                        other.x -= (dx / dist) * overlap
                        other.y -= (dy / dist) * overlap
                    elif is_other_static:
                        self.x += (dx / dist) * overlap
                        self.y += (dy / dist) * overlap
                    else:
                        push_x = (dx / dist) * overlap * 0.5
                        push_y = (dy / dist) * overlap * 0.5
                        self.x += push_x
                        self.y += push_y
                        other.x -= push_x
                        other.y -= push_y
                else:
                    if not is_self_static:
                        self.x += random.choice([-1, 1]) * 1.0
                        self.y += random.choice([-1, 1]) * 1.0
                    if not is_other_static:
                        other.x += random.choice([-1, 1]) * 1.0
                        other.y += random.choice([-1, 1]) * 1.0

    def update(self, player, game_map, bullet_manager, effect_manager, sound_manager, enemies=None):
        if getattr(self, 'stun_timer', 0) > 0:
            self.stun_timer -= 1
            self.is_moving = False
            self.step_timer += 0.05
            return
            
        if self.type == "dummy":
            self.is_moving = False
            self.path = []
            return
            
        if self.type == "moving_dummy":
            self.path_timer -= 1
            if self.path_timer <= 0 or not self.path:
                self.path_timer = random.randint(80, 120)
                cx = int(self.x // TILE_SIZE)
                cy = int(self.y // TILE_SIZE)
                for _ in range(15):
                    tx = cx + random.randint(-6, 6)
                    ty = cy + random.randint(-6, 6)
                    if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                        if game_map.grid[ty][tx] == TILE_EMPTY:
                            self.path = ai_logic.bfs_path(self.x, self.y, tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2, game_map)
                            break
            
            self.is_moving = False
            if self.path:
                tx, ty = self.path[0]
                if tx is not None:
                    dx = tx - self.x
                    dy = ty - self.y
                    dist = math.hypot(dx, dy)
                    if dist < 5:
                        self.path.pop(0)
                    else:
                        vx = (dx / dist) * self.speed
                        vy = (dy / dist) * self.speed
                        self.move_angle = math.atan2(vy, vx)
                        self.angle = self.move_angle
                        self.x += vx
                        self.y += vy
                        
                        self.resolve_wall_collision(game_map)
                        if enemies:
                            self.resolve_enemy_collisions(enemies)
                            self.resolve_wall_collision(game_map)
                            
                        self.is_moving = True
                        self.step_timer += 0.15 * (self.speed / 1.5)
            return

            
        dist_to_player = math.hypot(player.x - self.x, player.y - self.y)
        has_los = ai_logic.has_line_of_sight(self.x, self.y, player.x, player.y, game_map)
        
        # Kiểm tra nếu đường ngắm bắn bị che bởi lựu đạn khói
        if has_los and hasattr(effect_manager, 'smoke_clouds'):
            for sc in effect_manager.smoke_clouds:
                dx = player.x - self.x
                dy = player.y - self.y
                seg_len_sq = dx*dx + dy*dy
                if seg_len_sq > 0:
                    t = ((sc.x - self.x) * dx + (sc.y - self.y) * dy) / seg_len_sq
                    t = max(0.0, min(1.0, t))
                    proj_x = self.x + t * dx
                    proj_y = self.y + t * dy
                    dist_to_smoke = math.hypot(sc.x - proj_x, sc.y - proj_y)
                    current_r = getattr(sc, 'current_radius', sc.radius)
                    if dist_to_smoke < current_r:
                        has_los = False
                        break
        
        # ── Pathfinding / AI ────────────────────────────────────────────────
        self.path_timer -= 1

        # Transition to TRIGGER_ALARM if player noticed and alarm console is nearby
        if self.type != "boss" and not getattr(game_map, 'alarm_active', False):
            if self.state in ("HUNT", "SUSPICIOUS"):
                if not getattr(self, 'alarm_console_target', None):
                    console = self.find_nearest_alarm_console(game_map)
                    if console:
                        self.state = "TRIGGER_ALARM"
                        self.alarm_console_target = console
                        self.alarm_trigger_timer = 60
                        self.path = []
        
        # Check noise response
        if self.type != "boss" and self.state != "COVER":
            for nx, ny, nrad in game_map.active_noises:
                dist = math.hypot(self.x - nx, self.y - ny)
                if dist < nrad:
                    self.state = "SUSPICIOUS"
                    self.suspicious_target = (nx, ny)
                    self.suspicious_timer = 180  # 3 seconds at 60 FPS
                    self.path = []
                    break

        # State transitions
        if self.type != "boss" and self.state != "TRIGGER_ALARM":
            if self.hp / self.max_hp < 0.35:
                if self.state != "COVER":
                    self.state = "COVER"
                    self.cover_target = None
                    self.path = []
            elif self.type == "assault":
                # Xe tăng đỏ: phát hiện player bằng LOS (không giới hạn khoảng cách)
                # hoặc khi đến đủ gần (≤ 300px) trong lúc quét
                assault_detect = has_los or dist_to_player <= 300
                if assault_detect:
                    self.state = "HUNT"
                    self.last_player_pos = (player.x, player.y)
                    self.hunt_confirmed = True
                elif self.state == "HUNT" and not assault_detect:
                    # Mất dấu: nhớ vị trí cuối và tiếp tục đuổi
                    self.state = "SUSPICIOUS"
                    self.suspicious_target = self.last_player_pos or (player.x, player.y)
                    self.suspicious_timer = 300  # 5 giây
                    self.path = []
                    self.hunt_confirmed = False
            else:
                # Patrol (xanh), Sniper (vàng): phát hiện bằng LOS + range
                if has_los and dist_to_player <= self.range:
                    self.state = "HUNT"
                    self.last_player_pos = (player.x, player.y)
                elif self.state == "HUNT":
                    self.state = "SUSPICIOUS"
                    self.suspicious_target = self.last_player_pos if self.last_player_pos else (player.x, player.y)
                    self.suspicious_timer = 180
                    self.path = []

        # Execute State Logic
        if self.type != "boss":
            if self.state == "TRIGGER_ALARM":
                tx_c = int(self.alarm_console_target[0] // TILE_SIZE)
                ty_c = int(self.alarm_console_target[1] // TILE_SIZE)
                if game_map.get_tile(tx_c, ty_c) != TILE_ALARM_CONSOLE:
                    self.state = "HUNT"
                    self.alarm_console_target = None
                    self.path = []
                else:
                    dist_to_console = math.hypot(self.x - self.alarm_console_target[0], self.y - self.alarm_console_target[1])
                    if dist_to_console < 24:
                        self.is_moving = False
                        self.alarm_trigger_timer -= 1
                        if self.alarm_trigger_timer <= 0:
                            game_map.alarm_active = True
                            self.state = "HUNT"
                            self.alarm_console_target = None
                    else:
                        if self.path_timer <= 0 or not self.path:
                            self.path_timer = 20
                            self.path = ai_logic.bfs_path(self.x, self.y, self.alarm_console_target[0], self.alarm_console_target[1], game_map)
            elif self.state == "COVER":
                if self.cover_target:
                    if ai_logic.has_line_of_sight(self.cover_target[0], self.cover_target[1], player.x, player.y, game_map):
                        self.cover_target = None
                        self.path = []
                
                if not self.cover_target:
                    self.cover_target = self.find_cover_tile(player, game_map)
                    self.path = []
                    
                if self.cover_target:
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 20 + random.randint(0, 10)
                        self.path = ai_logic.astar_path(self.x, self.y, self.cover_target[0], self.cover_target[1], game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                else:
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 20 + random.randint(0, 10)
                        run_x = self.x + (self.x - player.x)
                        run_y = self.y + (self.y - player.y)
                        self.path = ai_logic.astar_path(self.x, self.y, run_x, run_y, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)

            elif self.state == "HUNT":
                if self.type == "assault":
                    # Map 1 (Red): BFS
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 20 + random.randint(0, 10)
                        self.current_algo = "BFS"
                        self.path = ai_logic.bfs_path(self.x, self.y, player.x, player.y, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "combat_dummy":
                    # Training range combat dummy: BFS
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 20 + random.randint(0, 10)
                        self.current_algo = "BFS"
                        self.path = ai_logic.bfs_path(self.x, self.y, player.x, player.y, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "sniper":
                    # Map 2 (Yellow): ASTAR (thay cho DFS để tránh đâm tường)
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 20 + random.randint(0, 10)
                        self.current_algo = "ASTAR"
                        self.path = ai_logic.astar_path(self.x, self.y, player.x, player.y, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "patrol":
                    # Map 3: ASTAR chặn đầu
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 15 + random.randint(0, 10)
                        self.current_algo = "ASTAR"
                        # Dự đoán vị trí người chơi 30 frame (nửa giây) tới
                        pred_x, pred_y = ai_logic.predict_player_pos(player, 30)
                        self.path = ai_logic.astar_path(self.x, self.y, pred_x, pred_y, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "heavy":
                    # Map 4: ASTAR (thay cho HEURISTIC để tránh kẹt tường)
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 15 + random.randint(0, 10)
                        self.current_algo = "ASTAR"
                        self.path = ai_logic.astar_path(self.x, self.y, player.x, player.y, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)

            elif self.state == "SUSPICIOUS":
                self.suspicious_timer -= 1
                if self.suspicious_target:
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 20 + random.randint(0, 10)
                        self.path = ai_logic.bfs_path(self.x, self.y, self.suspicious_target[0], self.suspicious_target[1], game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                
                dist_to_target = math.hypot(self.x - self.suspicious_target[0], self.y - self.suspicious_target[1]) if self.suspicious_target else 9999
                if dist_to_target < 15 or self.suspicious_timer <= 0:
                    if self.suspicious_timer <= 0:
                        self.state = "PATROL"
                        self.path = []

            elif self.state == "PATROL":
                if self.type == "assault":
                    # Map 1 (BFS): tuần tra tới ngẫu nhiên bằng BFS
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = random.randint(60, 100)
                        self.current_algo = "BFS"
                        cx = int(self.x // TILE_SIZE)
                        cy = int(self.y // TILE_SIZE)
                        for _ in range(15):
                            tx = cx + random.randint(-8, 8)
                            ty = cy + random.randint(-8, 8)
                            if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                                if game_map.grid[ty][tx] == TILE_EMPTY:
                                    self.path = ai_logic.bfs_path(self.x, self.y, tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2, game_map)
                                    break
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "combat_dummy":
                    # Training range combat dummy: BFS
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = random.randint(60, 100)
                        self.current_algo = "BFS"
                        cx = int(self.x // TILE_SIZE)
                        cy = int(self.y // TILE_SIZE)
                        for _ in range(15):
                            tx = cx + random.randint(-8, 8)
                            ty = cy + random.randint(-8, 8)
                            if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                                if game_map.grid[ty][tx] == TILE_EMPTY:
                                    self.path = ai_logic.bfs_path(self.x, self.y, tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2, game_map)
                                    break
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "sniper":
                    # Map 2 (DFS): tuần tra bằng DFS
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = 25 + random.randint(0, 10)
                        self.current_algo = "DFS"
                        nx, ny = ai_logic.dfs_patrol_step(self.x, self.y, self.visited_tiles, game_map)
                        tx, ty = ai_logic.tile(nx, ny)
                        self.visited_tiles.add((tx, ty))
                        if len(self.visited_tiles) > 30:
                            self.visited_tiles.clear()
                        self.path = ai_logic.astar_path(self.x, self.y, nx, ny, game_map)
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "patrol":
                    # Map 3 (ASTAR): tuần tra tới điểm ngẫu nhiên bằng A*
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = random.randint(60, 100)
                        self.current_algo = "ASTAR"
                        cx = int(self.x // TILE_SIZE)
                        cy = int(self.y // TILE_SIZE)
                        for _ in range(15):
                            tx = cx + random.randint(-8, 8)
                            ty = cy + random.randint(-8, 8)
                            if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                                if game_map.grid[ty][tx] == TILE_EMPTY:
                                    self.path = ai_logic.astar_path(self.x, self.y, tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2, game_map)
                                    break
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                elif self.type == "heavy":
                    # Map 4 (HEURISTIC): tuần tra tới điểm ngẫu nhiên bằng HEURISTIC
                    if self.path_timer <= 0 or not self.path:
                        self.path_timer = random.randint(60, 100)
                        self.current_algo = "HEURISTIC"
                        cx = int(self.x // TILE_SIZE)
                        cy = int(self.y // TILE_SIZE)
                        for _ in range(15):
                            tx = cx + random.randint(-8, 8)
                            ty = cy + random.randint(-8, 8)
                            if 0 <= tx < game_map.width and 0 <= ty < game_map.height:
                                if game_map.grid[ty][tx] == TILE_EMPTY:
                                    self.path = ai_logic.astar_path(self.x, self.y, tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2, game_map)
                                    break
                        if not self.path:
                            self.path_timer = 45 + random.randint(0, 15)
                    
        elif self.type == "boss":
            # Lưu tham chiếu để dùng khi vẽ tia quét
            self._last_player = player
            self._last_game_map = game_map
            
            if not hasattr(self, '_scanned_player_timer'):
                self._scanned_player_timer = 0
            if self._scanned_player_timer > 0:
                self._scanned_player_timer -= 1
                
            if not hasattr(self, 'laser_timer'):
                # Tăng timer lên thêm 120 frame (2 giây) để làm thời gian cảnh báo
                self.laser_timer = 240 if self.level >= 5 else 420 
            if not hasattr(self, 'active_lasers'):
                self.active_lasers = []
            if not hasattr(self, 'warning_lasers'):
                self.warning_lasers = []
                
            self.laser_timer -= 1
            
            # 1. Bật tia cảnh báo trước 2 giây (120 frames)
            if self.laser_timer == 120:
                num_lasers = 32 if self.level >= 5 else 3
                for i in range(num_lasers):
                    if self.level >= 5:
                        angle = (math.pi * 2 / 32) * i + random.uniform(-0.05, 0.05)
                    else:
                        angle = random.uniform(0, 2 * math.pi)
                    self.warning_lasers.append(angle)
                    
            # 2. Phát tia laser sát thương chính thức
            if self.laser_timer <= 0:
                self.laser_timer = 240 if self.level >= 5 else 420
                for angle in self.warning_lasers:
                    # Laser sát thương tồn tại trong 30 frame
                    self.active_lasers.append((self.x, self.y, angle, 30))
                self.warning_lasers = []
                    
            # Cập nhật tia laser và kiểm tra trúng mục tiêu (người chơi)
            new_lasers = []
            for lx, ly, angle, timer in self.active_lasers:
                timer -= 1
                
                if player:
                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)
                    v_px = player.x - lx
                    v_py = player.y - ly
                    proj_len = v_px * cos_a + v_py * sin_a
                    
                    # Tia laser dài 2000px
                    if 0 <= proj_len <= 2000:
                        perp_dist = abs(-v_px * sin_a + v_py * cos_a)
                        # Chiều rộng tia laser để xét va chạm là 20px
                        if perp_dist < player.radius + 20:
                            # Nếu người chơi trúng laser -> Boss báo động đỏ và đốt máu người chơi
                            self._scanned_player_timer = 240 if self.level >= 5 else 180 
                            player.take_damage(self.damage * 0.05, effect_manager, sound_manager)
                            
                if timer > 0:
                    new_lasers.append((lx, ly, angle, timer))
            self.active_lasers = new_lasers

            # 1. Tìm vị trí của ô lối thoát (Exit)
            if not hasattr(self, 'exit_pos'):
                self.exit_pos = None
                for gy in range(game_map.height):
                    for gx in range(game_map.width):
                        if game_map.grid[gy][gx] == TILE_EXIT:
                            self.exit_pos = (gx * TILE_SIZE + TILE_SIZE // 2, gy * TILE_SIZE + TILE_SIZE // 2)
                            break
                    if self.exit_pos: break

            # 2. Kiểm tra phát hiện người chơi
            player_near_exit = False
            dist_player_to_exit = 9999.0
            if self.exit_pos:
                dist_player_to_exit = math.hypot(player.x - self.exit_pos[0], player.y - self.exit_pos[1])
                if dist_player_to_exit < 400:  # Gần đích dưới 400px
                    player_near_exit = True
                    
            # Đổi cơ chế nhìn: Boss bị "mù", chủ yếu dò bằng Radar. 
            # Chỉ khi người chơi chạy lại RẤT gần (200px) thì Boss mới nhìn thấy bằng mắt thường.
            player_near_boss = (dist_to_player < 200 and has_los)
            
            # Boss các vòng luôn di chuyển liên tục để tìm kiếm người chơi
            is_detected = True

            # 3. Chuyển đổi trạng thái của Boss
            old_state = self.boss_state
            if is_detected:
                self.boss_state = "HUNT"
            else:
                # Nếu người chơi chạy xa khỏi boss và đích, chuyển lại tuần tra
                if self.boss_state == "HUNT" and dist_player_to_exit > 500 and dist_to_player > 600 and not getattr(self, 'force_hunt', False):
                    self.boss_state = "PATROL"
                    self.patrol_target = None
                    self.path = []

            # Phát âm thanh cảnh báo khi bắt đầu truy tìm
            if self.boss_state == "HUNT" and old_state == "PATROL":
                sound_manager.play('death') # âm thanh cảnh báo

            # 4. Tìm đường đi
            if self.boss_state == "HUNT":
                if self.path_timer <= 0 or not self.path:
                    self.path_timer = 12 + random.randint(0, 8)  # Staggered updates (was 6-10)
                    # Dự đoán trước 1 chút để đỡ bị kẹt
                    pred_x, pred_y = ai_logic.predict_player_pos(player, 10)
                    
                    # Sử dụng thuật toán A* thay vì BFS để Boss tìm thấy đường đi xa ở bản đồ rộng Màn 5
                    self.current_algo = "ASTAR"
                    self.path = ai_logic.astar_path(self.x, self.y, player.x, player.y, game_map)
                    if not self.path:
                        self.path_timer = 30 + random.randint(0, 15)
            else: # PATROL
                # Tuần tra linh hoạt
                if not self.patrol_target or not self.path:
                    found_target = False
                    for _ in range(100):
                        tx = random.randint(2, game_map.width - 3)
                        ty = random.randint(2, game_map.height - 3)
                        if game_map.grid[ty][tx] == TILE_EMPTY:
                            self.patrol_target = (tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2)
                            found_target = True
                            break
                    if not found_target:
                        self.patrol_target = (player.x, player.y)

                    # Boss tất cả các màn đều sử dụng BFS để tuần tra và truy đuổi, tránh kẹt vách
                    self.patrol_algo = "BFS"
                    path = ai_logic.bfs_path(self.x, self.y, self.patrol_target[0], self.patrol_target[1], game_map)
                        
                    if not path:
                        self.patrol_target = None
                        self.path_timer = 30 + random.randint(0, 15)
                    else:
                        self.path = path

        # ── Movement ────────────────────────────────────────────────────────
        self.is_moving = False
        if not hasattr(self, 'stuck_timer'):
            self.stuck_timer = 0
        if not hasattr(self, 'prev_pos'):
            self.prev_pos = (self.x, self.y)
            
        if self.path:
            tx, ty = self.path[0]
            if tx is not None:
                dx = tx - self.x
                dy = ty - self.y
                dist = math.hypot(dx, dy)
                if dist < 5:
                    self.path.pop(0)
                else:
                    move_speed = self.speed
                    if self.type == "boss" and getattr(self, "force_hunt", False):
                        move_speed = self.speed * 1.7  # Chạy siêu nhanh tìm người chơi
                    
                    desired_vx = dx / dist * move_speed
                    desired_vy = dy / dist * move_speed
                    
                    avoid_x, avoid_y = self.get_avoidance_force(game_map, enemies, desired_vx, desired_vy)
                    vx = desired_vx + avoid_x
                    vy = desired_vy + avoid_y
                    
                    # Cap speed to prevent excess velocity
                    v_len = math.hypot(vx, vy)
                    if v_len > move_speed:
                        vx = vx / v_len * move_speed
                        vy = vy / v_len * move_speed
                        
                    # Di chuyển trực tiếp vận tốc đã tính toán
                    self.x += vx
                    self.y += vy
                    
                    # Double-pass resolution: wall -> enemy -> wall
                    self.resolve_wall_collision(game_map)
                    if enemies:
                        self.resolve_enemy_collisions(enemies)
                        self.resolve_wall_collision(game_map)
                        
                    self.is_moving = True
                    self.step_timer += 0.15 * (self.speed / 1.5)
                    self.move_angle = math.atan2(vy, vx)  # thân xe theo hướng di chuyển
                    self.angle = self.move_angle           # nòng pháo mặc định cùng hướng
            
            # Cập nhật stuck_timer dựa trên thực tế vị trí thay đổi
            dist_moved = math.hypot(self.x - self.prev_pos[0], self.y - self.prev_pos[1])
            if dist_moved < 0.2:
                self.stuck_timer += 1
            else:
                self.stuck_timer = 0
            self.prev_pos = (self.x, self.y)
            
            if self.stuck_timer > 8:
                self.path = []
                self.stuck_timer = 0
                if self.type == "boss":
                    self.patrol_target = None
        
        # ── Shooting ────────────────────────────────────────────────────────
        if has_los and dist_to_player <= self.range:
            self.angle = math.atan2(player.y - self.y, player.x - self.x)  # nòng pháo nhắm player
            # thân xe KHÔNG thay đổi khi bắn — giữ move_angle
            
            self.cooldown -= 1
            if self.cooldown <= 0:
                self.cooldown = self.max_cooldown
                self.shoot(player, bullet_manager, effect_manager, sound_manager)

    def shoot(self, player, bullet_manager, effect_manager, sound_manager):
        sound = 'sniper_shot' if self.type == 'sniper' else 'enemy_shot'
        sound_manager.play(sound)
        
        nx = math.cos(self.angle)
        ny = math.sin(self.angle)
        mx = self.x + nx * (self.radius + 5)
        my = self.y + ny * (self.radius + 5)
        
        if self.type != "boss":
            spread = random.uniform(-0.1, 0.1)
            if self.type == "sniper": spread = 0
            fa = self.angle + spread
            tx = mx + math.cos(fa) * 100
            ty = my + math.sin(fa) * 100
            bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage)
            effect_manager.add_muzzle_flash(mx, my, self.angle)
        else:
            # Boss Signature Skills based on Level
            if self.level == 1:
                # JUNGLE SPREAD: 3-way spread target shot
                for s in [-0.25, 0, 0.25]:
                    fa = self.angle + s
                    tx = mx + math.cos(fa) * 100
                    ty = my + math.sin(fa) * 100
                    bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage)
                    
            elif self.level == 2:
                # DESERT BURST: Alternates between 5-way spread and 10-bullet ring
                self.skill_timer += 1
                if (self.skill_timer // 20) % 2 == 0:
                    # 5-way spread
                    for s in [-0.3, -0.15, 0, 0.15, 0.3]:
                        fa = self.angle + s
                        tx = mx + math.cos(fa) * 100
                        ty = my + math.sin(fa) * 100
                        bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.8)
                else:
                    # 10-bullet ring
                    for i in range(10):
                        fa = (math.pi * 2 / 10) * i
                        tx = mx + math.cos(fa) * 100
                        ty = my + math.sin(fa) * 100
                        bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.6)
                        
            elif self.level == 3:
                # SPIRAL BLIZZARD: Rapid spiral Blizzard fire
                self.cooldown = 4 # Very fast firing rate
                # Spiral angle rotates over time
                fa = (pygame.time.get_ticks() / 150) % (math.pi * 2)
                for i in range(3): # 3 spiral arms
                    fa2 = fa + i * (math.pi * 2 / 3)
                    tx = mx + math.cos(fa2) * 100
                    ty = my + math.sin(fa2) * 100
                    bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.5)
                    
            elif self.level == 4:
                # TÊN LỬA ĐỊNH VỊ (HOMING MISSILES): Bắn tên lửa định vị tự động truy tìm người chơi
                self.cooldown = 45 # Bắn mỗi 0.75 giây
                # Bắn 1 tên lửa định vị bám đuổi người chơi
                bullet_manager.add_missile(mx, my, player, damage=self.damage * 1.0)
                # Bắn thêm 2 đạn thường lệch góc để gây khó khăn cho người chơi
                for s in [-0.2, 0.2]:
                    fa = self.angle + s
                    tx = mx + math.cos(fa) * 100
                    ty = my + math.sin(fa) * 100
                    bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.5)
                        
            else: # Level 5 and up
                # CHIẾN HẠM HUỶ DIỆT (Level 5 Boss Skill Set) - SIÊU KHÓ
                self.skill_timer += 1
                self.cooldown = 6
                
                # ── SKILL 1: Tên lửa tầm nhiệt x3 mỗi 35 frame ──
                if self.skill_timer % 35 == 0:
                    for offset in [-25, 0, 25]:
                        bullet_manager.add_missile(
                            mx + offset * math.sin(self.angle),
                            my - offset * math.cos(self.angle),
                            player, damage=self.damage * 0.7)
                    
                # ── SKILL 2: Vòng đạn xoáy ốc 20 tia mỗi 50 frame ──
                if self.skill_timer % 50 == 0:
                    base_angle = (self.skill_timer * 0.15) % (math.pi * 2)
                    for i in range(20):
                        fa = base_angle + (math.pi * 2 / 20) * i
                        tx = mx + math.cos(fa) * 100
                        ty = my + math.sin(fa) * 100
                        bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.5, color=(255, 0, 255))
                        
                # ── SKILL 3: Bão lửa xoáy ốc liên tục (3 cánh xoay) ──
                if self.skill_timer % 8 == 0:
                    spiral_angle = (self.skill_timer * 0.1) % (math.pi * 2)
                    for arm in range(3):
                        fa = spiral_angle + arm * (math.pi * 2 / 3)
                        tx = mx + math.cos(fa) * 120
                        ty = my + math.sin(fa) * 120
                        bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.35, color=(255, 100, 0))
                        
                # ── SKILL 4: Ném bom liên hoàn (Molotov + Frag + Flashbang) mỗi 80 frame ──
                if self.skill_timer % 80 == 0:
                    for _ in range(2):
                        bullet_manager.add_grenade(self.x, self.y, player.x + random.randint(-50, 50), player.y + random.randint(-50, 50), "MOLOTOV")
                    bullet_manager.add_grenade(self.x, self.y, player.x + random.randint(-30, 30), player.y + random.randint(-30, 30), "FRAG")
                    bullet_manager.add_grenade(self.x, self.y, player.x + random.randint(-20, 20), player.y + random.randint(-20, 20), "FLASHBANG")
                    
                # ── SKILL 5: Bắn 5 loạt đạn thẳng vào người chơi mỗi 20 frame ──
                if self.skill_timer % 20 == 0:
                    for s in [-0.15, -0.07, 0, 0.07, 0.15]:
                        fa = self.angle + s
                        tx = mx + math.cos(fa) * 100
                        ty = my + math.sin(fa) * 100
                        bullet_manager.add_bullet(mx, my, tx, ty, is_enemy=True, damage=self.damage * 0.6)
                        
                # ── SKILL 6: Mưa tên lửa thảm sát toàn vùng mỗi 180 frame ──
                if self.skill_timer % 180 == 0:
                    for _ in range(5):
                        rx = player.x + random.randint(-200, 200)
                        ry = player.y + random.randint(-200, 200)
                        bullet_manager.add_missile(self.x, self.y, type('P', (), {'x': rx, 'y': ry})(), damage=self.damage * 0.6)

            effect_manager.add_muzzle_flash(mx, my, self.angle)

    def take_damage(self, amount, effect_manager, sound_manager):
        if self.type in ("dummy", "moving_dummy", "combat_dummy"):
            self.hp -= amount
            effect_manager.add_sparks(self.x, self.y, count=random.randint(4, 7))
            effect_manager.add_floating_text(self.x, self.y - 20, f"-{int(amount)}", (255, 150, 0))
            if self.hp <= 0:
                self.alive = False
                sound_manager.play('death')
            return

        # Giảm sát thương nhận vào đối với Boss cuối màn 6 để kéo dài trận đấu
        if self.type == "boss" and self.level == 6:
            amount *= 0.35  # Chỉ nhận 35% sát thương
            # Hiện text giảm sát thương màu neon đặc biệt để người chơi nhận biết
            effect_manager.add_floating_text(self.x, self.y - 45, f"-{int(amount)} (GIÁP HẤP THỤ)", (0, 220, 255))
        else:
            # Hiện text sát thương thường
            effect_manager.add_floating_text(self.x, self.y - 30, f"-{int(amount)}", (255, 100, 100))

        self.hp -= amount
        effect_manager.add_sparks(self.x, self.y, count=random.randint(6, 10))
        effect_manager.add_smoke(self.x, self.y, count=random.randint(1, 3))
        if self.hp <= 0:
            self.alive = False
            sound_manager.play('death')

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        
        # ── Draw Scanning Rays and Path for Boss ──────────────────────────
        if self.type == "boss":
            # 1. Vẽ đường đi màu đỏ (đậm nét neon) đại diện cho thuật toán tìm đường BFS/DFS
            if self.path:
                pts = [(tx - cam_x, ty - cam_y) for tx, ty in self.path]
                pts.insert(0, (self.x - cam_x, self.y - cam_y))
                if len(pts) >= 2:
                    ps = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                    pcol = (255, 0, 0)
                    pulse = int(120 + 80 * math.sin(pygame.time.get_ticks() / 150))
                    # Glow
                    pygame.draw.lines(ps, (*pcol, pulse // 4), False, pts, 8)
                    # Core
                    pygame.draw.lines(ps, (*pcol, pulse), False, pts, 3)
                    screen.blit(ps, (0, 0))

            # 2. Vẽ tia cảnh báo (mỏng, mờ, nhấp nháy) trước khi bắn
            if hasattr(self, 'warning_lasers') and self.warning_lasers:
                draw_start = (sx, sy)
                # Tính toán alpha nhấp nháy nhanh theo thời gian
                blink_alpha = int(100 + 80 * math.sin(pygame.time.get_ticks() / 50))
                ray_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                
                for angle in self.warning_lasers:
                    end_x = self.x + math.cos(angle) * 2000
                    end_y = self.y + math.sin(angle) * 2000
                    draw_end = (int(end_x - cam_x), int(end_y - cam_y))
                    
                    # Tia cảnh báo rất mỏng
                    pygame.draw.line(ray_surf, (255, 50, 50, blink_alpha), draw_start, draw_end, 1)
                screen.blit(ray_surf, (0, 0))

            # 3. Vẽ các tia laser ngẫu nhiên sát thương của Boss
            if hasattr(self, 'active_lasers') and self.active_lasers:
                draw_start = (sx, sy)
                # TỐI ƯU HÓA: Tạo duy nhất một Surface ngoài vòng lặp để tránh tụt FPS khi vẽ 32 tia
                ray_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
                
                for lx, ly, angle, timer in self.active_lasers:
                    # Laser rực rỡ và dày dần theo thời gian
                    alpha = min(255, timer * 8)
                    thickness = max(2, int((30 - timer) / 3))
                    
                    ray_color = (255, 30, 30, alpha)
                    core_color = (255, 200, 200, alpha)
                    
                    # Tia dài 2000px
                    end_x = lx + math.cos(angle) * 2000
                    end_y = ly + math.sin(angle) * 2000
                    draw_end = (int(end_x - cam_x), int(end_y - cam_y))
                    
                    pygame.draw.line(ray_surf, ray_color, draw_start, draw_end, thickness * 3)
                    pygame.draw.line(ray_surf, core_color, draw_start, draw_end, thickness)
                    
                screen.blit(ray_surf, (0, 0))
        
        bob_y = 0
        if self.is_moving:
            bob_y = abs(math.sin(self.step_timer * 8)) * 2

        # ── Smooth rotation cho thân xe (move_angle) và nòng pháo (angle) ──
        if not hasattr(self, 'draw_angle'):
            self.draw_angle = self.angle
        if not hasattr(self, 'draw_move_angle'):
            self.draw_move_angle = getattr(self, 'move_angle', self.angle)

        # Lerp nòng pháo nhanh (0.25) — phản ứng nhanh khi nhắm
        diff_gun = (self.angle - self.draw_angle + math.pi) % (2 * math.pi) - math.pi
        self.draw_angle += diff_gun * 0.25

        # Lerp thân xe chậm hơn (0.12) — xe tăng quay thân chậm, thực tế hơn
        move_a = getattr(self, 'move_angle', self.angle)
        diff_body = (move_a - self.draw_move_angle + math.pi) % (2 * math.pi) - math.pi
        self.draw_move_angle += diff_body * 0.12

        # ── Hàm vẽ xe tăng top-down bằng pygame.draw ──────────────────────
        def draw_tank(cx, cy, body_angle, gun_angle, body_color, track_color, gun_color, size=18):
            """
            Vẽ xe tăng nhìn từ trên xuống:
            - Thân xe: hình chữ nhật bo góc xoay theo body_angle
            - Bánh xích: 2 dải hai bên thân
            - Tháp pháo: hình tròn ở giữa
            - Nòng pháo: hình chữ nhật dài xoay theo gun_angle
            """
            import pygame
            cos_b = math.cos(body_angle)
            sin_b = math.sin(body_angle)

            # Kích thước xe tăng
            bw = size + 4   # chiều rộng thân (ngang với hướng di chuyển)
            bh = size - 2   # chiều cao thân (dọc)
            tw = 5          # chiều rộng bánh xích
            tl = size + 8   # chiều dài bánh xích

            def rot(px, py):
                """Xoay điểm (px,py) quanh gốc theo body_angle rồi dịch về (cx,cy)"""
                return (int(cx + px * cos_b - py * sin_b),
                        int(cy + px * sin_b + py * cos_b))

            # ── Bóng đổ ──
            shadow_surf = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60),
                                (size//2, size//2 + 4, size*3, size*2))
            screen.blit(shadow_surf, (cx - size*2, cy - size*2))

            # ── Bánh xích trái ──
            track_pts_l = [rot(-bw//2 - tw, -tl//2),
                           rot(-bw//2,      -tl//2),
                           rot(-bw//2,       tl//2),
                           rot(-bw//2 - tw,  tl//2)]
            pygame.draw.polygon(screen, track_color, track_pts_l)
            pygame.draw.polygon(screen, (track_color[0]//2, track_color[1]//2, track_color[2]//2),
                                track_pts_l, 1)
            # Vạch bánh xích
            for i in range(-3, 4):
                p1 = rot(-bw//2 - tw, i * (tl // 7))
                p2 = rot(-bw//2,      i * (tl // 7))
                pygame.draw.line(screen, (track_color[0]//3, track_color[1]//3, track_color[2]//3),
                                 p1, p2, 1)

            # ── Bánh xích phải ──
            track_pts_r = [rot(bw//2,      -tl//2),
                           rot(bw//2 + tw, -tl//2),
                           rot(bw//2 + tw,  tl//2),
                           rot(bw//2,       tl//2)]
            pygame.draw.polygon(screen, track_color, track_pts_r)
            pygame.draw.polygon(screen, (track_color[0]//2, track_color[1]//2, track_color[2]//2),
                                track_pts_r, 1)
            for i in range(-3, 4):
                p1 = rot(bw//2,      i * (tl // 7))
                p2 = rot(bw//2 + tw, i * (tl // 7))
                pygame.draw.line(screen, (track_color[0]//3, track_color[1]//3, track_color[2]//3),
                                 p1, p2, 1)

            # ── Thân xe ──
            body_pts = [rot(-bw//2, -bh//2),
                        rot( bw//2, -bh//2),
                        rot( bw//2,  bh//2),
                        rot(-bw//2,  bh//2)]
            # Nền thân
            pygame.draw.polygon(screen, body_color, body_pts)
            # Viền thân
            dark_body = (max(0, body_color[0]-40), max(0, body_color[1]-40), max(0, body_color[2]-40))
            pygame.draw.polygon(screen, dark_body, body_pts, 2)
            # Chi tiết tấm giáp trên thân
            armor_pts = [rot(-bw//2 + 3, -bh//2 + 3),
                         rot( bw//2 - 3, -bh//2 + 3),
                         rot( bw//2 - 3,  bh//2 - 3),
                         rot(-bw//2 + 3,  bh//2 - 3)]
            light_body = (min(255, body_color[0]+30), min(255, body_color[1]+30), min(255, body_color[2]+30))
            pygame.draw.polygon(screen, light_body, armor_pts, 1)

            # ── Tháp pháo (turret) ──
            turret_r = size // 2 - 1
            pygame.draw.circle(screen, dark_body, (cx, cy), turret_r + 2)
            pygame.draw.circle(screen, body_color, (cx, cy), turret_r)
            pygame.draw.circle(screen, light_body, (cx, cy), turret_r - 2, 1)

            # ── Nòng pháo — xoay theo gun_angle độc lập ──
            cos_g = math.cos(gun_angle)
            sin_g = math.sin(gun_angle)
            barrel_len = size + 6
            barrel_w   = 3
            # Điểm gốc nòng (tâm tháp pháo)
            # Vẽ nòng pháo như hình chữ nhật dài
            brl_pts = [
                (int(cx + (turret_r - 1) * cos_g - barrel_w * (-sin_g)),
                 int(cy + (turret_r - 1) * sin_g - barrel_w * cos_g)),
                (int(cx + (turret_r - 1) * cos_g + barrel_w * (-sin_g)),
                 int(cy + (turret_r - 1) * sin_g + barrel_w * cos_g)),
                (int(cx + barrel_len * cos_g + barrel_w * (-sin_g)),
                 int(cy + barrel_len * sin_g + barrel_w * cos_g)),
                (int(cx + barrel_len * cos_g - barrel_w * (-sin_g)),
                 int(cy + barrel_len * sin_g - barrel_w * cos_g)),
            ]
            pygame.draw.polygon(screen, gun_color, brl_pts)
            pygame.draw.polygon(screen, dark_body, brl_pts, 1)
            # Đầu nòng
            tip_x = int(cx + barrel_len * cos_g)
            tip_y = int(cy + barrel_len * sin_g)
            pygame.draw.circle(screen, dark_body, (tip_x, tip_y), barrel_w)

        # ── Chọn màu theo loại xe tăng và vẽ ─────────────────────────────
        boss_img = get_boss_image(self.level)
        drawn = False
        is_tank = self.type in ("assault", "sniper", "patrol", "heavy")

        if is_tank:
            if self.type == "assault":
                body_col  = (180, 45,  45)   # đỏ đậm
                track_col = (60,  20,  20)
                gun_col   = (120, 30,  30)
            elif self.type == "sniper":
                body_col  = (190, 165, 30)   # vàng đậm
                track_col = (70,  55,  10)
                gun_col   = (130, 110, 20)
            elif self.type == "patrol":
                body_col  = (40,  160, 60)   # xanh lá
                track_col = (15,  60,  20)
                gun_col   = (25,  110, 40)
            else:  # heavy
                body_col  = (50,  90,  200)  # xanh dương
                track_col = (20,  35,  80)
                gun_col   = (35,  65,  150)

            draw_tank(sx, sy - int(bob_y),
                      self.draw_move_angle,
                      self.draw_angle,
                      body_col, track_col, gun_col,
                      size=18)
            drawn = True

        elif self.type == "boss" and boss_img:
            # Boss vẫn dùng ảnh, chỉ flip ngang theo hướng nhìn
            flip_x = math.cos(self.angle) >= 0
            img_to_draw = pygame.transform.flip(boss_img, flip_x, False)
            draw_rect = img_to_draw.get_rect(center=(sx, sy - int(bob_y)))
            screen.blit(img_to_draw, draw_rect.topleft)
            drawn = True
        elif self.type in ("dummy", "moving_dummy", "combat_dummy"):
            # Vẽ bóng cho bia tập bắn
            pygame.draw.circle(screen, (20, 20, 20, 80), (sx, sy + 4), self.radius)
            # Vòng ngoài cùng (trắng)
            pygame.draw.circle(screen, (240, 240, 240), (sx, sy), self.radius)
            # Vòng đỏ
            pygame.draw.circle(screen, (255, 50, 50), (sx, sy), int(self.radius * 0.75))
            # Vòng trắng thứ 2
            pygame.draw.circle(screen, (240, 240, 240), (sx, sy), int(self.radius * 0.5))
            # Tâm đỏ
            pygame.draw.circle(screen, (255, 50, 50), (sx, sy), int(self.radius * 0.25))
            
            # Thêm vạch chữ thập mảnh ngắm bắn
            pygame.draw.line(screen, (30, 30, 30), (sx - self.radius - 2, sy), (sx + self.radius + 2, sy), 1)
            pygame.draw.line(screen, (30, 30, 30), (sx, sy - self.radius - 2), (sx, sy + self.radius + 2), 1)
            
            if self.type == "combat_dummy":
                # Nòng súng cho combat dummy để biết nó hướng về đâu
                nx = math.cos(self.angle)
                ny = math.sin(self.angle)
                gx = sx + nx * (self.radius + 6)
                gy = sy + ny * (self.radius + 6)
                pygame.draw.line(screen, (80, 80, 80), (sx, sy), (gx, gy), 3)
                
            # Vẽ thanh HP nhỏ màu neon cho bia tập bắn
            bar_w = 32
            bar_h = 4
            bx = sx - bar_w // 2
            by = sy - self.radius - 8
            pct = max(0.0, min(1.0, self.hp / self.max_hp))
            pygame.draw.rect(screen, (30, 30, 30), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
            pygame.draw.rect(screen, (150, 30, 30), (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, (0, 255, 100), (bx, by, int(bar_w * pct), bar_h))
            
            drawn = True
            
        if not drawn:
            # Shadow
            pygame.draw.circle(screen, (20, 20, 20, 100), (sx, sy+4), self.radius)
            
            # Body
            pygame.draw.circle(screen, DARK_GRAY, (sx, sy), self.radius)
            pygame.draw.circle(screen, self.color, (sx, sy), self.radius-2)
            
            # Gun
            nx = math.cos(self.angle)
            ny = math.sin(self.angle)
            gx = sx + nx * (self.radius + 6)
            gy = sy + ny * (self.radius + 6)
            pygame.draw.line(screen, (50, 50, 50), (sx, sy), (gx, gy), 3)
        
        # Boss glow and HUD
        if self.type == "boss":
            # Pulsing glow
            pulse = int(50 + 30 * math.sin(pygame.time.get_ticks() / 150))
            glow_r = 65 if self.level == 6 else (38 if self.level == 5 else (35 if self.level == 4 else 20))
            surf = pygame.Surface((glow_r*6, glow_r*6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*BOSS_COLOR, pulse), (glow_r*3, glow_r*3), int(glow_r*2.5))
            screen.blit(surf, (sx - glow_r*3, sy - glow_r*3))
            
            # HP Bar (Modern)
            bar_w = 60
            bar_h = 6
            bx = sx - bar_w//2
            by = sy - glow_r - 12
            pct = max(0, self.hp / self.max_hp)
            pygame.draw.rect(screen, (30, 30, 30), (bx-1, by-1, bar_w+2, bar_h+2))
            pygame.draw.rect(screen, RED, (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, LIME, (bx, by, int(bar_w*pct), bar_h))
            
            # Skill Indicator
            font = pygame.font.SysFont("arial", 12, bold=True)
            txt = font.render(self.skill_name, True, WHITE)
            screen.blit(txt, (sx - txt.get_width()//2, by - 14))
            
        # Vẽ vòng sao choáng trên đầu nếu bị choáng
        if getattr(self, 'stun_timer', 0) > 0:
            t = pygame.time.get_ticks() * 0.012
            for i in range(3):
                sa = t + i * (2 * math.pi / 3)
                s_offset_x = math.cos(sa) * 14
                s_offset_y = -self.radius - 12 + math.sin(sa) * 4
                pygame.draw.circle(screen, (0, 220, 255), (sx + int(s_offset_x), sy + int(s_offset_y)), 3)
                pygame.draw.circle(screen, WHITE, (sx + int(s_offset_x), sy + int(s_offset_y)), 3, 1)

        # Draw AI state indicator above their heads
        if self.type != "boss" and getattr(self, 'stun_timer', 0) <= 0:
            font = pygame.font.SysFont("arial", 11, bold=True)
            if getattr(self, 'state', None) == "TRIGGER_ALARM":
                txt = font.render("ALARM!", True, (255, 50, 50))
                screen.blit(txt, (sx - txt.get_width()//2, sy - self.radius - 14))
                if getattr(self, 'alarm_trigger_timer', 60) < 60:
                    pct = (60 - self.alarm_trigger_timer) / 60.0
                    pygame.draw.rect(screen, (30, 30, 30), (sx - 20, sy - self.radius - 22, 40, 5))
                    pygame.draw.rect(screen, (255, 50, 50), (sx - 20, sy - self.radius - 22, int(40 * pct), 5))
            elif getattr(self, 'state', None) == "SUSPICIOUS":
                txt = font.render("?", True, (255, 200, 0))
                screen.blit(txt, (sx - txt.get_width()//2, sy - self.radius - 14))
            elif getattr(self, 'state', None) == "HUNT":
                # Dấu chấm than đỏ
                excl = font.render("!", True, (255, 50, 50))
                screen.blit(excl, (sx - excl.get_width()//2, sy - self.radius - 14))
            elif getattr(self, 'state', None) == "COVER":
                txt = font.render("COVER", True, (0, 200, 255))
                screen.blit(txt, (sx - txt.get_width()//2, sy - self.radius - 14))


class EnemyManager:
    def __init__(self, map_spawns, level=1, game_map=None):
        self.enemies = []
        self.cameras = []
        self.level = level
        self.respawn_queue = []
        
        if level == 6:
            # Hang Boss cuối: Chỉ spawn duy nhất Boss 5 (trùm cuối) tại trung tâm
            bx = game_map.width // 2 * TILE_SIZE + TILE_SIZE // 2 if game_map else 25 * TILE_SIZE + TILE_SIZE // 2
            by = game_map.height // 2 * TILE_SIZE + TILE_SIZE // 2 if game_map else 20 * TILE_SIZE + TILE_SIZE // 2
            self.enemies.append(Enemy(bx, by, "boss", 5))
            return
            
        if game_map and hasattr(game_map, 'camera_spawns'):
            for cx, cy, base_angle in game_map.camera_spawns:
                self.cameras.append(SecurityCamera(cx, cy, base_angle))
        
        # Chọn loại lính theo Map
        if level == 0:
            types = ["dummy", "moving_dummy", "combat_dummy"]
        elif level == 1:
            types = ["assault"]
        elif level == 2:
            types = ["sniper"]
        elif level == 3:
            types = ["patrol"]
        elif level == 4:
            types = ["heavy"]
        else: # level 5
            types = ["assault", "sniper", "patrol", "heavy"]
            
        for px, py in map_spawns:
            etype = random.choice(types)
            self.enemies.append(Enemy(px, py, etype, level))
            
        # Add BOSS
        bx, by = None, None
        if game_map and level != 0:
            # Màn 4: Boss xuất hiện gần lối thoát hiểm
            if level == 4:
                target_tx = int(game_map.exit_px // TILE_SIZE)
                target_ty = int(game_map.exit_py // TILE_SIZE)
            # Các màn khác: Boss xuất hiện ở giữa trung tâm bản đồ
            else:
                target_tx = game_map.width // 2
                target_ty = game_map.height // 2
            
            best_dist = 999999
            for ty in range(1, game_map.height - 1):
                for tx in range(1, game_map.width - 1):
                    if game_map.grid[ty][tx] == TILE_EMPTY:
                        dist = (tx - target_tx) ** 2 + (ty - target_ty) ** 2
                        if dist < best_dist:
                            best_dist = dist
                            bx = tx * TILE_SIZE + TILE_SIZE // 2
                            by = ty * TILE_SIZE + TILE_SIZE // 2
                            
        # Fallback nếu không tìm thấy hoặc không có game_map
        if bx is None and map_spawns and level != 0:
            bx, by = map_spawns[-1]
            
        if bx is not None and level != 0:
            if level < 5:
                self.enemies.append(Enemy(bx, by, "boss", level))
            else:
                # Ở màn 5, đầu tiên chọn các vị trí ngẫu nhiên phân bố đều cho 4 boss
                spawn_pts = random.sample(map_spawns, min(4, len(map_spawns))) if len(map_spawns) >= 4 else [(bx, by)] * 4
                # Chỉ spawn Boss 1 ban đầu
                stx, sty = spawn_pts[0]
                self.enemies.append(Enemy(stx, sty, "boss", 1))
                
                # Lưu trữ các Boss 2, 3, 4 vào hàng đợi để spawn tuần tự
                self.boss_spawn_queue = []
                for i, b_lvl in enumerate([2, 3, 4]):
                    s_x, s_y = spawn_pts[i + 1]
                    self.boss_spawn_queue.append((s_x, s_y, b_lvl))

    def update(self, player, game_map, bullet_manager, effect_manager, sound_manager):
        # Update respawn queue
        new_respawn_queue = []
        if hasattr(self, 'respawn_queue'):
            for item in self.respawn_queue:
                item["timer"] -= 1
                if item["timer"] <= 0:
                    self.enemies.append(Enemy(item["x"], item["y"], item["type"], self.level))
                else:
                    new_respawn_queue.append(item)
            self.respawn_queue = new_respawn_queue

        new_enemies = []
        for e in self.enemies:
            if not e.alive:
                game_map.add_burnt_decal(e.x, e.y)
                effect_manager.add_explosion(e.x, e.y, radius=110 if e.type == "boss" else 80)
                if self.level == 0 and e.type in ("dummy", "moving_dummy", "combat_dummy"):
                    self.respawn_queue.append({
                        "x": e.x,
                        "y": e.y,
                        "type": e.type,
                        "timer": 180 # 3 seconds (60 FPS)
                    })
                continue
            e.update(player, game_map, bullet_manager, effect_manager, sound_manager, self.enemies)
            if not e.alive:
                game_map.add_burnt_decal(e.x, e.y)
                effect_manager.add_explosion(e.x, e.y, radius=110 if e.type == "boss" else 80)
                if self.level == 0 and e.type in ("dummy", "moving_dummy", "combat_dummy"):
                    self.respawn_queue.append({
                        "x": e.x,
                        "y": e.y,
                        "type": e.type,
                        "timer": 180
                    })
            else:
                new_enemies.append(e)
        self.enemies = new_enemies

        # Spawn boss tiếp theo ở màn 5 nếu boss hiện tại đã bị tiêu diệt
        if self.level == 5 and hasattr(self, 'boss_spawn_queue') and self.boss_spawn_queue:
            boss_alive = any(e.alive and e.type == "boss" for e in self.enemies)
            if not boss_alive:
                stx, sty, b_lvl = self.boss_spawn_queue.pop(0)
                next_boss = Enemy(stx, sty, "boss", b_lvl)
                self.enemies.append(next_boss)
                
                # Hiệu ứng xuất hiện hoành tráng
                sound_manager.play('hurt')
                effect_manager.add_floating_text(stx, sty - 40, f"CẢNH BÁO: BOSS CẤP {b_lvl} XUẤT HIỆN!", (255, 50, 50))
                effect_manager.add_explosion(stx, sty, radius=120)

        new_cameras = []
        for c in self.cameras:
            if not c.alive:
                continue
            triggered = c.update(player, game_map, effect_manager)
            if triggered:
                game_map.alarm_active = True
            if c.alive:
                new_cameras.append(c)
        self.cameras = new_cameras

    def draw(self, screen, cam_x, cam_y):
        for e in self.enemies:
            e.draw(screen, cam_x, cam_y)
        for c in self.cameras:
            c.draw(screen, cam_x, cam_y)
