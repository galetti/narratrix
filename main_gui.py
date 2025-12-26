import pygame
import sys
import threading
import math
import os
import pygame.scrap
import warnings

# Unterdrücke die pkg_resources Warnung von Pygame
warnings.filterwarnings("ignore", category=UserWarning, module='pygame')

# --- LOAD SYSTEM ---
from data.story_loader import StoryLoader
import engine.theme as theme # Importiere das neue Theme

from engine.game_state import GameState
from engine.action_dispatcher import ActionDispatcher 
from engine.parser.rule_based import RuleBasedParser

try:
    from engine.parser.spacy_parser import SpacyParser
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

INIT_WIDTH, INIT_HEIGHT = 1024, 768
PARSER_MODE = "SPACY" 

class AssetLoader:
    def __init__(self):
        self.cache = {}
        self.base_path = os.path.join(os.path.dirname(__file__), "data", "assets", "images")
        if not os.path.exists(self.base_path):
            try: os.makedirs(self.base_path)
            except: pass

    def get_image(self, img_id):
        if not img_id: return None
        if img_id in self.cache: return self.cache[img_id]
        found_path = None
        for ext in [".png", ".jpg", ".jpeg"]:
            p = os.path.join(self.base_path, img_id + ext)
            if os.path.exists(p): found_path = p; break
        if found_path:
            try:
                img = pygame.image.load(found_path).convert_alpha()
                self.cache[img_id] = img
                return img
            except Exception as e: print(f"[ERROR] {e}")
        self.cache[img_id] = None
        return None

class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("NARRATRIX v5.4 - Refactored UI") 
        
        try: pygame.scrap.init()
        except pygame.error: print("[WARN] Clipboard konnte nicht initialisiert werden.")

        self.clock = pygame.time.Clock()
        try: 
            self.font_log = pygame.font.SysFont("Consolas", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Verdana", theme.FONT_SIZE_HEADER, bold=True)
            self.font_big = pygame.font.SysFont("Verdana", theme.FONT_SIZE_GAME_OVER, bold=True)
        except: 
            self.font_log = pygame.font.SysFont("Arial", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Arial", theme.FONT_SIZE_HEADER)
            self.font_big = pygame.font.SysFont("Arial", theme.FONT_SIZE_GAME_OVER)

        self.assets = AssetLoader() 
        self.restart_game()

    def restart_game(self):
        """Lädt das Spiel komplett neu."""
        # --- KAPITEL LADEN ---
        initial_config = StoryLoader.load_chapter("data.chapters.ep1_station.config")
        
        if not initial_config:
            print("[FATAL] Konnte Startkapitel nicht laden! Überprüfe data/common und data/chapters.")
            sys.exit(1)

        self.game = GameState(initial_config)
        
        # INPUT STATE RESET
        self.user_text = ""
        self.cursor_pos = 0
        self.cursor_blink = 0
        self.is_processing = False
        self.history = []
        self.history_index = 0
        self.scroll_offset = 0 
        self.line_height = theme.FONT_SIZE_LOG + 4 
        
        self.parser = None
        if PARSER_MODE == "SPACY" and SPACY_AVAILABLE:
            print("Initialisiere Spacy Parser...")
            self.parser = SpacyParser(self.game)
            if not self.parser.available: self.parser = RuleBasedParser(self.game)
        else: self.parser = RuleBasedParser(self.game)

        self.submit_command("look", echo=False)

    def run(self):
        while True:
            self.handle_events(); self.update(); self.draw(); self.clock.tick(30)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            elif event.type == pygame.VIDEORESIZE: self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            # --- GAME OVER HANDLING ---
            if self.game.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                continue

            # --- SCROLLING INPUT (Mausrad) ---
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: # Mausrad Hoch
                    self.scroll_offset += theme.SCROLL_SPEED_MOUSE
                elif event.button == 5: # Mausrad Runter
                    self.scroll_offset -= theme.SCROLL_SPEED_MOUSE
                    if self.scroll_offset < 0: self.scroll_offset = 0
            
            elif event.type == pygame.KEYDOWN:
                if self.is_processing: continue 
                
                # --- NAVIGATION & EDITIERUNG ---
                if event.key == pygame.K_PAGEUP:
                    self.scroll_offset += theme.SCROLL_SPEED_KEY
                elif event.key == pygame.K_PAGEDOWN:
                    self.scroll_offset -= theme.SCROLL_SPEED_KEY
                    if self.scroll_offset < 0: self.scroll_offset = 0
                
                elif event.key == pygame.K_LEFT:
                    self.cursor_pos = max(0, self.cursor_pos - 1)
                    self.cursor_blink = 0 
                elif event.key == pygame.K_RIGHT:
                    self.cursor_pos = min(len(self.user_text), self.cursor_pos + 1)
                    self.cursor_blink = 0
                elif event.key == pygame.K_HOME:
                    self.cursor_pos = 0
                elif event.key == pygame.K_END:
                    self.cursor_pos = len(self.user_text)

                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    snapshot = self.game.get_logs()
                    text_dump = "\n".join([f"{l['type']}: {l['text']}" for l in snapshot])
                    try: pygame.scrap.put(pygame.SCRAP_TEXT, text_dump.encode('utf-8')); print("Clipboard copy success.")
                    except Exception as e: print(f"Clipboard Error: {e}")
                    continue

                elif event.key == pygame.K_RETURN:
                    if self.user_text.strip():
                        cmd = self.user_text
                        self.history.append(cmd)
                        self.history_index = len(self.history)
                        self.user_text = ""
                        self.cursor_pos = 0
                        self.scroll_offset = 0 
                        self.submit_command(cmd)
                elif event.key == pygame.K_UP:
                    if self.history: 
                        self.history_index = max(0, self.history_index - 1)
                        self.user_text = self.history[self.history_index]
                        self.cursor_pos = len(self.user_text) 
                elif event.key == pygame.K_DOWN:
                    if self.history:
                        self.history_index = min(len(self.history), self.history_index + 1)
                        self.user_text = self.history[self.history_index] if self.history_index < len(self.history) else ""
                        self.cursor_pos = len(self.user_text)
                
                elif event.key == pygame.K_BACKSPACE:
                    if self.cursor_pos > 0:
                        self.user_text = self.user_text[:self.cursor_pos-1] + self.user_text[self.cursor_pos:]
                        self.cursor_pos -= 1
                elif event.key == pygame.K_DELETE:
                    if self.cursor_pos < len(self.user_text):
                        self.user_text = self.user_text[:self.cursor_pos] + self.user_text[self.cursor_pos+1:]
                else: 
                    if len(self.user_text) < 120 and event.unicode and not (event.key == pygame.K_TAB):
                        self.user_text = self.user_text[:self.cursor_pos] + event.unicode + self.user_text[self.cursor_pos:]
                        self.cursor_pos += 1

    def submit_command(self, text, echo=True):
        self.is_processing = True
        if echo: self.game.log('user', f"> {text}")
        def worker():
            if self.game.dialogue_active: ActionDispatcher.dialogue_step(self.game, text)
            else: self.parser.parse(text)
            self.is_processing = False
        t = threading.Thread(target=worker); t.start()

    def update(self): self.cursor_blink += 1

    def wrap_text(self, text, font, max_width):
        words = text.split(' '); lines = []; current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            w, h = font.size(test_line)
            if w < max_width: current_line.append(word)
            else: lines.append(' '.join(current_line)); current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    def draw(self):
        snapshot = self.game.get_snapshot()
        self.screen.fill(theme.COLOR_BG); w, h = self.screen.get_size()
        
        # --- GAME OVER SCREEN ---
        if snapshot['game_over']:
            self.draw_game_over(w, h, snapshot)
            pygame.display.flip()
            return

        scene_height = int(h * theme.SCENE_HEIGHT_RATIO); input_height = theme.INPUT_HEIGHT; log_height = h - scene_height - input_height
        rect_scene = pygame.Rect(0, 0, w, scene_height); rect_log = pygame.Rect(0, scene_height, w, log_height); rect_input = pygame.Rect(0, h - input_height, w, input_height)
        self.draw_scene_area(rect_scene, snapshot); self.draw_log_area(rect_log, snapshot); self.draw_input_area(rect_input, snapshot)
        border_col = theme.COLOR_DIALOGUE_BORDER if snapshot['dialogue_active'] else theme.COLOR_UI_BORDER
        pygame.draw.line(self.screen, border_col, (0, scene_height), (w, scene_height), 2)
        pygame.draw.line(self.screen, border_col, (0, h - input_height), (w, h - input_height), 2)
        if self.is_processing: self.draw_loading_spinner(w, h, snapshot)
        pygame.display.flip()

    def draw_game_over(self, w, h, snap):
        # Dunkler roter Hintergrund, pulsierend
        pulse = abs(math.sin(self.cursor_blink * 0.05)) * 50
        base_r, base_g, base_b = theme.COLOR_GAME_OVER_BG
        bg_col = (min(255, base_r + int(pulse)), base_g, base_b)
        self.screen.fill(bg_col)
        
        text_go = self.font_big.render("GAME OVER", True, theme.COLOR_GAME_OVER_TEXT)
        go_rect = text_go.get_rect(center=(w//2, h//3))
        self.screen.blit(text_go, go_rect)
        
        last_logs = [l['text'] for l in snap['logs'] if l['type'] == 'alarm']
        death_msg = last_logs[-1] if last_logs else "Signal verloren."
        
        font_med = pygame.font.SysFont("Arial", 24)
        text_death = font_med.render(death_msg, True, (255, 200, 200))
        death_rect = text_death.get_rect(center=(w//2, h//2))
        self.screen.blit(text_death, death_rect)
        
        if (self.cursor_blink // 20) % 2 == 0:
            text_restart = font_med.render("Drücke [LEERTASTE] für Neustart", True, theme.COLOR_GAME_OVER_TEXT)
            res_rect = text_restart.get_rect(center=(w//2, h//2 + 100))
            self.screen.blit(text_restart, res_rect)

    def draw_scene_area(self, rect, snap):
        bg_color = (20, 20, 30)
        if snap['stability'] < 50 and (self.cursor_blink // 15) % 2 == 0: bg_color = (40, 20, 20)
        pygame.draw.rect(self.screen, bg_color, rect)
        
        max_h = rect.height - 40 
        max_w = int(rect.width * 0.4) 
        area_x = rect.width - max_w - 20
        
        placeholder_w = int(max_h * 1.33)
        if placeholder_w > max_w: placeholder_w = max_w
        placeholder_h = int(placeholder_w / 1.33)
        default_rect = pygame.Rect(rect.width - placeholder_w - 20, 20, placeholder_w, placeholder_h)
        
        room_img = self.assets.get_image(snap['room_img'])
        dialogue_img = self.assets.get_image(snap['dialogue_img']) if snap['dialogue_active'] else None
        
        def get_scaled_rect_and_surf(img, max_w, max_h):
            o_w, o_h = img.get_size()
            aspect = o_w / o_h
            t_h = max_h; t_w = int(t_h * aspect)
            if t_w > max_w: t_w = max_w; t_h = int(t_w / aspect)
            return pygame.Rect(0, 0, t_w, t_h), pygame.transform.smoothscale(img, (t_w, t_h))

        final_visual_rect = default_rect
        bg_surf_to_draw = None
        bg_pos = (0,0)
        
        if room_img:
            r_rect, r_surf = get_scaled_rect_and_surf(room_img, max_w, max_h)
            draw_x = area_x + (max_w - r_rect.width) // 2
            draw_y = 20 + (max_h - r_rect.height) // 2
            bg_pos = (draw_x, draw_y)
            final_visual_rect = pygame.Rect(draw_x, draw_y, r_rect.width, r_rect.height)
            
            if snap['dialogue_active']:
                pixel_scale = 8
                px_w, px_h = max(1, r_surf.get_width() // pixel_scale), max(1, r_surf.get_height() // pixel_scale)
                small = pygame.transform.scale(r_surf, (px_w, px_h))
                pixelated = pygame.transform.scale(small, r_surf.get_size())
                dark_overlay = pygame.Surface(pixelated.get_size()).convert_alpha()
                dark_overlay.fill((0, 0, 0, 160)) 
                pixelated.blit(dark_overlay, (0,0))
                bg_surf_to_draw = pixelated
            else:
                bg_surf_to_draw = r_surf
            self.screen.blit(bg_surf_to_draw, bg_pos)
        else:
            pygame.draw.rect(self.screen, (20, 20, 20), default_rect)
            if not snap['dialogue_active']:
                label_text = f"IMG: {snap['room_img']}"
                label_surf = self.font_log.render(label_text, True, (80, 80, 80))
                label_rect = label_surf.get_rect(center=final_visual_rect.center)
                self.screen.blit(label_surf, label_rect)

        if snap['dialogue_active'] and dialogue_img:
            c_rect, c_surf = get_scaled_rect_and_surf(dialogue_img, max_w, max_h)
            p_draw_x = final_visual_rect.x + (final_visual_rect.width - c_rect.width) // 2
            p_draw_y = final_visual_rect.y + (final_visual_rect.height - c_rect.height) // 2
            self.screen.blit(c_surf, (p_draw_x, p_draw_y))

        border_col = theme.COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else theme.COLOR_UI_BORDER
        pygame.draw.rect(self.screen, border_col, final_visual_rect, 2)

        if snap['dialogue_active']: header_text = snap['dialogue_header']; header_col = theme.COLOR_DIALOGUE_BORDER
        else: header_text = snap['room_name'].upper(); header_col = theme.COLOR_ACCENT
        text_room = self.font_header.render(header_text, True, header_col); self.screen.blit(text_room, (20, 20))
        surf_time = self.font_log.render(f"ZEIT: T+{snap['time']}m", True, theme.COLOR_TEXT); surf_stab = self.font_log.render(f"INTEGRITÄT: {snap['stability']}%", True, theme.COLOR_ACCENT if snap['stability'] > 50 else theme.COLOR_ALERT)
        self.screen.blit(surf_time, (20, 70)); self.screen.blit(surf_stab, (20, 95))

    def draw_log_area(self, rect, snap):
        padding_x = theme.PADDING; padding_y = theme.PADDING
        max_text_width = rect.width - (padding_x * 2)
        
        render_lines = []
        
        for log in snap['logs']: 
            color = theme.COLOR_TEXT; prefix = ""
            if log['type'] == 'user': color = theme.COLOR_USER_ECHO; prefix = ""
            elif log['type'] == 'error': color = (255, 80, 80)
            elif log['type'] == 'success': color = theme.COLOR_ACCENT
            elif log['type'] == 'event': color = (255, 200, 50)
            elif log['type'] == 'alarm': color = theme.COLOR_ALERT
            elif log['type'] == 'location': color = theme.COLOR_ACCENT
            elif log['type'] == 'character': color = (100, 200, 255)
            elif log['type'] == 'story': color = (220, 220, 220)
            elif log['type'] == 'info': color = theme.COLOR_INFO
            
            raw_lines = (prefix + log['text']).split('\n')
            for raw_line in raw_lines:
                wrapped = self.wrap_text(raw_line, self.font_log, max_text_width)
                for line in wrapped:
                    render_lines.append((line, color))
        
        total_content_height = len(render_lines) * self.line_height
        visible_height = rect.height - (2 * padding_y)
        
        max_scroll = max(0, total_content_height - visible_height)
        
        if self.scroll_offset > max_scroll: self.scroll_offset = max_scroll
        if self.scroll_offset < 0: self.scroll_offset = 0
        
        bottom_draw_y = rect.bottom - padding_y - self.line_height + self.scroll_offset
        current_y = bottom_draw_y
        
        for text, color in reversed(render_lines):
            if current_y + self.line_height > rect.top and current_y < rect.bottom:
                text_surf = self.font_log.render(text, True, color)
                self.screen.blit(text_surf, (padding_x, current_y))
            
            current_y -= self.line_height
            if current_y < rect.top - 50:
                break
        
        if max_scroll > 0:
            scroll_ratio = self.scroll_offset / max_scroll
            bar_height = max(20, (visible_height / total_content_height) * visible_height)
            bar_y = rect.bottom - padding_y - bar_height - (scroll_ratio * (visible_height - bar_height))
            
            pygame.draw.rect(self.screen, (60, 60, 80), (rect.right - 10, rect.top + padding_y, 4, visible_height))
            pygame.draw.rect(self.screen, theme.COLOR_ACCENT, (rect.right - 10, bar_y, 4, bar_height))

    def draw_input_area(self, rect, snap):
        pygame.draw.rect(self.screen, (0, 0, 0), rect)
        padding = theme.PADDING
        prompt = "> "
        
        col_prompt = theme.COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else theme.COLOR_ACCENT
        surf_prompt = self.font_log.render(prompt, True, col_prompt)
        self.screen.blit(surf_prompt, (rect.x + padding, rect.y + padding))
        prompt_w = surf_prompt.get_width()
        
        surf_text = self.font_log.render(self.user_text, True, theme.COLOR_INPUT)
        self.screen.blit(surf_text, (rect.x + padding + prompt_w, rect.y + padding))
        
        cursor_str = self.user_text[:self.cursor_pos]
        cursor_offset_x = self.font_log.size(cursor_str)[0]
        
        if (self.cursor_blink // theme.CURSOR_BLINK_SPEED) % 2 == 0:
            cursor_x = rect.x + padding + prompt_w + cursor_offset_x
            cursor_y = rect.y + padding
            cursor_h = surf_text.get_height()
            pygame.draw.line(self.screen, theme.COLOR_INPUT, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_h), 2)

    def draw_loading_spinner(self, w, h, snap):
        center_x, center_y = w - 30, h - 25; angle = (self.cursor_blink * theme.CURSOR_BLINK_SPEED) % 360; radius = 10
        end_x = center_x + radius * math.cos(math.radians(angle)); end_y = center_y + radius * math.sin(math.radians(angle))
        col = theme.COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else theme.COLOR_LOADING
        pygame.draw.circle(self.screen, col, (center_x, center_y), radius, 1); pygame.draw.line(self.screen, col, (center_x, center_y), (end_x, end_y), 2)

if __name__ == "__main__":
    gui = GameGUI()
    gui.run()