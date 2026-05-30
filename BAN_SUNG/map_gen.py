import random
import math
import os
from constants import (TILE_SIZE, MAP_W, MAP_H,
                       TILE_EMPTY, TILE_WALL, TILE_COVER, TILE_TUNNEL, TILE_EXIT, TILE_BARREL,
                       TILE_ALARM_CONSOLE, TILE_LASER, ALARM_CONSOLE_HP, LASER_HP, CAMERA_HP,
                       FLOOR_COLOR, TREE_COLOR, COVER_COLOR, TUNNEL_COLOR, EXIT_COLOR, BARREL_COLOR,
                       JUNGLE_DARK, JUNGLE_MID, JUNGLE_LIGHT, DARK_BG, WHITE, BLACK, YELLOW)
import pygame


class GameMap:
    def __init__(self, level=1):
        self.level       = level
        if level == 5:
            # Làm bản đồ màn 5 rộng ra (120x90 ô)
            self.width   = 120
            self.height  = 90
        elif level == 6:
            # Bản đồ màn 6: Hang Boss cuối (50x40 ô)
            self.width   = 50
            self.height  = 40
        else:
            self.width   = MAP_W
            self.height  = MAP_H
        self.pixel_w     = self.width * TILE_SIZE
        self.pixel_h     = self.height * TILE_SIZE
        self.grid        = [[TILE_EMPTY]*self.width for _ in range(self.height)]
        self.detail_grid = [[0]*self.width for _ in range(self.height)] # 0: Mud, 1: Path, 2: Crater, 3: Grass
        self.player_spawn  = (3*TILE_SIZE + TILE_SIZE//2, 3*TILE_SIZE + TILE_SIZE//2)
        self.enemy_spawns  = []
        self.item_spawns   = []
        self._surface      = None
        self._tree_image   = None
        self._small_tree_image = None
        self._big_tree_image = None
        
        def load_and_process_tree(filename, size):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(base_dir, "ANH", filename)
            if not os.path.exists(img_path): return None
            try:
                img = pygame.image.load(img_path).convert_alpha()
                bg_color = img.get_at((0, 0))
                img.lock()
                w, h = img.get_size()
                for x in range(w):
                    for y in range(h):
                        c = img.get_at((x, y))
                        dist = abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2])
                        if dist < 80:
                            img.set_at((x, y), (0, 0, 0, 0))
                img.unlock()
                return pygame.transform.scale(img, size)
            except Exception as e:
                print(f"Lỗi load ảnh {filename}:", e)
                return None
                
        self._tree_image = load_and_process_tree("cây nhỏ'.jpg", (TILE_SIZE + 4, TILE_SIZE + 4))
        self._small_tree_image = load_and_process_tree("cây nhỏ'.jpg", (20, 20))
        self._big_tree_image = load_and_process_tree("cây to.jpg", (TILE_SIZE + 24, TILE_SIZE + 24))
        
        self.cover_hp = {}
        self.alarm_console_hp = {}
        self.laser_hp = {}
        self.camera_spawns = []
        self.laser_lines = []
        
        self._generate(level)
        self._bake_surface()
        
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == TILE_COVER:
                    self.cover_hp[(x, y)] = 120.0
                elif self.grid[y][x] == TILE_ALARM_CONSOLE:
                    self.alarm_console_hp[(x, y)] = ALARM_CONSOLE_HP
                elif self.grid[y][x] == TILE_LASER:
                    self.laser_hp[(x, y)] = LASER_HP
                    
        self.leaking_barrels = {}
        self.active_noises = []
        self.minimap_dirty = False
        self.exit_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == TILE_EXIT:
                    self.exit_tiles.append((x, y))

    # ── Generation ──────────────────────────────────────────────────────────
    def _generate(self, level):
        # Dispatch to level-specific generator
        W, H = self.width, self.height
        for attempt in range(25):
            # Reset grid and arrays to prevent duplicating spawns
            self.enemy_spawns = []
            self.item_spawns = []
            self.detail_grid = [[0]*W for _ in range(H)]
            for y in range(H):
                for x in range(W):
                    self.grid[y][x] = TILE_EMPTY
                    
            # Draw borders
            for x in range(W):
                self.grid[0][x] = TILE_WALL
                self.grid[H-1][x] = TILE_WALL
            for y in range(H):
                self.grid[y][0] = TILE_WALL
                self.grid[y][W-1] = TILE_WALL
                
            if   level == 0: self._gen_training(W, H)
            elif level == 1: self._gen_jungle(W, H)
            elif level == 2: self._gen_village(W, H)
            elif level == 3: self._gen_city(W, H)
            elif level == 4: self._gen_base(W, H)
            elif level == 5: self._gen_hell(W, H)
            else:            self._gen_boss_cave(W, H)
            
            if level == 0 or level == 6:
                break
                
            self._place_common(W, H, level)
            
            # Check connectivity between spawn and exit
            tx_exit = int(self.exit_px // TILE_SIZE)
            ty_exit = int(self.exit_py // TILE_SIZE)
            if self._check_path_exists(4, 4, tx_exit, ty_exit):
                break
        else:
            if level != 0:
                # Fallback path carving if it fails 25 times
                tx_exit = int(self.exit_px // TILE_SIZE)
                ty_exit = int(self.exit_py // TILE_SIZE)
                cx, cy = 4, 4
                while cx != tx_exit:
                    if 0 < cx < W-1 and 0 < cy < H-1:
                        self.grid[cy][cx] = TILE_EMPTY
                    cx += 1 if tx_exit > cx else -1
                while cy != ty_exit:
                    if 0 < cx < W-1 and 0 < cy < H-1:
                        self.grid[cy][cx] = TILE_EMPTY
                    cy += 1 if ty_exit > cy else -1
                self.grid[ty_exit][tx_exit] = TILE_EXIT

    def _place_common(self, W, H, level):
        if level == 6:
            return
        for dy in range(-5,6):
            for dx in range(-5,6):
                ny,nx=4+dy,4+dx
                if 0<ny<H-1 and 0<nx<W-1: self.grid[ny][nx]=TILE_EMPTY
        self.player_spawn=(4*TILE_SIZE+TILE_SIZE//2,4*TILE_SIZE+TILE_SIZE//2)
        exit_px,exit_py=(W-4)*TILE_SIZE+TILE_SIZE//2,(H-4)*TILE_SIZE+TILE_SIZE//2
        for _ in range(100):
            ex,ey=random.randint(W-12,W-3),random.randint(H-12,H-3)
            if self.grid[ey][ex]==TILE_EMPTY:
                # Dọn sạch 3x3 ô xung quanh lối thoát để đảm bảo sự thông thoáng hoàn hảo
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        ny, nx = ey + dy, ex + dx
                        if 0 < ny < H-1 and 0 < nx < W-1:
                            self.grid[ny][nx] = TILE_EMPTY
                self.grid[ey][ex]=TILE_EXIT
                exit_px,exit_py=ex*TILE_SIZE+TILE_SIZE//2,ey*TILE_SIZE+TILE_SIZE//2; break
        else:
            # Dọn sạch 3x3 ô xung quanh điểm dự phòng (H-4, W-4)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    ny, nx = H-4 + dy, W-4 + dx
                    if 0 < ny < H-1 and 0 < nx < W-1:
                        self.grid[ny][nx] = TILE_EMPTY
            self.grid[H-4][W-4]=TILE_EXIT
        self.exit_px = exit_px
        self.exit_py = exit_py
        
        # Màn 1: Xe tăng rải đều toàn bản đồ theo lưới grid (BFS tìm đường hiệu quả trên bản đồ phân tầng đều)
        if level == 1:
            # Xác định vùng trung tâm (boss zone) — dịn sạch để boss có chỗ đứng
            boss_cx, boss_cy = W // 2, H // 2
            for dy in range(-5, 6):
                for dx in range(-5, 6):
                    ny2, nx2 = boss_cy + dy, boss_cx + dx
                    if 0 < ny2 < H-1 and 0 < nx2 < W-1:
                        self.grid[ny2][nx2] = TILE_EMPTY
            
            # Phân chia bản đồ thành lưới (8x6 vùng), mỗi vùng spawn 1 xe tăng
            grid_cols = 8   # số cột vùng
            grid_rows = 6   # số hàng vùng
            zone_w = (W - 8) // grid_cols  # độ rộng mỗi vùng
            zone_h = (H - 8) // grid_rows  # chiều cao mỗi vùng
            
            for row in range(grid_rows):
                for col in range(grid_cols):
                    # Vùng x = [4 + col*zone_w, 4 + (col+1)*zone_w)
                    zx0 = 4 + col * zone_w
                    zx1 = 4 + (col + 1) * zone_w
                    zy0 = 4 + row * zone_h
                    zy1 = 4 + (row + 1) * zone_h
                    
                    # Bỏ qua vùng trung tâm (bò qua 2 vùng giữa) — đó là chỗ của boss
                    is_boss_zone = (
                        abs((zx0 + zx1) // 2 - boss_cx) < zone_w and
                        abs((zy0 + zy1) // 2 - boss_cy) < zone_h
                    )
                    if is_boss_zone:
                        continue
                    
                    # Bỏ qua vùng spawn của player (góc trên-trái)
                    if zx0 < 10 and zy0 < 10:
                        continue
                    
                    # Thử tỬm ô trống ngẫu nhiên trong vùng để spawn
                    spawned = False
                    for _ in range(25):
                        tx = random.randint(zx0, max(zx0, zx1 - 1))
                        ty = random.randint(zy0, max(zy0, zy1 - 1))
                        if 1 <= tx < W-1 and 1 <= ty < H-1:
                            if self.grid[ty][tx] == TILE_EMPTY:
                                # Đảm bảo không quá gần spawn của player
                                if math.hypot(tx - 4, ty - 4) > 8:
                                    self.enemy_spawns.append((
                                        tx * TILE_SIZE + TILE_SIZE // 2,
                                        ty * TILE_SIZE + TILE_SIZE // 2
                                    ))
                                    spawned = True
                                    break
                    
                    # Nếu không tìm được trong vùng, thử vị trí gần trung tâm vùng
                    if not spawned:
                        cx2 = (zx0 + zx1) // 2
                        cy2 = (zy0 + zy1) // 2
                        for r in range(1, 4):
                            for dy2 in range(-r, r+1):
                                for dx2 in range(-r, r+1):
                                    nx2, ny2 = cx2 + dx2, cy2 + dy2
                                    if 1 <= nx2 < W-1 and 1 <= ny2 < H-1:
                                        if self.grid[ny2][nx2] == TILE_EMPTY:
                                            if math.hypot(nx2 - 4, ny2 - 4) > 8:
                                                self.enemy_spawns.append((
                                                    nx2 * TILE_SIZE + TILE_SIZE // 2,
                                                    ny2 * TILE_SIZE + TILE_SIZE // 2
                                                ))
                                                spawned = True
                                                break
                                if spawned:
                                    break
                            if spawned:
                                break
        else:
            # Các màn khác: spawn random như cũ
            for _ in range(15+level*5):
                for _ in range(30):
                    ex,ey=random.randint(W//3,W-3),random.randint(2,H-3)
                    if self.grid[ey][ex]==TILE_EMPTY:
                        self.enemy_spawns.append((ex*TILE_SIZE+TILE_SIZE//2,ey*TILE_SIZE+TILE_SIZE//2)); break
            self.enemy_spawns.append((exit_px,exit_py))
        for _ in range(25+level*5):
            for _ in range(20):
                ix,iy=random.randint(2,W-3),random.randint(2,H-3)
                if self.grid[iy][ix]==TILE_EMPTY: self.item_spawns.append((ix,iy)); break
        for _ in range(5+level*2):
            for _ in range(20):
                bx,by=random.randint(5,W-5),random.randint(5,H-5)
                if self.grid[by][bx]==TILE_EMPTY: self.grid[by][bx]=TILE_BARREL; break
        for _ in range(5):
            cx,cy=random.randint(0,W-1),random.randint(0,H-1)
            for _ in range(180):
                if 0<=cx<W and 0<=cy<H and self.grid[cy][cx]==TILE_EMPTY: self.detail_grid[cy][cx]=1
                cx+=random.choice([-1,0,1]); cy+=random.choice([-1,0,1])

        if level >= 2:
            # Place Alarm Consoles
            consoles_placed = 0
            for _ in range(40):
                if consoles_placed >= (3 if level >= 4 else 2):
                    break
                cx = random.randint(5, W - 6)
                cy = random.randint(5, H - 6)
                if self.grid[cy][cx] == TILE_EMPTY and math.hypot(cx - 4, cy - 4) > 10:
                    has_wall_adj = False
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if self.grid[cy + dy][cx + dx] in (TILE_WALL, TILE_COVER):
                            has_wall_adj = True
                            break
                    if has_wall_adj:
                        self.grid[cy][cx] = TILE_ALARM_CONSOLE
                        consoles_placed += 1

            # Place Laser Emitters
            lasers_placed = 0
            for _ in range(80):
                if lasers_placed >= (4 if level >= 4 else 2):
                    break
                lx = random.randint(5, W - 6)
                ly = random.randint(5, H - 6)
                if self.grid[ly][lx] in (TILE_WALL, TILE_COVER):
                    for dx, dy in [(1, 0), (0, 1)]:
                        valid = True
                        length = random.randint(3, 5)
                        end_x = lx + dx * (length + 1)
                        end_y = ly + dy * (length + 1)
                        if 0 <= end_x < W and 0 <= end_y < H:
                            if self.grid[end_y][end_x] in (TILE_WALL, TILE_COVER):
                                for step in range(1, length + 1):
                                    px = lx + dx * step
                                    py = ly + dy * step
                                    if self.grid[py][px] != TILE_EMPTY:
                                        valid = False
                                        break
                                if valid:
                                    ex1_x, ex1_y = lx + dx, ly + dy
                                    ex2_x, ex2_y = lx + dx * length, ly + dy * length
                                    if self.grid[ex1_y][ex1_x] == TILE_EMPTY and self.grid[ex2_y][ex2_x] == TILE_EMPTY:
                                        self.grid[ex1_y][ex1_x] = TILE_LASER
                                        self.grid[ex2_y][ex2_x] = TILE_LASER
                                        lasers_placed += 1
                                        break

            # Place Security Cameras
            cameras_placed = 0
            for _ in range(50):
                if cameras_placed >= (4 if level >= 4 else 2):
                    break
                cx = random.randint(5, W - 6)
                cy = random.randint(5, H - 6)
                if self.grid[cy][cx] == TILE_EMPTY and math.hypot(cx - 4, cy - 4) > 12:
                    wall_dir = None
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if self.grid[cy + dy][cx + dx] == TILE_WALL:
                            wall_dir = (dx, dy)
                            break
                    if wall_dir:
                        px = cx * TILE_SIZE + TILE_SIZE // 2
                        py = cy * TILE_SIZE + TILE_SIZE // 2
                        base_angle = math.atan2(-wall_dir[1], -wall_dir[0])
                        self.camera_spawns.append((px, py, base_angle))
                        cameras_placed += 1

    # MAN 0: TRAINING RANGE (Shooting Range)
    def _gen_training(self, W, H):
        # Create a large open concrete area
        for y in range(1, H-1):
            for x in range(1, W-1):
                self.grid[y][x] = TILE_EMPTY
                self.detail_grid[y][x] = 0  # Standard floor
                
        # Player spawn at bottom center
        self.player_spawn = (W//2 * TILE_SIZE, (H - 6) * TILE_SIZE)
        
        # We don't need a real exit, but let's put one at the very top just in case
        self.grid[1][W//2] = TILE_EXIT
        self.exit_px = (W//2) * TILE_SIZE + TILE_SIZE//2
        self.exit_py = 1 * TILE_SIZE + TILE_SIZE//2
        
        # Create shooting lanes with low walls (covers)
        lane_x_coords = [W//2 - 10, W//2 - 5, W//2, W//2 + 5, W//2 + 10]
        for lx in lane_x_coords:
            for ly in range(4, H - 10):
                self._set_cover(lx, ly)
                
        # Spawn dummies at different distances
        self.enemy_spawns = []
        distances = [H - 15, H - 20, H - 25, H - 30]
        for dy in distances:
            for lx in [W//2 - 7, W//2 - 2, W//2 + 2, W//2 + 7]:
                if 1 < lx < W-1 and 1 < dy < H-1:
                    self.enemy_spawns.append((lx * TILE_SIZE + TILE_SIZE//2, dy * TILE_SIZE + TILE_SIZE//2))

    def _sw(self,x,y):
        if 1<=x<self.width-1 and 1<=y<self.height-1: self.grid[y][x]=TILE_WALL

    # MAN 1: RUNG RAM (Organic Jungle Canyons)
    def _gen_jungle(self, W, H):
        # Tạo rừng bằng các cụm cây tròn tự nhiên rải rác
        for _ in range(12):
            cx = random.randint(5, W - 6)
            cy = random.randint(5, H - 6)
            # Tránh xa điểm xuất phát (4, 4) và điểm kết thúc (W-4, H-4)
            if math.hypot(cx - 4, cy - 4) < 8 or math.hypot(cx - (W-4), cy - (H-4)) < 8:
                continue
            r = random.randint(2, 4)
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r*r:
                        nx, ny = cx + dx, cy + dy
                        if 1 < nx < W - 2 and 1 < ny < H - 2:
                            self.grid[ny][nx] = TILE_WALL

        # Tạo lối mòn đất đỏ ngoằn ngoèo nối từ spawn tới exit
        cx, cy = 4, 4
        tx_exit, ty_exit = W-4, H-4
        while (cx, cy) != (tx_exit, ty_exit):
            # Clear 4x4 xung quanh vị trí đường đi để tạo sự thông thoáng rộng rãi
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = cx + dx, cy + dy
                    if 0 < nx < W-1 and 0 < ny < H-1:
                        self.grid[ny][nx] = TILE_EMPTY
                        self.detail_grid[ny][nx] = 1 # Vẽ vệt đất đỏ
            
            # Di chuyển về phía exit
            if cx != tx_exit and random.random() < 0.6:
                cx += 1 if tx_exit > cx else -1
            elif cy != ty_exit:
                cy += 1 if ty_exit > cy else -1

        # Rải các bụi rậm và hầm ngầm quân sự ẩn giấu (tunnels)
        for _ in range(6):
            bx = random.randint(6, W-12)
            by = random.randint(6, H-12)
            if self.grid[by][bx] == TILE_EMPTY and math.hypot(bx-4, by-4) > 8:
                for dx in range(3):
                    self._set_cover(bx+dx, by)
                    self._set_cover(bx+dx, by+2)
                self._set_cover(bx, by+1)
                self._set_cover(bx+2, by+1)

        # Cổng đường hầm dịch chuyển tức thời
        for _ in range(2):
            t1x, t1y = random.randint(4, W//2 - 3), random.randint(4, H - 5)
            t2x, t2y = random.randint(W//2 + 3, W - 4), random.randint(4, H - 5)
            if self.grid[t1y][t1x] == TILE_EMPTY and self.grid[t2y][t2x] == TILE_EMPTY:
                self.grid[t1y][t1x] = TILE_TUNNEL
                self.grid[t2y][t2x] = TILE_TUNNEL

    # MAN 2: LANG QUE (Spacious Rural Village)
    def _gen_village(self, W, H):
        # Đặt các căn nhà gỗ của làng cách xa nhau
        house_centers = []
        for _ in range(30):
            if len(house_centers) >= 8:
                break
            hx = random.randint(5, W - 15)
            hy = random.randint(5, H - 15)
            # Tránh spawn & exit
            if math.hypot(hx - 4, hy - 4) < 10 or math.hypot(hx - (W-4), hy - (H-4)) < 10:
                continue
            # Tránh nhà khác chồng lên nhau quá gần
            too_close = False
            for cx, cy in house_centers:
                if math.hypot(hx - cx, hy - cy) < 14:
                    too_close = True
                    break
            if too_close:
                continue
                
            house_centers.append((hx, hy))
            bw = random.randint(5, 7)
            bh = random.randint(4, 6)
            # Xây dựng tường nhà
            for dx in range(bw):
                self._sw(hx + dx, hy)
                self._sw(hx + dx, hy + bh)
            for dy in range(bh):
                self._sw(hx, hy + dy)
                self._sw(hx + bw, hy + dy)
            # Tạo cửa ra vào ở 2 phía
            self.grid[hy][hx + bw // 2] = TILE_EMPTY
            self.grid[hy + bh][hx + bw // 2] = TILE_EMPTY
            
            # Sàn nhà lót gạch gỗ (detail 1)
            for dy in range(1, bh):
                for dx in range(1, bw):
                    self.detail_grid[hy + dy][hx + dx] = 1

        # Nối các căn nhà bằng các con đường đất rộng 5 ô thoáng đãng
        for hx, hy in house_centers:
            # Đường nối ra trục chính ở giữa
            for tx in range(min(hx, W//2), max(hx, W//2) + 1):
                for w in range(-2, 3):
                    if 0 < hy+w < H-1:
                        self.grid[hy+w][tx] = TILE_EMPTY
                        self.detail_grid[hy+w][tx] = 1
            for ty in range(min(hy, H//2), max(hy, H//2) + 1):
                for w in range(-2, 3):
                    if 0 < hx+w < W-1:
                        self.grid[ty][hx+w] = TILE_EMPTY
                        self.detail_grid[ty][hx+w] = 1

        # Vẽ trục đường làng chính siêu rộng chạy dọc và ngang bản đồ
        for rx in range(1, W-1):
            for w in range(-2, 3):
                if 0 < H//2+w < H-1:
                    self.grid[H//2+w][rx] = TILE_EMPTY
                    self.detail_grid[H//2+w][rx] = 1
        for ry in range(1, H-1):
            for w in range(-2, 3):
                if 0 < W//2+w < W-1:
                    self.grid[ry][W//2+w] = TILE_EMPTY
                    self.detail_grid[ry][W//2+w] = 1

    # MAN 3: LANG QUE CHIEN TRANH (Rural Countryside Village)
    def _gen_city(self, W, H):
        """
        Màn 3: Làng Quê Chiến Tranh — Nông thôn với nhà gỗ, lều, hàng rào, ruộng lúa.
        Thiết kế đảm bảo hành lang ≥ 4 tile giữa các công trình để xe tăng (A*)
        không bao giờ bị kẹt trong khe hẹp.
        """
        # ── Bước 1: Vẽ nền cỏ xanh cho toàn bộ bản đồ (detail_grid = 3 = cỏ)
        for y in range(1, H-1):
            for x in range(1, W-1):
                self.detail_grid[y][x] = 3  # cỏ xanh

        # ── Bước 2: Đường làng chính — 2 trục ngang + 1 trục dọc, rộng 6 ô
        # Trục ngang trên (y ≈ H//3)
        road_y1 = H // 3
        # Trục ngang dưới (y ≈ H*2//3)
        road_y2 = H * 2 // 3
        # Trục dọc giữa (x ≈ W//2)
        road_x  = W // 2

        for rx in range(1, W-1):
            for w in range(-3, 4):   # 7 ô rộng
                for ry in [road_y1, road_y2]:
                    ny = ry + w
                    if 0 < ny < H-1:
                        self.grid[ny][rx] = TILE_EMPTY
                        self.detail_grid[ny][rx] = 1  # đường đất nâu

        for ry in range(1, H-1):
            for w in range(-3, 4):   # 7 ô rộng
                nx = road_x + w
                if 0 < nx < W-1:
                    self.grid[ry][nx] = TILE_EMPTY
                    self.detail_grid[ry][nx] = 1  # đường đất nâu

        # Đường chéo nối spawn → exit (đảm bảo luôn có đường thoát)
        for rx in range(1, W-1):
            diag_y = int(H * rx / W)
            for w in range(-2, 3):
                ny = diag_y + w
                if 0 < ny < H-1:
                    self.grid[ny][rx] = TILE_EMPTY
                    self.detail_grid[ny][rx] = 1

        # ── Bước 3: Đặt nhà gỗ nông thôn (5–7 nhà)
        # Mỗi nhà cách nhau ≥ 12 tile, cách đường ≥ 2 tile, cách spawn/exit ≥ 10 tile
        house_centers = []
        house_attempts = 0
        while len(house_centers) < 7 and house_attempts < 200:
            house_attempts += 1
            hx = random.randint(6, W - 16)
            hy = random.randint(6, H - 14)

            # Tránh spawn và exit
            if math.hypot(hx - 4, hy - 4) < 12:
                continue
            if math.hypot(hx - (W-4), hy - (H-4)) < 12:
                continue

            # Tránh đường chính (buffer 4 tile)
            near_road = False
            for w in range(-4, 5):
                if abs(hy - road_y1) < 5 or abs(hy - road_y2) < 5:
                    near_road = True; break
                if abs(hx - road_x) < 5:
                    near_road = True; break
            if near_road:
                continue

            # Tránh nhà khác (khoảng cách ≥ 14 tile)
            too_close = any(math.hypot(hx - cx, hy - cy) < 14 for cx, cy, _bw, _bh in house_centers)
            if too_close:
                continue

            # Kích thước nhà: rộng 5–8, cao 4–6 tile
            bw = random.randint(5, 8)
            bh = random.randint(4, 6)

            # Kiểm tra vùng đặt nhà không chồng lên đường
            overlap_road = False
            for dy in range(-1, bh + 2):
                for dx in range(-1, bw + 2):
                    nx2, ny2 = hx + dx, hy + dy
                    if 0 <= nx2 < W and 0 <= ny2 < H:
                        if self.detail_grid[ny2][nx2] == 1:
                            overlap_road = True; break
                if overlap_road: break
            if overlap_road:
                continue

            house_centers.append((hx, hy, bw, bh))

            # Xây tường nhà gỗ
            for dx in range(bw + 1):
                self._sw(hx + dx, hy)
                self._sw(hx + dx, hy + bh)
            for dy in range(1, bh):
                self._sw(hx, hy + dy)
                self._sw(hx + bw, hy + dy)

            # Cửa trước (phía dưới) rộng 2 ô
            door_x = hx + bw // 2
            if 0 < door_x < W-1:
                self.grid[hy + bh][door_x] = TILE_EMPTY
            if 0 < door_x + 1 < W-1:
                self.grid[hy + bh][door_x + 1] = TILE_EMPTY

            # Cửa hông (phía phải) rộng 2 ô
            door_y = hy + bh // 2
            if 0 < door_y < H-1:
                self.grid[door_y][hx + bw] = TILE_EMPTY
            if 0 < door_y + 1 < H-1:
                self.grid[door_y + 1][hx + bw] = TILE_EMPTY

            # Sàn nhà (detail = 1 = gỗ)
            for dy in range(1, bh):
                for dx in range(1, bw):
                    if 0 < hx+dx < W-1 and 0 < hy+dy < H-1:
                        self.detail_grid[hy + dy][hx + dx] = 1

            # Đồ đạc bên trong: 1–2 cover (bàn, thùng)
            for _ in range(random.randint(1, 2)):
                fx = hx + random.randint(1, max(1, bw - 1))
                fy = hy + random.randint(1, max(1, bh - 1))
                if self.grid[fy][fx] == TILE_EMPTY:
                    self._set_cover(fx, fy)

        # ── Bước 4: Đặt lều vải (tent) — nhỏ hơn nhà, không có sàn
        # Lều là hình chữ L hoặc hình vuông nhỏ 3×3
        tent_centers = []
        for _ in range(200):
            if len(tent_centers) >= 5:
                break
            tx2 = random.randint(5, W - 10)
            ty2 = random.randint(5, H - 10)

            if math.hypot(tx2 - 4, ty2 - 4) < 10:
                continue
            if math.hypot(tx2 - (W-4), ty2 - (H-4)) < 10:
                continue

            # Tránh đường và nhà
            near_obstacle = False
            for w in range(-3, 7):
                if abs(ty2 - road_y1) < 4 or abs(ty2 - road_y2) < 4:
                    near_obstacle = True; break
                if abs(tx2 - road_x) < 4:
                    near_obstacle = True; break
            if near_obstacle:
                continue

            too_close = any(math.hypot(tx2 - cx, ty2 - cy) < 10 for cx, cy, _, _ in house_centers)
            too_close = too_close or any(math.hypot(tx2 - cx, ty2 - cy) < 8 for cx, cy in tent_centers)
            if too_close:
                continue

            tent_centers.append((tx2, ty2))

            # Lều hình chữ U (3 cạnh, mở 1 cạnh)
            tw, th = 3, 3
            for dx in range(tw + 1):
                self._sw(tx2 + dx, ty2)        # cạnh trên
            for dy in range(1, th + 1):
                self._sw(tx2, ty2 + dy)         # cạnh trái
                self._sw(tx2 + tw, ty2 + dy)    # cạnh phải
            # Cạnh dưới mở (không vẽ) → lối vào lều

        # ── Bước 5: Hàng rào gỗ (fence) dọc theo ruộng
        # Hàng rào là dải COVER dài 4–8 ô, nằm ngang hoặc dọc
        for _ in range(300):
            if _ > 299:
                break
            fx = random.randint(5, W - 10)
            fy = random.randint(5, H - 10)

            # Tránh đường, spawn, exit
            if self.detail_grid[fy][fx] == 1:
                continue
            if math.hypot(fx - 4, fy - 4) < 8:
                continue
            if math.hypot(fx - (W-4), fy - (H-4)) < 8:
                continue
            if self.grid[fy][fx] != TILE_EMPTY:
                continue

            fence_len = random.randint(4, 8)
            horizontal = random.random() < 0.5

            # Kiểm tra toàn bộ hàng rào không chồng đường
            valid = True
            for i in range(fence_len):
                nx2 = fx + (i if horizontal else 0)
                ny2 = fy + (0 if horizontal else i)
                if not (0 < nx2 < W-1 and 0 < ny2 < H-1):
                    valid = False; break
                if self.detail_grid[ny2][nx2] == 1:
                    valid = False; break
                if self.grid[ny2][nx2] != TILE_EMPTY:
                    valid = False; break
            if not valid:
                continue

            for i in range(fence_len):
                nx2 = fx + (i if horizontal else 0)
                ny2 = fy + (0 if horizontal else i)
                self._set_cover(nx2, ny2)

        # ── Bước 6: Ruộng lúa — ô vuông cỏ xanh đậm (detail = 3) xen kẽ
        # Đã được set ở bước 1, không cần thêm

        # ── Bước 7: Giếng làng ở trung tâm (cover tròn 2×2)
        well_x, well_y = W // 2 + random.randint(-3, 3), H // 2 + random.randint(-3, 3)
        # Dọn sạch vùng giếng
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                nx2, ny2 = well_x + dx, well_y + dy
                if 0 < nx2 < W-1 and 0 < ny2 < H-1:
                    self.grid[ny2][nx2] = TILE_EMPTY
                    self.detail_grid[ny2][nx2] = 1  # sân đất quanh giếng
        # Đặt giếng (cover)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if abs(dx) + abs(dy) <= 1:  # hình thập
                    self._set_cover(well_x + dx, well_y + dy)

        # ── Bước 8: Post-processing — Mở rộng khe hẹp ≤ 2 tile
        # Đảm bảo xe tăng (radius=12px ≈ 0.75 tile) không bị kẹt
        for _pass in range(8):
            for y in range(2, H-2):
                for x in range(2, W-2):
                    if self.grid[y][x] != TILE_EMPTY:
                        continue
                    # Kẹt dọc: tường trên VÀ dưới trong vòng 2 ô
                    top1 = self.grid[y-1][x] in (TILE_WALL, TILE_COVER)
                    top2 = self.grid[y-2][x] in (TILE_WALL, TILE_COVER)
                    bot1 = self.grid[y+1][x] in (TILE_WALL, TILE_COVER)
                    bot2 = self.grid[y+2][x] in (TILE_WALL, TILE_COVER)
                    # Hành lang chỉ 1 ô: phá tường
                    if top1 and bot1:
                        if self.grid[y+1][x] == TILE_WALL:
                            self.grid[y+1][x] = TILE_EMPTY
                        else:
                            self.grid[y-1][x] = TILE_EMPTY
                    # Hành lang chỉ 2 ô: phá thêm 1 tường nữa
                    elif (top1 and bot2 and self.grid[y+1][x] == TILE_EMPTY) or \
                         (top2 and bot1 and self.grid[y-1][x] == TILE_EMPTY):
                        if bot1 and self.grid[y+1][x] == TILE_WALL:
                            self.grid[y+1][x] = TILE_EMPTY
                        elif top1 and self.grid[y-1][x] == TILE_WALL:
                            self.grid[y-1][x] = TILE_EMPTY
                    # Kẹt ngang: tường trái VÀ phải
                    lft1 = self.grid[y][x-1] in (TILE_WALL, TILE_COVER)
                    lft2 = self.grid[y][x-2] in (TILE_WALL, TILE_COVER)
                    rgt1 = self.grid[y][x+1] in (TILE_WALL, TILE_COVER)
                    rgt2 = self.grid[y][x+2] in (TILE_WALL, TILE_COVER)
                    if lft1 and rgt1:
                        if self.grid[y][x+1] == TILE_WALL:
                            self.grid[y][x+1] = TILE_EMPTY
                        else:
                            self.grid[y][x-1] = TILE_EMPTY
                    elif (lft1 and rgt2 and self.grid[y][x+1] == TILE_EMPTY) or \
                         (lft2 and rgt1 and self.grid[y][x-1] == TILE_EMPTY):
                        if rgt1 and self.grid[y][x+1] == TILE_WALL:
                            self.grid[y][x+1] = TILE_EMPTY
                        elif lft1 and self.grid[y][x-1] == TILE_WALL:
                            self.grid[y][x-1] = TILE_EMPTY

    # MAN 4: CAN CU QUAN SU (Industrial Tech Base)
    def _gen_base(self, W, H):
        # 4 Phòng điều khiển/lò phản ứng cực lớn ở các góc
        rooms = [
            {"cx": W//4,     "cy": H//4,     "name": "REACTOR"},
            {"cx": W*3//4,   "cy": H//4,     "name": "HANGAR"},
            {"cx": W//4,     "cy": H*3//4,   "name": "CONTROL"},
            {"cx": W*3//4,   "cy": H*3//4,   "name": "ARMORY"}
        ]
        
        for rm in rooms:
            rx, ry = rm["cx"] - 6, rm["cy"] - 5
            rw, rh = 12, 10
            # Xây vách thép kiên cố
            for dx in range(rw):
                self._sw(rx+dx, ry)
                self._sw(rx+dx, ry+rh)
            for dy in range(rh):
                self._sw(rx, ry+dy)
                self._sw(rx+rw, ry+dy)
            # Mỗi phòng có 3 lối ra vào rộng 3 ô để xe tăng dễ dàng truy đuổi
            for dx in range(rw//2 - 1, rw//2 + 2):
                self.grid[ry][rx+dx] = TILE_EMPTY
                self.grid[ry+rh][rx+dx] = TILE_EMPTY
            for dy in range(rh//2 - 1, rh//2 + 2):
                self.grid[ry+dy][rx] = TILE_EMPTY
                self.grid[ry+dy][rx+rw] = TILE_EMPTY

            # Đặt các lò phản ứng năng lượng / hộp sắt bên trong làm chướng ngại vật
            self.grid[rm["cy"]][rm["cx"]] = TILE_WALL
            self.grid[rm["cy"]][rm["cx"]-1] = TILE_COVER
            self.grid[rm["cy"]][rm["cx"]+1] = TILE_COVER

        # Hành lang nối liên thông rộng 5 ô tạo cấu trúc mạch lạc
        for rx in range(1, W-1):
            for w in range(-2, 3):
                if 0 < H//2+w < H-1:
                    self.grid[H//2+w][rx] = TILE_EMPTY
                    self.detail_grid[H//2+w][rx] = 1
        for ry in range(1, H-1):
            for w in range(-2, 3):
                if 0 < W//2+w < W-1:
                    self.grid[ry][W//2+w] = TILE_EMPTY
                    self.detail_grid[ry][W//2+w] = 1

        # Rải một số hộp sắt bảo vệ chiến thuật trên các lối đi
        for _ in range(25):
            rx = random.randint(5, W-6)
            ry = random.randint(5, H-6)
            if self.grid[ry][rx] == TILE_EMPTY and math.hypot(rx-4, ry-4) > 8:
                self.grid[ry][rx] = TILE_COVER

    # MAN 5: DIA NGUC (Doom Battleship Deck)
    def _gen_hell(self, W, H):
        # 1. Vẽ nền boong tàu thép
        for y in range(1, H-1):
            for x in range(1, W-1):
                self.grid[y][x] = TILE_EMPTY
                self.detail_grid[y][x] = 0  # 0: Sàn kim loại tối

        # 2. Đảm bảo khu vực Spawn (4,4) và Exit (W-4, H-4) hoàn toàn trống trải và an toàn
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                # Spawn area
                if 0 < 4+dy < H-1 and 0 < 4+dx < W-1:
                    self.grid[4+dy][4+dx] = TILE_EMPTY
                    self.detail_grid[4+dy][4+dx] = 2  # Sàn đệm Landing Pad
                # Exit area
                if 0 < H-4+dy < H-1 and 0 < W-4+dx < W-1:
                    self.grid[H-4+dy][W-4+dx] = TILE_EMPTY
                    self.detail_grid[H-4+dy][W-4+dx] = 2 # Sàn đệm Extraction Pad

        # 3. Tạo các bức tường phòng thủ chia cắt bản đồ thành các khu vực chiến thuật
        # Bức tường chữ thập ngăn cách trung tâm nhưng có các lối mở lớn
        for x in range(12, W-12):
            if abs(x - W//2) > 10:
                self._sw(x, H//3)
                self._sw(x, H*2//3)
        for y in range(10, H-10):
            if abs(y - H//2) > 8:
                self._sw(W//4, y)
                self._sw(W*3//4, y)

        # 4. Tạo các dòng sông plasma dung nham chảy ngang qua (detail 1) làm rào cản
        # Người chơi có thể bắn xuyên qua nhưng không thể đi qua trực tiếp (TILE_COVER)
        for ly in [H//2 - 12, H//2 + 12]:
            for lx in range(10, W-10):
                if abs(lx - W//2) < 8 or lx == W//4 or lx == W*3//4:
                    continue
                self.detail_grid[ly][lx] = 1 # Plasma nóng đỏ
                self.grid[ly][lx] = TILE_COVER

        # 5. 4 Phòng bảo an ở 4 góc chiến thuật
        room_centers = [
            (W//6, H//3), (W*5//6, H//3),
            (W//6, H*2//3), (W*5//6, H*2//3)
        ]
        for rx, ry in room_centers:
            # Tạo các phòng bảo vệ nhỏ 6x6
            rw, rh = 6, 6
            start_x, start_y = rx - rw//2, ry - rh//2
            for dx in range(rw):
                self._sw(start_x+dx, start_y)
                self._sw(start_x+dx, start_y+rh)
            for dy in range(rh):
                self._sw(start_x, start_y+dy)
                self._sw(start_x+rw, start_y+dy)
            # Mở cửa phòng
            self.grid[start_y][start_x + rw//2] = TILE_EMPTY
            self.grid[start_y + rh][start_x + rw//2] = TILE_EMPTY
            # Sàn phòng bảo an
            for dy in range(1, rh):
                for dx in range(1, rw):
                    self.detail_grid[start_y+dy][start_x+dx] = 2

        # 6. Cổng Dịch Chuyển Tức Thời (Tunnels) kết nối các phòng bảo an chéo nhau
        self.grid[H//3][W//6] = TILE_TUNNEL
        self.grid[H*2//3][W*5//6] = TILE_TUNNEL
        self.grid[H//3][W*5//6] = TILE_TUNNEL
        self.grid[H*2//3][W//6] = TILE_TUNNEL

        # 7. Dọn sạch và tạo Đấu Trường Hạt Nhân ở Trung Tâm (rộng 26x20)
        for dy in range(-10, 11):
            for dx in range(-15, 16):
                nx, ny = W//2 + dx, H//2 + dy
                if 0 < nx < W-1 and 0 < ny < H-1:
                    self.grid[ny][nx] = TILE_EMPTY
                    self.detail_grid[ny][nx] = 0

        # 8. Đặt 4 cột từ trường bảo vệ (Shield Generators) khổng lồ ở trung tâm làm cover
        shield_cols = [
            (W//2 - 8, H//2 - 5), (W//2 + 8, H//2 - 5),
            (W//2 - 8, H//2 + 5), (W//2 + 8, H//2 + 5)
        ]
        for cx, cy in shield_cols:
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    self.grid[cy+dy][cx+dx] = TILE_WALL

        # 9. Rải thêm các hộp tủ console cảnh báo và các thùng xăng dễ nổ quanh phòng
        for cx, cy in [(W//2, H//2 - 9), (W//2, H//2 + 9), (W//4 - 5, H//2), (W*3//4 + 5, H//2)]:
            if self.grid[cy][cx] == TILE_EMPTY:
                self.grid[cy][cx] = TILE_ALARM_CONSOLE

    def _gen_boss_cave(self, W, H):
        # 1. Vẽ nền boong tàu thép / hang đá
        for y in range(1, H-1):
            for x in range(1, W-1):
                self.grid[y][x] = TILE_EMPTY
                self.detail_grid[y][x] = 0  # 0: Sàn kim loại tối
                
        # 2. Đặt spawn cho người chơi ở phía Nam bản đồ
        self.player_spawn = (W // 2 * TILE_SIZE + TILE_SIZE // 2, (H - 6) * TILE_SIZE + TILE_SIZE // 2)
        
        # 3. Đặt spawn cho Boss ở phía Bắc bản đồ
        self.enemy_spawns = [(W // 2 * TILE_SIZE + TILE_SIZE // 2, 6 * TILE_SIZE + TILE_SIZE // 2)]
        
        # 4. Đặt vật phẩm cứu trợ ở các góc và rìa
        self.item_spawns = [
            (3, 3), (W - 4, 3),
            (3, H - 4), (W - 4, H - 4),
            (W // 2 - 8, H // 2), (W // 2 + 8, H // 2)
        ]
        
        # 5. Tạo chướng ngại vật (Cover) ở trung tâm làm vật chắn đạn chiến thuật
        cover_positions = [
            (W // 2 - 5, H // 2 - 4),
            (W // 2 + 3, H // 2 - 4),
            (W // 2 - 5, H // 2 + 2),
            (W // 2 + 3, H // 2 + 2)
        ]
        for cx, cy in cover_positions:
            for dy in range(2):
                for dx in range(2):
                    self.grid[cy + dy][cx + dx] = TILE_COVER
                    
        # 6. Đặt thùng xăng nổ chiến thuật
        barrel_positions = [
            (W // 2 - 8, H // 2 - 6),
            (W // 2 + 7, H // 2 - 6),
            (W // 2 - 8, H // 2 + 4),
            (W // 2 + 7, H // 2 + 4),
            (W // 2, H // 2)
        ]
        for bx, by in barrel_positions:
            self.grid[by][bx] = TILE_BARREL
            
        # Không có lối thoát (TILE_EXIT), exit_px/py đặt về 0
        self.exit_px = 0
        self.exit_py = 0

    def _set_cover(self, x, y):
        if 1 <= x < self.width-1 and 1 <= y < self.height-1:
            self.grid[y][x] = TILE_COVER

    def _in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    # ── Surface bake ────────────────────────────────────────────────────────
    def _draw_tile_floor(self, surface, tx, ty):
        ts = TILE_SIZE
        rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
        lv = min(max(self.level, 1), 5)
        
        if lv == 1: # Jungle
            pygame.draw.rect(surface, (42, 54, 38), rect)
            det = self.detail_grid[ty][tx]
            if det == 1: # path
                pygame.draw.rect(surface, (55, 45, 25), rect)
                pygame.draw.line(surface, (45, 35, 20), (rect.x, rect.y + 10), (rect.right, rect.y + 10), 1)
                pygame.draw.line(surface, (45, 35, 20), (rect.x, rect.y + 22), (rect.right, rect.y + 22), 1)
            else:
                state = random.getstate()
                random.seed(tx * 997 + ty * 31)
                if random.random() < 0.3:
                    for _ in range(random.randint(2, 4)):
                        gx = rect.x + random.randint(4, ts - 6)
                        gy = rect.y + random.randint(6, ts - 4)
                        pygame.draw.line(surface, (30, 80, 25), (gx, gy), (gx - 1, gy - random.randint(3, 5)), 1)
                        pygame.draw.line(surface, (55, 95, 30), (gx, gy), (gx + 1, gy - random.randint(2, 4)), 1)
                if random.random() < 0.08:
                    wx = rect.x + random.randint(6, ts - 6)
                    wy = rect.y + random.randint(6, ts - 6)
                    pygame.draw.circle(surface, (30, 80, 20), (wx, wy + 2), 2)
                    color = random.choice([(255, 210, 0), (255, 255, 255), (255, 100, 100)])
                    pygame.draw.circle(surface, color, (wx, wy), 2)
                random.setstate(state)
                
        elif lv == 2: # Village
            det = self.detail_grid[ty][tx]
            if det == 1:
                pygame.draw.rect(surface, (100, 75, 50), rect)
                pygame.draw.line(surface, (60, 45, 30), (rect.x, rect.y), (rect.right, rect.y), 1)
                pygame.draw.line(surface, (60, 45, 30), (rect.x, rect.bottom - 1), (rect.right, rect.bottom - 1), 1)
                for px in range(rect.x + 8, rect.right, 8):
                    pygame.draw.line(surface, (60, 45, 30), (px, rect.y), (px, rect.bottom), 1)
            else:
                pygame.draw.rect(surface, (28, 34, 42), rect)
                if det == 2: # crater
                    pygame.draw.rect(surface, (15, 10, 5), rect)
                    pygame.draw.circle(surface, (10, 5, 0), rect.center, ts//2 - 2)
                    pygame.draw.circle(surface, (40, 30, 20), rect.center, ts//2, 1)
                elif det == 3: # grass
                    bx = rect.centerx
                    by = rect.centery
                    pygame.draw.rect(surface, (30, 70, 30), (bx-8, by-8, 16, 16), border_radius=3)
                    pygame.draw.rect(surface, (50, 90, 40), (bx-4, by-4, 8, 8), border_radius=2)
                else:
                    pygame.draw.rect(surface, (35, 45, 30), rect)
                    state = random.getstate()
                    random.seed(tx * 73 + ty * 97)
                    if random.random() < 0.2:
                        for _ in range(random.randint(1, 2)):
                            gx = rect.x + random.randint(4, ts - 6)
                            gy = rect.y + random.randint(4, ts - 6)
                            pygame.draw.circle(surface, (20, 50, 15), (gx, gy), 1)
                    random.setstate(state)
                    
        elif lv == 3: # Rural Countryside Village
            det = self.detail_grid[ty][tx]
            if det == 1:  # đường đất nâu / sàn gỗ nhà
                pygame.draw.rect(surface, (110, 80, 50), rect)
                # Vân gỗ / vết bánh xe
                state = random.getstate()
                random.seed(tx * 13 + ty * 101)
                for i in range(rect.y + 4, rect.bottom, 7):
                    pygame.draw.line(surface, (90, 62, 38), (rect.x, i), (rect.right, i), 1)
                if random.random() < 0.3:
                    pygame.draw.line(surface, (80, 55, 30), (rect.x + random.randint(2, 8), rect.y),
                                     (rect.x + random.randint(2, 8), rect.bottom), 1)
                random.setstate(state)
            elif det == 3:  # cỏ xanh nông thôn
                state = random.getstate()
                random.seed(tx * 59 + ty * 83)
                # Màu cỏ ngẫu nhiên nhẹ
                g_shade = random.randint(55, 85)
                pygame.draw.rect(surface, (30, g_shade, 25), rect)
                # Ngọn cỏ nhỏ
                if random.random() < 0.35:
                    for _ in range(random.randint(2, 4)):
                        gx2 = rect.x + random.randint(3, ts - 5)
                        gy2 = rect.y + random.randint(6, ts - 4)
                        pygame.draw.line(surface, (20, 100, 20), (gx2, gy2),
                                         (gx2 + random.randint(-2, 2), gy2 - random.randint(3, 6)), 1)
                # Hoa dại nhỏ
                if random.random() < 0.06:
                    fx2 = rect.x + random.randint(5, ts - 7)
                    fy2 = rect.y + random.randint(5, ts - 7)
                    pygame.draw.circle(surface, (255, 220, 60), (fx2, fy2), 2)
                    pygame.draw.circle(surface, (255, 255, 255), (fx2, fy2), 1)
                random.setstate(state)
            else:
                # Đất trống / sân
                pygame.draw.rect(surface, (75, 60, 40), rect)
                state = random.getstate()
                random.seed(tx * 233 + ty * 41)
                if random.random() < 0.12:
                    pygame.draw.circle(surface, (60, 48, 30), rect.center, random.randint(3, 6))
                random.setstate(state)
                
        elif lv == 4: # Tech Base
            pygame.draw.rect(surface, (38, 48, 30), rect)
            pygame.draw.rect(surface, (28, 38, 22), rect, 1)
            det = self.detail_grid[ty][tx]
            if det == 1:
                pygame.draw.rect(surface, (50, 60, 40), rect)
                pygame.draw.rect(surface, (35, 45, 28), rect, 1)
            state = random.getstate()
            random.seed(tx * 123 + ty * 47)
            if random.random() < 0.1:
                if random.random() < 0.5:
                    pygame.draw.line(surface, (0, 150, 255), (rect.x, rect.centery), (rect.right, rect.centery), 1)
                else:
                    pygame.draw.line(surface, (0, 150, 255), (rect.centerx, rect.y), (rect.centerx, rect.bottom), 1)
            elif random.random() < 0.05:
                pygame.draw.rect(surface, (15, 20, 10), (rect.x + 6, rect.y + 6, ts - 12, ts - 12))
                for i in range(rect.y + 8, rect.bottom - 6, 3):
                    pygame.draw.line(surface, (50, 50, 50), (rect.x + 8, i), (rect.right - 8, i), 1)
            random.setstate(state)
            
        elif lv == 5: # Hell
            det = self.detail_grid[ty][tx]
            if det == 1: # Dung nham
                pygame.draw.rect(surface, (180, 30, 0), rect)
                state = random.getstate()
                random.seed(tx * 31 + ty * 109)
                for _ in range(2):
                    ly = rect.y + random.randint(2, ts-6)
                    pygame.draw.rect(surface, (255, 90, 0), (rect.x, ly, ts, random.randint(2, 4)))
                    if random.random() < 0.3:
                        pygame.draw.rect(surface, (255, 200, 0), (rect.x + random.randint(0, 10), ly + 1, random.randint(5, 12), 1))
                random.setstate(state)
            elif det == 2: # Sàn phòng thủ (Bunker)
                pygame.draw.rect(surface, (26, 28, 32), rect)
                pygame.draw.rect(surface, (45, 50, 60), rect, 1)
                pygame.draw.line(surface, (15, 16, 18), (rect.x, rect.y), (rect.right, rect.bottom), 1)
                pygame.draw.line(surface, (15, 16, 18), (rect.right, rect.y), (rect.x, rect.bottom), 1)
            else: # Boong tàu thường
                pygame.draw.rect(surface, (35, 30, 28), rect)
                pygame.draw.rect(surface, (25, 20, 18), rect, 1)
                state = random.getstate()
                random.seed(tx * 233 + ty * 41)
                if random.random() < 0.1:
                    p1 = (rect.x + random.randint(2, 12), rect.y + random.randint(2, 12))
                    p2 = (rect.right - random.randint(2, 12), rect.bottom - random.randint(2, 12))
                    pygame.draw.line(surface, (220, 50, 0), p1, p2, 2)
                    pygame.draw.line(surface, (255, 150, 0), p1, p2, 1)
                elif random.random() < 0.08:
                    pygame.draw.circle(surface, (18, 14, 12), rect.center, random.randint(3, 5))
                random.setstate(state)

    def _draw_tile_object(self, surface, tx, ty):
        ts = TILE_SIZE
        t = self.grid[ty][tx]
        if t == TILE_EMPTY:
            lv = min(max(self.level, 1), 5)
            if lv in [1, 2]:
                state = random.getstate()
                random.seed(tx * 883 + ty * 19)
                if random.random() < 0.05:
                    rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
                    if random.random() < 0.2 and hasattr(self, '_big_tree_image') and self._big_tree_image:
                        rx = rect.centerx + random.randint(-8, 8)
                        ry = rect.centery + random.randint(-8, 8)
                        pygame.draw.circle(surface, (15, 25, 10), (rx + 4, ry + 8), ts//2)
                        draw_rect = self._big_tree_image.get_rect(center=(rx, ry))
                        surface.blit(self._big_tree_image, draw_rect.topleft)
                    elif hasattr(self, '_small_tree_image') and self._small_tree_image:
                        rx = rect.centerx + random.randint(-6, 6)
                        ry = rect.centery + random.randint(-6, 6)
                        pygame.draw.circle(surface, (15, 25, 10), (rx + 3, ry + 6), ts//3)
                        draw_rect = self._small_tree_image.get_rect(center=(rx, ry))
                        surface.blit(self._small_tree_image, draw_rect.topleft)
                random.setstate(state)
            return

        rect = pygame.Rect(tx * ts, ty * ts, ts, ts)
        lv = min(max(self.level, 1), 5)
        
        h_ext = 14
        if t == TILE_COVER:
            h_ext = 10
        elif t == TILE_BARREL:
            h_ext = 12
        elif t == TILE_ALARM_CONSOLE:
            h_ext = 10
        elif t == TILE_LASER:
            h_ext = 12
        elif t == TILE_TUNNEL:
            h_ext = 14
        elif t == TILE_EXIT:
            h_ext = 6

        top_rect = pygame.Rect(rect.x, rect.y - h_ext, ts, ts)
        front_rect = pygame.Rect(rect.x, rect.y - h_ext + ts, ts, h_ext)

        if t == TILE_WALL:
            if lv == 1: # Jungle Cliff Wall
                pygame.draw.rect(surface, (60, 48, 38), front_rect)
                state = random.getstate()
                random.seed(tx * 43 + ty * 91)
                for _ in range(random.randint(1, 3)):
                    vx = front_rect.x + random.randint(3, ts - 5)
                    vh = random.randint(4, h_ext)
                    pygame.draw.line(surface, (45, 95, 30), (vx, front_rect.y), (vx, front_rect.y + vh), 1)
                random.setstate(state)
                pygame.draw.rect(surface, (34, 62, 18), top_rect, border_radius=2)
                pygame.draw.line(surface, (82, 120, 50), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
                
            elif lv == 2: # Village Wooden Cabin Wall
                pygame.draw.rect(surface, (80, 50, 30), front_rect)
                for ly in range(front_rect.y + 3, front_rect.bottom, 4):
                    pygame.draw.line(surface, (55, 30, 15), (front_rect.x, ly), (front_rect.right, ly), 1)
                pygame.draw.rect(surface, (130, 95, 55), top_rect, border_radius=2)
                for i in range(top_rect.x + 4, top_rect.right, 6):
                    pygame.draw.line(surface, (95, 65, 35), (i, top_rect.y), (i - 4, top_rect.bottom), 1)
                pygame.draw.line(surface, (165, 125, 80), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
                
            elif lv == 3: # Rural Wooden House Wall
                # Mặt trước: ván gỗ nâu đậm
                pygame.draw.rect(surface, (90, 58, 30), front_rect)
                for ly in range(front_rect.y + 3, front_rect.bottom, 4):
                    pygame.draw.line(surface, (65, 40, 18), (front_rect.x, ly), (front_rect.right, ly), 1)
                # Mái nhà: gỗ sáng hơn
                pygame.draw.rect(surface, (140, 100, 60), top_rect, border_radius=2)
                for i in range(top_rect.x + 5, top_rect.right, 6):
                    pygame.draw.line(surface, (105, 72, 38), (i, top_rect.y), (i - 3, top_rect.bottom), 1)
                pygame.draw.line(surface, (175, 135, 85), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
                
            elif lv == 4: # Tech Base Bunker
                pygame.draw.rect(surface, (35, 40, 50), front_rect)
                pygame.draw.line(surface, (18, 22, 28), (front_rect.x, front_rect.y + 4), (front_rect.right, front_rect.y + 4), 1)
                state = random.getstate()
                random.seed(tx * 17 + ty * 131)
                if random.random() < 0.2:
                    pygame.draw.circle(surface, (255, 50, 50), (front_rect.centerx, front_rect.y + 6), 2)
                random.setstate(state)
                pygame.draw.rect(surface, (65, 75, 90), top_rect, border_radius=2)
                pygame.draw.rect(surface, (50, 60, 72), (top_rect.x + 3, top_rect.y + 3, ts - 6, ts - 6), 1)
                for rx, ry in [(top_rect.x + 4, top_rect.y + 4), (top_rect.right - 6, top_rect.y + 4), (top_rect.x + 4, top_rect.bottom - 6), (top_rect.right - 6, top_rect.bottom - 6)]:
                    pygame.draw.circle(surface, (100, 115, 135), (rx, ry), 1)
                pygame.draw.line(surface, (110, 125, 145), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
                
            elif lv == 5: # Hell Obsidian Wall
                pygame.draw.rect(surface, (25, 12, 12), front_rect)
                state = random.getstate()
                random.seed(tx * 23 + ty * 313)
                p1 = (front_rect.x + random.randint(4, 12), front_rect.y)
                p2 = (front_rect.x + random.randint(12, ts-6), front_rect.bottom)
                pygame.draw.line(surface, (255, 60, 0), p1, p2, 2)
                pygame.draw.line(surface, (255, 180, 0), p1, p2, 1)
                random.setstate(state)
                pygame.draw.rect(surface, (18, 18, 22), top_rect, border_radius=1)
                pygame.draw.polygon(surface, (45, 30, 50), [(top_rect.x + 4, top_rect.y + 4), (top_rect.right - 8, top_rect.y + 2), (top_rect.centerx, top_rect.centery)])
                pygame.draw.line(surface, (255, 80, 0), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
                
        elif t == TILE_COVER:
            if lv == 3:
                # Bao cát / thùng gỗ nông thôn
                pygame.draw.rect(surface, (120, 90, 55), front_rect)
                pygame.draw.line(surface, (85, 60, 30), (front_rect.x + 2, front_rect.y + 2), (front_rect.right - 3, front_rect.bottom - 2), 2)
                pygame.draw.rect(surface, (160, 125, 80), top_rect, border_radius=2)
                for i in range(top_rect.x + 5, top_rect.right, 6):
                    pygame.draw.line(surface, (120, 90, 55), (i, top_rect.y), (i, top_rect.bottom), 1)
                pygame.draw.line(surface, (200, 165, 110), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
            elif lv == 4:
                pygame.draw.rect(surface, (50, 55, 65), front_rect)
                pygame.draw.rect(surface, (30, 35, 42), (front_rect.x + 2, front_rect.y + 2, ts - 4, h_ext - 4), 1)
                pygame.draw.rect(surface, (90, 100, 115), top_rect, border_radius=2)
                pygame.draw.rect(surface, (70, 80, 92), (top_rect.x + 3, top_rect.y + 3, ts - 6, ts - 6), 1)
                pygame.draw.line(surface, (120, 130, 150), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
            elif lv == 5:
                pygame.draw.rect(surface, (35, 15, 10), front_rect)
                pygame.draw.line(surface, (220, 45, 0), (front_rect.x, front_rect.y + h_ext//2), (front_rect.right, front_rect.y + h_ext//2), 1)
                pygame.draw.rect(surface, (20, 10, 8), top_rect, border_radius=2)
                pygame.draw.circle(surface, (255, 80, 0), top_rect.center, 4)
            else:
                pygame.draw.rect(surface, (100, 75, 50), front_rect)
                pygame.draw.line(surface, (70, 50, 30), (front_rect.x + 2, front_rect.y + 2), (front_rect.right - 3, front_rect.bottom - 2), 2)
                pygame.draw.line(surface, (70, 50, 30), (front_rect.right - 3, front_rect.y + 2), (front_rect.x + 2, front_rect.bottom - 2), 2)
                pygame.draw.rect(surface, (145, 115, 80), top_rect, border_radius=2)
                for i in range(top_rect.x + 6, top_rect.right, 6):
                    pygame.draw.line(surface, (110, 85, 55), (i, top_rect.y), (i, top_rect.bottom), 1)
                pygame.draw.line(surface, (190, 160, 120), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)

        elif t == TILE_BARREL:
            cx = rect.centerx
            cy = rect.centery
            r = 10
            side_rect = pygame.Rect(cx - r, cy - h_ext, r * 2, h_ext)
            if lv == 5:
                pygame.draw.rect(surface, (50, 15, 10), side_rect)
                pygame.draw.rect(surface, (255, 60, 0), (cx - r, cy - h_ext + 3, r * 2, 4))
                pygame.draw.circle(surface, (30, 10, 8), (cx, cy - h_ext), r)
                pygame.draw.circle(surface, (255, 150, 0), (cx, cy - h_ext), r - 3)
            elif lv == 4:
                pygame.draw.rect(surface, (40, 45, 50), side_rect)
                pygame.draw.rect(surface, (230, 180, 0), (cx - r, cy - h_ext + 4, r * 2, 3))
                pygame.draw.rect(surface, (0, 255, 50), (cx - 3, cy - h_ext + 2, 2, h_ext - 3))
                pygame.draw.circle(surface, (55, 60, 65), (cx, cy - h_ext), r)
                pygame.draw.circle(surface, (0, 200, 30), (cx, cy - h_ext), r - 3)
            else:
                pygame.draw.rect(surface, (130, 35, 20), side_rect)
                pygame.draw.rect(surface, (180, 60, 40), (cx - r + 3, cy - h_ext, 4, h_ext))
                pygame.draw.rect(surface, (80, 15, 10), (cx + r - 5, cy - h_ext, 4, h_ext))
                pygame.draw.line(surface, (230, 180, 0), (cx - 5, cy - h_ext + 3), (cx + 5, cy - 3), 2)
                pygame.draw.line(surface, (230, 180, 0), (cx + 5, cy - h_ext + 3), (cx - 5, cy - 3), 2)
                pygame.draw.circle(surface, (90, 25, 15), (cx, cy - h_ext), r)
                pygame.draw.circle(surface, (50, 15, 10), (cx, cy - h_ext), r - 3)

        elif t == TILE_ALARM_CONSOLE:
            pygame.draw.rect(surface, (35, 38, 42), front_rect)
            pygame.draw.circle(surface, (255, 0, 0), (front_rect.x + 6, front_rect.y + 4), 2)
            pygame.draw.circle(surface, (0, 255, 0), (front_rect.right - 6, front_rect.y + 4), 2)
            pygame.draw.rect(surface, (60, 65, 70), top_rect, border_radius=2)
            monitor_color = (0, 120, 180) if lv != 5 else (180, 20, 10)
            pygame.draw.rect(surface, monitor_color, (top_rect.x + 4, top_rect.y + 3, ts - 8, ts - 12), border_radius=1)
            pygame.draw.line(surface, (255, 255, 255), (top_rect.x + 6, top_rect.y + 6), (top_rect.right - 8, top_rect.y + 6), 1)
            pygame.draw.rect(surface, (25, 25, 28), (top_rect.x + 4, top_rect.bottom - 7, ts - 8, 4))

        elif t == TILE_LASER:
            cx = rect.centerx
            cy = rect.centery
            r = 6
            pillar_rect = pygame.Rect(cx - r, cy - h_ext, r * 2, h_ext)
            pygame.draw.rect(surface, (45, 50, 58), pillar_rect)
            pygame.draw.rect(surface, (80, 90, 105), (cx - r + 1, cy - h_ext, 2, h_ext))
            pygame.draw.circle(surface, (25, 28, 32), (cx, cy), r + 2)
            sphere_color = (255, 60, 60) if lv != 1 else (0, 255, 100)
            pygame.draw.circle(surface, sphere_color, (cx, cy - h_ext), 5)
            pygame.draw.circle(surface, (255, 255, 255), (cx - 1, cy - h_ext - 1), 2)

        elif t == TILE_TUNNEL:
            pygame.draw.rect(surface, (45, 45, 45), front_rect)
            pygame.draw.rect(surface, (85, 85, 85), top_rect, border_radius=3)
            pygame.draw.line(surface, (60, 60, 60), (top_rect.centerx, top_rect.y), (top_rect.centerx, top_rect.bottom), 1)
            pygame.draw.line(surface, (120, 120, 120), (top_rect.x, top_rect.bottom - 1), (top_rect.right, top_rect.bottom - 1), 1)
            pygame.draw.circle(surface, (0, 0, 0), (rect.centerx, rect.bottom - 6), ts//2 - 4)

        elif t == TILE_EXIT:
            pygame.draw.rect(surface, (50, 50, 50), front_rect)
            for i in range(front_rect.x, front_rect.right, 8):
                pygame.draw.line(surface, (230, 180, 0), (i, front_rect.y), (i + 4, front_rect.bottom), 2)
            pygame.draw.rect(surface, (75, 80, 85), top_rect, border_radius=4)
            pygame.draw.circle(surface, (20, 20, 20), top_rect.center, ts//2 - 2)
            pygame.draw.circle(surface, (0, 150, 255), top_rect.center, ts//2 - 4, 2)

    def _bake_surface(self):
        """Pre-render map to a Surface for fast blitting."""
        self._surface = pygame.Surface((self.pixel_w, self.pixel_h))
        palettes_bg = {
            1: (20, 30, 15),
            2: (12, 16, 22),
            3: (22, 38, 18),   # Nông thôn: nền cỏ xanh tối
            4: (20, 28, 18),
            5: (30, 8, 5)
        }
        lv = min(max(self.level, 1), 5)
        self._surface.fill(palettes_bg[lv])
        ts = TILE_SIZE

        # PASS 1: Floor tiles
        for y in range(self.height):
            for x in range(self.width):
                self._draw_tile_floor(self._surface, x, y)

        # PASS 2: 3D Object Drop Shadows
        shadow_surf = pygame.Surface((self.pixel_w, self.pixel_h), pygame.SRCALPHA)
        dx, dy = 6, 8
        for y in range(self.height):
            for x in range(self.width):
                t = self.grid[y][x]
                if t != TILE_EMPTY:
                    h_ext = 14
                    if t == TILE_COVER:
                        h_ext = 10
                    elif t == TILE_BARREL:
                        h_ext = 12
                    elif t == TILE_ALARM_CONSOLE:
                        h_ext = 10
                    elif t == TILE_LASER:
                        h_ext = 12
                    elif t == TILE_TUNNEL:
                        h_ext = 14
                    elif t == TILE_EXIT:
                        h_ext = 6

                    if t == TILE_BARREL:
                        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), (x * ts + dx - 2, y * ts - 4 + dy, ts + 4, ts + 4))
                    else:
                        pygame.draw.rect(shadow_surf, (0, 0, 0, 120), (x * ts + dx, y * ts - h_ext + dy, ts, ts + h_ext), border_radius=4)
        self._surface.blit(shadow_surf, (0, 0))

        # PASS 3: 3D Objects rendering using Painter's Algorithm
        for y in range(self.height):
            for x in range(self.width):
                self._draw_tile_object(self._surface, x, y)

    def is_wall(self, tx, ty):
        if tx < 0 or tx >= self.width or ty < 0 or ty >= self.height:
            return True
        return self.grid[ty][tx] in (TILE_WALL, TILE_COVER, TILE_BARREL, TILE_ALARM_CONSOLE, TILE_LASER)

    def is_wall_pixel(self, px, py):
        return self.is_wall(int(px // TILE_SIZE), int(py // TILE_SIZE))

    def is_wall_pixel_radius(self, px, py, r=10):
        """Check collision with a circular radius using optimized bounding box tiles."""
        tx1 = int((px - r) // TILE_SIZE)
        tx2 = int((px + r) // TILE_SIZE)
        ty1 = int((py - r) // TILE_SIZE)
        ty2 = int((py + r) // TILE_SIZE)
        for ty in range(ty1, ty2 + 1):
            for tx in range(tx1, tx2 + 1):
                if self.is_wall(tx, ty):
                    return True
        return False

    def get_tile(self, tx, ty):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return TILE_WALL

    def _check_path_exists(self, sx, sy, gx, gy):
        """Kiểm tra BFS xem có đường đi từ (sx, sy) tới (gx, gy) mà không bị cản bởi TILE_WALL/TILE_COVER hay không."""
        from collections import deque
        queue = deque([(sx, sy)])
        visited = {(sx, sy)}
        while queue:
            cx, cy = queue.popleft()
            if cx == gx and cy == gy:
                return True
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0)]:
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in visited and not self.is_wall(nx, ny):
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        return False

    def find_path_bfs(self, start_px, start_py, target_tile):
        """Find path from pixel coordinates to a specific tile type using BFS."""
        from collections import deque
        start_tx = int(start_px // TILE_SIZE)
        start_ty = int(start_py // TILE_SIZE)
        
        if self.get_tile(start_tx, start_ty) == target_tile:
            return [(start_tx, start_ty)]
            
        queue = deque([(start_tx, start_ty, [])])
        visited = {(start_tx, start_ty)}
        
        while queue:
            tx, ty, path = queue.popleft()
            
            # Check if reached target
            if self.get_tile(tx, ty) == target_tile:
                return path + [(tx, ty)]
                
            # Neighbors (Ngang, dọc, và chéo)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = tx + dx, ty + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in visited and not self.is_wall(nx, ny):
                        # Prevent corner-cutting
                        if dx != 0 and dy != 0:
                            if self.is_wall(tx, ty+dy) or self.is_wall(tx+dx, ty):
                                continue
                        visited.add((nx, ny))
                        queue.append((nx, ny, path + [(tx, ty)]))
        return None

    def find_path_to_point_list(self, start_px, start_py, target_pixels, algorithm="BFS", avoid_tiles=None):
        """Find path from pixel to the nearest of several pixel targets using specified algorithm."""
        from collections import deque
        import heapq
        
        if avoid_tiles is None:
            avoid_tiles = set()
            
        start_tx = int(start_px // TILE_SIZE)
        start_ty = int(start_py // TILE_SIZE)
        
        target_tiles = set()
        for px, py in target_pixels:
            tx = int(px // TILE_SIZE)
            ty = int(py // TILE_SIZE)
            if not self.is_wall(tx, ty):
                target_tiles.add((tx, ty))
            else:
                # Find nearest walkable tile to this target using BFS
                queue = deque([(tx, ty)])
                tgt_visited = {(tx, ty)}
                found = False
                while queue:
                    cx, cy = queue.popleft()
                    if not self.is_wall(cx, cy):
                        target_tiles.add((cx, cy))
                        found = True
                        break
                    if abs(cx - tx) > 3 or abs(cy - ty) > 3:
                        continue
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if (nx, ny) not in tgt_visited:
                                tgt_visited.add((nx, ny))
                                queue.append((nx, ny))
                if not found:
                    target_tiles.add((tx, ty))
            
        if (start_tx, start_ty) in target_tiles:
            return [(start_tx, start_ty)]
            
        def heuristic(tx, ty):
            # Octile distance to nearest target
            if not target_tiles: return 0
            dists = []
            for tgt in target_tiles:
                dx = abs(tx - tgt[0])
                dy = abs(ty - tgt[1])
                dists.append(min(dx, dy) * 1.414 + (max(dx, dy) - min(dx, dy)))
            return min(dists)
            
        visited = set()
        
        if algorithm == "BFS":
            queue = deque([(start_tx, start_ty, [])])
            visited.add((start_tx, start_ty))
            while queue:
                tx, ty, path = queue.popleft()
                if (tx, ty) in target_tiles: return path + [(tx, ty)]
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if (nx, ny) not in visited and not self.is_wall(nx, ny) and (nx, ny) not in avoid_tiles:
                            # Prevent corner-cutting
                            if dx != 0 and dy != 0:
                                if self.is_wall(tx, ty+dy) or self.is_wall(tx+dx, ty):
                                    continue
                            visited.add((nx, ny))
                            queue.append((nx, ny, path + [(tx, ty)]))
        elif algorithm == "DFS":
            stack = [(start_tx, start_ty, [])]
            visited.add((start_tx, start_ty))
            while stack:
                tx, ty, path = stack.pop()
                if (tx, ty) in target_tiles: return path + [(tx, ty)]
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if (nx, ny) not in visited and not self.is_wall(nx, ny) and (nx, ny) not in avoid_tiles:
                            # Prevent corner-cutting
                            if dx != 0 and dy != 0:
                                if self.is_wall(tx, ty+dy) or self.is_wall(tx+dx, ty):
                                    continue
                            visited.add((nx, ny))
                            stack.append((nx, ny, path + [(tx, ty)]))
        elif algorithm == "A*":
            pq = []
            heapq.heappush(pq, (0.0, 0.0, start_tx, start_ty, []))
            costs = {(start_tx, start_ty): 0.0}
            while pq:
                _, cost, tx, ty, path = heapq.heappop(pq)
                if (tx, ty) in target_tiles: return path + [(tx, ty)]
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height and not self.is_wall(nx, ny) and (nx, ny) not in avoid_tiles:
                        # Prevent corner-cutting
                        if dx != 0 and dy != 0:
                            if self.is_wall(tx, ty+dy) or self.is_wall(tx+dx, ty):
                                continue
                        move_cost = cost + (1.414 if (dx != 0 and dy != 0) else 1.0)
                        if (nx, ny) not in costs or move_cost < costs[(nx, ny)]:
                            costs[(nx, ny)] = move_cost
                            priority = move_cost + heuristic(nx, ny)
                            heapq.heappush(pq, (priority, move_cost, nx, ny, path + [(tx, ty)]))
        elif algorithm == "HEURISTIC":
            pq = []
            heapq.heappush(pq, (heuristic(start_tx, start_ty), start_tx, start_ty, []))
            visited.add((start_tx, start_ty))
            while pq:
                _, tx, ty, path = heapq.heappop(pq)
                if (tx, ty) in target_tiles: return path + [(tx, ty)]
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height and not self.is_wall(nx, ny) and (nx, ny) not in avoid_tiles:
                        # Prevent corner-cutting
                        if dx != 0 and dy != 0:
                            if self.is_wall(tx, ty+dy) or self.is_wall(tx+dx, ty):
                                continue
                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            priority = heuristic(nx, ny)
                            heapq.heappush(pq, (priority, nx, ny, path + [(tx, ty)]))
                            
        return None
                            
        return None

    def add_burnt_decal(self, px, py):
        """Draw a burnt crater/wreckage decal onto the map surface at pixel coordinates."""
        if not self._surface:
            return
        surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(surf, (15, 10, 8, 140), (40, 40), 30)
        pygame.draw.circle(surf, (30, 20, 15, 180), (40, 40), 22)
        pygame.draw.circle(surf, (10, 5, 0, 210), (40, 40), 12)
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            length = random.randint(18, 38)
            ex = 40 + math.cos(angle) * length
            ey = 40 + math.sin(angle) * length
            pygame.draw.line(surf, (15, 10, 8, 160), (40, 40), (ex, ey), random.randint(2, 5))
        self._surface.blit(surf, (int(px - 40), int(py - 40)))

    def tunnel_partner(self, tx, ty):
        """Find the other tunnel entrance if standing on one."""
        if self.get_tile(tx, ty) != TILE_TUNNEL:
            return None
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) != (tx, ty) and self.grid[y][x] == TILE_TUNNEL:
                    return (x*TILE_SIZE + TILE_SIZE//2, y*TILE_SIZE + TILE_SIZE//2)
        return None

    # ── Tactical AI Noise & Cover/Barrel Destruction ──────────────────────────
    def add_noise(self, x, y, radius):
        self.active_noises.append((x, y, radius))

    def start_barrel_leak(self, tx, ty):
        if self.get_tile(tx, ty) == TILE_BARREL and (tx, ty) not in self.leaking_barrels:
            self.leaking_barrels[(tx, ty)] = 120  # 2 seconds (120 frames at 60 FPS)

    def damage_cover(self, tx, ty, damage, effect_manager, sound_manager):
        key = (tx, ty)
        if key not in self.cover_hp:
            self.cover_hp[key] = 120.0
        self.cover_hp[key] -= damage
        
        px = tx * TILE_SIZE + TILE_SIZE // 2
        py = ty * TILE_SIZE + TILE_SIZE // 2
        effect_manager.add_sparks(px, py, count=2)
        
        if self.cover_hp[key] <= 0:
            self.destroy_cover(tx, ty, effect_manager, sound_manager)
        else:
            # Add visual cracking/damage on the pre-baked cover tile
            hp_percentage = self.cover_hp[key] / 120.0
            if hp_percentage < 0.75 and random.random() < 0.4:
                ts = TILE_SIZE
                cx = tx * ts + random.randint(4, ts - 8)
                cy = ty * ts + random.randint(4, ts - 8)
                ex = cx + random.randint(-10, 10)
                ey = cy + random.randint(-10, 10)
                pygame.draw.line(self._surface, (35, 25, 20), (cx, cy), (ex, ey), 2)

    def destroy_cover(self, tx, ty, effect_manager, sound_manager):
        self.grid[ty][tx] = TILE_EMPTY
        self.cover_hp.pop((tx, ty), None)
        self.minimap_dirty = True
        
        px = tx * TILE_SIZE + TILE_SIZE // 2
        py = ty * TILE_SIZE + TILE_SIZE // 2
        sound_manager.play("wood_break")
        effect_manager.add_cover_destruction(px, py)
        self.redraw_tile_floor(tx, ty)
        self.draw_wooden_debris_decal(tx, ty)

    def redraw_tile_floor(self, tx, ty):
        if not self._surface:
            return
        # 1. Clear/draw the floor for the targeted tile
        self._draw_tile_floor(self._surface, tx, ty)
        
        # 2. Redraw objects in row ty-1, ty, ty+1 to preserve 3D stacking layers
        for ny in [ty - 1, ty, ty + 1]:
            if 0 <= ny < self.height and 0 <= tx < self.width:
                self._draw_tile_object(self._surface, tx, ny)

    def draw_wooden_debris_decal(self, tx, ty):
        if not self._surface:
            return
        ts = TILE_SIZE
        for _ in range(random.randint(4, 7)):
            w = random.randint(4, 9)
            h = random.randint(2, 4)
            rx = tx*ts + random.randint(4, ts - 12)
            ry = ty*ts + random.randint(4, ts - 8)
            color = random.choice([(105, 85, 65), (135, 95, 55), (85, 65, 45)])
            pts = [
                (rx, ry),
                (rx + w, ry + random.randint(-1, 1)),
                (rx + w + random.randint(-1, 1), ry + h),
                (rx + random.randint(-1, 1), ry + h)
            ]
            pygame.draw.polygon(self._surface, color, pts)

    def update(self, effect_manager, sound_manager):
        exploded_barrels = []
        finished = []
        for (tx, ty), frames in list(self.leaking_barrels.items()):
            new_frames = frames - 1
            if new_frames <= 0:
                finished.append((tx, ty))
            else:
                self.leaking_barrels[(tx, ty)] = new_frames
                px = tx * TILE_SIZE + TILE_SIZE // 2
                py = ty * TILE_SIZE + TILE_SIZE // 2
                
                # Emit fire & smoke particles
                if random.random() < 0.4:
                    effect_manager.add_fire(px + random.uniform(-6, 6), py - 10, count=1)
                if random.random() < 0.6:
                    effect_manager.add_smoke(px + random.uniform(-6, 6), py - 15, count=1)
                
                # Play hiss sound
                if new_frames % 25 == 0:
                    sound_manager.play("hiss")
                    
        for tx, ty in finished:
            self.leaking_barrels.pop((tx, ty), None)
            self.grid[ty][tx] = TILE_EMPTY
            self.minimap_dirty = True
            px = tx * TILE_SIZE + TILE_SIZE // 2
            py = ty * TILE_SIZE + TILE_SIZE // 2
            exploded_barrels.append((px, py))
            self.redraw_tile_floor(tx, ty)
            
        return exploded_barrels

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, screen, camera_x, camera_y):
        screen.blit(self._surface, (-camera_x, -camera_y))
        
        # Overlay leaking barrels fire/glow
        for (tx, ty), frames in self.leaking_barrels.items():
            px = tx * TILE_SIZE + TILE_SIZE // 2 - camera_x
            py = ty * TILE_SIZE + TILE_SIZE // 2 - camera_y
            
            # Pulsing orange glow
            glow_radius = int(22 + 6 * math.sin(pygame.time.get_ticks() / 80.0))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 75, 0, 75), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (px - glow_radius, py - glow_radius))
            
            # Dynamic flames
            for _ in range(2):
                fx = px + random.randint(-6, 6)
                fy = py + random.randint(-10, 2)
                pygame.draw.circle(screen, random.choice([(255, 90, 0), (255, 180, 40), (220, 45, 0)]), (fx, fy), random.randint(3, 6))

        # Swirling rotating portal concentric circles for exit wormholes
        for tx, ty in getattr(self, 'exit_tiles', []):
            cx = tx * TILE_SIZE + TILE_SIZE // 2 - camera_x
            cy = ty * TILE_SIZE + TILE_SIZE // 2 - camera_y
            
            # Pulse center core
            time_ticks = pygame.time.get_ticks()
            pulse = int(12 + 6 * math.sin(time_ticks * 0.008))
            
            # Draw core glow
            core_surf = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, (0, 180, 255, 45 + int(15 * math.sin(time_ticks * 0.005))), 
                               (TILE_SIZE, TILE_SIZE), pulse + 6)
            pygame.draw.circle(core_surf, (0, 255, 200, 90), (TILE_SIZE, TILE_SIZE), pulse, 2)
            screen.blit(core_surf, (cx - TILE_SIZE, cy - TILE_SIZE), special_flags=pygame.BLEND_ADD)
            
            # Draw 3 concentric rings rotating in alternating directions
            ring_configs = [
                {"radius": 18, "speed": 0.002, "color": (0, 255, 200), "dashes": 8, "dash_len": 0.3},
                {"radius": 26, "speed": -0.0015, "color": (0, 150, 255), "dashes": 12, "dash_len": 0.2},
                {"radius": 34, "speed": 0.001, "color": (0, 80, 255), "dashes": 16, "dash_len": 0.15}
            ]
            
            for config in ring_configs:
                r = config["radius"]
                angle_offset = time_ticks * config["speed"]
                num_dashes = config["dashes"]
                dash_len = config["dash_len"] # fraction of step
                
                for i in range(num_dashes):
                    a1 = angle_offset + (i * 2 * math.pi / num_dashes)
                    a2 = a1 + dash_len * (2 * math.pi / num_dashes)
                    
                    x1 = cx + math.cos(a1) * r
                    y1 = cy + math.sin(a1) * r
                    x2 = cx + math.cos(a2) * r
                    y2 = cy + math.sin(a2) * r
                    
                    pygame.draw.line(screen, config["color"], (x1, y1), (x2, y2), 2)

    def parse_laser_lines(self):
        self.laser_lines = []
        visited = set()
        ts = TILE_SIZE
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == TILE_LASER and (x, y) not in visited:
                    for dx, dy in [(1, 0), (0, 1)]:
                        for length in range(1, 10):
                            nx = x + dx * length
                            ny = y + dy * length
                            if not (0 <= nx < self.width and 0 <= ny < self.height):
                                break
                            if self.grid[ny][nx] == TILE_WALL:
                                break
                            if self.grid[ny][nx] == TILE_LASER:
                                p1 = (x * ts + ts // 2, y * ts + ts // 2)
                                p2 = (nx * ts + ts // 2, ny * ts + ts // 2)
                                self.laser_lines.append({
                                    "p1": p1,
                                    "p2": p2,
                                    "t1": (x, y),
                                    "t2": (nx, ny),
                                    "active": True
                                })
                                visited.add((x, y))
                                visited.add((nx, ny))
                                break

    def damage_alarm_console(self, tx, ty, damage, effect_manager, sound_manager):
        key = (tx, ty)
        if key not in self.alarm_console_hp:
            self.alarm_console_hp[key] = ALARM_CONSOLE_HP
        self.alarm_console_hp[key] -= damage
        px = tx * TILE_SIZE + TILE_SIZE // 2
        py = ty * TILE_SIZE + TILE_SIZE // 2
        effect_manager.add_sparks(px, py, count=3)
        if self.alarm_console_hp[key] <= 0:
            self.destroy_alarm_console(tx, ty, effect_manager, sound_manager)

    def destroy_alarm_console(self, tx, ty, effect_manager, sound_manager):
        self.grid[ty][tx] = TILE_EMPTY
        self.alarm_console_hp.pop((tx, ty), None)
        self.minimap_dirty = True
        px = tx * TILE_SIZE + TILE_SIZE // 2
        py = ty * TILE_SIZE + TILE_SIZE // 2
        sound_manager.play("wood_break")
        effect_manager.add_cover_destruction(px, py)
        self.redraw_tile_floor(tx, ty)

    def damage_laser(self, tx, ty, damage, effect_manager, sound_manager):
        key = (tx, ty)
        if key not in self.laser_hp:
            self.laser_hp[key] = LASER_HP
        self.laser_hp[key] -= damage
        px = tx * TILE_SIZE + TILE_SIZE // 2
        py = ty * TILE_SIZE + TILE_SIZE // 2
        effect_manager.add_sparks(px, py, count=2)
        if self.laser_hp[key] <= 0:
            self.destroy_laser(tx, ty, effect_manager, sound_manager)

    def destroy_laser(self, tx, ty, effect_manager, sound_manager):
        self.grid[ty][tx] = TILE_EMPTY
        self.laser_hp.pop((tx, ty), None)
        self.minimap_dirty = True
        px = tx * TILE_SIZE + TILE_SIZE // 2
        py = ty * TILE_SIZE + TILE_SIZE // 2
        sound_manager.play("wood_break")
        effect_manager.add_cover_destruction(px, py)
        self.redraw_tile_floor(tx, ty)
        for laser in self.laser_lines:
            if laser["t1"] == (tx, ty) or laser["t2"] == (tx, ty):
                laser["active"] = False
