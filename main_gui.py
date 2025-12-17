import pygame
import sys
import threading
import math
import os
import pygame.scrap

from data.story_config import CONFIG
from engine.game_state import GameState
from engine.action_dispatcher import ActionDispatcher 
from engine.parser.rule_based import RuleBasedParser

try:
    from engine.parser.spacy_parser import SpacyParser
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("[WARN] Spacy Modul nicht gefunden.")

INIT_WIDTH, INIT_HEIGHT = 1024, 768
COLOR_BG = (10, 10, 15); COLOR_UI_BORDER = (40, 40, 60); COLOR_TEXT = (200, 200, 200)
COLOR_ACCENT = (0, 255, 136); COLOR_ALERT = (255, 50, 50); COLOR_INPUT = (255, 255, 255)
COLOR_LOADING = (255, 200, 0); COLOR_USER_ECHO = (150, 150, 150); COLOR_DIALOGUE_BORDER = (0, 150, 255)
FONT_SIZE_LOG = 18; FONT_SIZE_HEADER = 32
PARSER_MODE = "SPACY" 

class AssetLoader:
    """Lädt Bilder aus dem Content-Ordner (data/assets) und cacht sie."""
    def __init__(self):
        self.cache = {}
        # Pfad zeigt in den data Ordner
        self.base_path = os.path.join(os.path.dirname(__file__), "data", "assets", "images")
        
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path)
                print(f"[SYSTEM] Asset-Ordner erstellt: {self.base_path}")
            except: pass

    def get_image(self, img_id):
        """Lädt das Originalbild (ohne Skalierung)."""
        if not img_id: return None
        
        if img_id in self.cache:
            return self.cache[img_id]
            
        found_path = None
        for ext in [".png", ".jpg", ".jpeg"]:
            p = os.path.join(self.base_path, img_id + ext)
            if os.path.exists(p):
                found_path = p
                break
        
        if found_path:
            try:
                img = pygame.image.load(found_path).convert()
                self.cache[img_id] = img
                return img
            except Exception as e:
                print(f"[ERROR] Konnte Bild {found_path} nicht laden: {e}")
                
        self.cache[img_id] = None
        return None

class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("NARRATRIX v4.2 - Proportional Images")
        
        try: pygame.scrap.init()
        except pygame.error: print("[WARN] Clipboard konnte nicht initialisiert werden.")

        self.clock = pygame.time.Clock()
        try: self.font_log = pygame.font.SysFont("Consolas", FONT_SIZE_LOG); self.font_header = pygame.font.SysFont("Verdana", FONT_SIZE_HEADER, bold=True)
        except: self.font_log = pygame.font.SysFont("Arial", FONT_SIZE_LOG); self.font_header = pygame.font.SysFont("Arial", FONT_SIZE_HEADER)

        self.game = GameState(CONFIG)
        self.assets = AssetLoader() 
        
        self.user_text = ""; self.cursor_blink = 0; self.is_processing = False
        self.history = []; self.history_index = 0
        
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
            elif event.type == pygame.KEYDOWN:
                if self.game.game_over: continue
                if self.is_processing: continue 
                
                if event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    snapshot = self.game.get_logs()
                    text_dump = "\n".join([f"{l['type']}: {l['text']}" for l in snapshot])
                    try: pygame.scrap.put(pygame.SCRAP_TEXT, text_dump.encode('utf-8')); print("Clipboard copy success.")
                    except Exception as e: print(f"Clipboard Error: {e}")
                    continue

                if event.key == pygame.K_RETURN:
                    if self.user_text.strip():
                        cmd = self.user_text; self.history.append(cmd); self.history_index = len(self.history); self.user_text = ""; self.submit_command(cmd)
                elif event.key == pygame.K_UP:
                    if self.history: self.history_index = max(0, self.history_index - 1); self.user_text = self.history[self.history_index]
                elif event.key == pygame.K_DOWN:
                    if self.history:
                        self.history_index = min(len(self.history), self.history_index + 1)
                        self.user_text = self.history[self.history_index] if self.history_index < len(self.history) else ""
                elif event.key == pygame.K_BACKSPACE: self.user_text = self.user_text[:-1]
                else: 
                    if len(self.user_text) < 120: self.user_text += event.unicode

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
        self.screen.fill(COLOR_BG); w, h = self.screen.get_size()
        scene_height = int(h * 0.4); input_height = 50; log_height = h - scene_height - input_height
        rect_scene = pygame.Rect(0, 0, w, scene_height); rect_log = pygame.Rect(0, scene_height, w, log_height); rect_input = pygame.Rect(0, h - input_height, w, input_height)
        self.draw_scene_area(rect_scene, snapshot); self.draw_log_area(rect_log, snapshot); self.draw_input_area(rect_input, snapshot)
        border_col = COLOR_DIALOGUE_BORDER if snapshot['dialogue_active'] else COLOR_UI_BORDER
        pygame.draw.line(self.screen, border_col, (0, scene_height), (w, scene_height), 2)
        pygame.draw.line(self.screen, border_col, (0, h - input_height), (w, h - input_height), 2)
        if self.is_processing: self.draw_loading_spinner(w, h, snapshot)
        pygame.display.flip()

    def draw_scene_area(self, rect, snap):
        bg_color = (20, 20, 30)
        if snap['stability'] < 50 and (self.cursor_blink // 15) % 2 == 0: bg_color = (40, 20, 20)
        pygame.draw.rect(self.screen, bg_color, rect)
        
        # Maximaler Platz für das Bild
        max_h = rect.height - 40 
        max_w = int(rect.width * 0.4) 
        
        img_x = rect.width - max_w - 20
        img_y = 20
        
        # Standard-Platzhalter Rechteck (4:3)
        placeholder_w = int(max_h * 1.33)
        if placeholder_w > max_w: placeholder_w = max_w
        placeholder_h = int(placeholder_w / 1.33)
        
        final_img_rect = pygame.Rect(rect.width - placeholder_w - 20, 20, placeholder_w, placeholder_h)
        
        img_id = snap['dialogue_img'] if snap['dialogue_active'] else snap['room_img']
        original_img = self.assets.get_image(img_id)
        
        if original_img:
            # Skalierung berechnen (Fit inside)
            o_w, o_h = original_img.get_size()
            aspect = o_w / o_h
            
            # Versuche, Höhe zu maximieren
            target_h = max_h
            target_w = int(target_h * aspect)
            
            # Wenn zu breit, limitiere Breite
            if target_w > max_w:
                target_w = max_w
                target_h = int(target_w / aspect)
            
            # Zentrieren im verfügbaren Bereich (rechtsbündig)
            # Bereich ist (rect.width - max_w - 20) bis (rect.width - 20)
            area_x = rect.width - max_w - 20
            # Zentriere das Bild in diesem Bereich horizontal
            draw_x = area_x + (max_w - target_w) // 2
            draw_y = 20 + (max_h - target_h) // 2
            
            final_img_rect = pygame.Rect(draw_x, draw_y, target_w, target_h)
            
            scaled_img = pygame.transform.smoothscale(original_img, (target_w, target_h))
            self.screen.blit(scaled_img, (draw_x, draw_y))
            
            border_col = COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else COLOR_UI_BORDER
            pygame.draw.rect(self.screen, border_col, final_img_rect, 2)
            
        else:
            # Fallback: Platzhalter zeichnen
            pygame.draw.rect(self.screen, (0, 0, 0), final_img_rect)
            border_col = COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else COLOR_UI_BORDER
            pygame.draw.rect(self.screen, border_col, final_img_rect, 2)
            if snap['dialogue_active']: label_text = f"PORTRAIT: {img_id}"; col_label = COLOR_DIALOGUE_BORDER
            else: label_text = f"IMG: {img_id}"; col_label = (80, 80, 80)
            label_surf = self.font_log.render(label_text, True, col_label); label_rect = label_surf.get_rect(center=final_img_rect.center)
            self.screen.blit(label_surf, label_rect)

        if snap['dialogue_active']: header_text = snap['dialogue_header']; header_col = COLOR_DIALOGUE_BORDER
        else: header_text = snap['room_name'].upper(); header_col = COLOR_ACCENT
        text_room = self.font_header.render(header_text, True, header_col); self.screen.blit(text_room, (20, 20))
        surf_time = self.font_log.render(f"ZEIT: T+{snap['time']}m", True, COLOR_TEXT); surf_stab = self.font_log.render(f"INTEGRITÄT: {snap['stability']}%", True, COLOR_ACCENT if snap['stability'] > 50 else COLOR_ALERT)
        self.screen.blit(surf_time, (20, 70)); self.screen.blit(surf_stab, (20, 95))

    def draw_log_area(self, rect, snap):
        padding_x = 20; padding_y = 10; line_height = FONT_SIZE_LOG + 4
        bottom_y = rect.bottom - padding_y - line_height; current_y = bottom_y; max_text_width = rect.width - (padding_x * 2)
        
        for log in reversed(snap['logs']):
            color = COLOR_TEXT; prefix = ""
            if log['type'] == 'user': color = COLOR_USER_ECHO; prefix = ""
            elif log['type'] == 'error': color = (255, 80, 80)
            elif log['type'] == 'success': color = COLOR_ACCENT
            elif log['type'] == 'event': color = (255, 200, 50)
            elif log['type'] == 'alarm': color = COLOR_ALERT
            elif log['type'] == 'location': color = COLOR_ACCENT
            elif log['type'] == 'character': color = (100, 200, 255)
            elif log['type'] == 'story': color = (220, 220, 220)
            
            wrapped_lines = self.wrap_text(prefix + log['text'], self.font_log, max_text_width)
            for line in reversed(wrapped_lines):
                if current_y < rect.top: break
                text_surf = self.font_log.render(line, True, color); self.screen.blit(text_surf, (padding_x, current_y)); current_y -= line_height
            if current_y < rect.top: break

    def draw_input_area(self, rect, snap):
        pygame.draw.rect(self.screen, (0, 0, 0), rect); padding = 10; prompt = "> " if (self.cursor_blink // 20) % 2 == 0 else ">_"
        col_prompt = COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else COLOR_ACCENT
        surf_prompt = self.font_log.render(prompt, True, col_prompt); surf_text = self.font_log.render(self.user_text, True, COLOR_INPUT)
        self.screen.blit(surf_prompt, (rect.x + padding, rect.y + padding)); self.screen.blit(surf_text, (rect.x + padding + 30, rect.y + padding))

    def draw_loading_spinner(self, w, h, snap):
        center_x, center_y = w - 30, h - 25; angle = (self.cursor_blink * 15) % 360; radius = 10
        end_x = center_x + radius * math.cos(math.radians(angle)); end_y = center_y + radius * math.sin(math.radians(angle))
        col = COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else COLOR_LOADING
        pygame.draw.circle(self.screen, col, (center_x, center_y), radius, 1); pygame.draw.line(self.screen, col, (center_x, center_y), (end_x, end_y), 2)

if __name__ == "__main__":
    gui = GameGUI()
    gui.run()