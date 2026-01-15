# narratrix_engine/main_gui.py
import pygame
import sys
import threading
import math
import os
import re 
import pygame.scrap
import warnings
import queue
import json 

warnings.filterwarnings("ignore", category=UserWarning, module='pygame')

# --- LOAD SYSTEM ---
from engine.story_loader import StoryLoader
import engine.theme as theme

from engine.game_state import GameState
from engine.action_dispatcher import ActionDispatcher 
from engine.parser.rule_based import RuleBasedParser
from engine.constants import LOC_INVENTORY

try:
    from engine.parser.spacy_parser import SpacyParser
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("[SYSTEM] Spacy nicht gefunden, nutze RuleBasedParser.")

# NEU: Config Loader aus 'data/' Verzeichnis
def load_system_config():
    default_conf = {
        "game": {"start_chapter": "data.chapters.ep0_arrival.config", "title": "Narratrix"},
        "system": {"resolution_width": 1024, "resolution_height": 768}
    }
    
    # Pfadänderung: Config liegt jetzt in data/config.json
    base_path = os.path.dirname(__file__)
    config_path = os.path.join(base_path, "data", "config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "game" in data: default_conf["game"].update(data["game"])
                if "system" in data: default_conf["system"].update(data["system"])
                print(f"[SYSTEM] Config geladen von: {config_path}")
                return default_conf
        except Exception as e:
            print(f"[WARN] Konnte data/config.json nicht lesen: {e}")
    else:
        print(f"[INFO] Keine Config gefunden unter {config_path}, nutze Defaults.")
    
    return default_conf

SYS_CONFIG = load_system_config()
INIT_WIDTH = SYS_CONFIG["system"].get("resolution_width", 1024)
INIT_HEIGHT = SYS_CONFIG["system"].get("resolution_height", 768)
PARSER_MODE = "SPACY" 

class RichTextRenderer:
    def __init__(self, font, default_color):
        self.font = font
        self.default_color = default_color
        self.color_map = {
            "alert": theme.COLOR_ALERT,   
            "alarm": theme.COLOR_ALERT,
            "success": theme.COLOR_ACCENT, 
            "accent": theme.COLOR_ACCENT,
            "info": theme.COLOR_INFO,      
            "cmd": (255, 255, 255),        
            "user": theme.COLOR_USER_ECHO, 
            "char": (100, 200, 255),       
            "story": (220, 220, 220),      
            "yellow": (255, 200, 50),
            "red": (255, 80, 80),
            "blue": (100, 200, 255),
            "header": (255, 255, 100)
        }
        self.tag_pattern = re.compile(r'(<[/a-zA-Z0-9]+>)')

    def parse_and_wrap(self, text, max_width, base_color=None):
        if base_color is None: base_color = self.default_color
        
        # Newlines
        raw_lines = text.split('\n')
        all_wrapped_lines = []
        
        for raw_line in raw_lines:
            if not raw_line:
                all_wrapped_lines.append([{'text': " ", 'color': base_color, 'width': 0, 'raw': ""}])
                continue

            parts = self.tag_pattern.split(raw_line)
            segments = [] 
            color_stack = [base_color]
            
            for part in parts:
                if not part: continue
                
                # Tag check
                if part.startswith("<") and part.endswith(">"):
                    tag_content = part[1:-1]
                    if tag_content.startswith("/"): 
                        if len(color_stack) > 1: color_stack.pop()
                    else: 
                        if tag_content in self.color_map:
                            color_stack.append(self.color_map[tag_content])
                    # WICHTIG: Tags selbst nie rendern!
                    continue 
                
                words = part.split(' ')
                current_col = color_stack[-1]
                
                for i, w in enumerate(words):
                    if w:
                        w_width = self.font.size(w)[0]
                        segments.append({'text': w, 'color': current_col, 'width': w_width, 'raw': w})
                    elif i < len(words)-1:
                         sp_w = self.font.size(" ")[0]
                         segments.append({'text': " ", 'color': current_col, 'width': sp_w, 'raw': ""})

            # Wrapping
            current_line = []
            current_width = 0
            space_width = self.font.size(" ")[0]
            
            for seg in segments:
                seg_w = seg['width']
                needs_space = False
                add_width = seg_w
                
                if current_line and seg['text'] != " " and current_line[-1][0]['text'] != " ":
                     needs_space = True
                     add_width += space_width

                if current_width + add_width <= max_width:
                    if needs_space:
                         space_dict = {'text': " ", 'color': seg['color'], 'width': space_width, 'raw': " "}
                         current_line.append((space_dict, space_width)) 
                         current_width += space_width
                    
                    current_line.append((seg, seg_w))
                    current_width += seg_w
                else:
                    all_wrapped_lines.append([s[0] for s in current_line])
                    current_line = [(seg, seg_w)]
                    current_width = seg_w
                    
            if current_line:
                all_wrapped_lines.append([s[0] for s in current_line])
        
        return all_wrapped_lines

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
            except Exception as e: print(f"[ERROR] Fehler beim Laden von {img_id}: {e}")
        
        self.cache[img_id] = None
        return None

class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((INIT_WIDTH, INIT_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(f"{SYS_CONFIG['game'].get('title', 'Narratrix')} v5.9") 
        
        try: pygame.scrap.init()
        except pygame.error: print("[WARN] Clipboard konnte nicht initialisiert werden.")

        self.clock = pygame.time.Clock()
        
        try: 
            self.font_log = pygame.font.SysFont("Consolas", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Verdana", theme.FONT_SIZE_HEADER, bold=True)
            self.font_big = pygame.font.SysFont("Verdana", theme.FONT_SIZE_GAME_OVER, bold=True)
            self.font_sensor = pygame.font.SysFont("Consolas", 14) # Kleine Schrift für Sensoren
        except: 
            print("[WARN] Systemfonts nicht gefunden, nutze Fallback.")
            self.font_log = pygame.font.SysFont("Arial", theme.FONT_SIZE_LOG)
            self.font_header = pygame.font.SysFont("Arial", theme.FONT_SIZE_HEADER)
            self.font_big = pygame.font.SysFont("Arial", theme.FONT_SIZE_GAME_OVER)
            self.font_sensor = pygame.font.SysFont("Arial", 12)

        self.renderer = RichTextRenderer(self.font_log, theme.COLOR_TEXT)
        self.assets = AssetLoader() 
        
        self.result_queue = queue.Queue()
        
        self.current_chapter = SYS_CONFIG['game'].get("start_chapter", "data.chapters.ep0_arrival.config")
        print(f"[SYSTEM] Starte mit Kapitel: {self.current_chapter}")
        self.load_game_chapter(self.current_chapter)
        
        # DEBUG FLAG: Setze auf True, um alle Logs auch unten zu sehen
        self.show_all_logs_in_main = False

    def load_game_chapter(self, chapter_path, transfer_state=None):
        new_config = StoryLoader.load_chapter(chapter_path)
        
        if not new_config:
            print(f"[FATAL] Konnte Kapitel '{chapter_path}' nicht laden!")
            sys.exit(1)

        self.game = GameState(new_config)
        
        if transfer_state:
            self.game.knowledge = transfer_state.get('knowledge', set())
            old_inventory_ids = transfer_state.get('inventory_ids', [])
            for item_id in old_inventory_ids:
                if item_id in self.game.objects:
                    self.game.objects[item_id]['location'] = LOC_INVENTORY
        
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
        else: 
            self.parser = RuleBasedParser(self.game)

        self.submit_command("look", echo=False)

    def restart_game(self):
        self.current_chapter = SYS_CONFIG['game'].get("start_chapter", "data.chapters.ep0_arrival.config")
        self.load_game_chapter(self.current_chapter)

    def run(self):
        while True:
            self.handle_events(); self.update(); self.draw(); self.clock.tick(30)

    def handle_events(self):
        try:
            while not self.result_queue.empty():
                msg = self.result_queue.get_nowait()
                if msg == "DONE":
                    self.is_processing = False
        except queue.Empty: pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            elif event.type == pygame.VIDEORESIZE: self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            
            if self.game.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                continue

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: self.scroll_offset += theme.SCROLL_SPEED_MOUSE
                elif event.button == 5: 
                    self.scroll_offset -= theme.SCROLL_SPEED_MOUSE
                    if self.scroll_offset < 0: self.scroll_offset = 0
            
            elif event.type == pygame.KEYDOWN:
                if self.is_processing: continue 
                
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
                elif event.key == pygame.K_HOME: self.cursor_pos = 0
                elif event.key == pygame.K_END: self.cursor_pos = len(self.user_text)

                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    snapshot = self.game.get_logs()
                    text_dump = "\n".join([f"{l['type']}: {l['text']}" for l in snapshot])
                    try: 
                        pygame.scrap.put(pygame.SCRAP_TEXT, text_dump.encode('utf-8'))
                        print("Clipboard copy success.")
                    except Exception as e: print(f"Clipboard Error: {e}")
                    continue
                
                # DEBUG TOGGLE: F1 umschalten der Log-Ansicht
                elif event.key == pygame.K_F1:
                    self.show_all_logs_in_main = not self.show_all_logs_in_main
                    print(f"DEBUG: Show all logs = {self.show_all_logs_in_main}")

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
            try:
                if self.game.dialogue_active:
                    ActionDispatcher.dialogue_step(self.game, text)
                elif self.game.disambiguation:
                    ActionDispatcher.dispatch(self.game, "disambiguate", [text])
                else:
                    self.parser.parse(text)
            except Exception as e:
                print(f"[ERROR] Worker Thread Exception: {e}")
                self.game.log('error', f"Systemfehler: {str(e)}")
            finally:
                self.result_queue.put("DONE")

        t = threading.Thread(target=worker)
        t.daemon = True 
        t.start()

    def update(self): 
        self.cursor_blink += 1
        
        if self.game.pending_chapter_load:
            target_chapter = self.game.pending_chapter_load
            print(f"[SYSTEM] Wechsle zu Kapitel: {target_chapter}")
            
            transfer_state = {
                "knowledge": self.game.knowledge,
                "inventory_ids": [o['id'] for o in self.game.objects.values() if o['location'] == LOC_INVENTORY]
            }
            
            chapter_map = {
                "ep1_station": "data.chapters.ep1_station.config",
                "ep0_arrival": "data.chapters.ep0_arrival.config"
            }
            
            path = chapter_map.get(target_chapter)
            if not path:
                if "data.chapters" in target_chapter: path = target_chapter

            if path:
                self.load_game_chapter(path, transfer_state)
            else:
                self.game.log('error', f"[SYSTEM] Fehler: Kapitel '{target_chapter}' nicht gefunden.")
                self.game.pending_chapter_load = None

    def draw(self):
        snapshot = self.game.get_snapshot()
        self.screen.fill(theme.COLOR_BG); w, h = self.screen.get_size()
        
        if snapshot['game_over']:
            self.draw_game_over(w, h, snapshot)
            pygame.display.flip()
            return

        scene_height = int(h * theme.SCENE_HEIGHT_RATIO); input_height = theme.INPUT_HEIGHT; log_height = h - scene_height - input_height
        rect_scene = pygame.Rect(0, 0, w, scene_height); rect_log = pygame.Rect(0, scene_height, w, log_height); rect_input = pygame.Rect(0, h - input_height, w, input_height)
        
        self.draw_scene_area(rect_scene, snapshot)
        self.draw_log_area(rect_log, snapshot)
        self.draw_input_area(rect_input, snapshot)
        
        border_col = theme.COLOR_DIALOGUE_BORDER if snapshot['dialogue_active'] else theme.COLOR_UI_BORDER
        pygame.draw.line(self.screen, border_col, (0, scene_height), (w, scene_height), 2)
        pygame.draw.line(self.screen, border_col, (0, h - input_height), (w, h - input_height), 2)
        
        if self.is_processing: self.draw_loading_spinner(w, h, snapshot)
        pygame.display.flip()

    def draw_game_over(self, w, h, snap):
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
        
        # --- HEADER & STATUS ---
        header_text = snap['dialogue_header'] if snap['dialogue_active'] else snap['room_name'].upper()
        header_col = theme.COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else theme.COLOR_ACCENT
        
        text_room = self.font_header.render(header_text, True, header_col)
        self.screen.blit(text_room, (20, 20))
        
        surf_time = self.font_log.render(f"ZEIT: T+{snap['time']}m", True, theme.COLOR_TEXT)
        self.screen.blit(surf_time, (20, 70))

        # --- VISUALS (Rechts) ---
        max_h = rect.height - 40 
        max_w = int(rect.width * 0.4) 
        area_x = rect.width - max_w - 20
        
        placeholder_w = int(max_h * 1.33)
        if placeholder_w > max_w: placeholder_w = max_w
        placeholder_h = int(placeholder_w / 1.33)
        default_rect = pygame.Rect(rect.width - placeholder_w - 20, 20, placeholder_w, placeholder_h)
        
        room_img = self.assets.get_image(snap['room_img'])
        dialogue_img = self.assets.get_image(snap['dialogue_img']) if snap['dialogue_active'] else None
        
        final_visual_rect = default_rect
        bg_surf_to_draw = None
        bg_pos = (0,0)
        
        def get_scaled_rect_and_surf(img, max_w, max_h):
            o_w, o_h = img.get_size()
            aspect = o_w / o_h
            t_h = max_h; t_w = int(t_h * aspect)
            if t_w > max_w: t_w = max_w; t_h = int(t_w / aspect)
            return pygame.Rect(0, 0, t_w, t_h), pygame.transform.smoothscale(img, (t_w, t_h))

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

        # --- SENSOR HUD (NEU: Oben Links) ---
        sensor_x = 20
        sensor_y = 110
        sensor_width = rect.width - final_visual_rect.width - 60
        
        # 1. Personen Scan
        # Da wir im Snapshot keine NPCs haben (nur in 'logs'), müssen wir das besser lösen.
        # Aktuell haben wir aber "Personen: Name" als Log-Typ 'character', wenn look ausgeführt wird.
        # Besser: Wir nutzen get_snapshot() und greifen auf game.npcs zu?
        # get_snapshot() gibt nur ein Dict zurück.
        # Hack: Wir suchen in logs nach der letzten "Personen: ..." Zeile
        
        # Aber halt! GameState.get_snapshot könnte auch direkt die NPCs im Raum liefern.
        # Das wäre sauberer. Da ich GameState aber hier nicht ändern kann, nutzen wir den Log-Parsing-Hack
        # oder wir hoffen auf ein zukünftiges Update.
        # Für jetzt: Zeige einfach die letzte "Personen:" Meldung permanent an, wenn sie aktuell ist?
        # Nein, zu fehleranfällig.
        
        # Besser: Sensor Log (Events & Character Actions)
        # Sammle Logs für HUD
        hud_logs = []
        # Wir durchsuchen rückwärts
        for l in reversed(snap['logs']):
            if l['type'] in ['event', 'character']:
                # Filter '---' (Dialog-Trenner) und 'Personen:' (Statusmeldungen)
                if '---' in l['text']: continue
                if l['text'].startswith("Personen:"): continue 
                hud_logs.append(l)
            if len(hud_logs) >= 5: break # Max 5 Einträge
        
        # 1. Überschrift: PERSONEN IM RAUM
        # Wir scannen die Logs nach "Personen: X, Y" (wird von ExplorationHandler.look erzeugt)
        last_people_log = None
        for l in reversed(snap['logs']):
            if l['type'] == 'character' and l['text'].startswith("Personen:"):
                # Prüfen ob dieser Log seit dem letzten Raumwechsel war?
                # Wir nehmen einfach den allerletzten.
                last_people_log = l['text'].replace("Personen: ", "")
                break
        
        if last_people_log:
            lbl = self.font_sensor.render("SCAN: LEBENSFORMEN", True, (100, 255, 100))
            self.screen.blit(lbl, (sensor_x, sensor_y))
            sensor_y += 20
            
            people = last_people_log.split(", ")
            for p in people:
                surf = self.font_sensor.render(f" [!] {p}", True, (150, 255, 150))
                self.screen.blit(surf, (sensor_x, sensor_y))
                sensor_y += 18
            sensor_y += 10 # Abstand
            
        pygame.draw.line(self.screen, (50, 50, 60), (sensor_x, sensor_y), (sensor_x + 200, sensor_y), 1)
        sensor_y += 10
        
        # 2. Sensor Log (Events)
        lbl = self.font_sensor.render("SENSOR LOG:", True, (100, 150, 200))
        self.screen.blit(lbl, (sensor_x, sensor_y))
        sensor_y += 20
        
        # Zeige Logs (Neueste oben? Nein, Liste ist reversed -> index 0 ist neueste)
        # Wir wollen Neueste UNTEN oder OBEN? Sensor Logs laufen meist von unten nach oben oder oben nach unten.
        # Hier: Neueste OBEN (unter dem Label).
        
        for i, log in enumerate(hud_logs):
            # Alpha/Farbe berechnen (Dimmen älterer Beiträge)
            # Index 0 = Hell, Index 2+ = Dunkel
            brightness = 255
            if i == 1: brightness = 200
            elif i == 2: brightness = 150
            elif i >= 3: brightness = 100 # Stark gedimmt
            
            base_col = (brightness, brightness, brightness)
            if log['type'] == 'event': base_col = (brightness, int(brightness*0.8), 50) # Orange-ish
            elif log['type'] == 'character': base_col = (int(brightness*0.4), int(brightness*0.8), brightness) # Blue-ish
            
            txt = log['text']
            if len(txt) > 55: txt = txt[:52] + "..."
            
            surf = self.font_sensor.render(f"> {txt}", True, base_col)
            self.screen.blit(surf, (sensor_x, sensor_y))
            sensor_y += 18

    def draw_log_area(self, rect, snap):
        padding_x = theme.PADDING; padding_y = theme.PADDING
        max_text_width = rect.width - (padding_x * 2)
        
        render_rows = []
        
        for log in snap['logs']: 
            # FILTERUNG:
            # Wenn Debug-Flag NICHT gesetzt ist, filtern wir Sensor-Nachrichten aus dem Haupt-Log
            if not self.show_all_logs_in_main:
                if log['type'] in ['event', 'character']:
                    # Ausnahme: Dialog-Trenner und "Personen:" Listen sollen vielleicht bleiben?
                    # Nein, "Personen" ist jetzt im HUD. Dialoge sollten im Log bleiben.
                    # Dialoge sind meist 'character' type. Das ist tricky.
                    # Dialoge haben Anführungszeichen oder Doppelpunkt.
                    if '---' in log['text']: pass # Trenner behalten
                    elif '"' in log['text']: pass # Gesprochener Text behalten
                    elif log['text'].startswith("Personen:"): continue # Filtern (ist im HUD)
                    else:
                        continue # Allgemeine Events/Bewegungen filtern (sind im HUD)

            base_color = theme.COLOR_TEXT
            prefix = ""
            
            if log['type'] == 'user': base_color = theme.COLOR_USER_ECHO; prefix = ""
            elif log['type'] == 'error': base_color = (255, 80, 80)
            elif log['type'] == 'success': base_color = theme.COLOR_ACCENT
            elif log['type'] == 'event': base_color = (255, 200, 50)
            elif log['type'] == 'alarm': base_color = theme.COLOR_ALERT
            elif log['type'] == 'location': base_color = theme.COLOR_ACCENT
            elif log['type'] == 'character': base_color = (100, 200, 255)
            elif log['type'] == 'story': base_color = (220, 220, 220)
            elif log['type'] == 'info': base_color = theme.COLOR_INFO
            
            raw_text = prefix + log['text']
            
            wrapped_lines = self.renderer.parse_and_wrap(str(raw_text), max_text_width, base_color)
            render_rows.extend(wrapped_lines)
        
        total_content_height = len(render_rows) * self.line_height
        visible_height = rect.height - (2 * padding_y)
        
        max_scroll = max(0, total_content_height - visible_height)
        
        if self.scroll_offset > max_scroll: self.scroll_offset = max_scroll
        if self.scroll_offset < 0: self.scroll_offset = 0
        
        bottom_draw_y = rect.bottom - padding_y - self.line_height + self.scroll_offset
        current_y = bottom_draw_y
        
        for row in reversed(render_rows):
            if current_y + self.line_height > rect.top and current_y < rect.bottom:
                current_x = rect.x + padding_x
                for segment in row:
                    text_surf = self.font_log.render(segment['text'], True, segment['color'])
                    self.screen.blit(text_surf, (current_x, current_y))
                    current_x += segment['width']
            
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
        # ... (unverändert) ...
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
        # ... (unverändert) ...
        center_x, center_y = w - 30, h - 25
        angle = (self.cursor_blink * theme.CURSOR_BLINK_SPEED) % 360
        radius = 10
        end_x = center_x + radius * math.cos(math.radians(angle))
        end_y = center_y + radius * math.sin(math.radians(angle))
        col = theme.COLOR_DIALOGUE_BORDER if snap['dialogue_active'] else theme.COLOR_LOADING
        pygame.draw.circle(self.screen, col, (center_x, center_y), radius, 1)
        pygame.draw.line(self.screen, col, (center_x, center_y), (end_x, end_y), 2)

if __name__ == "__main__":
    gui = GameGUI()
    gui.run()