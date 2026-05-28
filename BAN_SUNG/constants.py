# constants.py — ĐẶC NHIỆM — CHIẾN DỊCH ĐEN — Tactical FPS Constants

# ── Screen ──────────────────────────────────────────────────────────────────────────
SCREEN_W  = 1200
SCREEN_H  = 800
FPS       = 60
TITLE     = "ĐẶC NHIỆM — CHIẾN DỊCH ĐEN"

# ── Map ─────────────────────────────────────────────────────────────────────
TILE_SIZE  = 32
MAP_W      = 80
MAP_H      = 60

TILE_EMPTY  = 0
TILE_WALL   = 1
TILE_COVER  = 2
TILE_TUNNEL = 3
TILE_EXIT   = 4
TILE_BARREL = 5
TILE_ALARM_CONSOLE = 6
TILE_LASER = 7

# ── Alarm Tuning ─────────────────────────────────────────────────────────────
ALARM_CONSOLE_HP     = 60
LASER_HP             = 30
CAMERA_HP            = 30
ALARM_SPAWN_INTERVAL = 480

# ── Base Colors ─────────────────────────────────────────────────────────────
BLACK        = (0,   0,   0)
WHITE        = (255, 255, 255)
DARK_BG      = (5,   5,   10)

# ── Environment Colors ─────────────────────────────────────────────────────
JUNGLE_DARK  = (25,  35,  20)
JUNGLE_MID   = (45,  60,  30)
JUNGLE_LIGHT = (80,  100, 60)
TREE_COLOR   = (30,  80,  30)
COVER_COLOR  = (120, 110, 90)
TUNNEL_COLOR = (60,  50,  30)
EXIT_COLOR   = (180, 180, 180)
BARREL_COLOR = (200, 60,  60)
FLOOR_COLOR  = (45,  50,  35)

# ── General Palette ─────────────────────────────────────────────────────────
RED         = (220, 40,  40)
DARK_RED    = (140, 10,  10)
ORANGE      = (255, 140, 0)
YELLOW      = (255, 220, 0)
GREEN       = (50,  200, 50)
LIME        = (150, 255, 50)
CYAN        = (0,   220, 220)
BLUE        = (50,  120, 255)
PINK        = (255, 100, 150)
PURPLE      = (160, 32, 240)
GRAY        = (150, 150, 150)
DARK_GRAY   = (60,  60,  60)
GRID_COLOR  = (30, 40, 50)
UI_BORDER   = (50, 200, 255)
GOLD        = (255, 215, 0)
SAND        = (200, 180, 130)
BROWN       = (100, 65,  25)
DARK_BROWN  = (55,  35,  10)

# ── UI Theme — Modern Clean ───────────────────────────────────────────────
UI_BG            = (15,  15,  18)   # Dark Slate
UI_PANEL         = (25,  25,  30)   # Lighter Slate
UI_PANEL_LIGHT   = (40,  40,  45)
UI_BORDER        = (255, 70,  85)   # Vivid Red (Primary Accent)
UI_HIGHLIGHT     = (255, 255, 255)  # Crisp White
UI_TEXT          = (220, 220, 225)
UI_TEXT_DIM      = (130, 130, 140)
UI_HP            = (255, 70,  85)   # Red
UI_ARMOR         = (70,  200, 255)  # Bright Blue
UI_STAMINA       = (255, 200, 50)
UI_WARNING       = (255, 180, 0)
UI_DANGER        = (255, 50,  50)
UI_SUCCESS       = (50,  255, 120)

# ── Rarity Colors ───────────────────────────────────────────────────────────
RARITY_COMMON     = (150, 150, 150)
RARITY_RARE       = (50,  150, 255)
RARITY_EPIC       = (160, 60,  220)
RARITY_LEGENDARY  = (255, 200, 50)

# ── Player Colors ───────────────────────────────────────────────────────────
PLAYER_COLOR      = (50, 200, 80)
PLAYER_DARK       = (20, 120, 40)
PLAYER_MUZZLE     = (255, 240, 180)

# ── Enemy Colors ────────────────────────────────────────────────────────────
PATROL_COLOR  = (80,  160, 80)
SNIPER_COLOR  = (220, 180, 60)
ASSAULT_COLOR = (220, 60,  60)
BOSS_COLOR    = (180, 60,  220)

# ── Player / Human Movement ─────────────────────────────────────────────────
PLAYER_SPEED      = 4.5
PLAYER_ACCEL      = 0.25
PLAYER_FRICTION   = 0.15
PLAYER_SPRINT_MUL = 1.6
PLAYER_AIM_MUL    = 0.6
PLAYER_HP_MAX     = 100
PLAYER_ARMOR_MAX  = 100
PLAYER_STAMINA_MAX = 100
STAMINA_DRAIN     = 0.8
STAMINA_REGEN     = 0.3

# ── Movement Tuning ─────────────────────────────────────────────────────────
WALK_ANIM_SPEED   = 0.15
BREATH_ANIM_SPEED = 0.05
LEAN_INTENSITY    = 5.0
WEIGHT_MOMENTUM   = 0.95
RECOIL_RECOVERY   = 0.15

# ── Combat States ────────────────────────────────────────────────────────────
UNDER_FIRE_SPEED_MUL = 1.25
FLINCH_INTENSITY     = 8.0
GRENADE_COOLDOWN     = 120
AK_COOLDOWN          = 8
AK_DAMAGE            = 25
FLAME_COOLDOWN       = 3
FLAME_DAMAGE         = 8
FLAME_RANGE          = 180
FOCUS_MAX            = 100
FOCUS_DRAIN          = 1.5
FOCUS_REGEN          = 0.5
DASH_SPEED           = 12.0
DASH_DURATION        = 12
DASH_COOLDOWN        = 60
GRENADE_RADIUS       = 90
GRENADE_DAMAGE       = 70
GRENADE_FUSE         = 90
TIME_SLOW_FACTOR     = 0.4

# ── Enemy Stats ──────────────────────────────────────────────────────────────
PATROL_HP       = 45
PATROL_SPEED    = 1.4
PATROL_DAMAGE   = 10
PATROL_RANGE    = 200
PATROL_COOLDOWN = 50

SNIPER_HP       = 35
SNIPER_SPEED    = 0.9
SNIPER_DAMAGE   = 30
SNIPER_RANGE    = 420
SNIPER_COOLDOWN = 80

ASSAULT_HP       = 65
ASSAULT_SPEED    = 2.4
ASSAULT_DAMAGE   = 12
ASSAULT_RANGE    = 180
ASSAULT_COOLDOWN = 35

BOSS_HP          = 600
BOSS_SPEED       = 1.6
BOSS_DAMAGE      = 25
BOSS_RANGE       = 450
BOSS_COOLDOWN    = 40

# ── Bullet ───────────────────────────────────────────────────────────────────
BULLET_SPEED      = 11
ENEMY_BULLET_SPD  = 7

# ── Items ────────────────────────────────────────────────────────────────────
ITEM_HEALTH  = "health"
ITEM_AMMO    = "ammo"
ITEM_ARMOR   = "armor"
ITEM_GRENADE = "grenade"
ITEM_RADAR   = "radar"
ITEM_GOLD    = "gold"

# ── Levels ───────────────────────────────────────────────────────────────────
MAX_LEVEL = 6
