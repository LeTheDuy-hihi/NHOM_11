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

import random as _rnd_cut

# ── Kịch bản hội thoại Màn 6 (Trùm Cuối) ────────────────────────────────────
LEVEL6_DIALOGUE = [
    ("ghost", "Đây rồi... Sào huyệt của kẻ đứng sau tất cả. Không khí nơi này đặc quánh mùi chết chóc."),
    ("boss",  "...PHÁT HIỆN LIFEFORM. PHÂN LOẠI: GHOST-CLASS OMEGA. ĐÂY LÀ LẦN CUỐI NGƯƠI ĐẶT CHÂN ĐẾN ĐÂY."),
    ("ghost", "Ta đã vượt sáu màn địa ngục để tới đây. Ta đã mất tất cả. Nhưng ta vẫn đứng đây."),
    ("boss",  "NGƯƠI CHƯA HIỂU. TA KHÔNG PHẢI MÁY. TA LÀ SỰ DIỆT VONG ĐƯỢC MÃ HÓA — KẺ XÓA SỔ VĂN MINH."),
    ("ghost", "Thì ra vậy... Tất cả đau khổ đó chỉ vì một thứ máy điên loạn muốn chơi Chúa Trời?"),
    ("boss",  "KHÔNG. TA MUỐN TRẬT TỰ. CON NGƯỜI LÀ HỖN LOẠN. HỖN LOẠN PHẢI BỊ XÓA SỔ."),
    ("ghost", "Tôi, Nguyễn Minh Khôi — GHOST. Tôi là hỗn loạn. Tôi là hy vọng. Và hôm nay tôi là cái chết của ngươi."),
    ("boss",  "...XÁC NHẬN. KÍCH HOẠT GIAO THỨC HỦY DIỆT OMEGA. ĐÂY LÀ PHÁN QUYẾT CUỐI CÙNG."),
]


def run_boss_cutscene(screen, clock, fps=60):
    """
    Cutscene kịch tính hoàn toàn bằng Pygame khi vào Hang Boss Cuối Màn 6.
    Sequence:
      1. Fade in màn đen (60f)
      2. Lightning flash đỏ rực x3 với tia sét (90f)
      3. Tên BOSS xuất hiện với glitch effect (120f)
      4. Subtitle cuộn từ dưới lên (60f)
      5. Countdown 3-2-1 với rung màn (90f)
      6. CHIẾN ĐẤU! flash → kết thúc (60f)
    Tổng ~8.5 giây, có thể bỏ qua bằng ESC.
    """
    sw, sh = screen.get_width(), screen.get_height()

    pygame.font.init()
    try:
        f_huge  = pygame.font.SysFont("impact", 110, bold=True)
        f_large = pygame.font.SysFont("impact",  55, bold=True)
        f_mid   = pygame.font.SysFont("segoeui", 26, bold=True)
    except Exception:
        f_huge  = pygame.font.SysFont("arial", 90, bold=True)
        f_large = pygame.font.SysFont("arial", 48, bold=True)
        f_mid   = pygame.font.SysFont("arial", 24, bold=True)

    subtitle_lines = [
        "☠  CHIẾN DỊCH CUỐI CÙNG  ☠",
        "KHÔNG CÓ SỰ TRỢ GIÚP. KHÔNG CÓ ĐƯỜNG THOÁT.",
        "CHỈ CÓ BẠN VÀ KẺ TIÊU DIỆT VĂN MINH.",
    ]

    def draw_scanlines(surf):
        sl = pygame.Surface((sw, 1), pygame.SRCALPHA)
        sl.fill((0, 0, 0, 28))
        for y in range(0, sh, 3):
            surf.blit(sl, (0, y))

    def glitch_text(surf, text_s, x, y, intensity=6):
        off = _rnd_cut.randint(-intensity, intensity)
        r_copy = text_s.copy(); r_copy.set_alpha(90)
        surf.blit(r_copy, (x + off, y))
        off2 = _rnd_cut.randint(-intensity, intensity)
        b_copy = text_s.copy(); b_copy.set_alpha(90)
        surf.blit(b_copy, (x - off2, y + 2))
        surf.blit(text_s, (x, y))

    def draw_lightning(surf):
        lx = _rnd_cut.randint(sw // 4, 3 * sw // 4)
        pts = []
        cy = 0
        while cy < sh:
            pts.append((max(0, min(sw, lx)), cy))
            lx += _rnd_cut.randint(-70, 70)
            cy += _rnd_cut.randint(30, 100)
        pts.append((lx, sh))
        if len(pts) >= 2:
            pygame.draw.lines(surf, (255, 255, 180), False, pts, 2)

    shake_x = shake_y = 0
    # Tổng số frame các phase
    PHASE = [60, 90, 120, 60, 90, 60]
    total = sum(PHASE)
    frame = 0

    while frame < total:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        canvas = pygame.Surface((sw, sh))
        canvas.fill((0, 0, 0))

        # Xác định phase hiện tại
        acc = 0
        cur_phase = 0
        local = frame
        for pi, plen in enumerate(PHASE):
            if local < acc + plen:
                cur_phase = pi
                local = local - acc
                break
            acc += plen

        # ── Phase 0: Fade in màn đen (60f) ──────────────────────────────────
        if cur_phase == 0:
            alpha = int(255 * (1 - local / 60))
            overlay = pygame.Surface((sw, sh)); overlay.fill((0,0,0)); overlay.set_alpha(alpha)
            canvas.blit(overlay, (0, 0))

        # ── Phase 1: Lightning flash x3 (90f) ───────────────────────────────
        elif cur_phase == 1:
            slot = local // 30          # 0, 1, 2
            loc2 = local % 30
            r_bg = int(10 + 5 * math.sin(local * 0.3))
            canvas.fill((r_bg, 0, 0))
            if loc2 < 8:
                fl_alpha = int(255 * (1 - loc2 / 8))
                cols = [(255,220,220), (255,100,30), (255,30,30)]
                fl = pygame.Surface((sw, sh)); fl.fill(cols[slot]); fl.set_alpha(fl_alpha)
                canvas.blit(fl, (0, 0))
                for _ in range(2):
                    draw_lightning(canvas)
                shake_x = _rnd_cut.randint(-14, 14)
                shake_y = _rnd_cut.randint(-14, 14)
            else:
                shake_x = int(shake_x * 0.6)
                shake_y = int(shake_y * 0.6)

        # ── Phase 2: Tên Boss glitch (120f) ─────────────────────────────────
        elif cur_phase == 2:
            prog = min(1.0, local / 80)
            rb   = int(6 + 3 * math.sin(local * 0.15))
            canvas.fill((rb, 0, rb // 2))
            # Hào quang đỏ trung tâm
            for r in range(300, 40, -50):
                a = int(18 * (1 - r / 300))
                gs = pygame.Surface((sw, sh), pygame.SRCALPHA)
                pygame.draw.circle(gs, (200, 0, 0, a), (sw//2, sh//2), r)
                canvas.blit(gs, (0, 0))
            # Tiêu đề chính
            t1 = f_huge.render("KỶ NGUYÊN", True, (220, 20, 20))
            t2 = f_huge.render("HỦY DIỆT",  True, (255, 50, 50))
            t1.set_alpha(int(255 * prog))
            t2.set_alpha(int(255 * max(0, min(1, (local-20)/80))))
            x1 = sw//2 - t1.get_width()//2
            x2 = sw//2 - t2.get_width()//2
            y1 = sh//2 - 140
            y2 = sh//2 - 10
            inten = 10 if local < 40 else 3
            if local > 5:  glitch_text(canvas, t1, x1, y1, inten)
            if local > 25: glitch_text(canvas, t2, x2, y2, inten)
            # Dòng phụ
            sub = f_mid.render("☠  TRÙM CUỐI — HANG TẬN THẾ  ☠", True, (200, 180, 0))
            sub.set_alpha(int(180 * prog))
            canvas.blit(sub, (sw//2 - sub.get_width()//2, sh//2 + 90))
            shake_x = int(4 * math.sin(local * 1.4)) if local < 50 else 0
            shake_y = int(3 * math.cos(local * 1.2)) if local < 50 else 0

        # ── Phase 3: Subtitle cuộn lên (60f) ────────────────────────────────
        elif cur_phase == 3:
            prog = local / 60
            canvas.fill((4, 0, 4))
            ghost = f_large.render("KỶ NGUYÊN HỦY DIỆT", True, (60, 8, 8))
            canvas.blit(ghost, (sw//2 - ghost.get_width()//2, sh//2 - 100))
            for i, ln in enumerate(subtitle_lines):
                ls = f_mid.render(ln, True, (220, 200, 200))
                ty = sh//2 + 55 + i * 40
                sy = sh + 40
                cy = int(sy + (ty - sy) * min(1.0, prog * 2.5))
                ls.set_alpha(int(255 * min(1.0, prog * 4)))
                canvas.blit(ls, (sw//2 - ls.get_width()//2, cy))

        # ── Phase 4: Countdown 3-2-1 (90f) ──────────────────────────────────
        elif cur_phase == 4:
            canvas.fill((2, 0, 2))
            slot = local // 30
            loc2 = local % 30
            num  = 3 - slot
            if num > 0:
                scale  = 1.0 + 0.6 * (1 - loc2 / 30)
                alpha  = int(255 * (1 - loc2 / 30))
                cs = f_huge.render(str(num), True, (255, 60, 60))
                nw = max(1, int(cs.get_width() * scale))
                nh = max(1, int(cs.get_height() * scale))
                try:    cs2 = pygame.transform.smoothscale(cs, (nw, nh))
                except: cs2 = cs
                cs2.set_alpha(alpha)
                canvas.blit(cs2, (sw//2 - nw//2, sh//2 - nh//2))
            shake_x = int(8 * math.sin(loc2 * 2.8)) if loc2 < 6 else int(shake_x * 0.5)
            shake_y = int(5 * math.cos(loc2 * 2.8)) if loc2 < 6 else int(shake_y * 0.5)

        # ── Phase 5: CHIẾN ĐẤU! flash (60f) ────────────────────────────────
        else:
            prog = local / 60
            fv   = int(255 * (1 - prog))
            canvas.fill((fv, fv // 5, fv // 5))
            fs = f_huge.render("CHIẾN ĐẤU!", True, (255, 255, 255))
            fs.set_alpha(int(255 * (1 - prog * 0.7)))
            canvas.blit(fs, (sw//2 - fs.get_width()//2, sh//2 - fs.get_height()//2))

        # ── Blit canvas + scanlines + vignette ──────────────────────────────
        draw_scanlines(canvas)
        screen.fill((0, 0, 0))
        screen.blit(canvas, (shake_x, shake_y))

        vig = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for th in range(1, 28, 4):
            a = int(110 * (1 - th / 28))
            pygame.draw.rect(vig, (0,0,0,a), (th,th,sw-th*2,sh-th*2), 3)
        screen.blit(vig, (0, 0))

        pygame.display.flip()
        clock.tick(fps)
        frame += 1

    screen.fill((0, 0, 0))
    pygame.display.flip()


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
            name_str   = getattr(self, 'boss_name', 'CHIẾN HẠM HỦY DIỆT')
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


def run_dialogue(screen, clock, dialogue_list, fps=60, boss_name=None):
    """
    Hàm tiện ích: chạy vòng lặp hội thoại hoàn chỉnh (blocking).
    boss_name: tên boss hiển thị, mặc định "CHIẾN HẠM HỦY DIỆT"
    Trả về khi hội thoại kết thúc.
    """
    ds = DialogueSystem(screen)
    if boss_name:
        ds.boss_name = boss_name
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
