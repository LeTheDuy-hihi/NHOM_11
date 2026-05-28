import re

with open("menu.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update image scale from (48, 48) to (96, 96)
content = content.replace("img = pygame.transform.smoothscale(img, (48, 48))", "img = pygame.transform.smoothscale(img, (96, 96))")

# 2. Add inventory variables in __init__
init_target = """        # Initialize menu items slide-right offsets
        self.menu_offsets = [0.0] * len(self.menu_items)"""
init_replace = """        # Initialize menu items slide-right offsets
        self.menu_offsets = [0.0] * len(self.menu_items)
        
        self.inventory_tab = 0
        self.inventory_focus = "TABS"
        self.inventory_selected_index = 0"""
content = content.replace(init_target, init_replace)

# 3. Add KEYDOWN for INVENTORY
keydown_target = """                            else:
                                if self._buy_item(g): sound_manager.play('pickup')
                                else: sound_manager.play('error')

            elif self.state == "MISSIONS":"""
keydown_replace = """                            else:
                                if self._buy_item(g): sound_manager.play('pickup')
                                else: sound_manager.play('error')

            elif self.state == "INVENTORY":
                if self.inventory_focus == "TABS":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.inventory_tab = (self.inventory_tab - 1) % len(self.inventory_catalog)
                        self.inventory_selected_index = 0
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.inventory_tab = (self.inventory_tab + 1) % len(self.inventory_catalog)
                        self.inventory_selected_index = 0
                        sound_manager.play('menu_select')
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.inventory_focus = "ITEMS"
                        self.inventory_selected_index = 0
                elif self.inventory_focus == "ITEMS":
                    items = self.inventory_catalog[self.inventory_tab][2]
                    idx = self.inventory_selected_index
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.inventory_selected_index = (idx - 1) % len(items)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.inventory_selected_index = (idx + 1) % len(items)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if idx < 2:
                            self.inventory_focus = "TABS"
                        else:
                            self.inventory_selected_index = idx - 2
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if idx + 2 < len(items):
                            self.inventory_selected_index = idx + 2
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        item = items[idx]
                        if self._buy_item(item["name"]):
                            sound_manager.play('pickup')
                        else:
                            sound_manager.play('error')

            elif self.state == "MISSIONS":"""
content = content.replace(keydown_target, keydown_replace)

# 4. Add MOUSEMOTION for INVENTORY
mousemotion_target = """                            self.loadout_focus = "ITEMS"
                            self.loadout_selected_index = gi

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:"""
mousemotion_replace = """                            self.loadout_focus = "ITEMS"
                            self.loadout_selected_index = gi

            elif self.state == "INVENTORY":
                if hasattr(self, "_inv_tab_rects"):
                    for ti, rect in enumerate(self._inv_tab_rects):
                        if rect.collidepoint(mpos):
                            self.inventory_focus = "TABS"
                            self.inventory_tab = ti
                if hasattr(self, "_inventory_rects"):
                    for name, rect in self._inventory_rects.items():
                        if rect.collidepoint(mpos):
                            self.inventory_focus = "ITEMS"
                            items = self.inventory_catalog[self.inventory_tab][2]
                            for ii, it in enumerate(items):
                                if it["name"] == name:
                                    self.inventory_selected_index = ii
                                    break

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:"""
content = content.replace(mousemotion_target, mousemotion_replace)

# 5. Add MOUSEBUTTONDOWN for INVENTORY
# Original INVENTORY MOUSEBUTTONDOWN logic
mbd_target = """            elif self.state == "INVENTORY":
                if hasattr(self, "_inventory_rects"):
                    for name, rect in self._inventory_rects.items():
                        if rect.collidepoint(mpos):
                            if self._buy_item(name):
                                sound_manager.play('pickup')
                            else:
                                sound_manager.play('error')
                            break
                panel_rect = pygame.Rect(SCREEN_W//2-480, 45, 960, 710)
                if not panel_rect.collidepoint(mpos):
                    self.state = "MAIN\"\"\"""" # Will use regex

mbd_replace = """            elif self.state == "INVENTORY":
                clicked = False
                if hasattr(self, "_inv_tab_rects"):
                    for ti, rect in enumerate(self._inv_tab_rects):
                        if rect.collidepoint(mpos):
                            self.inventory_tab = ti
                            self.inventory_focus = "ITEMS"
                            self.inventory_selected_index = 0
                            clicked = True
                            break
                if not clicked and hasattr(self, "_inventory_rects"):
                    for name, rect in self._inventory_rects.items():
                        if rect.collidepoint(mpos):
                            self.inventory_focus = "ITEMS"
                            items = self.inventory_catalog[self.inventory_tab][2]
                            for ii, it in enumerate(items):
                                if it["name"] == name:
                                    self.inventory_selected_index = ii
                                    break
                            if self._buy_item(name):
                                sound_manager.play('pickup')
                            else:
                                sound_manager.play('error')
                            clicked = True
                            break
                panel_rect = pygame.Rect(SCREEN_W//2-480, 45, 960, 710)
                if not clicked and not panel_rect.collidepoint(mpos):
                    self.state = "MAIN\"\"\""""

pattern_mbd = re.compile(r'elif self\.state == "INVENTORY":\s*if hasattr\(self, "_inventory_rects"\):.*?if not panel_rect\.collidepoint\(mpos\):\s*self\.state = "MAIN"', re.DOTALL)
content = re.sub(pattern_mbd, mbd_replace.strip().rstrip('\"'), content)

# 6. Replace _draw_inventory entirely
draw_inventory_new = """    def _draw_inventory(self, screen):
        panel = Panel(SCREEN_W//2-480, 45, 960, 710, "KHO ĐỒ — INVENTORY VAULT")
        panel.draw(screen, self.font_normal)

        gold_txt = self.font_normal.render(f"VÀNG: {self.gold} $", True, (255, 215, 0))
        screen.blit(gold_txt, (SCREEN_W//2 + 480 - gold_txt.get_width() - 20, 55))

        rarity_col = {
            "THƯỜNG": (110, 120, 130), "HIẾM": (60, 140, 200),
            "SỬ THI": (160, 90, 210), "HUYỀN THOẠI": (210, 140, 20), "SIÊU HIẾM": (200, 80, 200)
        }

        mouse_pos = pygame.mouse.get_pos()
        mx_cur, my_cur = mouse_pos
        cur_tilt_x = int((mx_cur - SCREEN_W / 2) / (SCREEN_W / 2) * 12)
        cur_tilt_y = int((my_cur - SCREEN_H / 2) / (SCREEN_H / 2) * 12)
        mpos = (mx_cur - cur_tilt_x, my_cur - cur_tilt_y)

        # ── TABS ──
        self._inv_tab_rects = []
        tab_w = 210
        tab_h = 40
        tab_gap = 15
        num_tabs = len(self.inventory_catalog)
        total_tab_w = num_tabs * tab_w + (num_tabs - 1) * tab_gap
        tab_start_x = SCREEN_W // 2 - total_tab_w // 2
        grid_y = 110

        for ti, (cat_name, cc, items) in enumerate(self.inventory_catalog):
            tx = tab_start_x + ti * (tab_w + tab_gap)
            tr = pygame.Rect(tx, grid_y, tab_w, tab_h)
            self._inv_tab_rects.append(tr)
            
            is_active = (self.inventory_tab == ti)
            is_hov = tr.collidepoint(mpos)
            is_focused = (self.inventory_focus == "TABS" and self.inventory_tab == ti)
            
            tbg = pygame.Surface((tab_w, tab_h), pygame.SRCALPHA)
            if is_focused:
                tbg.fill((*cc, 80)); tc = cc; border_w = 3
            elif is_active:
                tbg.fill((*cc, 40)); tc = cc; border_w = 2
            elif is_hov:
                tbg.fill((255, 255, 255, 15)); tc = WHITE; border_w = 1
            else:
                tbg.fill((10, 15, 10, 180)); tc = (130, 140, 130); border_w = 1
                
            screen.blit(tbg, (tx, grid_y))
            pygame.draw.rect(screen, tc, tr, border_w, border_radius=2)
            
            txt_surf = self.font_small.render(cat_name, True, tc)
            screen.blit(txt_surf, (tx + (tab_w - txt_surf.get_width()) // 2, grid_y + (tab_h - txt_surf.get_height()) // 2))

        # ── ITEMS GRID ──
        self._inventory_rects = {}
        cat_name, cc, items = self.inventory_catalog[self.inventory_tab]
        
        card_w, card_h = 420, 220
        w_gap, h_gap = 25, 20
        grid_x0 = SCREEN_W // 2 - (card_w * 2 + w_gap) // 2
        grid_y0 = 175

        for ii, item in enumerate(items):
            col = ii % 2
            row = ii // 2
            ix = grid_x0 + col * (card_w + w_gap)
            iy = grid_y0 + row * (card_h + h_gap)
            
            ir = pygame.Rect(ix, iy, card_w, card_h)
            self._inventory_rects[item["name"]] = ir
            
            is_hov = ir.collidepoint(mpos)
            is_focused = (self.inventory_focus == "ITEMS" and self.inventory_selected_index == ii)
            
            rc = rarity_col.get(item["rarity"], (130, 145, 160))
            if is_focused: wc = (235, 120, 0)
            elif is_hov: wc = WHITE
            else: wc = rc
            
            cb = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            if is_focused: cb.fill((235, 120, 0, 30))
            elif is_hov: cb.fill((255, 255, 255, 15))
            else: 
                cb.fill((8, 10, 12, 235))
                tint = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                tint.fill((*rc, 6))
                cb.blit(tint, (0, 0))
            
            screen.blit(cb, (ix, iy))
            pygame.draw.rect(screen, wc, ir, 2 if is_focused else 1, border_radius=2)
            
            for dx, dy in [(1,1), (-1,1), (1,-1), (-1,-1)]:
                c_x = ix if dx==1 else ix+card_w
                c_y = iy if dy==1 else iy+card_h
                pygame.draw.line(screen, wc, (c_x, c_y), (c_x+8*dx, c_y), 1)
                pygame.draw.line(screen, wc, (c_x, c_y), (c_x, c_y+8*dy), 1)

            name_s = self.font_normal.render(item["name"], True, wc)
            screen.blit(name_s, (ix + 130, iy + 20))
            
            # Big Icon Area
            self._draw_item_icon(screen, item["name"], pygame.Rect(ix + 15, iy + 55, 96, 96), rc)
            
            desc_words = item["desc"].split(" ")
            desc_lines = []
            cur_line = ""
            for dw in desc_words:
                test_t = cur_line + dw + " "
                if self.font_small.size(test_t)[0] > card_w - 140:
                    desc_lines.append(cur_line.strip())
                    cur_line = dw + " "
                else: cur_line = test_t
            desc_lines.append(cur_line.strip())
            
            for dli, dl in enumerate(desc_lines[:3]):
                dl_s = self.font_small.render(dl, True, (160, 170, 180))
                screen.blit(dl_s, (ix + 130, iy + 65 + dli * 18))
                
            if "effect" in item:
                eff_s = self.font_small.render(f"Hiệu ứng: {item['effect']}", True, (245, 165, 30))
                screen.blit(eff_s, (ix + 130, iy + 130))
                
            qty = self.inventory.get(item["name"], 0)
            qty_s = self.font_small.render(f"SỞ HỮU: {qty}", True, (100, 180, 80) if qty > 0 else (130, 140, 150))
            screen.blit(qty_s, (ix + 15, iy + 165))
            
            price = item.get("price", self.prices.get(item["name"], 0))
            btn_txt = f"{price} $"
            btn_color = (220, 60, 50) if self.gold < price else (245, 165, 30)
            if is_focused and self.gold >= price: btn_color = (255, 255, 100)
            
            btn_s = self.font_small.render(btn_txt, True, btn_color)
            btn_w = btn_s.get_width() + 16
            pygame.draw.rect(screen, btn_color, (ix + card_w - btn_w - 15, iy + card_h - 40, btn_w, 24), 1, border_radius=2)
            screen.blit(btn_s, (ix + card_w - btn_w - 7, iy + card_h - 38))

        ty = SCREEN_H - 80
        pygame.draw.line(screen, (42, 52, 65), (SCREEN_W//2-455, ty), (SCREEN_W//2+455, ty), 1)
        tip = self.font_small.render("CLICK hoặc MŨI TÊN/ENTER để chọn vật phẩm  •  ESC Quay lại sảnh chờ", True, (88, 98, 115))
        screen.blit(tip, (SCREEN_W//2-tip.get_width()//2, ty+12))"""

pattern_draw = re.compile(r'    def _draw_inventory\(self, screen\):.*?def _draw_missions\(self, screen\):', re.DOTALL)
content = re.sub(pattern_draw, draw_inventory_new + "\n\n    def _draw_missions(self, screen):", content)

with open("menu.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated menu.py successfully!")
