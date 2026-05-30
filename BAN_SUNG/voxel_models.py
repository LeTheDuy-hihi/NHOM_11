"""
voxel_models.py
Voxel-stack renderer cho BAN_SUNG.
Mỗi "model" là danh sách các lớp (layer) từ dưới lên trên.
Mỗi layer là list[(dx, dy, color)] — offset so với tâm và màu RGBA.
render_stack() xếp chồng các lớp lên nhau với khoảng cách `spacing` pixel/lớp,
xoay toàn bộ theo góc `angle` (radians).
"""

import pygame
import math

# ─── Cache ──────────────────────────────────────────────────────────────────
_model_cache = {}   # key → list[layer]


# ─── Helpers ────────────────────────────────────────────────────────────────
def _tint(base_color, tint):
    """Blend base_color với tint (50/50)."""
    if tint is None:
        return base_color
    r = (base_color[0] + tint[0]) // 2
    g = (base_color[1] + tint[1]) // 2
    b = (base_color[2] + tint[2]) // 2
    return (r, g, b)


def _darken(color, factor=0.7):
    return (int(color[0]*factor), int(color[1]*factor), int(color[2]*factor))


def _lighten(color, factor=1.3):
    return (min(255,int(color[0]*factor)), min(255,int(color[1]*factor)), min(255,int(color[2]*factor)))


# ─── Model definitions ───────────────────────────────────────────────────────
def _build_player_model():
    """
    Nhân vật người chơi nhìn từ trên xuống (top-down).
    Layers từ dưới lên: thân → giáp → đầu.
    Mỗi layer: list[(dx, dy, (r,g,b))]
    """
    body_col   = (60,  100, 60)    # Quân phục xanh
    armor_col  = (80,  130, 80)    # Giáp nhẹ hơn
    head_col   = (200, 160, 120)   # Da mặt
    helmet_col = (50,  70,  50)    # Mũ bảo hiểm
    gun_col    = (40,  40,  40)    # Súng

    layers = []

    # Layer 0: Bóng mờ (chân)
    shadow = [(dx, dy, (15, 20, 15))
              for dx in range(-7, 8) for dy in range(-5, 6)
              if dx*dx/49 + dy*dy/25 <= 1.0]
    layers.append(shadow)

    # Layer 1: Thân dưới (hông/chân)
    body_lower = [(dx, dy, _darken(body_col))
                  for dx in range(-5, 6) for dy in range(-4, 5)
                  if dx*dx/25 + dy*dy/16 <= 1.0]
    layers.append(body_lower)

    # Layer 2: Thân trên (ngực)
    body_upper = [(dx, dy, body_col)
                  for dx in range(-5, 6) for dy in range(-4, 5)
                  if dx*dx/25 + dy*dy/16 <= 1.0]
    layers.append(body_upper)

    # Layer 3: Giáp ngực
    chest = [(dx, dy, armor_col)
             for dx in range(-4, 5) for dy in range(-3, 4)
             if dx*dx/16 + dy*dy/9 <= 1.0]
    layers.append(chest)

    # Layer 4: Vai + cánh tay
    shoulders = [(-5, 0, armor_col), (-5, -1, armor_col), (-5, 1, armor_col),
                 ( 5, 0, armor_col), ( 5, -1, armor_col), ( 5, 1, armor_col)]
    layers.append(shoulders)

    # Layer 5: Đầu
    head = [(dx, dy, head_col)
            for dx in range(-3, 4) for dy in range(-3, 4)
            if dx*dx + dy*dy <= 9]
    layers.append(head)

    # Layer 6: Mũ bảo hiểm (nửa trên)
    helmet = [(dx, dy, helmet_col)
              for dx in range(-3, 4) for dy in range(-3, 1)
              if dx*dx + dy*dy <= 9]
    layers.append(helmet)

    # Layer 7: Súng (kéo dài về phía trước — hướng +x)
    gun = [(gx, 0, gun_col) for gx in range(3, 12)] + \
          [(gx, -1, gun_col) for gx in range(3, 9)]
    layers.append(gun)

    return layers


def _build_boss_model():
    """Boss khổng lồ — mech/robot."""
    base_col   = (120, 20,  20)    # Đỏ thẫm
    armor_col  = (180, 30,  30)    # Giáp đỏ tươi
    glow_col   = (255, 80,  0)     # Cam phát sáng
    metal_col  = (80,  80,  90)    # Kim loại

    layers = []

    # Bóng to
    shadow = [(dx, dy, (10, 5, 5))
              for dx in range(-14, 15) for dy in range(-10, 11)
              if dx*dx/196 + dy*dy/100 <= 1.0]
    layers.append(shadow)

    # Thân dưới
    for i in range(3):
        body = [(dx, dy, _darken(base_col, 0.6 + i*0.15))
                for dx in range(-10, 11) for dy in range(-8, 9)
                if dx*dx/100 + dy*dy/64 <= 1.0]
        layers.append(body)

    # Giáp ngực dày
    for i in range(4):
        chest = [(dx, dy, _darken(armor_col, 0.7 + i*0.1))
                 for dx in range(-9, 10) for dy in range(-7, 8)
                 if dx*dx/81 + dy*dy/49 <= 1.0]
        layers.append(chest)

    # Vai to
    for i in range(2):
        shoulders = [(dx, dy, metal_col)
                     for dx in (list(range(-14, -9)) + list(range(10, 15)))
                     for dy in range(-3, 4)]
        layers.append(shoulders)

    # Lõi phát sáng
    core = [(dx, dy, glow_col)
            for dx in range(-4, 5) for dy in range(-4, 5)
            if dx*dx + dy*dy <= 16]
    layers.append(core)

    # Đầu
    for i in range(3):
        head = [(dx, dy, _darken(metal_col, 0.8 + i*0.15))
                for dx in range(-7, 8) for dy in range(-6, 7)
                if dx*dx/49 + dy*dy/36 <= 1.0]
        layers.append(head)

    # Mắt phát sáng
    eyes = [(-3, -2, glow_col), (-2, -2, glow_col), (-3, -1, glow_col),
            ( 3, -2, glow_col), ( 2, -2, glow_col), ( 3, -1, glow_col)]
    layers.append(eyes)

    # Súng to (2 nòng)
    for gy in (-2, 2):
        gun = [(gx, gy, metal_col) for gx in range(7, 20)]
        layers.append(gun)

    return layers


def _build_tank_hull_model(tint_color=None):
    """Thân xe tăng."""
    base  = _tint((80, 130, 80), tint_color)   # Xanh quân sự
    dark  = _darken(base, 0.6)
    light = _lighten(base, 1.2)
    track = (40, 40, 40)   # Xích sắt

    layers = []

    # Bóng
    shadow = [(dx, dy, (10, 15, 10))
              for dx in range(-13, 14) for dy in range(-8, 9)
              if dx*dx/169 + dy*dy/64 <= 1.0]
    layers.append(shadow)

    # Xích (hai bên)
    for _ in range(2):
        tracks = [(dx, dy, track)
                  for dx in range(-13, 14)
                  for dy in [-6, -5, 5, 6]
                  if -13 <= dx <= 13]
        layers.append(tracks)

    # Thân chính
    for i in range(5):
        hull = [(dx, dy, _darken(base, 0.7 + i*0.08))
                for dx in range(-10, 11) for dy in range(-5, 6)
                if -10 <= dx <= 10 and -5 <= dy <= 5]
        layers.append(hull)

    # Đường viền sáng
    edge = [(dx, -5, light) for dx in range(-10, 11)] + \
           [(dx,  5, light) for dx in range(-10, 11)]
    layers.append(edge)

    return layers


def _build_tank_turret_model(tint_color=None):
    """Tháp pháo xe tăng."""
    base  = _tint((60, 110, 60), tint_color)
    dark  = _darken(base, 0.6)
    gun   = (35, 35, 35)

    layers = []

    # Tháp pháo tròn
    for i in range(4):
        turret = [(dx, dy, _darken(base, 0.7 + i*0.1))
                  for dx in range(-7, 8) for dy in range(-6, 7)
                  if dx*dx/49 + dy*dy/36 <= 1.0]
        layers.append(turret)

    # Nắp trên
    top = [(dx, dy, _lighten(base, 1.15))
           for dx in range(-5, 6) for dy in range(-4, 5)
           if dx*dx/25 + dy*dy/16 <= 1.0]
    layers.append(top)

    # Nòng pháo (kéo dài theo hướng +x)
    barrel = [(gx,  0, gun) for gx in range(6, 18)] + \
             [(gx, -1, gun) for gx in range(6, 16)] + \
             [(gx,  1, gun) for gx in range(6, 16)]
    layers.append(barrel)

    return layers


# ─── Public API ─────────────────────────────────────────────────────────────
def get_model(name, tint_color=None):
    """
    Lấy model theo tên. Cache để không build lại mỗi frame.
    name: "player" | "boss" | "tank_hull" | "tank_turret"
    tint_color: tuple RGB hoặc None
    """
    cache_key = (name, tint_color)
    if cache_key in _model_cache:
        return _model_cache[cache_key]

    if name == "player":
        model = _build_player_model()
    elif name == "boss":
        model = _build_boss_model()
    elif name == "tank_hull":
        model = _build_tank_hull_model(tint_color)
    elif name == "tank_turret":
        model = _build_tank_turret_model(tint_color)
    else:
        # Fallback: hình tròn đơn giản
        model = [[(dx, dy, (150, 150, 150))
                  for dx in range(-6, 7) for dy in range(-6, 7)
                  if dx*dx + dy*dy <= 36]]

    _model_cache[cache_key] = model
    return model


def render_stack(screen, model, cx, cy, angle, spacing=1):
    """
    Vẽ model voxel-stack lên screen.
    model : list[layer]  — danh sách các lớp từ dưới lên
    cx, cy: tọa độ tâm trên màn hình (có thể float)
    angle : góc quay (radians), 0 = hướng phải (+x)
    spacing: khoảng cách pixel giữa các lớp (tạo chiều cao 3D)
    """
    if not model:
        return

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    icx = int(cx)
    icy = int(cy)

    n_layers = len(model)
    for layer_idx, layer in enumerate(model):
        # Lớp càng cao → vẽ cao hơn (dịch lên trên màn hình)
        z_offset = layer_idx * spacing

        for (dx, dy, color) in layer:
            # Xoay điểm (dx, dy) theo angle
            rx = dx * cos_a - dy * sin_a
            ry = dx * sin_a + dy * cos_a

            px = icx + int(rx)
            py = icy + int(ry) - z_offset  # lớp trên cao hơn

            # Đảm bảo trong bounds màn hình
            sw, sh = screen.get_size()
            if 0 <= px < sw and 0 <= py < sh:
                # Viền shadow nhẹ ở lớp dưới
                if layer_idx == 0:
                    draw_color = (color[0]//3, color[1]//3, color[2]//3)
                else:
                    draw_color = color
                screen.set_at((px, py), draw_color)
