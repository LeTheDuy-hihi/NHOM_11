"""
dialogue.py — Hệ thống hội thoại điện ảnh (Cinematic Dialogue System)
Hiển thị ảnh nhân vật + hộp thoại cuộn chữ trước khi vào màn chơi.
"""

import pygame
import math
import os
import sys
from sound_manager import sound_manager

# ── Màu sắc ──────────────────────────────────────────────────────────────────
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
CYAN        = (0, 220, 255)
RED         = (255, 50, 50)
GOLD        = (255, 210, 60)
GRAY        = (180, 180, 180)
DARK        = (10, 8, 20)

# ── Kịch bản hội thoại Màn 5 ────────────────────────────────────────────────
LEVEL5_DIALOGUE = [
    # (speaker, text)
    # speaker: "ghost" | "boss"
    ("ghost", "Cuối cùng... ta đã tìm ra ngươi, Chiến Hạm Hủy Diệt."),
    ("boss",  "CẢNH BÁO: PHÁT HIỆN XÂM NHẬP. KHỞI ĐỘNG GIAO THỨC TIÊU DIỆT."),
    ("ghost", "Bao nhiêu đồng đội của ta đã ngã xuống vì ngươi. Hôm nay là ngày kết thúc."),
    ("boss",  "ĐƠN VỊ CỦA NGƯƠI ĐÃ BỊ XÓA SỔ. NGƯƠI CŨNG SẼ CHUNG SỐ PHẬN."),
    ("ghost", "Khác biệt là... ta vẫn đang đứng đây. Còn ngươi sắp thành đống sắt vụn."),
    ("boss",  "SỨC MẠNH CỦA NGƯƠI = 0.0001% KHẢ NĂNG CHIẾN ĐẤU CỦA TA. VÔ NGHĨA."),
    ("ghost", "Thật không? Thì hãy thử xem. Tôi, Nguyễn Minh Khôi — GHOST — thách thức ngươi!"),
    ("boss",  "...PHÂN TÍCH HOÀN TẤT. KẺ NÀY LÀ MỐI ĐE DỌA CẤP ĐỘ OMEGA. KHAI HỎA!"),
]

# Kịch bản hội thoại Màn 1 (intro dài)
LEVEL1_DIALOGUE = [
    ("ghost", "Chiến dịch Alpha... Cuối cùng ta cũng đặt chân đến sào huyệt của các người."),
    ("boss", "Phát hiện tín hiệu sống sót đơn độc. Kẻ xâm nhập, ngươi đã bước vào vùng cấm tử địa."),
    ("ghost", "Chỉ huy của ta đâu? Đồng đội của ta đâu? Các người đã tàn sát họ sao?"),
    ("boss", "Căn cứ của các ngươi đã tan tành thành tro bụi. Kẻ yếu thì phải bị nghiền nát. Ngươi là con mồi duy nhất còn sót lại."),
    ("ghost", "Vậy là đủ. Ta không cần viện binh. Ta mang theo sự phẫn nộ của những người đã ngã xuống."),
    ("boss", "Tự tin đến ngu xuẩn. Kẻ thù đang bủa vây mọi lối thoát. Ngươi không có đường lui đâu."),
    ("ghost", "Ta không tìm đường lui. Ta tìm đường xuyên qua xác của các người. Kích hoạt vũ khí!"),
    ("boss", "Giao thức tiêu diệt đã sẵn sàng. Hãy xem ngươi trụ được bao lâu trên chiến trường đẫm máu này.")
]



class DialogueSystem:
    """Hệ thống hội thoại điện ảnh với ảnh nhân vật và chữ cuộn."""

    PORTRAIT_SIZE = (200, 220)
    BOX_H         = 160

    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.sw      = screen.get_width()
        self.sh      = screen.get_height()

        # Font
        pygame.font.init()
        base = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base, "ANH", "SVN-Determination Sans.ttf")
        if os.path.exists(font_path):
            self.font_name = pygame.font.Font(font_path, 18)
            self.font_text = pygame.font.Font(font_path, 16)
        else:
            self.font_name = pygame.font.SysFont("segoeui", 18, bold=True)
            self.font_text = pygame.font.SysFont("segoeui", 16)

        # Load portraits
        self.portraits = {}
        for key, fname in [("ghost", "ghost_portrait.png"), ("boss", "boss_portrait.png")]:
            p = os.path.join(base, "ANH", fname)
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    img = pygame.transform.smoothscale(img, self.PORTRAIT_SIZE)
                    self.portraits[key] = img
                except Exception as e:
                    print(f"Lỗi load portrait {fname}:", e)
                    self.portraits[key] = self._make_placeholder(key)
            else:
                self.portraits[key] = self._make_placeholder(key)

        # Load background
        self.bg_image = None
        bg_path = os.path.join(base, "ANH", "anhnen.png")
        if os.path.exists(bg_path):
            try:
                bg = pygame.image.load(bg_path).convert()
                self.bg_image = pygame.transform.smoothscale(bg, (self.sw, self.sh))
            except Exception as e:
                print(f"Lỗi load ảnh nền: {e}")

        # Trạng thái nội tại
        self.dialogue    = []
        self.index       = 0
        self.char_timer  = 0
        self.revealed    = 0      # số ký tự đã hiện
        self.done        = False
        self.timer       = 0      # frame counter
        self.skip_held   = False

    def _make_placeholder(self, key):
        """Tạo ảnh placeholder nếu không tìm thấy file."""
        surf = pygame.Surface(self.PORTRAIT_SIZE, pygame.SRCALPHA)
        color = (0, 180, 220) if key == "ghost" else (220, 40, 40)
        pygame.draw.rect(surf, color, surf.get_rect(), border_radius=12)
        f = pygame.font.SysFont("arial", 40, bold=True)
        lbl = f.render("?" , True, WHITE)
        surf.blit(lbl, (self.PORTRAIT_SIZE[0]//2 - lbl.get_width()//2,
                        self.PORTRAIT_SIZE[1]//2 - lbl.get_height()//2))
        return surf

    # ── API công khai ────────────────────────────────────────────────────────

    def start(self, dialogue_list):
        """Bắt đầu một chuỗi hội thoại."""
        self.dialogue   = dialogue_list
        self.index      = 0
        self.char_timer = 0
        self.revealed   = 0
        self.done       = False
        self.timer      = 0

    def is_done(self):
        return self.done

    def handle_event(self, event):
        if self.done:
            return
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_SPACE, pygame.K_RETURN, pygame.K_z,
            pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
        ):
            self._advance()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._advance()

    def _advance(self):
        """Nhấn phím/chuột: nếu chưa hiện hết thì hiện hết, nếu rồi thì sang câu tiếp."""
        speaker, text = self.dialogue[self.index]
        if self.revealed < len(text):
            self.revealed = len(text)  # hiện hết tức thì
        else:
            self.index += 1
            self.revealed  = 0
            self.char_timer = 0
            if self.index >= len(self.dialogue):
                self.done = True

    def update(self):
        if self.done or not self.dialogue:
            return
        self.timer += 1
        speaker, text = self.dialogue[self.index]

        # Tốc độ hiện chữ: 2 ký tự mỗi frame, tăng lên 10 khi giữ phím mũi tên
        keys = pygame.key.get_pressed()
        is_speed_up = keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]
        char_step = 10 if is_speed_up else 2

        self.char_timer += 1
        if self.char_timer >= 1:
            self.char_timer = 0
            if self.revealed < len(text):
                self.revealed = min(self.revealed + char_step, len(text))
                sound_interval = 5 if is_speed_up else 3
                if self.timer % sound_interval == 0:
                    try:
                        sound_manager.play('typing')
                    except Exception:
                        pass

    def draw(self):
        if self.done or not self.dialogue:
            return

        speaker, text = self.dialogue[self.index]
        is_ghost = (speaker == "ghost")

        # ── Nền ────────────────────────────────────────
        if getattr(self, "bg_image", None):
            self.screen.blit(self.bg_image, (0, 0))
            overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
        else:
            overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

        # ── Vị trí và màu sắc theo nhân vật ─────────────────────────────────
        box_y  = self.sh - self.BOX_H - 20
        p_size = self.PORTRAIT_SIZE

        if is_ghost:
            portrait_x = 30
            box_x      = portrait_x + p_size[0] + 20
            box_w      = self.sw - box_x - 30
            name_str   = "GHOST"
            name_col   = CYAN
            box_col    = (0, 40, 60, 210)
            border_col = CYAN
            portrait_flip = False
        else:
            portrait_x = self.sw - p_size[0] - 30
            box_x      = 30
            box_w      = portrait_x - box_x - 20
            name_str   = "CHIẾN HẠM HỦY DIỆT"
            name_col   = RED
            box_col    = (60, 0, 0, 210)
            border_col = RED
            portrait_flip = True

        portrait_y = box_y - p_size[1] + self.BOX_H

        # ── Vẽ ảnh nhân vật với hiệu ứng glow ───────────────────────────────
        portrait = self.portraits.get(speaker)
        if portrait:
            if portrait_flip:
                portrait = pygame.transform.flip(portrait, True, False)
            # Bob animation
            bob = int(4 * math.sin(self.timer * 0.08))
            # Glow ring
            glow_surf = pygame.Surface((p_size[0]+20, p_size[1]+20), pygame.SRCALPHA)
            pulse = int(80 + 50 * math.sin(self.timer * 0.1))
            gc = (*border_col[:3], pulse)
            pygame.draw.rect(glow_surf, gc, (0, 0, p_size[0]+20, p_size[1]+20), border_radius=14)
            self.screen.blit(glow_surf, (portrait_x - 10, portrait_y - 10 + bob))
            self.screen.blit(portrait, (portrait_x, portrait_y + bob))

        # ── Hộp thoại ────────────────────────────────────────────────────────
        box_surf = pygame.Surface((box_w, self.BOX_H), pygame.SRCALPHA)
        box_surf.fill(box_col)
        self.screen.blit(box_surf, (box_x, box_y))
        pygame.draw.rect(self.screen, border_col, (box_x, box_y, box_w, self.BOX_H), 2, border_radius=8)

        # Tên nhân vật
        name_lbl = self.font_name.render(name_str, True, name_col)
        self.screen.blit(name_lbl, (box_x + 16, box_y + 12))

        # Đường kẻ tên
        pygame.draw.line(self.screen, border_col,
                         (box_x + 16, box_y + 38),
                         (box_x + name_lbl.get_width() + 16, box_y + 38), 1)

        # Văn bản hội thoại cuộn chữ với word-wrap
        visible_text = text[:self.revealed]
        self._draw_wrapped(visible_text, box_x + 16, box_y + 48, box_w - 32, self.BOX_H - 60)

        # Mũi tên nhấp nháy "nhấn để tiếp"
        if self.revealed >= len(text):
            if (self.timer // 20) % 2 == 0:
                arrow = self.font_text.render("▼ SPACE / CLICK để tiếp", True, GOLD)
                self.screen.blit(arrow, (box_x + box_w - arrow.get_width() - 16,
                                         box_y + self.BOX_H - 26))

        # Số thứ tự hội thoại
        prog = self.font_text.render(f"{self.index+1}/{len(self.dialogue)}", True, (120,120,120))
        self.screen.blit(prog, (box_x + 16, box_y + self.BOX_H - 26))

    def _draw_wrapped(self, text, x, y, max_w, max_h):
        """Vẽ văn bản xuống dòng tự động."""
        words  = text.split(" ")
        lines  = []
        line   = ""
        for word in words:
            test = line + word + " "
            if self.font_text.size(test)[0] > max_w:
                lines.append(line)
                line = word + " "
            else:
                line = test
        lines.append(line)

        line_h = self.font_text.get_linesize() + 4
        for i, ln in enumerate(lines):
            if i * line_h > max_h:
                break
            surf = self.font_text.render(ln, True, WHITE)
            self.screen.blit(surf, (x, y + i * line_h))


def run_dialogue(screen, clock, dialogue_list, fps=60):
    """
    Hàm tiện ích: chạy vòng lặp hội thoại hoàn chỉnh (blocking).
    Trả về khi hội thoại kết thúc.
    """
    ds = DialogueSystem(screen)
    ds.start(dialogue_list)

    while not ds.is_done():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return  # bỏ qua hội thoại
            ds.handle_event(event)

        ds.update()
        ds.draw()
        pygame.display.flip()
        clock.tick(fps)
