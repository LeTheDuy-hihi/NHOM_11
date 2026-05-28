import pygame
import math
import random
import os
from constants import *
import ai_logic

class Player:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 0.0, 0.0
        self.speed = PLAYER_SPEED
        
        self.hp = PLAYER_HP_MAX
        self.max_hp = PLAYER_HP_MAX
        self.armor = 0
        self.max_armor = PLAYER_ARMOR_MAX
        
        self.angle = 0.0
        self.torso_angle = 0.0
        self.head_angle = 0.0
        self.target_angle = 0.0
        
        # Physics & Movement State
        self.accel = PLAYER_ACCEL
        self.friction = PLAYER_FRICTION
        self.is_sprinting = False
        self.is_aiming = False
        self.under_fire_timer = 0
        self.is_under_fire = False
        
        # Animations
        self.breath_timer = 0.0
        self.lean_amount = 0.0
        self.idle_shift_timer = 0
        self.flinch_vec = [0.0, 0.0]
        
        # Weapon state
        self.equipped_weapons = ["AK-47"]
        self.weapon = "AK-47"
        self.ak_cooldown = 0
        self.grenades = 3
        self.grenade_cooldown = 0
        self.ammo = 150
        self.max_ammo = 150
        
        # Visuals
        self.radius = 12
        self.step_timer = 0
        
        # Upgrades
        self.damage_mult = 1.0
        
        # New Mechanics
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.is_dashing = False
        self.focus = FOCUS_MAX
        self.is_focusing = False
        self.recoil = 0.0
        self.tilt = 0.0
        self.dash_dir = (0, 0)
        self.ai_algorithm = "A*"
        
        # Load custom image
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_dir, "ANH", "nha-vat_chinh.jpg")
        
        if os.path.exists(img_path):
            try:
                # Load with alpha support for PNG
                img = pygame.image.load(img_path).convert_alpha()
                # Xóa khung nền đen (xử lý nhiễu JPG bằng thuật toán lọc màu)
                bg_color = img.get_at((0, 0))
                img.lock()
                w, h = img.get_size()
                for x in range(w):
                    for y in range(h):
                        c = img.get_at((x, y))
                        # Tính độ lệch màu so với màu nền góc trái
                        dist = abs(c[0] - bg_color[0]) + abs(c[1] - bg_color[1]) + abs(c[2] - bg_color[2])
                        if dist < 50: # Ngưỡng sai số màu (giảm xuống 50 để ảnh sắc nét hơn, không bị lẹm)
                            img.set_at((x, y), (0, 0, 0, 0))
                img.unlock()
                # Scale to fit player size (tăng kích thước lên 80x80)
                self.image = pygame.transform.smoothscale(img, (80, 80))

            except Exception as e:
                print(f"Error loading player image: {e}")
                pass

        self.support_drone = None
        self.inventory = {}

    def update(self, keys_dict, mouse_pos, cam_x, cam_y, game_map, bullet_manager, effect_manager, sound_manager, enemies=None):
        # ── 1. Input Handling (Bypass Unikey via Windows API) ────────────────
        pygame_keys = keys_dict["pygame_keys"]
        raw_keys = keys_dict["raw_keys"]
        mouse_btns = pygame.mouse.get_pressed()
        
        # Direct hardware key polling — Windows GetAsyncKeyState
        # This ALWAYS works regardless of Unikey/Telex/VNI
        import ctypes
        def key_down(vk_code):
            return ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000 != 0
        
        # Virtual key codes for WASD and others
        VK_W, VK_A, VK_S, VK_D = 0x57, 0x41, 0x53, 0x44
        VK_Q, VK_R, VK_G = 0x51, 0x52, 0x47
        VK_SHIFT = 0x10
        VK_UP, VK_DOWN, VK_LEFT, VK_RIGHT = 0x26, 0x28, 0x25, 0x27
        
        w_pressed = key_down(VK_W) or key_down(VK_UP)
        a_pressed = key_down(VK_A) or key_down(VK_LEFT)
        s_pressed = key_down(VK_S) or key_down(VK_DOWN)
        d_pressed = key_down(VK_D) or key_down(VK_RIGHT)
        shift_pressed = key_down(VK_SHIFT)
        q_pressed = key_down(VK_Q)
        g_pressed = key_down(VK_G)
        
        # Phím cận chiến V (0x56) hoặc phím số 4 (0x34)
        VK_V, VK_4 = 0x56, 0x34
        melee_pressed = key_down(VK_V) or key_down(VK_4)
        
        VK_TAB = 0x09
        tab_pressed = key_down(VK_TAB)
        
        VK_E = 0x45
        dash_pressed = key_down(VK_E) or pygame_keys[pygame.K_e]
        
        # Weapon switching
        # Weapon switching
        VK_1, VK_2, VK_3 = 0x31, 0x32, 0x33
        if key_down(VK_1) and len(self.equipped_weapons) > 0:
            self.weapon = self.equipped_weapons[0]
        elif key_down(VK_2) and len(self.equipped_weapons) > 1:
            self.weapon = self.equipped_weapons[1]
        elif key_down(VK_3) and len(self.equipped_weapons) > 2:
            self.weapon = self.equipped_weapons[2]
            
        # Right click to draw/equip melee weapon
        if not hasattr(self, 'right_click_pressed_last'):
            self.right_click_pressed_last = False
        right_click = mouse_btns[2]
        if right_click and not self.right_click_pressed_last:
            if self.weapon != "MELEE":
                self.last_gun = self.weapon
                self.weapon = "MELEE"
            else:
                self.weapon = getattr(self, 'last_gun', self.equipped_weapons[0] if self.equipped_weapons else "AK-47")
        self.right_click_pressed_last = right_click
        
        # ── 2. Movement States ───────────────────────────────────────────────
        self.is_aiming = False # Disabled right-click laser aim
        self.is_sprinting = shift_pressed
        self.is_under_fire = self.under_fire_timer > 0
        if self.under_fire_timer > 0: self.under_fire_timer -= 1
        
        # Calculate Target Speed
        current_max_speed = PLAYER_SPEED
        if self.weapon == "MELEE":
            current_max_speed *= 1.15 # Move 15% faster when running with melee!
        elif self.is_sprinting:
            current_max_speed *= PLAYER_SPRINT_MUL
        if self.is_under_fire:
            current_max_speed *= UNDER_FIRE_SPEED_MUL
        
        # ── 3. Physics (Accel / Friction) ──────────────────────────────────
        target_vx, target_vy = 0.0, 0.0
        if self.is_dashing:
            target_vx = self.dash_dir[0] * DASH_SPEED
            target_vy = self.dash_dir[1] * DASH_SPEED
            self.vx = target_vx
            self.vy = target_vy
        else:
            if w_pressed: target_vy -= 1
            if s_pressed: target_vy += 1
            if a_pressed: target_vx -= 1
            if d_pressed: target_vx += 1
            
            if target_vx != 0 and target_vy != 0:
                norm = math.hypot(target_vx, target_vy)
                target_vx, target_vy = (target_vx/norm), (target_vy/norm)
                
            target_vx *= current_max_speed
            target_vy *= current_max_speed
            
            # Smooth Accel/Decel
            self.vx += (target_vx - self.vx) * self.accel
            self.vy += (target_vy - self.vy) * self.accel
            
            # Friction when no input
            if target_vx == 0 and target_vy == 0:
                self.vx *= (1.0 - self.friction)
                self.vy *= (1.0 - self.friction)

        # ── 4. Collision ───────────────────────────────────────────────────
        if not game_map.is_wall_pixel_radius(self.x + self.vx, self.y, self.radius):
            self.x += self.vx
        if not game_map.is_wall_pixel_radius(self.x, self.y + self.vy, self.radius):
            self.y += self.vy
            
        # ── Movement Noise ──────────────────────────────────────────────────
        if abs(self.vx) > 0.5 or abs(self.vy) > 0.5:
            if self.is_sprinting:
                game_map.add_noise(self.x, self.y, 120)
            else:
                game_map.add_noise(self.x, self.y, 50)
            
        # ── 5. Rotation & Tactical Aiming ──────────────────────────────────
        mx, my = mouse_pos
        world_mx, world_my = mx + cam_x, my + cam_y
        
        # Nếu đang bắn (chuột trái), đang cầm cận chiến hoặc đứng yên thì xoay theo chuột
        if mouse_btns[0] or self.weapon == "MELEE" or (abs(self.vx) < 0.5 and abs(self.vy) < 0.5):
            self.target_angle = math.atan2(world_my - self.y, world_mx - self.x)
        else:
            # Nếu đang di chuyển mà không bắn/ngắm, quay mặt về phía đang chạy để "thấy đường"
            self.target_angle = math.atan2(self.vy, self.vx)
        
        # Torso rotates first, then head follows with a slight lag
        # But for top-down, let's make torso follow target_angle smoothly
        angle_diff = (self.target_angle - self.torso_angle + math.pi) % (2 * math.pi) - math.pi
        self.torso_angle += angle_diff * 0.15 # Torso speed
        
        angle_diff_head = (self.target_angle - self.head_angle + math.pi) % (2 * math.pi) - math.pi
        self.head_angle += angle_diff_head * 0.25 # Head is faster but lags behind torso? 
        # Actually head usually snaps faster. Let's make head snap, torso lag.
        
        self.angle = self.torso_angle # Current aim angle
        
        # ── 6. Animations (Breathing, Flinching, Lean) ─────────────────────
        self.breath_timer += BREATH_ANIM_SPEED
        self.flinch_vec[0] *= 0.85
        self.flinch_vec[1] *= 0.85
        
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            self.step_timer += WALK_ANIM_SPEED * (current_max_speed / PLAYER_SPEED)
            # Lean into movement
            self.lean_amount += (self.vx * LEAN_INTENSITY - self.lean_amount) * 0.1
        else:
            self.lean_amount *= 0.9
            self.idle_shift_timer += 1
            
        # ── 7. Combat Mechanics ────────────────────────────────────────────
        if self.ak_cooldown > 0: self.ak_cooldown -= 1
        if not hasattr(self, 'melee_cooldown'):
            self.melee_cooldown = 0
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
            
        if self.weapon == "MELEE":
            # Chuột trái vung vũ khí cận chiến khi đang chọn vũ khí cận chiến
            if mouse_btns[0] and self.melee_cooldown <= 0:
                self.perform_melee(enemies, effect_manager, sound_manager)
        else:
            # Bắn súng thông thường
            if mouse_btns[0] and self.ak_cooldown <= 0 and self.ammo > 0:
                self.shoot(world_mx, world_my, bullet_manager, effect_manager, sound_manager, game_map)
            
        # ── Focus Update ──────────────────────────────────────────────────
        self.is_focusing = q_pressed and self.focus > 5
        if self.is_focusing:
            self.focus -= FOCUS_DRAIN
        else:
            self.focus = min(FOCUS_MAX, self.focus + FOCUS_REGEN)
            
        # ── Grenade Update ────────────────────────────────────────────────
        if self.grenade_cooldown > 0: self.grenade_cooldown -= 1
        if g_pressed and self.grenade_cooldown <= 0 and self.grenades > 0:
            self.throw_grenade(world_mx, world_my, bullet_manager, sound_manager)
            
        # ── Melee Update ──────────────────────────────────────────────────
        if not hasattr(self, 'melee_cooldown'):
            self.melee_cooldown = 0
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if melee_pressed and self.melee_cooldown <= 0:
            self.perform_melee(enemies, effect_manager, sound_manager)
            
        # ── Heal Update (TAB) ─────────────────────────────────────────────
        if tab_pressed and self.hp < self.max_hp:
            if not hasattr(self, 'heal_cooldown'):
                self.heal_cooldown = 0
            if self.heal_cooldown <= 0:
                self.heal_cooldown = 60 # Cooldown to avoid healing too fast
                # Heal by 25
                self.hp = min(self.max_hp, self.hp + 25)
                sound_manager.play('pickup')
        
        if hasattr(self, 'heal_cooldown') and self.heal_cooldown > 0:
            self.heal_cooldown -= 1

        # ── Tự Động Dùng Vật Phẩm Hỗ Trợ ──
        if self.hp < self.max_hp * 0.3: # HP dưới 30%
            if "Túi Cứu Thương" in self.inventory and self.inventory["Túi Cứu Thương"] > 0:
                self.inventory["Túi Cứu Thương"] -= 1
                self.hp = min(self.max_hp, self.hp + 50)
                sound_manager.play('pickup')
                effect_manager.add_slash(self.x, self.y, self.angle, 40, (50, 255, 50))
            elif "Thuốc Hồi Phục" in self.inventory and self.inventory["Thuốc Hồi Phục"] > 0:
                self.inventory["Thuốc Hồi Phục"] -= 1
                self.hp = self.max_hp
                sound_manager.play('pickup')
                effect_manager.add_slash(self.x, self.y, self.angle, 40, (50, 255, 50))


        # ── Dash cooldown & duration update ──
        if self.dash_timer > 0:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # ── Trigger Dash ──
        if dash_pressed and self.dash_cooldown <= 0 and not self.is_dashing:
            dash_dx, dash_dy = 0.0, 0.0
            if w_pressed: dash_dy -= 1.0
            if s_pressed: dash_dy += 1.0
            if a_pressed: dash_dx -= 1.0
            if d_pressed: dash_dx += 1.0
            
            if dash_dx == 0.0 and dash_dy == 0.0:
                dash_dx = math.cos(self.angle)
                dash_dy = math.sin(self.angle)
            
            dn = math.hypot(dash_dx, dash_dy)
            if dn > 0:
                self.dash(sound_manager, dash_dx / dn, dash_dy / dn)

        # ── Update Support Drone ──
        if getattr(self, 'support_drone', None):
            self.support_drone.update(self, enemies, bullet_manager, effect_manager, sound_manager, game_map)

    def perform_melee(self, enemies, effect_manager, sound_manager):
        m_type = getattr(self, 'equipped_melee', 'PAN')
        
        # Thiết lập chỉ số cận chiến
        sweep_angle = 1.4
        knockback_dist = 0
        
        if m_type == "PAN":
            m_range = 70
            m_dmg = 40
            m_cooldown = 20
            color = (200, 200, 255) # Bạc sáng
            knockback_dist = 25
        elif m_type == "SABER":
            m_range = 90
            m_dmg = 80
            m_cooldown = 35
            color = (255, 60, 60) # Đỏ thẫm
        elif m_type == "BAT":
            m_range = 80
            m_dmg = 50
            m_cooldown = 22
            color = (255, 215, 0) # Vàng kim
            knockback_dist = 30
        elif m_type == "SWORD":
            m_range = 85
            m_dmg = 65
            m_cooldown = 24
            color = (0, 255, 255) # Xanh băng
        elif m_type == "SCYTHE":
            m_range = 115
            m_dmg = 70
            m_cooldown = 30
            color = (200, 100, 255) # Tím neon
            sweep_angle = 1.6
        else:
            m_range = 70
            m_dmg = 40
            m_cooldown = 20
            color = (200, 200, 255)
            
        self.melee_cooldown = m_cooldown
        sound_manager.play('step') # Âm thanh tạm
        
        # Tạo hiệu ứng chém visual
        effect_manager.add_slash(self.x, self.y, self.angle, m_range, color)
        
        if not enemies:
            return
            
        # Kiểm tra va chạm với enemies
        for e in enemies:
            dist = math.hypot(e.x - self.x, e.y - self.y)
            if dist < m_range + e.radius:
                angle_to_enemy = math.atan2(e.y - self.y, e.x - self.x)
                diff = (angle_to_enemy - self.angle + math.pi) % (2 * math.pi) - math.pi
                if abs(diff) < sweep_angle:
                    e.take_damage(m_dmg, effect_manager, sound_manager)
                    if knockback_dist > 0:
                        e.x += math.cos(self.angle) * knockback_dist
                        e.y += math.sin(self.angle) * knockback_dist
            
    def shoot(self, tx, ty, bullet_manager, effect_manager, sound_manager, game_map):
        if not hasattr(self, 'weapon'):
            self.weapon = "AK-47"
            
        if self.max_ammo != 9999:
            self.ammo -= 1
        
        # Noise System on shoot
        noise_rad = 550
        if self.weapon == "SHOTGUN":
            noise_rad = 650
        elif self.weapon == "SMG":
            noise_rad = 450
        elif self.weapon == "FLAMETHROWER":
            noise_rad = 300
        game_map.add_noise(self.x, self.y, noise_rad)
        
        aim_angle = math.atan2(ty - self.y, tx - self.x)
        self.angle = aim_angle
        self.torso_angle = aim_angle
        self.head_angle = aim_angle
        
        nx = math.cos(aim_angle)
        ny = math.sin(aim_angle)
        mx = self.x + nx * 18
        my = self.y + ny * 18
        
        if self.weapon == "SHOTGUN":
            sound_manager.play('shotgun_shot', maxtime=600)
            self.ak_cooldown = 40
            for i in range(5):
                spread = random.uniform(-0.2, 0.2)
                final_angle = self.angle + spread
                ftx = mx + math.cos(final_angle) * 100
                fty = my + math.sin(final_angle) * 100
                dmg = 15 * self.damage_mult
                bullet_manager.add_bullet(mx, my, ftx, fty, is_enemy=False, damage=dmg)
            self.recoil = 8.0
            effect_manager.shake.trigger(8, 5)
            
        elif self.weapon == "SMG":
            sound_manager.play('smg_shot', maxtime=90)
            self.ak_cooldown = 5
            spread = random.uniform(-0.12, 0.12)
            final_angle = self.angle + spread
            ftx = mx + math.cos(final_angle) * 100
            fty = my + math.sin(final_angle) * 100
            dmg = 12 * self.damage_mult
            bullet_manager.add_bullet(mx, my, ftx, fty, is_enemy=False, damage=dmg)
            self.recoil = 3.0
            effect_manager.shake.trigger(2, 4)

        elif self.weapon == "FLAMETHROWER":
            sound_manager.play('ak_shot', maxtime=60)
            self.ak_cooldown = FLAME_COOLDOWN
            # Bắn 4 luồng lửa có độ tản rộng
            import random as _rnd
            for i in range(4):
                spread = _rnd.uniform(-0.35, 0.35)
                final_angle = self.angle + spread
                # Tầm bắn ngắn hơn
                dist = _rnd.uniform(60, FLAME_RANGE)
                ftx = mx + math.cos(final_angle) * dist
                fty = my + math.sin(final_angle) * dist
                dmg = FLAME_DAMAGE * self.damage_mult
                flame_col = _rnd.choice([(255,80,0),(255,140,0),(255,50,0)])
                bullet_manager.add_bullet(mx, my, ftx, fty, is_enemy=False, damage=dmg, color=flame_col)
            # Sprinkle fire particles as visual flame burst
            effect_manager.add_flame_burst(mx, my, self.angle)
            self.recoil = 2.0
            effect_manager.shake.trigger(3, 3)
            
        else: # AK-47
            sound_manager.play('ak_shot', maxtime=200)
            self.ak_cooldown = AK_COOLDOWN
            spread = random.uniform(-0.05, 0.05)
            final_angle = self.angle + spread
            ftx = mx + math.cos(final_angle) * 100
            fty = my + math.sin(final_angle) * 100
            dmg = AK_DAMAGE * self.damage_mult
            bullet_manager.add_bullet(mx, my, ftx, fty, is_enemy=False, damage=dmg)
            self.recoil = 6.0
            effect_manager.shake.trigger(4, 5)

        effect_manager.add_muzzle_flash(mx, my, self.angle)
        effect_manager.add_shell(self.x, self.y, self.angle)

    def dash(self, sound_manager, dx, dy):
        self.is_dashing = True
        self.dash_timer = DASH_DURATION
        self.dash_cooldown = getattr(self, 'max_dash_cooldown', DASH_COOLDOWN)
        self.dash_dir = (dx, dy)
        sound_manager.play('step') # Use step sound for now

    def throw_grenade(self, tx, ty, bullet_manager, sound_manager):
        if self.grenades < 90:
            self.grenades -= 1
        self.grenade_cooldown = GRENADE_COOLDOWN
        sound_manager.play('grenade_throw')
        g_type = getattr(self, 'equipped_grenade', 'FRAG')
        bullet_manager.add_grenade(self.x, self.y, tx, ty, g_type)

    # ── AI AUTO-PLAY (UNBEATABLE) ───────────────────────────────────────────
    def ai_update(self, enemies, items, game_map, bullet_manager, effect_manager, sound_manager, bullets=None):
        """AI chắc chắn thắng: chỉ bắn khi thấy địch, né đạn, đi theo đường BFS xanh/đỏ."""

        # ── GODMODE ──
        regen = 8 if self.hp < self.max_hp * 0.3 else 2  # Hồi nhanh hơn khi sắp chết
        self.hp = min(self.max_hp, self.hp + regen)

        if not hasattr(self, 'ai_stuck_timer'):  self.ai_stuck_timer = 0
        if not hasattr(self, 'ai_prev_pos'):     self.ai_prev_pos = (self.x, self.y)
        if not hasattr(self, 'ai_dodge_dir'):    self.ai_dodge_dir = 1
        if not hasattr(self, 'ai_bfs_path'):     self.ai_bfs_path = []
        if not hasattr(self, 'ai_bfs_timer'):    self.ai_bfs_timer = 0
        if not hasattr(self, 'ai_mode_label'):   self.ai_mode_label = ""
        if not hasattr(self, 'ai_dodge_vec'):    self.ai_dodge_vec = (0.0, 0.0)
        if not hasattr(self, 'ai_dodge_frames'): self.ai_dodge_frames = 0
        if not hasattr(self, 'ai_pos_hist'):     self.ai_pos_hist = []
        if not hasattr(self, 'ai_avoid_tiles'):  self.ai_avoid_tiles = {}

        # Decay avoid tiles timers
        to_remove = []
        for tile in self.ai_avoid_tiles:
            self.ai_avoid_tiles[tile] -= 1
            if self.ai_avoid_tiles[tile] <= 0:
                to_remove.append(tile)
        for tile in to_remove:
            del self.ai_avoid_tiles[tile]

        alive = [e for e in enemies if e.alive]

        # ── 1. BULLET & ENEMY EVASION (NÉ ĐẠN & NÉ ĐỊCH) ──────────────────────
        evade_x, evade_y = 0.0, 0.0
        bullet_threats = 0
        DODGE_RADIUS = 150
        if bullets:
            for b in bullets:
                if not getattr(b, 'alive', True): continue
                if not getattr(b, 'is_enemy', False): continue  # Chỉ né đạn kẻ địch
                bd = math.hypot(b.x - self.x, b.y - self.y)
                if bd > DODGE_RADIUS: continue
                # Kiểm tra xem đạn có đang bay về phía người chơi không
                to_px = self.x - b.x
                to_py = self.y - b.y
                dot = b.vx * to_px + b.vy * to_py
                if dot <= 0: continue  # Đạn đang bay xa dần

                bullet_threats += 1
                perp1_x, perp1_y = -b.vy, b.vx
                perp2_x, perp2_y = b.vy, -b.vx
                sp = math.hypot(perp1_x, perp1_y)
                if sp > 0:
                    perp1_x /= sp; perp1_y /= sp
                    perp2_x /= sp; perp2_y /= sp

                # Chọn hướng né không va tường
                if not game_map.is_wall_pixel_radius(self.x + perp1_x * 20, self.y + perp1_y * 20, self.radius):
                    evade_x += perp1_x; evade_y += perp1_y
                else:
                    evade_x += perp2_x; evade_y += perp2_y

        # Né Địch khi địch ở quá gần
        ENEMY_SAFE_DIST = 140
        enemy_threats = 0
        for e in alive:
            ed = math.hypot(self.x - e.x, self.y - e.y)
            if ed < ENEMY_SAFE_DIST:
                enemy_threats += 1
                # Lực đẩy tỷ lệ nghịch với khoảng cách
                weight = (ENEMY_SAFE_DIST - ed) / ENEMY_SAFE_DIST
                if ed < 65:  # Nếu kẻ địch áp sát quá gần
                    weight *= 2.5
                dx = self.x - e.x
                dy = self.y - e.y
                if ed > 0:
                    evade_x += (dx / ed) * weight * 1.5
                    evade_y += (dy / ed) * weight * 1.5

        is_evading = False
        if bullet_threats > 0 or enemy_threats > 0:
            el = math.hypot(evade_x, evade_y)
            if el > 0:
                evade_x /= el; evade_y /= el
                spd = PLAYER_SPEED * 1.3
                # Di chuyển trượt theo tường nếu hướng đi trực diện bị chặn
                for angle_offset in [0, 0.4, -0.4, 0.8, -0.8, 1.2, -1.2]:
                    a_ev = math.atan2(evade_y, evade_x) + angle_offset
                    vx_ev = math.cos(a_ev) * spd
                    vy_ev = math.sin(a_ev) * spd
                    
                    if not game_map.is_wall_pixel_radius(self.x + vx_ev, self.y + vy_ev, self.radius):
                        self.x += vx_ev
                        self.y += vy_ev
                        is_evading = True
                        break
                    else:
                        # Slide along walls while evading
                        moved_x = False
                        moved_y = False
                        if not game_map.is_wall_pixel_radius(self.x + vx_ev, self.y, self.radius):
                            self.x += vx_ev
                            moved_x = True
                        if not game_map.is_wall_pixel_radius(self.x, self.y + vy_ev, self.radius):
                            self.y += vy_ev
                            moved_y = True
                        if moved_x or moved_y:
                            is_evading = True
                            break

        def has_los(tx, ty):
            dist = math.hypot(tx - self.x, ty - self.y)
            if dist <= 24:  # Rất gần thì coi như thấy
                return True
            
            # Tránh tự va chạm ngay sát người chơi hoặc kẻ địch (bỏ qua 12px đầu và cuối)
            start_dist = 12
            end_dist = dist - 12
            if start_dist >= end_dist:
                return True
                
            # Quét dọc theo đường đạn với bước nhảy ngắn (4px)
            step_size = 4
            steps = int((end_dist - start_dist) / step_size) + 1
            if steps < 1:
                steps = 1
                
            dx = (tx - self.x) / dist
            dy = (ty - self.y) / dist
            
            for i in range(steps + 1):
                t_dist = start_dist + (end_dist - start_dist) * (i / steps)
                rx = self.x + dx * t_dist
                ry = self.y + dy * t_dist
                # Kiểm tra vật cản (Wall, Cover, Barrel, Console, Laser) với bán kính an toàn r=8px
                if game_map.is_wall_pixel_radius(rx, ry, 8):
                    return False
            return True


        # Tìm kẻ địch gần nhất trong tầm nhìn
        visible_enemy = None
        min_vd = float('inf')
        for e in alive:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < 450 and has_los(e.x, e.y):
                if d < min_vd:
                    min_vd = d
                    visible_enemy = e

        # ── 3. CHỌN MỤC TIÊU BFS ──────────────────────────────────────────────
        # Ưu tiên: đỏ (máu) → vàng (đạn) → kẻ địch/Boss → xanh (lối thoát)
        bfs_target_px, bfs_target_py = None, None
        self.ai_mode_label = ""

        if self.hp < self.max_hp * 0.5:
            h_targets = [(item.x, item.y) for item in items if getattr(item, 'type', None) == ITEM_HEALTH]
            if h_targets:
                best = min(h_targets, key=lambda p: math.hypot(p[0]-self.x, p[1]-self.y))
                bfs_target_px, bfs_target_py = best
                self.ai_mode_label = "RED"

        if bfs_target_px is None and self.ammo <= 0:
            a_targets = [(item.x, item.y) for item in items if getattr(item, 'type', None) == ITEM_AMMO]
            if a_targets:
                best = min(a_targets, key=lambda p: math.hypot(p[0]-self.x, p[1]-self.y))
                bfs_target_px, bfs_target_py = best
                self.ai_mode_label = "YELLOW"

        # Ưu tiên di chuyển tiếp theo: Chiến đấu với kẻ địch trong tầm nhìn (bao gồm cả Boss)
        if bfs_target_px is None:
            if visible_enemy:
                dist_to_enemy = min_vd
                COMBAT_DIST = 180
                if dist_to_enemy < COMBAT_DIST * 0.6:
                    angle_away = math.atan2(self.y - visible_enemy.y, self.x - visible_enemy.x)
                    bfs_target_px = self.x + math.cos(angle_away) * COMBAT_DIST
                    bfs_target_py = self.y + math.sin(angle_away) * COMBAT_DIST
                elif dist_to_enemy > COMBAT_DIST * 1.4:
                    angle_in = math.atan2(visible_enemy.y - self.y, visible_enemy.x - self.x)
                    bfs_target_px = visible_enemy.x - math.cos(angle_in) * COMBAT_DIST
                    bfs_target_py = visible_enemy.y - math.sin(angle_in) * COMBAT_DIST
                else:
                    if not hasattr(self, "ai_orbit_angle"): self.ai_orbit_angle = 0.0
                    self.ai_orbit_angle += 0.04
                    bfs_target_px = visible_enemy.x + math.cos(self.ai_orbit_angle) * COMBAT_DIST
                    bfs_target_py = visible_enemy.y + math.sin(self.ai_orbit_angle) * COMBAT_DIST
                self.ai_mode_label = "RED" # Đang chiến đấu
            else:
                # Không quét thấy địch ở gần -> Đi tới điểm đích (Boss hoặc Lối thoát)
                # Săn Boss nếu có bất kỳ Boss nào còn sống
                bosses = [e for e in alive if getattr(e, 'type', '') == 'boss']
                if bosses:
                    closest_boss = min(bosses, key=lambda b: math.hypot(b.x - self.x, b.y - self.y))
                    bfs_target_px = closest_boss.x
                    bfs_target_py = closest_boss.y
                    self.ai_mode_label = "RED"  # Săn Boss
                else:
                    # Đi tới Lối thoát
                    for gy in range(game_map.height):
                        for gx in range(game_map.width):
                            if game_map.grid[gy][gx] == TILE_EXIT:
                                bfs_target_px = gx * TILE_SIZE + TILE_SIZE // 2
                                bfs_target_py = gy * TILE_SIZE + TILE_SIZE // 2
                                break
                        if bfs_target_px: break
                    self.ai_mode_label = "CYAN"

        # ── 4. BFS PATH FOLLOW ───────────────────────────────────────────────
        self.ai_pos_hist.append((self.x, self.y))
        if len(self.ai_pos_hist) > 40: self.ai_pos_hist.pop(0)
        really_stuck = False
        if len(self.ai_pos_hist) >= 30:
            h30 = self.ai_pos_hist[-30:]
            travel = sum(math.hypot(h30[j][0]-h30[j-1][0], h30[j][1]-h30[j-1][1]) for j in range(1, len(h30)))
            if travel < 8:
                really_stuck = True
                self.ai_pos_hist.clear()
                self.ai_bfs_path = []
                self.ai_bfs_timer = 0

        self.ai_bfs_timer -= 1
        algo = getattr(self, 'ai_algorithm', 'BFS')
        if algo == "DFS":
            need_replan = (not self.ai_bfs_path) or really_stuck
        else:
            need_replan = (self.ai_bfs_timer <= 0) or really_stuck

        if need_replan:
            self.ai_bfs_timer = 20
            self.ai_bfs_path = []
            if bfs_target_px:
                sx = int(self.x // TILE_SIZE)
                sy = int(self.y // TILE_SIZE)
                
                if game_map.get_tile(sx, sy) in (TILE_WALL, TILE_COVER, TILE_BARREL):
                    found_free = False
                    for r in range(1, 6):
                        for ddx in range(-r, r+1):
                            for ddy in range(-r, r+1):
                                if abs(ddx)==r or abs(ddy)==r:
                                    fx, fy = sx+ddx, sy+ddy
                                    t2 = game_map.get_tile(fx, fy)
                                    if t2 not in (TILE_WALL, TILE_COVER, TILE_BARREL):
                                        sx, sy = fx, fy
                                        self.x = sx*TILE_SIZE + TILE_SIZE//2
                                        self.y = sy*TILE_SIZE + TILE_SIZE//2
                                        found_free = True; break
                            if found_free: break
                        if found_free: break

                algo = getattr(self, 'ai_algorithm', 'BFS')
                path = game_map.find_path_to_point_list(self.x, self.y, [(bfs_target_px, bfs_target_py)], algorithm=algo, avoid_tiles=set(self.ai_avoid_tiles.keys()))
                if path:
                    # Bỏ điểm xuất phát (ô hiện tại của nhân vật) để tránh đi giật lùi về tâm ô hiện tại khi tìm lại đường
                    if len(path) > 1:
                        path = path[1:]
                    pixel_path = [(tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2) for tx, ty in path]
                    self.ai_bfs_path = ai_logic.smooth_pixel_path(pixel_path, game_map, radius_px=self.radius + 2)

        dx, dy, dist_move = 0.0, 0.0, 0.0
        if not is_evading:
            # Di chuyển theo BFS path
            move_tx, move_ty = bfs_target_px or self.x, bfs_target_py or self.y
            if self.ai_bfs_path:
                while self.ai_bfs_path and math.hypot(self.ai_bfs_path[0][0] - self.x, self.ai_bfs_path[0][1] - self.y) < 16:
                    self.ai_bfs_path.pop(0)
                if self.ai_bfs_path:
                    move_tx, move_ty = self.ai_bfs_path[0]

            dx = move_tx - self.x
            dy = move_ty - self.y
            dist_move = math.hypot(dx, dy)
            speed = PLAYER_SPEED * 1.15

            if dist_move > 4:
                ndx, ndy = dx / dist_move, dy / dist_move
                moved = False
                angles = [0, 0.2, -0.2, 0.4, -0.4, 0.6, -0.6,
                          0.8, -0.8, 1.0, -1.0, 1.3, -1.3,
                          math.pi*0.6, math.pi*0.8, math.pi]
                for ao in angles:
                    a2 = math.atan2(ndy, ndx) + ao
                    vx = math.cos(a2) * speed
                    vy = math.sin(a2) * speed
                    
                    # Check moving both axes together
                    if not game_map.is_wall_pixel_radius(self.x + vx, self.y + vy, self.radius):
                        self.x += vx
                        self.y += vy
                        self.ai_stuck_timer = max(0, self.ai_stuck_timer - 1)
                        moved = True
                        break
                    else:
                        # Slide along walls: check axes independently
                        moved_x = False
                        moved_y = False
                        if not game_map.is_wall_pixel_radius(self.x + vx, self.y, self.radius):
                            self.x += vx
                            moved_x = True
                        if not game_map.is_wall_pixel_radius(self.x, self.y + vy, self.radius):
                            self.y += vy
                            moved_y = True
                        if moved_x or moved_y:
                            self.ai_stuck_timer = max(0, self.ai_stuck_timer - 1)
                            moved = True
                            break
                # Quick stuck detection: if we tried to move but actually covered almost no distance
                dist_actually_moved = math.hypot(self.x - self.ai_prev_pos[0], self.y - self.ai_prev_pos[1])
                if dist_move > 4 and dist_actually_moved < 0.8:
                    if not hasattr(self, 'ai_stuck_frame_count'): self.ai_stuck_frame_count = 0
                    self.ai_stuck_frame_count += 1
                    if self.ai_stuck_frame_count >= 5: # If stuck for 5 consecutive frames
                        self.ai_stuck_frame_count = 0
                        # Mark this tile in avoid_tiles so we plan a path around it
                        avoid_tx = int(move_tx // TILE_SIZE)
                        avoid_ty = int(move_ty // TILE_SIZE)
                        self.ai_avoid_tiles[(avoid_tx, avoid_ty)] = 120 # avoid for 2 seconds
                        self.ai_bfs_path = []
                        self.ai_bfs_timer = 0
                else:
                    self.ai_stuck_frame_count = 0

                if not moved:
                    self.ai_stuck_timer += 1
                    if self.ai_stuck_timer > 3:
                        avoid_x = int(move_tx // TILE_SIZE)
                        avoid_y = int(move_ty // TILE_SIZE)
                        self.ai_avoid_tiles[(avoid_x, avoid_y)] = 180
                        self.ai_bfs_path = []
                        self.ai_bfs_timer = 0
                    if self.ai_stuck_timer > 12:
                        self.ai_stuck_timer = 0
                        self.ai_bfs_path = []
                        self.ai_bfs_timer = 0
                        tx_c = int(self.x // TILE_SIZE)
                        ty_c = int(self.y // TILE_SIZE)
                        for r in range(1, 8):
                            escaped = False
                            for ddx in range(-r, r+1):
                                for ddy in range(-r, r+1):
                                    if abs(ddx)==r or abs(ddy)==r:
                                        fx2, fy2 = tx_c+ddx, ty_c+ddy
                                        t3 = game_map.get_tile(fx2, fy2)
                                        if t3 not in (TILE_WALL, TILE_COVER, TILE_BARREL):
                                            self.x = fx2*TILE_SIZE + TILE_SIZE//2
                                            self.y = fy2*TILE_SIZE + TILE_SIZE//2
                                            escaped = True; break
                                if escaped: break
                            if escaped: break
        else:
            dx, dy = evade_x, evade_y
            dist_move = 10.0

        self.ai_prev_pos = (self.x, self.y)

        # ── 4. NHẮM + BẮN CHỈ KHI THẤY ĐỊCH ────────────────────────────────
        if visible_enemy:
            self.angle = math.atan2(visible_enemy.y - self.y, visible_enemy.x - self.x)
            self.torso_angle = self.angle
            self.head_angle  = self.angle
            if self.ak_cooldown > 0: self.ak_cooldown -= 1
            if self.ak_cooldown <= 0 and self.ammo > 0:
                self.shoot(visible_enemy.x, visible_enemy.y,
                           bullet_manager, effect_manager, sound_manager, game_map)
            # Ném lựu đạn khi địch cụm
            if self.grenade_cooldown > 0: self.grenade_cooldown -= 1
            nearby = sum(1 for e in alive
                         if math.hypot(e.x-visible_enemy.x, e.y-visible_enemy.y) < 100)
            if nearby >= 2 and self.grenades > 0 and self.grenade_cooldown <= 0 and min_vd < 300:
                self.throw_grenade(visible_enemy.x, visible_enemy.y, bullet_manager, sound_manager)
        else:
            # Không thấy địch trong tầm nhìn → Quét điểm địch gần nhất (nếu có kẻ địch còn sống)
            scan_target = None
            if alive:
                scan_target = min(alive, key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
            
            if scan_target:
                self.angle = math.atan2(scan_target.y - self.y, scan_target.x - self.x)
                self.torso_angle = self.angle
                self.head_angle  = self.angle
            elif dist_move > 4:
                # Nếu không còn kẻ địch nào trên bản đồ → nhìn về hướng đang đi
                self.angle = math.atan2(dy, dx)
                self.torso_angle = self.angle
                self.head_angle  = self.angle
                
            if self.ak_cooldown > 0: self.ak_cooldown -= 1
            if self.grenade_cooldown > 0: self.grenade_cooldown -= 1

        # Auto reload khi hết đạn
        if self.ammo <= 0:
            self.ammo = self.max_ammo
            sound_manager.play('reload')

        # Animation
        self.breath_timer += BREATH_ANIM_SPEED
        self.step_timer   += WALK_ANIM_SPEED
        self.flinch_vec[0] *= 0.85
        self.flinch_vec[1] *= 0.85
        if self.under_fire_timer > 0: self.under_fire_timer -= 1
        if hasattr(self, 'heal_cooldown') and self.heal_cooldown > 0: self.heal_cooldown -= 1

        # ── Update Support Drone ──
        if getattr(self, 'support_drone', None):
            self.support_drone.update(self, enemies, bullet_manager, effect_manager, sound_manager, game_map)

    def take_damage(self, amount, effect_manager, sound_manager):
        if self.is_dashing: return # Invulnerable while dashing
        
        # Check drone shield
        if getattr(self, 'support_drone', None) and self.support_drone.shield_active:
            amount = int(amount * 0.4) # 60% damage reduction
            if amount <= 0:
                return

        sound_manager.play('hurt')
        effect_manager.add_blood(self.x, self.y)
        effect_manager.shake.trigger(10, 15)
        
        # Tactical: Suppression & Flinch
        self.under_fire_timer = 90 # 1.5 seconds of nervousness
        self.flinch_vec = [random.uniform(-1, 1) * FLINCH_INTENSITY, random.uniform(-1, 1) * FLINCH_INTENSITY]
        
        if self.armor > 0:
            if self.armor >= amount:
                self.armor -= amount
                return
            else:
                amount -= self.armor
                self.armor = 0
                
        self.hp -= amount
        if self.hp < 0:
            self.hp = 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def draw(self, screen, cam_x, cam_y, effect_manager=None, level=1):
        # ── 1. Calculate Offsets & Scale ───────────────────────────────────
        # Flinch and breathing effects
        fx, fy = self.flinch_vec
        breath_scale = 1.0 + math.sin(self.breath_timer) * 0.02
        
        sx = int(self.x - cam_x + fx)
        sy = int(self.y - cam_y + fy)
        
        # Determine movement direction for legs
        is_moving = abs(self.vx) > 0.5 or abs(self.vy) > 0.5
        move_dir = math.atan2(self.vy, self.vx) if is_moving else self.torso_angle

        # ── Hiệu ứng bước chân — sinh dấu chân mỗi nửa chu kỳ bước ──────
        if not hasattr(self, '_last_step_phase'):
            self._last_step_phase = 0
            self._foot_side = 1
        if is_moving and effect_manager is not None:
            step_phase = math.sin(self.step_timer * 8)
            # Khi phase đổi dấu (bước chân chạm đất)
            if self._last_step_phase * step_phase < 0:
                self._foot_side *= -1
                # Vị trí dấu chân: lùi về phía sau nhân vật một chút
                back_x = self.x - math.cos(move_dir) * 8
                back_y = self.y - math.sin(move_dir) * 8
                effect_manager.add_footstep(back_x, back_y, move_dir, self._foot_side, level)
            self._last_step_phase = step_phase

        # ── 2. Bóng đổ 3D dưới nhân vật ──────────────────────────────────
        shadow_w = int(self.radius * 2.2)
        shadow_h = int(self.radius * 1.1)
        shadow_surf = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90),
                            (0, shadow_h // 2, shadow_w * 2, shadow_h))
        screen.blit(shadow_surf, (sx - shadow_w, sy - shadow_h // 2 + 10))

        # ── 3. Draw Legs (Tactical Swing) ──────────────────────────────────
        swing = math.sin(self.step_timer * 8) * 12 if is_moving else 0
        side = 7
        
        # Tactical: Lean into movement
        lean_x = self.vx * 2
        lean_y = self.vy * 2
        
        # Luôn vẽ chân (bước chân) ở dưới nhân vật
        for i in [-1, 1]: # Left/Right legs
            s = swing if i == 1 else -swing
            lx = sx + math.cos(move_dir) * s + math.cos(move_dir + i * math.pi/2) * side
            ly = sy + math.sin(move_dir) * s + math.sin(move_dir + i * math.pi/2) * side
            pygame.draw.circle(screen, (20, 25, 20), (int(lx), int(ly)), 6) # Boot
            pygame.draw.circle(screen, (40, 50, 40), (int(lx), int(ly)), 4) # Detail
        # ── 3. Draw Body (Torso) ───────────────────────────────────────────
        if hasattr(self, 'image') and self.image is not None:
            # Scale for breathing
            size = int(80 * breath_scale)
            scaled_img = pygame.transform.scale(self.image, (size, size))
            
            # Hiệu ứng bước chân (nhấp nhô và lắc lư nhẹ)
            bob_y = 0
            wobble_angle = 0
            if is_moving:
                bob_y = abs(math.sin(self.step_timer * 8)) * 4
                wobble_angle = math.sin(self.step_timer * 4) * 3
                
            # Nhân vật đứng thẳng, chỉ lật trái/phải
            final_img = scaled_img
            
            # Nếu nhân vật đang nhìn về bên trái (cos < 0), lật ngang ảnh
            if math.cos(self.angle) < 0:
                final_img = pygame.transform.flip(final_img, True, False)
                
            # Chỉ kết hợp hiệu ứng lắc lư khi bước đi (giữ nhân vật đứng thẳng khi đi lên/xuống)
            rotated_img = pygame.transform.rotate(final_img, wobble_angle)
            
            rect = rotated_img.get_rect(center=(sx + lean_x, sy + lean_y - bob_y))
            screen.blit(rotated_img, rect.topleft)
        else:
            pygame.draw.circle(screen, PLAYER_DARK, (sx, sy), int(self.radius * breath_scale))
            
        # ── 4. Draw Aiming & Laser (Head/Gun) ──────────────────────────────
        nx = math.cos(self.angle)
        ny = math.sin(self.angle)
        
        # Laser Sight (Tactical)
        if self.is_aiming:
            laser_end = (sx + nx * 500, sy + ny * 500)
            pygame.draw.line(screen, (255, 0, 0, 100), (sx, sy), laser_end, 1)
            
        # Vẽ vũ khí cận chiến trên tay nhân vật nếu đang chọn
        if self.weapon == "MELEE":
            m_type = getattr(self, 'equipped_melee', 'PAN')
            if m_type == "PAN":
                color = (120, 120, 130)
                hx = sx + nx * 22
                hy = sy + ny * 22
                pygame.draw.line(screen, (50, 50, 50), (sx, sy), (hx, hy), 4)
                px = sx + nx * 32
                py = sy + ny * 32
                pygame.draw.circle(screen, color, (int(px), int(py)), 8)
                pygame.draw.circle(screen, (30, 30, 30), (int(px), int(py)), 6)
            elif m_type == "SABER":
                color = (255, 60, 60)
                hx = sx + nx * 20
                hy = sy + ny * 20
                bx = sx + nx * 45
                by = sy + ny * 45
                pygame.draw.line(screen, (255, 255, 255), (hx, hy), (bx, by), 4)
                pygame.draw.line(screen, color, (hx, hy), (bx, by), 2)
            elif m_type == "BAT":
                color = (200, 170, 40)
                hx = sx + nx * 20
                hy = sy + ny * 20
                bx = sx + nx * 40
                by = sy + ny * 40
                pygame.draw.line(screen, (100, 80, 40), (sx, sy), (hx, hy), 3)
                pygame.draw.line(screen, color, (hx, hy), (bx, by), 6)
            elif m_type == "SWORD":
                color = (0, 255, 255)
                hx = sx + nx * 20
                hy = sy + ny * 20
                bx = sx + nx * 45
                by = sy + ny * 45
                tx = -ny
                ty = nx
                pygame.draw.line(screen, (100, 100, 100), (hx - tx*8, hy - ty*8), (hx + tx*8, hy + ty*8), 3)
                pygame.draw.line(screen, (255, 255, 255), (hx, hy), (bx, by), 4)
                pygame.draw.line(screen, color, (hx, hy), (bx, by), 2)
            elif m_type == "SCYTHE":
                color = (200, 100, 255)
                hx = sx + nx * 20
                hy = sy + ny * 20
                bx = sx + nx * 42
                by = sy + ny * 42
                pygame.draw.line(screen, (50, 40, 30), (sx, sy), (bx, by), 4)
                tx = -ny
                ty = nx
                pygame.draw.line(screen, color, (bx, by), (bx + tx*20 + nx*5, by + ty*20 + ny*5), 4)
                pygame.draw.line(screen, (255, 255, 255), (bx, by), (bx + tx*20 + nx*5, by + ty*20 + ny*5), 2)
            
        # Gun (Coupled to Torso but pointing to mouse)
        if self.weapon != "MELEE":
            # Select color, length, thickness based on weapon
            gun_color = (60, 60, 60) # Default
            gun_len = 24
            gun_thick = 4
            
            w = self.weapon
            if w == "AK-47":
                gun_color = (139, 69, 19) # Brown/Wood
                gun_len = 26
                gun_thick = 5
            elif w == "SHOTGUN":
                gun_color = (80, 80, 90) # Steel
                gun_len = 24
                gun_thick = 7
            elif w == "SMG":
                gun_color = (40, 40, 40) # Dark grey
                gun_len = 20
                gun_thick = 4
            elif w == "FLAMETHROWER":
                gun_color = (200, 50, 20) # Red
                gun_len = 25
                gun_thick = 6
            elif w == "SNIPER":
                gun_color = (50, 70, 50) # Olive green
                gun_len = 34
                gun_thick = 4
            elif w == "MINIGUN":
                gun_color = (180, 160, 40) # Brass/Gold
                gun_len = 28
                gun_thick = 8
            elif w == "LASER_RIFLE":
                gun_color = (0, 180, 255) # Cyan
                gun_len = 28
                gun_thick = 5
            elif w == "PLASMA_GUN":
                gun_color = (50, 220, 100) # Lime green
                gun_len = 26
                gun_thick = 6
                
            gx = sx + nx * gun_len + lean_x
            gy = sy + ny * gun_len + lean_y
            
            # Draw a black shadow/outline line first
            pygame.draw.line(screen, (10, 10, 10), (sx + lean_x, sy + lean_y), (gx, gy), gun_thick + 2)
            # Draw the main colored barrel
            pygame.draw.line(screen, gun_color, (sx + lean_x, sy + lean_y), (gx, gy), gun_thick)
            
            # Special features:
            if w == "SNIPER":
                # Scope
                sc_x = sx + nx * 16 + lean_x
                sc_y = sy + ny * 16 + lean_y
                pygame.draw.circle(screen, (20, 20, 20), (int(sc_x), int(sc_y)), 4)
            elif w == "FLAMETHROWER":
                # Gas tank
                gt_x = sx + nx * 10 + lean_x
                gt_y = sy + ny * 10 + lean_y
                pygame.draw.circle(screen, (245, 120, 30), (int(gt_x), int(gt_y)), 5)

        # Head (Independent Rotation) - Only when using fallback shapes
        if not hasattr(self, 'image') or self.image is None:
            head_x = sx + math.cos(self.head_angle) * 3 + lean_x
            head_y = sy + math.sin(self.head_angle) * 3 + lean_y
            pygame.draw.circle(screen, (50, 70, 50), (int(head_x), int(head_y)), 9) # Helmet
            pygame.draw.circle(screen, (80, 100, 80), (int(head_x), int(head_y)), 7) # Detail

        # ── Draw Support Drone ──
        if getattr(self, 'support_drone', None):
            self.support_drone.draw(screen, cam_x, cam_y, self)


class SupportDrone:
    def __init__(self, owner):
        self.owner = owner
        self.x = float(owner.x)
        self.y = float(owner.y - 40)
        self.hover_timer = 0.0
        self.angle = 0.0
        self.shoot_cooldown = 0
        self.healing_cooldown = 0
        self.ammo_cooldown = 0
        self.shield_active = False
        self.shield_timer = 0
        
        # Load drone image
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(base_dir, "ANH", "drone.png")
        self.image = None
        if os.path.exists(img_path):
            try:
                img = pygame.image.load(img_path).convert_alpha()
                bg_color = img.get_at((0, 0))
                img.lock()
                w, h = img.get_size()
                for x_img in range(w):
                    for y_img in range(h):
                        c = img.get_at((x_img, y_img))
                        if abs(c[0]-bg_color[0]) + abs(c[1]-bg_color[1]) + abs(c[2]-bg_color[2]) < 45 or (c[0] < 15 and c[1] < 15 and c[2] < 15):
                            img.set_at((x_img, y_img), (0, 0, 0, 0))
                img.unlock()
                self.image = pygame.transform.smoothscale(img, (28, 28))
            except Exception as e:
                print(f"Error loading drone image: {e}")

    def update(self, player, enemies, bullet_manager, effect_manager, sound_manager, game_map):
        from effects import Particle

        # Follow player with smooth trailing interpolation
        self.hover_timer += 0.05
        bob_y = math.sin(self.hover_timer) * 6
        bob_x = math.cos(self.hover_timer * 1.5) * 4
        
        # drone coordinates relative to player face angle
        target_x = player.x - math.cos(player.angle) * 40 + bob_x
        target_y = player.y - math.sin(player.angle) * 40 + bob_y
        
        self.x += (target_x - self.x) * 0.1
        self.y += (target_y - self.y) * 0.1
        
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.healing_cooldown > 0:
            self.healing_cooldown -= 1
        if self.ammo_cooldown > 0:
            self.ammo_cooldown -= 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

        alive_enemies = [e for e in enemies if e.alive] if enemies else []
        target_enemy = None
        if alive_enemies:
            target_enemy = min(alive_enemies, key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
            dist = math.hypot(target_enemy.x - self.x, target_enemy.y - self.y)
            if dist < 300:
                self.angle = math.atan2(target_enemy.y - self.y, target_enemy.x - self.x)
            else:
                self.angle = player.angle
                target_enemy = None
        else:
            self.angle = player.angle

        # ── Emergency Support Trigger 1: Low Health ──
        if player.hp < player.max_hp * 0.35 and self.healing_cooldown <= 0:
            has_heal = False
            heal_type = None
            if hasattr(player, 'inventory'):
                if player.inventory.get("Túi Cứu Thương", 0) > 0:
                    heal_type = "Túi Cứu Thương"
                    has_heal = True
                elif player.inventory.get("Thuốc Hồi Phục", 0) > 0:
                    heal_type = "Thuốc Hồi Phục"
                    has_heal = True
                elif player.inventory.get("Nước Uống Năng Lượng", 0) > 0:
                    heal_type = "Nước Uống Năng Lượng"
                    has_heal = True
            
            if has_heal and heal_type:
                player.inventory[heal_type] -= 1
                heal_amt = 50 if heal_type == "Túi Cứu Thương" else (100 if heal_type == "Thuốc Hồi Phục" else 20)
                player.hp = min(player.max_hp, player.hp + heal_amt)
                self.healing_cooldown = 180
                sound_manager.play('pickup')
                
                for _ in range(12):
                    ang = random.uniform(0, math.pi*2)
                    sp = random.uniform(2, 4)
                    effect_manager.particles.append(Particle(player.x, player.y, math.cos(ang)*sp, math.sin(ang)*sp, (100, 255, 100), random.randint(2, 5), 40))
                
                effect_manager.add_floating_text(player.x, player.y - 30, f"DRONE: DÙNG {heal_type.upper()}! (+{heal_amt} HP)", (100, 255, 100))
            else:
                # Shield Barrier
                player.hp = min(player.max_hp, player.hp + 20)
                player.armor = min(player.max_armor, player.armor + 15)
                self.healing_cooldown = 360
                self.shield_active = True
                self.shield_timer = 120
                sound_manager.play('pickup')
                effect_manager.add_floating_text(player.x, player.y - 30, "DRONE: LÁ CHẮN NANO KHẨN CẤP! (+HP & ARMOR)", (0, 255, 255))
                
                for _ in range(12):
                    ang = random.uniform(0, math.pi*2)
                    sp = random.uniform(1.5, 3.5)
                    effect_manager.particles.append(Particle(player.x, player.y, math.cos(ang)*sp, math.sin(ang)*sp, (0, 255, 255), random.randint(2, 4), 40))

        # ── Emergency Support Trigger 2: Out of Ammo ──
        if player.ammo <= 0 and self.ammo_cooldown <= 0:
            player.ammo = min(player.max_ammo, player.ammo + 40)
            self.ammo_cooldown = 240
            sound_manager.play('reload')
            effect_manager.add_floating_text(player.x, player.y - 30, "DRONE: TIẾP TẾ ĐẠN! (+40 AMMO)", (255, 200, 0))
            
            for _ in range(8):
                ang = random.uniform(0, math.pi*2)
                sp = random.uniform(1, 3)
                effect_manager.particles.append(Particle(player.x, player.y, math.cos(ang)*sp, math.sin(ang)*sp, (255, 200, 0), random.randint(1, 3), 30))

        # ── Combat Support Trigger 3: Shoot lasers ──
        enemies_in_range = [e for e in alive_enemies if math.hypot(e.x - player.x, e.y - player.y) < 250]
        is_heavily_pressed = len(enemies_in_range) >= 2 or player.hp < player.max_hp * 0.4 or player.ammo <= 10
        fire_cooldown_max = 12 if is_heavily_pressed else 25
        
        if target_enemy and self.shoot_cooldown <= 0:
            self.shoot_cooldown = fire_cooldown_max
            sound_manager.play('smg_shot', maxtime=80)
            aim_angle = math.atan2(target_enemy.y - self.y, target_enemy.x - self.x)
            nx = math.cos(aim_angle)
            ny = math.sin(aim_angle)
            
            bullet_manager.add_bullet(
                self.x, self.y, 
                self.x + nx * 100, self.y + ny * 100, 
                is_enemy=False, 
                damage=10, 
                color=(0, 255, 255)
            )
            effect_manager.add_muzzle_flash(self.x, self.y, aim_angle)

    def draw(self, screen, cam_x, cam_y, player):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        px = int(player.x - cam_x)
        py = int(player.y - cam_y)
        
        # 1. Connection beam
        pygame.draw.line(screen, (0, 255, 255, 50), (sx, sy), (px, py), 1)
        
        # 2. Draw shield bubble around player if active
        if self.shield_active:
            shield_rad = int(player.radius + 15 + math.sin(pygame.time.get_ticks() / 100.0) * 3)
            shield_surf = pygame.Surface((shield_rad * 2 + 4, shield_rad * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0, 255, 255, 25), (shield_rad + 2, shield_rad + 2), shield_rad)
            pygame.draw.circle(shield_surf, (0, 255, 255, 140), (shield_rad + 2, shield_rad + 2), shield_rad, 2)
            screen.blit(shield_surf, (px - shield_rad - 2, py - shield_rad - 2))

        # 3. Draw drone body
        if self.image:
            rotated = pygame.transform.rotate(self.image, math.degrees(-self.angle))
            rect = rotated.get_rect(center=(sx, sy))
            screen.blit(rotated, rect.topleft)
        else:
            # Procedural drawing
            pygame.draw.circle(screen, (80, 100, 120), (sx, sy), 6)
            pygame.draw.circle(screen, (0, 255, 255), (sx, sy), 3)
            # Propeller pads
            for angle_offset in [-math.pi/4, math.pi/4, 3*math.pi/4, -3*math.pi/4]:
                px_prop = sx + int(math.cos(self.angle + angle_offset) * 10)
                py_prop = sy + int(math.sin(self.angle + angle_offset) * 10)
                pygame.draw.line(screen, (50, 60, 70), (sx, sy), (px_prop, py_prop), 2)
                pygame.draw.circle(screen, (0, 255, 255), (px_prop, py_prop), 3, 1)

