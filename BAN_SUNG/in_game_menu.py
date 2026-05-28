# in_game_menu.py — Menu tạm dừng trong game (Pause / Settings)
import pygame
import math
import sys
from constants import *


class InGameSettings:
    """Menu dừng game với điều chỉnh âm lượng và độ sáng theo phong cách tactical."""

    def __init__(self, font_title, font_normal):
        self.font_title  = font_title
        self.font_normal = font_normal

        # Cài đặt mặc định
        self.brightness    = 10   # 0 (tối) → 10 (sáng nhất)
        self.sfx_volume    = 8    # 0-10
        self.music_volume  = 6    # 0-10

        # Các mục trong menu
        self._items = ["ÂM LƯỢNG SFX", "ÂM LƯỢNG NHẠC", "ĐỘ SÁNG", "TIẾP TỤC", "VỀ MENU"]
        self._selected = 0
        self._pulse = 0.0

        # Panel kích thước / vị trí
        self._pw = 460
        self._ph = 380
        self._px = (SCREEN_W - self._pw) // 2
        self._py = (SCREEN_H - self._ph) // 2

    # ── Đồng bộ từ player ────────────────────────────────────────────────────
    def sync_with_player(self, player):
        """Giữ chỗ để tương thích — hiện không cần đọc dữ liệu từ player."""
        pass

    # ── Xử lý sự kiện ────────────────────────────────────────────────────────
    def handle_input(self, event, player, sound_manager=None) -> str:
        """Trả về 'RESUME' nếu cần quay lại game, 'MENU' nếu về main menu, hoặc ''."""
        if event.type != pygame.KEYDOWN:
            return ""

        k = event.key

        if k in (pygame.K_UP, pygame.K_w):
            self._selected = (self._selected - 1) % len(self._items)

        elif k in (pygame.K_DOWN, pygame.K_s):
            self._selected = (self._selected + 1) % len(self._items)

        elif k in (pygame.K_LEFT, pygame.K_a):
            self._adjust(-1, sound_manager)

        elif k in (pygame.K_RIGHT, pygame.K_d):
            self._adjust(+1, sound_manager)

        elif k in (pygame.K_RETURN, pygame.K_SPACE):
            item = self._items[self._selected]
            if item == "TIẾP TỤC":
                return "RESUME"
            elif item == "VỀ MENU":
                return "MENU"

        elif k == pygame.K_ESCAPE or k == pygame.K_p:
            return "RESUME"

        return ""

    def _adjust(self, delta: int, sound_manager=None):
        item = self._items[self._selected]
        if item == "ÂM LƯỢNG SFX":
            self.sfx_volume = max(0, min(10, self.sfx_volume + delta))
            if sound_manager:
                sound_manager.set_sfx_volume(self.sfx_volume / 10.0)
        elif item == "ÂM LƯỢNG NHẠC":
            self.music_volume = max(0, min(10, self.music_volume + delta))
            if sound_manager:
                sound_manager.set_music_volume(self.music_volume / 10.0)
        elif item == "ĐỘ SÁNG":
            self.brightness = max(0, min(10, self.brightness + delta))

    # ── Vẽ ───────────────────────────────────────────────────────────────────
    def draw(self, screen):
        self._pulse += 0.05

        # Overlay mờ toàn màn hình
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        px, py, pw, ph = self._px, self._py, self._pw, self._ph

        # Panel nền
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((12, 18, 28, 220))
        screen.blit(panel, (px, py))

        # Viền neon
        border_col = UI_HIGHLIGHT
        pygame.draw.rect(screen, border_col, (px, py, pw, ph), 2, border_radius=8)

        # Góc cắt tactical
        corner = 16
        for cx, cy, dx, dy in [
            (px, py, 1, 1), (px+pw, py, -1, 1),
            (px, py+ph, 1, -1), (px+pw, py+ph, -1, -1)
        ]:
            pygame.draw.line(screen, UI_HIGHLIGHT, (cx, cy), (cx + dx*corner, cy), 2)
            pygame.draw.line(screen, UI_HIGHLIGHT, (cx, cy), (cx, cy + dy*corner), 2)

        # Tiêu đề
        title = self.font_title.render("⚙  TẠM DỪNG", True, UI_HIGHLIGHT)
        screen.blit(title, (px + pw//2 - title.get_width()//2, py + 18))

        # Đường kẻ dưới tiêu đề
        pygame.draw.line(screen, UI_BORDER,
                         (px + 20, py + 60), (px + pw - 20, py + 60), 1)

        # Các mục menu
        item_y = py + 80
        for i, item_name in enumerate(self._items):
            is_sel = (i == self._selected)

            # Nền highlight khi được chọn
            if is_sel:
                pulse_alpha = int(30 + 20 * math.sin(self._pulse * 4))
                hl = pygame.Surface((pw - 40, 38), pygame.SRCALPHA)
                hl.fill((*UI_HIGHLIGHT[:3], pulse_alpha))
                screen.blit(hl, (px + 20, item_y - 4))
                pygame.draw.rect(screen, UI_HIGHLIGHT, (px + 20, item_y - 4, pw - 40, 38), 1, border_radius=4)
                # Thanh dọc bên trái
                pygame.draw.rect(screen, UI_HIGHLIGHT, (px + 20, item_y - 4, 3, 38), border_radius=2)

            # Màu chữ
            txt_col = UI_HIGHLIGHT if is_sel else UI_TEXT

            # Vẽ tên mục
            lbl = self.font_normal.render(item_name, True, txt_col)
            screen.blit(lbl, (px + 34, item_y + 4))

            # Vẽ giá trị / thanh trượt nếu là cài đặt số
            val_map = {
                "ÂM LƯỢNG SFX":   self.sfx_volume,
                "ÂM LƯỢNG NHẠC":  self.music_volume,
                "ĐỘ SÁNG":        self.brightness,
            }
            if item_name in val_map:
                val = val_map[item_name]
                bar_x = px + pw - 180
                bar_y = item_y + 8
                # nền thanh
                pygame.draw.rect(screen, (20, 25, 35), (bar_x, bar_y, 130, 14), border_radius=3)
                # fill thanh
                fill_w = int(130 * val / 10)
                if fill_w > 0:
                    bar_col = UI_HIGHLIGHT if is_sel else UI_BORDER
                    pygame.draw.rect(screen, bar_col, (bar_x, bar_y, fill_w, 14), border_radius=3)
                # số
                num = self.font_normal.render(str(val), True, txt_col)
                screen.blit(num, (bar_x + 138, bar_y - 2))

            elif item_name in ("TIẾP TỤC", "VỀ MENU"):
                # Hiển thị phím tắt
                hint_col = (80, 100, 120)
                if is_sel:
                    hint_col = (160, 210, 255)
                hint = self.font_normal.render("[ENTER]", True, hint_col)
                screen.blit(hint, (px + pw - hint.get_width() - 30, item_y + 4))

            item_y += 52

        # Chú thích điều khiển dưới cùng
        controls = self.font_normal.render(
            "↑↓ chọn  |  ←→ chỉnh  |  P/ESC tiếp tục", True, UI_TEXT_DIM)
        screen.blit(controls, (px + pw//2 - controls.get_width()//2, py + ph - 30))
