import pygame
import math
import random
from constants import *


class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, intensity, duration):
        self.intensity = intensity
        self.duration = duration

    def update(self):
        if self.duration > 0:
            self.offset_x = random.randint(-self.intensity, self.intensity)
            self.offset_y = random.randint(-self.intensity, self.intensity)
            self.duration -= 1
        else:
            self.offset_x = 0
            self.offset_y = 0

    def apply(self, x, y):
        return x + self.offset_x, y + self.offset_y


class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0

    @property
    def alpha(self):
        return int(255 * self.lifetime / self.max_lifetime)

    def draw(self, screen, cam_x, cam_y):
        if self.size < 1:
            return
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        # Vẽ trực tiếp không tạo Surface mới — nhanh hơn nhiều
        pygame.draw.circle(screen, self.color, (sx, sy), max(1, int(self.size)))


class FireParticle(Particle):
    def __init__(self, x, y):
        vx = random.uniform(-1.2, 1.2)
        vy = random.uniform(-2.5, -0.5)
        color = random.choice([ORANGE, (255,100,0), YELLOW, RED])
        size = random.randint(4, 9)
        super().__init__(x, y, vx, vy, color, size, random.randint(20, 40))

    def update(self):
        self.size = max(0, self.size - 0.15)
        return super().update()


class SmokeParticle(Particle):
    def __init__(self, x, y):
        vx = random.uniform(-0.6, 0.6)
        vy = random.uniform(-1.5, -0.3)
        c = random.randint(80, 140)
        super().__init__(x, y, vx, vy, (c,c,c), random.randint(5, 12), random.randint(30, 60))

    def update(self):
        self.size = min(self.size + 0.08, 14)
        return super().update()


class BloodParticle(Particle):
    def __init__(self, x, y, angle=None):
        if angle is None:
            angle = random.uniform(0, math.pi*2)
        spd = random.uniform(1.5, 5.0)
        super().__init__(x, y,
                         math.cos(angle)*spd, math.sin(angle)*spd,
                         random.choice([RED, DARK_RED, (180,10,10)]),
                         random.randint(2, 5), random.randint(20, 45))

    def update(self):
        self.vy += 0.15  # gravity
        return super().update()


class VolcanicEmberParticle(Particle):
    def __init__(self, x, y):
        vx = random.uniform(-0.6, 0.6)
        vy = random.uniform(-2.2, -0.8)
        color = random.choice([(255, 100, 0), (255, 60, 0), (220, 30, 0), (255, 160, 10)])
        size = random.uniform(2, 4)
        lifetime = random.randint(70, 120)
        super().__init__(x, y, vx, vy, color, size, lifetime)
        self.wave_offset = random.uniform(0, math.pi * 2)
        self.wave_speed = random.uniform(0.04, 0.08)
        self.wave_amp = random.uniform(0.8, 2.0)
        self.history = []

    def update(self):
        # Save position history for trail
        self.history.append((self.x, self.y))
        if len(self.history) > 6:
            self.history.pop(0)
            
        # Horizontal sway via sine wave
        self.x += math.sin(pygame.time.get_ticks() * self.wave_speed + self.wave_offset) * self.wave_amp
        
        # Shrink slightly over time
        self.size = max(0.5, self.size - 0.01)
        return super().update()

    def draw(self, screen, cam_x, cam_y):
        if self.size < 1:
            return
            
        # Draw trailing heat line
        if len(self.history) >= 2:
            pts = [(int(hx - cam_x), int(hy - cam_y)) for hx, hy in self.history]
            pygame.draw.lines(screen, self.color, False, pts, 1)
            
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        pygame.draw.circle(screen, self.color, (sx, sy), max(1, int(self.size)))
        # White-hot inner core
        pygame.draw.circle(screen, (255, 240, 200), (sx, sy), max(1, int(self.size) - 2))


class SparkParticle:
    def __init__(self, x, y, angle=None):
        self.x, self.y = x, y
        if angle is None:
            angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(3.0, 7.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.randint(15, 30)
        self.max_lifetime = self.lifetime
        self.color = random.choice([(255, 220, 100), (255, 140, 50), (255, 255, 255)])
        self.gravity = 0.12

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        speed = math.hypot(self.vx, self.vy)
        length = max(3.0, speed * 1.5)
        angle = math.atan2(self.vy, self.vx)
        ex = int(sx - math.cos(angle) * length)
        ey = int(sy - math.sin(angle) * length)
        # Vẽ tia lửa trực tiếp lên screen — không cấp phát Surface
        pygame.draw.line(screen, (200, 80, 0), (sx, sy), (ex, ey), 2)
        pygame.draw.line(screen, self.color, (sx, sy), (ex, ey), 1)


class WallDebrisParticle(Particle):
    def __init__(self, x, y):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.0, 3.5)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        color = random.choice([(100, 90, 80), (120, 110, 100), (80, 80, 80), (150, 130, 110)])
        size = random.randint(2, 5)
        lifetime = random.randint(20, 40)
        super().__init__(x, y, vx, vy, color, size, lifetime)

    def update(self):
        self.vy += 0.2
        self.vx *= 0.98
        self.size = max(0.5, self.size - 0.05)
        return super().update()


class TrailParticle(Particle):
    def __init__(self, x, y, color):
        super().__init__(x, y, 0, 0, color, random.randint(2, 4), 10)

    def update(self):
        self.size *= 0.8
        return super().update()


class ShellCasing(Particle):
    def __init__(self, x, y, angle):
        spd = random.uniform(2, 4)
        side_angle = angle + math.pi/2 + random.uniform(-0.5, 0.5)
        vx = math.cos(side_angle) * spd
        vy = math.sin(side_angle) * spd
        super().__init__(x, y, vx, vy, GOLD, 2, 40)

    def update(self):
        self.vx *= 0.95
        self.vy *= 0.95
        self.vy += 0.2 # gravity
        return super().update()


class MuzzleFlash:
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.lifetime = 5
        self.size = random.randint(10, 18)

    def update(self):
        self.lifetime -= 1
        self.size = max(0, self.size - 2)
        return self.lifetime > 0

    def draw(self, screen, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        # Draw standard core circles
        pygame.draw.circle(screen, (255, 240, 180), (sx, sy), self.size)
        pygame.draw.circle(screen, (255, 255, 220), (sx, sy), self.size // 2)
        
        # Soft bloom glow using BLEND_ADD
        glow_r = int(self.size * 2.5)
        if glow_r > 0:
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            for r_step in range(glow_r, 0, -4):
                alpha = int(45 * (1.0 - r_step / glow_r))
                pygame.draw.circle(glow_surf, (255, 180, 50, alpha), (glow_r, glow_r), r_step)
            screen.blit(glow_surf, (sx - glow_r, sy - glow_r), special_flags=pygame.BLEND_ADD)


class ExplosionEffect:
    def __init__(self, x, y, radius):
        self.x, self.y = x, y
        self.radius = radius
        self.lifetime = 45
        self.max_lt = 45
        self.particles = []
        # Fire core — giảm còn 18 để tránh lag
        for _ in range(18):
            self.particles.append(FireParticle(x + random.uniform(-10,10),
                                               y + random.uniform(-10,10)))
        # Smoke ring — giảm còn 12
        for _ in range(12):
            angle = random.uniform(0, math.pi*2)
            dist = random.uniform(radius*0.3, radius*0.8)
            self.particles.append(SmokeParticle(
                x + math.cos(angle)*dist, y + math.sin(angle)*dist))
        # Debris — giảm còn 10
        for _ in range(10):
            angle = random.uniform(0, math.pi*2)
            spd = random.uniform(3, 8)
            c = random.choice([BROWN, DARK_GRAY, (60,40,20)])
            p = Particle(x, y, math.cos(angle)*spd, math.sin(angle)*spd,
                         c, random.randint(2,5), 40)
            self.particles.append(p)

    def update(self):
        self.lifetime -= 1
        self.particles = [p for p in self.particles if p.update()]
        return self.lifetime > 0

    def draw(self, screen, cam_x, cam_y):
        for p in self.particles:
            p.draw(screen, cam_x, cam_y)
        # Shockwave ring
        prog = 1 - self.lifetime / self.max_lt
        if prog < 0.4:
            r = int(self.radius * prog / 0.4)
            alpha = int(200 * (1 - prog/0.4))
            sx, sy = int(self.x - cam_x), int(self.y - cam_y)
            if 0 < r < 300:
                surf = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255,200,100,alpha), (r+2,r+2), r, 3)
                screen.blit(surf, (sx-r-2, sy-r-2))


class EffectManager:
    def __init__(self):
        self.particles  = []
        self.flashes    = []
        self.explosions = []
        self.shake      = ScreenShake()
        self.snowflakes = []
        self.screen_flash = 0
        self.fire_pools = []
        self.smoke_clouds = []
        self.slashes = []
        self.rain_splashes = []
        self.floating_texts = []
        self.footsteps = []   # Dấu bước chân trên mặt đất

    def add_trail(self, x, y, color):
        self.particles.append(TrailParticle(x, y, color))

    def add_sparks(self, x, y, count=6, angle=None):
        for _ in range(count):
            a = angle + random.uniform(-0.8, 0.8) if angle is not None else None
            self.particles.append(SparkParticle(x, y, a))


    def add_shell(self, x, y, angle):
        self.particles.append(ShellCasing(x, y, angle))

    def add_blood(self, x, y, count=8, angle=None):
        for _ in range(count):
            a = angle + random.uniform(-0.8, 0.8) if angle else None
            self.particles.append(BloodParticle(x, y, a))

    def add_muzzle_flash(self, x, y, angle):
        self.flashes.append(MuzzleFlash(x, y, angle))

    def add_smoke(self, x, y, count=3):
        for _ in range(count):
            self.particles.append(SmokeParticle(
                x+random.uniform(-5,5), y+random.uniform(-5,5)))

    def add_fire(self, x, y, count=5):
        for _ in range(count):
            self.particles.append(FireParticle(x+random.uniform(-8,8), y))

    def add_flame_burst(self, x, y, angle, count=18):
        """Hiệu ứng ngọn lửa phún ra khi bắn súng lửa."""
        for _ in range(count):
            spread = random.uniform(-0.45, 0.45)
            a = angle + spread
            dist = random.uniform(10, 80)
            px = x + math.cos(a) * dist
            py = y + math.sin(a) * dist
            spd_x = math.cos(a) * random.uniform(2.5, 6.0)
            spd_y = math.sin(a) * random.uniform(2.5, 6.0)
            color = random.choice([(255,80,0),(255,140,0),(255,200,50),(255,50,0),(220,30,0)])
            size  = random.randint(5, 14)
            life  = random.randint(15, 35)
            p = FireParticle(px, py)
            p.vx = spd_x; p.vy = spd_y
            p.color = color; p.size = size; p.lifetime = life; p.max_lifetime = life
            self.particles.append(p)
        # Thêm một làn khói theo sau ngọn lửa
        for _ in range(8):
            spread = random.uniform(-0.3, 0.3)
            a = angle + spread
            dist = random.uniform(30, 100)
            px = x + math.cos(a) * dist
            py = y + math.sin(a) * dist
            self.particles.append(SmokeParticle(px, py))

    def add_explosion(self, x, y, radius=90):
        self.explosions.append(ExplosionEffect(x, y, radius))

    def add_cover_destruction(self, x, y):
        for _ in range(12):
            self.particles.append(WallDebrisParticle(x, y))
        for _ in range(5):
            self.particles.append(SmokeParticle(
                x + random.uniform(-8, 8), y + random.uniform(-8, 8)))

    def add_bullet_impact(self, x, y):
        for _ in range(5):
            angle = random.uniform(0, math.pi*2)
            spd = random.uniform(1, 3)
            c = random.choice([GRAY, (120,100,80), DARK_GRAY])
            self.particles.append(Particle(
                x, y, math.cos(angle)*spd, math.sin(angle)*spd,
                c, random.randint(2,4), 20))
        for _ in range(random.randint(4, 7)):
            self.particles.append(WallDebrisParticle(x, y))

    # Giới hạn tổng số particle để tránh lag
    MAX_PARTICLES = 350

    def update_ambient(self, cam_x, cam_y, level=1):
        """Add random smoke and embers to simulate a battlefield."""
        # Chỉ thêm particle nếu chưa vượt giới hạn
        if len(self.particles) >= self.MAX_PARTICLES:
            return

        if random.random() > 0.94: # Random smoke drifts — giảm tần suất
            ax = cam_x + random.randint(-100, SCREEN_W + 100)
            ay = cam_y + random.randint(-100, SCREEN_H + 100)
            self.particles.append(SmokeParticle(ax, ay))
        
        if random.random() > 0.99: # Random embers — giảm tần suất
            ax = cam_x + random.randint(0, SCREEN_W)
            ay = cam_y + random.randint(0, SCREEN_H)
            self.particles.append(FireParticle(ax, ay))

        # Volcanic embers effect for level 5 (Hell/Volcano map)
        if level == 5:
            if random.random() > 0.88: # Giảm tần suất tàn tro nhưng vẫn sinh động
                ax = cam_x + random.randint(-50, SCREEN_W + 50)
                ay = cam_y + SCREEN_H + 20
                self.particles.append(VolcanicEmberParticle(ax, ay))

        # Snow effect for level 3 (Ice/Snow map)
        if level == 3:
            if not self.snowflakes:
                # Initialize snowflakes — giảm còn 80 để tránh lag
                for _ in range(80):
                    self.snowflakes.append({
                        "x": random.uniform(0, SCREEN_W),
                        "y": random.uniform(0, SCREEN_H),
                        "speed": random.uniform(1.2, 3.0),
                        "size": random.randint(1, 4),
                        "drift": random.uniform(-0.3, 0.3)
                    })
            for flake in self.snowflakes:
                flake["y"] += flake["speed"]
                # Sinusoidal wind sway + drift to the right
                flake["x"] += flake["drift"] + 0.4 + 0.25 * math.sin(pygame.time.get_ticks() * 0.004 + flake["y"] * 0.02)
                
                # Wrap boundaries
                if flake["y"] > SCREEN_H:
                    flake["y"] = 0
                    flake["x"] = random.uniform(0, SCREEN_W)
                if flake["x"] > SCREEN_W:
                    flake["x"] = 0
                elif flake["x"] < 0:
                    flake["x"] = SCREEN_W
        else:
            if self.snowflakes:
                self.snowflakes = []

        # Rain and wind storm effect for level 2
        if level == 2:
            if not hasattr(self, 'raindrops') or not self.raindrops:
                self.raindrops = []
                for _ in range(120):
                    self.raindrops.append({
                        "x": random.uniform(-100, SCREEN_W + 100),
                        "y": random.uniform(-50, SCREEN_H),
                        "speed_y": random.uniform(12.0, 18.0),
                        "speed_x": random.uniform(5.0, 8.0), # wind direction: right
                        "length": random.randint(14, 25),
                        "thickness": random.randint(1, 2)
                    })
            for drop in self.raindrops:
                drop["y"] += drop["speed_y"]
                drop["x"] += drop["speed_x"]
                if drop["y"] > SCREEN_H:
                    # Spawn rain splash
                    if len(self.rain_splashes) < 60 and random.random() > 0.6:
                        self.rain_splashes.append({
                            "x": drop["x"],
                            "y": SCREEN_H - random.uniform(5, 120),
                            "radius": 1.0,
                            "grow_speed": random.uniform(0.6, 1.2),
                            "lifetime": 20,
                            "max_lifetime": 20
                        })
                    drop["y"] = -20
                    drop["x"] = random.uniform(-100, SCREEN_W + 100)
                if drop["x"] > SCREEN_W + 100:
                    drop["x"] = -100
                elif drop["x"] < -100:
                    drop["x"] = SCREEN_W + 100

            # Also spawn some random splashes inside the view
            if random.random() > 0.65 and len(self.rain_splashes) < 60:
                self.rain_splashes.append({
                    "x": random.uniform(0, SCREEN_W),
                    "y": random.uniform(0, SCREEN_H),
                    "radius": 1.0,
                    "grow_speed": random.uniform(0.5, 1.0),
                    "lifetime": random.randint(15, 25),
                    "max_lifetime": 25
                })

            # Lightning sequence
            if not hasattr(self, 'lightning_timer'):
                self.lightning_timer = random.randint(180, 450)
            if not hasattr(self, 'lightning_seq'):
                self.lightning_seq = 0
            if not hasattr(self, 'lightning_seq_timer'):
                self.lightning_seq_timer = 0

            self.lightning_timer -= 1
            if self.lightning_timer <= 0 and self.lightning_seq == 0:
                self.lightning_seq = 1
                
            from sound_manager import sound_manager
            if self.lightning_seq == 1:
                self.screen_flash = 240
                self.shake.trigger(8, 12)
                sound_manager.play('explosion')
                self.lightning_seq = 2
                self.lightning_seq_timer = 12
            elif self.lightning_seq == 2:
                self.lightning_seq_timer -= 1
                if self.lightning_seq_timer <= 0:
                    self.screen_flash = 180
                    self.lightning_seq = 0
                    self.lightning_timer = random.randint(240, 550)
        else:
            if hasattr(self, 'raindrops') and self.raindrops:
                self.raindrops = []
                if hasattr(self, 'lightning_timer'): delattr(self, 'lightning_timer')
                if hasattr(self, 'lightning_seq'): delattr(self, 'lightning_seq')
                if hasattr(self, 'lightning_seq_timer'): delattr(self, 'lightning_seq_timer')

    def add_fire_pool(self, x, y, radius=75, lifetime=300):
        self.fire_pools.append(FirePool(x, y, radius, lifetime))

    def add_smoke_cloud(self, x, y, radius=120, lifetime=450):
        self.smoke_clouds.append(SmokeCloud(x, y, radius, lifetime))

    def add_slash(self, x, y, angle, radius, color):
        self.slashes.append(SlashEffect(x, y, angle, radius, color))

    def add_floating_text(self, x, y, text, color):
        if not hasattr(self, 'floating_texts'):
            self.floating_texts = []
        self.floating_texts.append(FloatingText(x, y, text, color))

    def add_footstep(self, x, y, angle, foot_side, level=1):
        """Thêm dấu bước chân tại vị trí (x,y), giới hạn tối đa 40 dấu."""
        if not hasattr(self, 'footsteps'):
            self.footsteps = []
        if len(self.footsteps) < 40:
            self.footsteps.append(FootstepEffect(x, y, angle, foot_side, level))

    def update(self):
        self.particles  = [p for p in self.particles  if p.update()]
        self.flashes    = [f for f in self.flashes    if f.update()]
        self.explosions = [e for e in self.explosions if e.update()]
        self.fire_pools = [fp for fp in self.fire_pools if fp.update(self)]
        self.smoke_clouds = [sc for sc in self.smoke_clouds if sc.update(self)]
        self.slashes    = [s for s in self.slashes if s.update()]
        if not hasattr(self, 'floating_texts'):
            self.floating_texts = []
        self.floating_texts = [ft for ft in self.floating_texts if ft.update()]
        if not hasattr(self, 'footsteps'):
            self.footsteps = []
        self.footsteps = [fs for fs in self.footsteps if fs.update()]
        
        # Update rain splashes
        active_splashes = []
        if hasattr(self, 'rain_splashes'):
            for splash in self.rain_splashes:
                splash["radius"] += splash["grow_speed"]
                splash["lifetime"] -= 1
                if splash["lifetime"] > 0:
                    active_splashes.append(splash)
            self.rain_splashes = active_splashes
            
        if self.screen_flash > 0:
            self.screen_flash = max(0, self.screen_flash - 8)
        self.shake.update()

    def draw(self, screen, cam_x, cam_y, level=1):
        # Dấu bước chân vẽ đầu tiên (dưới mặt đất, dưới mọi thứ)
        if hasattr(self, 'footsteps'):
            for fs in self.footsteps:
                fs.draw(screen, cam_x, cam_y)
        for fp in self.fire_pools:
            fp.draw(screen, cam_x, cam_y)
        for sc in self.smoke_clouds:
            sc.draw(screen, cam_x, cam_y)
        for p in self.particles:
            p.draw(screen, cam_x, cam_y)
        for f in self.flashes:
            f.draw(screen, cam_x, cam_y)
        for e in self.explosions:
            e.draw(screen, cam_x, cam_y)
        for s in self.slashes:
            s.draw(screen, cam_x, cam_y)
        if hasattr(self, 'floating_texts'):
            for ft in self.floating_texts:
                ft.draw(screen, cam_x, cam_y)
            
        # Draw screen-space rain splashes for Level 2
        if level == 2 and hasattr(self, 'rain_splashes'):
            for splash in self.rain_splashes:
                x, y = int(splash["x"]), int(splash["y"])
                r = int(splash["radius"])
                alpha = int(120 * (splash["lifetime"] / splash["max_lifetime"]))
                if alpha > 0 and r > 0:
                    surf = pygame.Surface((r * 2 + 4, r + 4), pygame.SRCALPHA)
                    pygame.draw.ellipse(surf, (150, 180, 210, alpha), (2, 2, r * 2, r), 1)
                    screen.blit(surf, (x - r - 1, y - r // 2 - 1))
            
        # Draw screen-space falling snow for Level 3 — vẽ trực tiếp, không tạo Surface
        if level == 3 and self.snowflakes:
            for flake in self.snowflakes:
                sx, sy = int(flake["x"]), int(flake["y"])
                r = max(1, flake["size"])
                pygame.draw.circle(screen, (220, 235, 255), (sx, sy), r)

        # Draw screen-space falling rain for Level 2 — vẽ trực tiếp các vệt xiên gió thổi
        if level == 2 and hasattr(self, 'raindrops') and self.raindrops:
            for drop in self.raindrops:
                sx, sy = int(drop["x"]), int(drop["y"])
                length = drop["length"]
                spd = math.hypot(drop["speed_x"], drop["speed_y"])
                dx = (drop["speed_x"] / spd) * length
                dy = (drop["speed_y"] / spd) * length
                ex = int(sx - dx)
                ey = int(sy - dy)
                pygame.draw.line(screen, (140, 165, 190), (sx, sy), (ex, ey), drop["thickness"])


class SmokeCloud:
    """Vùng khói từ lựu đạn khói — che tầm nhìn kẻ địch và người chơi."""
    def __init__(self, x, y, radius=120, lifetime=450):
        self.x, self.y = x, y
        self.radius = radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.expand_timer = 60  # Nở rộng dần trong 1 giây

    def update(self, effect_manager):
        self.lifetime -= 1
        # Nở rộng dần trong giai đoạn đầu
        if self.expand_timer > 0:
            self.expand_timer -= 1
            progress = 1 - self.expand_timer / 60
            self.current_radius = int(self.radius * progress)
        else:
            self.current_radius = self.radius
        # Sinh khói liên tục
        if random.random() > 0.3:
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(0, getattr(self, 'current_radius', self.radius))
            px = self.x + math.cos(angle) * dist
            py = self.y + math.sin(angle) * dist
            sp = SmokeParticle(px, py)
            sp.size = random.randint(12, 22)
            sp.lifetime = random.randint(20, 40)
            sp.max_lifetime = sp.lifetime
            effect_manager.particles.append(sp)
        return self.lifetime > 0

    def is_inside(self, px, py):
        """Kiểm tra xem điểm (px, py) có nằm trong đám khói không."""
        r = getattr(self, 'current_radius', self.radius)
        return math.hypot(px - self.x, py - self.y) < r

    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r = getattr(self, 'current_radius', self.radius)
        if r <= 0:
            return
        fade = min(1.0, self.lifetime / (self.max_lifetime * 0.3))
        alpha = int(55 * fade)
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (180, 180, 180, alpha), (r, r), r)
        pygame.draw.circle(surf, (150, 150, 155, max(0, alpha - 20)), (r, r), int(r * 0.6))
        screen.blit(surf, (sx - r, sy - r))


class FirePool:
    def __init__(self, x, y, radius=75, lifetime=300):
        self.x, self.y = x, y
        self.radius = radius
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        
    def update(self, effect_manager):
        self.lifetime -= 1
        # Sinh các hạt lửa ngẫu nhiên trong bán kính
        if random.random() > 0.4:
            angle = random.uniform(0, math.pi*2)
            dist = random.uniform(0, self.radius)
            px = self.x + math.cos(angle) * dist
            py = self.y + math.sin(angle) * dist
            p = FireParticle(px, py)
            p.vx = random.uniform(-0.4, 0.4)
            p.vy = random.uniform(-1.2, -0.4) # bay lên trên nhẹ nhàng
            p.color = random.choice([(255, 80, 0), (255, 140, 0), (255, 50, 0)])
            p.size = random.randint(3, 8)
            p.lifetime = random.randint(12, 24)
            p.max_lifetime = p.lifetime
            effect_manager.particles.append(p)
        return self.lifetime > 0
        
    def draw(self, screen, cam_x, cam_y):
        # Vẽ vòng lửa cảnh báo dưới nền đất
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        # Hiệu ứng nhấp nháy theo thời gian
        pulse = int(12 + 8 * math.sin(self.lifetime * 0.15))
        pygame.draw.circle(surf, (255, 80, 0, pulse), (self.radius, self.radius), self.radius)
        pygame.draw.circle(surf, (255, 120, 0, 70), (self.radius, self.radius), self.radius, 2)
        screen.blit(surf, (sx - self.radius, sy - self.radius))


class SlashEffect:
    def __init__(self, x, y, angle, radius, color):
        self.x, self.y = x, y
        self.angle = angle
        self.radius = radius
        self.color = color
        self.lifetime = 10
        self.max_lifetime = 10
        
    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0
        
    def draw(self, screen, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        t = 1.0 - (self.lifetime / self.max_lifetime)
        
        # Cung chém quét rộng từ angle - 1.2 đến angle + 1.2
        start_angle = self.angle - 1.2 + t * 0.4
        end_angle = self.angle + 1.2 - (1.0 - t) * 0.4
        
        points = []
        steps = 10
        for i in range(steps + 1):
            a = start_angle + (end_angle - start_angle) * (i / steps)
            px = sx + math.cos(a) * self.radius
            py = sy + math.sin(a) * self.radius
            points.append((px, py))
            
        if len(points) >= 2:
            # Vẽ trực tiếp, không tạo Surface toàn màn hình
            pygame.draw.lines(screen, self.color, False, points, 4)
            pygame.draw.lines(screen, (255, 255, 255), False, points, 2)


class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.lifetime = 90
        self.max_lifetime = 90
        self.vy = -1.0 # rises up slowly
        # Use simple fallback font
        self.font = pygame.font.SysFont("segoeui", 14, bold=True)

    def update(self):
        self.y += self.vy
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen, cam_x, cam_y):
        alpha = int(255 * self.lifetime / self.max_lifetime)
        if alpha <= 0:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        
        # Render text
        txt_s = self.font.render(self.text, True, self.color)
        
        # Make a surface with alpha support to multiply alphas
        txt_w, txt_h = txt_s.get_size()
        alpha_surf = pygame.Surface((txt_w, txt_h), pygame.SRCALPHA)
        alpha_surf.blit(txt_s, (0, 0))
        alpha_surf.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)

        # Draw shadow
        shadow_surf = self.font.render(self.text, True, (0, 0, 0))
        shadow_alpha = pygame.Surface((txt_w, txt_h), pygame.SRCALPHA)
        shadow_alpha.blit(shadow_surf, (0, 0))
        shadow_alpha.fill((255, 255, 255, int(alpha * 0.7)), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(shadow_alpha, (sx - txt_w//2 + 1, sy + 1))
        
        screen.blit(alpha_surf, (sx - txt_w//2, sy))


class FootstepEffect:
    """Dấu bước chân in trên mặt đất — fade dần theo thời gian."""
    def __init__(self, x, y, angle, foot_side, level=1):
        self.x, self.y = x, y
        self.angle = angle
        self.foot_side = foot_side  # -1 = trái, 1 = phải
        self.lifetime = 55
        self.max_lifetime = 55
        # Màu dấu chân theo level
        level_colors = {
            1: (15, 22, 10),    # Rừng: đất tối
            2: (20, 18, 12),    # Làng: bùn nâu
            3: (25, 35, 18),    # Nông thôn: đất xanh
            4: (18, 22, 15),    # Căn cứ: bê tông
            5: (35, 10, 5),     # Địa ngục: tro đỏ
        }
        self.color = level_colors.get(level, (15, 20, 10))

    def update(self):
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen, cam_x, cam_y):
        alpha = int(180 * (self.lifetime / self.max_lifetime) ** 1.5)
        if alpha < 5:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Vẽ dấu chân hình ellipse nhỏ xoay theo hướng di chuyển
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        # Offset sang trái/phải theo foot_side
        perp_x = -sin_a * 4 * self.foot_side
        perp_y =  cos_a * 4 * self.foot_side
        fx = sx + int(perp_x)
        fy = sy + int(perp_y)

        # Vẽ ellipse nhỏ (dấu giày)
        foot_w, foot_h = 5, 8
        surf = pygame.Surface((foot_w * 2 + 2, foot_h * 2 + 2), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.ellipse(surf, (r, g, b, alpha), (1, 1, foot_w * 2, foot_h * 2))
        # Xoay ellipse theo hướng di chuyển
        rot_deg = -math.degrees(self.angle)
        rotated = pygame.transform.rotate(surf, rot_deg)
        rect = rotated.get_rect(center=(fx, fy))
        screen.blit(rotated, rect.topleft)
