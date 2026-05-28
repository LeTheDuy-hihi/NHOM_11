import pygame
import math
from constants import *


class Bullet:
    def __init__(self, x, y, target_x, target_y, is_enemy=False, color=None):
        self.x, self.y = x, y
        self.is_enemy = is_enemy
        self.custom_color = color  # None = default
        
        # Calculate angle and velocity
        angle = math.atan2(target_y - y, target_x - x)
        speed = ENEMY_BULLET_SPD if is_enemy else BULLET_SPEED
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.alive = True
        self.damage = 0  # Set by shooter
        
        # Trail history
        self.history = []

    def update(self):
        self.history.append((self.x, self.y))
        if len(self.history) > 3:
            self.history.pop(0)
            
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        
        color = self.custom_color if self.custom_color else (ORANGE if not self.is_enemy else RED)
        
        # Draw trail
        if len(self.history) > 1:
            pts = [(int(hx - cam_x), int(hy - cam_y)) for hx, hy in self.history]
            pygame.draw.lines(screen, color, False, pts, 2)
            
        # Draw bullet head
        pygame.draw.circle(screen, WHITE, (sx, sy), 3)
        # Glow
        surf = pygame.Surface((12, 12), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*color, 120), (6, 6), 6)
        screen.blit(surf, (sx - 6, sy - 6))


class Grenade:
    def __init__(self, x, y, target_x, target_y, g_type="FRAG"):
        self.x, self.y = x, y
        self.type = g_type
        
        # Calculate throw trajectory
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        
        # Cap throw distance
        max_dist = 250
        if dist > max_dist:
            dx = dx / dist * max_dist
            dy = dy / dist * max_dist
            dist = max_dist
            
        # Time to target
        self.duration = int(dist / 5)
        self.timer = 0
        
        self.start_x, self.start_y = x, y
        self.target_x = x + dx
        self.target_y = y + dy
        
        self.fuse_timer = GRENADE_FUSE
        self.exploded = False
        
        # Arc variables
        self.height = 0

    def update(self):
        self.fuse_timer -= 1
        if self.fuse_timer <= 0:
            self.exploded = True
            
        if self.timer < self.duration:
            self.timer += 1
            t = self.timer / self.duration
            # Linear interp
            self.x = self.start_x + (self.target_x - self.start_x) * t
            self.y = self.start_y + (self.target_y - self.start_y) * t
            # Parabolic arc
            self.height = math.sin(t * math.pi) * 40
        else:
            self.height = 0

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y - self.height)
        
        # Shadow
        shadow_y = int(self.y - cam_y)
        pygame.draw.ellipse(screen, (20, 20, 20, 100), (sx-6, shadow_y-3, 12, 6))
        
        if self.type == "MOLOTOV":
            # Bottle shape (brown bottle + orange flame tail)
            pygame.draw.rect(screen, (139, 69, 19), (sx-3, sy-5, 6, 10))
            pygame.draw.rect(screen, (200, 100, 50), (sx-2, sy-7, 4, 3))
            # Flame wick
            blink = (self.fuse_timer % 6) < 3
            if blink:
                pygame.draw.circle(screen, (255, 100, 0), (sx, sy-8), 3)
            else:
                pygame.draw.circle(screen, (255, 200, 0), (sx, sy-9), 2)
        elif self.type == "FLASH":
            # Silver stun grenade
            pygame.draw.rect(screen, (180, 180, 185), (sx-3, sy-6, 6, 12))
            pygame.draw.rect(screen, (100, 100, 105), (sx-4, sy-3, 8, 2))
            # Blinking blue indicator
            blink = (self.fuse_timer % 10) < 5
            color = (0, 150, 255) if blink else (50, 50, 60)
            pygame.draw.circle(screen, color, (sx, sy-4), 2)
        elif self.type == "SMOKE":
            # Grey smoke canister
            pygame.draw.rect(screen, (100, 100, 100), (sx-3, sy-6, 6, 12))
            pygame.draw.rect(screen, (130, 130, 130), (sx-4, sy-3, 8, 2))
            # Blinking white/grey light
            blink = (self.fuse_timer % 10) < 5
            color = (255, 255, 255) if blink else (50, 50, 50)
            pygame.draw.circle(screen, color, (sx, sy-4), 2)
        else: # FRAG
            # Green fragmentation grenade
            blink = (self.fuse_timer % 10) < 5
            color = (255, 0, 0) if blink else (30, 80, 30)
            pygame.draw.circle(screen, color, (sx, sy), 5)
            pygame.draw.circle(screen, (0, 0, 0), (sx, sy), 5, 1)

class HomingMissile:
    def __init__(self, x, y, target_player, is_enemy=True, damage=25):
        self.x, self.y = float(x), float(y)
        self.target_player = target_player
        self.is_enemy = is_enemy
        self.damage = damage
        self.alive = True
        self.hit_player = False
        
        # Initial angle towards player
        self.angle = math.atan2(target_player.y - y, target_player.x - x)
        self.speed = 3.6  # Tốc độ vừa phải để người chơi có thể né tránh bằng Dash
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        
        self.history = []
        self.life = 240 # Max 4 giây

    def update(self, game_map):
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
            
        self.history.append((self.x, self.y))
        if len(self.history) > 8:
            self.history.pop(0)
            
        # Hướng định vị tìm người chơi
        if self.target_player and getattr(self.target_player, 'hp', 0) > 0:
            target_angle = math.atan2(self.target_player.y - self.y, self.target_player.x - self.x)
            
            # Xoay dần góc di chuyển của tên lửa về phía người chơi (0.05 rad/khung hình)
            angle_diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
            turn_speed = 0.045
            if abs(angle_diff) < turn_speed:
                self.angle = target_angle
            else:
                self.angle += turn_speed if angle_diff > 0 else -turn_speed
                
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        
        self.x += self.vx
        self.y += self.vy

        # Va chạm tường
        if game_map.is_wall_pixel(self.x, self.y):
            self.alive = False
            
        # Va chạm người chơi
        if self.target_player and getattr(self.target_player, 'hp', 0) > 0:
            dist = math.hypot(self.x - self.target_player.x, self.y - self.target_player.y)
            if dist < self.target_player.radius + 6:
                self.alive = False
                self.hit_player = True

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        
        # Đuôi khói/lửa phản lực
        if len(self.history) > 1:
            pts = [(int(hx - cam_x), int(hy - cam_y)) for hx, hy in self.history]
            pygame.draw.lines(screen, (255, 100, 0), False, pts, 4)
            pygame.draw.lines(screen, (255, 200, 50), False, pts, 2)
            
        # Vẽ thân tên lửa
        pygame.draw.circle(screen, (80, 90, 100), (sx, sy), 6)
        pygame.draw.circle(screen, RED, (sx, sy), 3) # Đầu đạn đỏ
        
        # Ngọn lửa phụt ở đuôi
        ex = sx - int(math.cos(self.angle) * 8)
        ey = sy - int(math.sin(self.angle) * 8)
        pygame.draw.circle(screen, (255, 150, 0), (ex, ey), 3)


class BulletManager:
    def __init__(self):
        self.bullets = []
        self.grenades = []
        self.missiles = []

    def add_bullet(self, x, y, target_x, target_y, is_enemy=False, damage=10, color=None):
        b = Bullet(x, y, target_x, target_y, is_enemy, color=color)
        b.damage = damage
        self.bullets.append(b)

    def add_grenade(self, x, y, target_x, target_y, g_type="FRAG"):
        self.grenades.append(Grenade(x, y, target_x, target_y, g_type))

    def add_missile(self, x, y, target_player, damage=25):
        self.missiles.append(HomingMissile(x, y, target_player, is_enemy=True, damage=damage))

    def update(self, game_map, effect_manager, sound_manager):
        explosions = []
        
        # Update bullets
        for b in self.bullets:
            b.update()
            if game_map.is_wall_pixel(b.x, b.y):
                tx, ty = int(b.x // TILE_SIZE), int(b.y // TILE_SIZE)
                tile = game_map.get_tile(tx, ty)
                if tile == TILE_BARREL:
                    if (tx, ty) in game_map.leaking_barrels:
                        # Explode immediately if already leaking
                        game_map.grid[ty][tx] = TILE_EMPTY
                        game_map.leaking_barrels.pop((tx, ty), None)
                        explosions.append((b.x, b.y, "FRAG"))
                        effect_manager.add_explosion(b.x, b.y, GRENADE_RADIUS * 1.2)
                        sound_manager.play('explosion')
                        game_map.redraw_tile_floor(tx, ty)
                    else:
                        game_map.start_barrel_leak(tx, ty)
                elif tile == TILE_COVER:
                    game_map.damage_cover(tx, ty, b.damage, effect_manager, sound_manager)
                elif tile == TILE_ALARM_CONSOLE:
                    game_map.damage_alarm_console(tx, ty, b.damage, effect_manager, sound_manager)
                elif tile == TILE_LASER:
                    game_map.damage_laser(tx, ty, b.damage, effect_manager, sound_manager)
                
                b.alive = False
                effect_manager.add_bullet_impact(b.x, b.y)
                
        self.bullets = [b for b in self.bullets if b.alive]
        
        # Update grenades
        for g in self.grenades:
            g.update()
            if g.exploded:
                explosions.append((g.x, g.y, g.type))
                if g.type == "FRAG":
                    effect_manager.add_explosion(g.x, g.y, GRENADE_RADIUS)
                    sound_manager.play('explosion')
                    game_map.add_noise(g.x, g.y, 800)
                elif g.type == "MOLOTOV":
                    effect_manager.add_explosion(g.x, g.y, GRENADE_RADIUS * 0.7)
                    effect_manager.add_fire_pool(g.x, g.y, radius=75, lifetime=300)
                    sound_manager.play('explosion')
                    game_map.add_noise(g.x, g.y, 600)
                elif g.type == "FLASH":
                    effect_manager.add_explosion(g.x, g.y, GRENADE_RADIUS * 1.2)
                    effect_manager.screen_flash = 255
                    sound_manager.play('explosion')
                    game_map.add_noise(g.x, g.y, 700)
                elif g.type == "SMOKE":
                    effect_manager.add_smoke_cloud(g.x, g.y, radius=120, lifetime=450)
                    sound_manager.play('explosion')
                    game_map.add_noise(g.x, g.y, 400)
                
        self.grenades = [g for g in self.grenades if not g.exploded]

        # Update missiles
        for m in self.missiles:
            m.update(game_map)
            if not m.alive:
                explosions.append((m.x, m.y, "FRAG"))
                effect_manager.add_explosion(m.x, m.y, GRENADE_RADIUS * 0.7)
                sound_manager.play('explosion')
                game_map.add_noise(m.x, m.y, 700)
                if m.hit_player:
                    m.target_player.take_damage(m.damage, effect_manager, sound_manager)
                    
        self.missiles = [m for m in self.missiles if m.alive]
        
        return explosions

    def draw(self, screen, cam_x, cam_y):
        for g in self.grenades:
            g.draw(screen, cam_x, cam_y)
        for b in self.bullets:
            b.draw(screen, cam_x, cam_y)
        for m in self.missiles:
            m.draw(screen, cam_x, cam_y)
