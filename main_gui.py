import pygame
import threading
import time
import os
import sys
import subprocess

# Engine Importe
from engine.game_state import GameState
from data.story_config import CONFIG
from engine.parser.spacy_parser import SpacyParser
from engine.constants import *

# KONSTANTEN GUI
WIDTH, HEIGHT = 1024, 768
COLOR_BG = (20, 20, 25)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (100, 200, 255)
COLOR_ALERT = (255, 80, 80)
COLOR_INPUT_BG = (30, 30, 35)
COLOR_BORDER = (60, 60, 70)
COLOR_DIALOGUE_BG = (40, 40, 50)
COLOR_DIALOGUE_BORDER = (100, 255, 150)

FONT_SIZE_MAIN = 22
FONT_SIZE_LOG = 18

class NarratrixGUI:
    def __init__(self):
        pygame.init()
        # Scrap Modul init (versuchen)
        try:
            pygame.scrap.init()
        except:
            pass

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("NARRATRIX - Terminal Uplink")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Fonts
        try:
            self.font_main = pygame.font.SysFont("Consolas, 'Courier New', monospace", FONT_SIZE_MAIN)
            self.font_log = pygame.font.SysFont("Consolas, 'Courier New', monospace", FONT_SIZE_LOG)
        except:
            self.font_main = pygame.font.SysFont(None, FONT_SIZE_MAIN)
            self.font_log = pygame.font.SysFont(None, FONT_SIZE_LOG)

        # Game Engine Init
        self.game = GameState(CONFIG)
        self.parser = SpacyParser(self.game)
        
        # UI State
        self.input_text = ""
        self.cursor_visible = True
        self.last_cursor_blink = time.time()
        self.scroll_offset = 0
        self.loading = False
        
        # Command History
        self.command_history = []
        self.history_index = -1 # -1 bedeutet: wir sind am Ende (neuer Input)
        
        # Asset Cache
        self.images = {}
        # Pfad korrigieren: data/assets/images ist der korrekte Ort
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "assets", "images"))
        
        print(f"[SYSTEM] Asset-Pfad: {self.base_path}")
        if not os.path.exists(self.base_path):
            # Fallback Versuche
            alt_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "assets"))
            if os.path.exists(alt_path):
                print(f"[SYSTEM] 'images' Unterordner nicht gefunden, versuche {alt_path}")
                self.base_path = alt_path
            else:
                print(f"[SYSTEM] WARNUNG: Asset-Ordner existiert nicht!")
                try: os.makedirs(self.base_path, exist_ok=True)
                except: pass

        # Initiales Log
        self.game.log('system', "Verbindung hergestellt...")
        self.game.log('system', f"Lade Modul: {CONFIG['meta']['title']}")
        
        from engine.handlers.interaction import InteractionHandler
        InteractionHandler.look(self.game, [])

    def load_image(self, name):
        if not name: return None
        if name in self.images: return self.images[name]
        
        # Dateinamen prüfen
        extensions = [".png", ".jpg", ".jpeg"]
        found_path = None
        
        for ext in extensions:
            test_path = os.path.join(self.base_path, name + ext)
            if os.path.exists(test_path):
                found_path = test_path
                break
        
        if found_path:
            try:
                img = pygame.image.load(found_path).convert_alpha()
                self.images[name] = img
                print(f"[IMG] Geladen: {name}")
                return img
            except Exception as e:
                print(f"[IMG] Fehler bei {name}: {e}")
                return None
        else:
            # Debugging: Nur einmal pro Name warnen
            if name not in self.images: 
                print(f"[IMG] Nicht gefunden: {name} (in {self.base_path})")
                self.images[name] = None 
        return None

    def copy_to_clipboard(self, text):
        """
        Robuste Kopierfunktion für Linux/Ubuntu.
        Priorität: subprocess (xclip/xsel) -> pygame -> fallback print
        """
        # 1. Versuch: Native Linux Tools
        try:
            # Versuche xclip
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(input=text.encode('utf-8'))
            print("[Clipboard] Via xclip kopiert.")
            return True
        except FileNotFoundError:
            try:
                # Versuche xsel als Alternative
                process = subprocess.Popen(['xsel', '-b', '-i'], stdin=subprocess.PIPE)
                process.communicate(input=text.encode('utf-8'))
                print("[Clipboard] Via xsel kopiert.")
                return True
            except FileNotFoundError:
                pass 
        except Exception as e:
            print(f"[Clipboard] Subprocess Fehler: {e}")

        # 2. Versuch: Pygame Builtin
        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, text.encode('utf-8'))
            return True
        except Exception as e:
            print(f"[Clipboard] Pygame Fehler: {e}")

        return False

    def run(self):
        """Hauptschleife."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(30)
        
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    cmd = self.input_text.strip()
                    if cmd:
                        # Zur History hinzufügen, wenn nicht identisch zum letzten
                        if not self.command_history or self.command_history[-1] != cmd:
                            self.command_history.append(cmd)
                        self.history_index = -1 # Reset nach Absenden
                        
                        self.process_command(cmd)
                        self.input_text = ""
                        
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # Command History Navigation (Pfeil Rauf/Runter)
                elif event.key == pygame.K_UP:
                    if self.command_history:
                        if self.history_index == -1:
                            self.history_index = len(self.command_history) - 1
                        else:
                            self.history_index = max(0, self.history_index - 1)
                        self.input_text = self.command_history[self.history_index]
                
                elif event.key == pygame.K_DOWN:
                    if self.command_history and self.history_index != -1:
                        self.history_index = min(len(self.command_history) - 1, self.history_index + 1)
                        # Wenn wir wieder am Ende ankommen -> leeres Feld
                        if self.history_index == len(self.command_history) - 1 and self.input_text == self.command_history[-1]:
                             # Optional: Wenn man ganz unten ist und nochmal drückt -> clear?
                             # Hier: Einfach weiter den letzten anzeigen oder clearen
                             pass 
                        self.input_text = self.command_history[self.history_index]
                        
                        # Spezialfall: Wenn wir "über" das Ende hinaus wollen -> leeren
                        # (Wir machen es so: history_index zeigt auf das Item. Wenn man am Ende ist, bleibt man da)

                # COPY LOG LOGIK
                elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    try:
                        logs = self.game.get_logs()
                        text_lines = [f"[{l['type'].upper()}] {l['text']}" for l in logs]
                        full_text = "\n".join(text_lines)
                        
                        if self.copy_to_clipboard(full_text):
                            self.game.log('system', "Log in Zwischenablage kopiert.")
                        else:
                            self.game.log('error', "Clipboard fehlgeschlagen (Installiere 'xclip').")
                            print("\n--- LOG DUMP ---")
                            print(full_text)
                            print("----------------")
                            
                    except Exception as e: 
                        print(f"[SYSTEM] Log Fehler: {e}")
                        self.game.log('error', "Fehler beim Kopieren.")

                elif event.key == pygame.K_PAGEUP:
                    self.scroll_offset += 1
                elif event.key == pygame.K_PAGEDOWN:
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                else:
                    if len(self.input_text) < 200:
                        self.input_text += event.unicode

            elif event.type == pygame.MOUSEWHEEL:
                self.scroll_offset = max(0, self.scroll_offset + event.y)

    def process_command(self, text):
        self.game.log('user', f"> {text}")
        self.loading = True
        t = threading.Thread(target=self.worker, args=(text,))
        t.start()

    def worker(self, text):
        if self.game.dialogue_active:
            from engine.handlers.dialogue import DialogueHandler
            DialogueHandler.step(self.game, text)
        else:
            self.parser.parse(text)
        self.loading = False
        self.scroll_offset = 0

    def update(self):
        if time.time() - self.last_cursor_blink > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_blink = time.time()

    def draw(self):
        self.screen.fill(COLOR_BG)
        snapshot = self.game.get_snapshot()
        
        h_scene = int(HEIGHT * 0.3)
        h_input = int(HEIGHT * 0.08)
        h_log = HEIGHT - h_scene - h_input
        
        rect_scene = pygame.Rect(0, 0, WIDTH, h_scene)
        rect_log = pygame.Rect(0, h_scene, WIDTH, h_log)
        rect_input = pygame.Rect(0, HEIGHT - h_input, WIDTH, h_input)
        
        self.draw_scene_area(rect_scene, snapshot)
        self.draw_log_area(rect_log, snapshot)
        self.draw_input_area(rect_input, snapshot)
        
        if self.loading:
            pygame.draw.circle(self.screen, COLOR_ACCENT, (WIDTH-20, 20), 5)

        pygame.display.flip()

    def apply_pixel_effect(self, surface, scale_factor=0.2, brightness=128):
        """
        Verpixelt ein Bild und dunkelt es ab.
        scale_factor: 0.1 = sehr stark verpixelt, 0.5 = leicht verpixelt
        brightness: 0-255 (255 = original, 0 = schwarz)
        """
        w, h = surface.get_size()
        small_w = max(1, int(w * scale_factor))
        small_h = max(1, int(h * scale_factor))
        
        # Herunterskalieren (Pixel verlieren)
        small_surf = pygame.transform.smoothscale(surface, (small_w, small_h))
        # Hochskalieren (Pixel groß machen)
        pixel_surf = pygame.transform.scale(small_surf, (w, h))
        
        # Abdunkeln
        dark = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        dark.fill((0, 0, 0, 255 - brightness))
        pixel_surf.blit(dark, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        return pixel_surf

    def draw_scene_area(self, rect, snap):
        pygame.draw.rect(self.screen, (30, 30, 40), rect)
        pygame.draw.line(self.screen, COLOR_BORDER, rect.bottomleft, rect.bottomright, 2)
        
        # 1. Hintergrund-Bild (Raum) laden
        room_img_id = snap['room_img']
        room_img = self.load_image(room_img_id)
        
        final_bg = None
        img_size = rect.height - 20
        # Position für das Bild (quadratisch links)
        img_rect = pygame.Rect(10, 10, img_size, img_size)
        
        if room_img:
            # Skalieren auf Zielgröße
            room_scaled = pygame.transform.scale(room_img, (img_size, img_size))
            
            if snap['dialogue_active']:
                # Wenn Dialog: Verpixeln & Abdunkeln
                # ANGEPASST: scale_factor von 0.1 auf 0.25 erhöht (weniger pixelig)
                # ANGEPASST: brightness von 100 auf 80 (etwas dunkler für mehr Kontrast zum Portrait)
                final_bg = self.apply_pixel_effect(room_scaled, scale_factor=0.25, brightness=80)
            else:
                # Normal: Klar anzeigen
                final_bg = room_scaled
                
            # Hintergrund zeichnen
            self.screen.blit(final_bg, img_rect)
        else:
            # Fallback Platzhalter
            pygame.draw.rect(self.screen, (20, 20, 20), img_rect)

        # 2. Charakter-Overlay (nur bei Dialog)
        if snap['dialogue_active']:
            char_img_id = snap['dialogue_img']
            char_img = self.load_image(char_img_id)
            
            if char_img:
                # Charakter skalieren (etwas kleiner oder voll?) -> Voll im Rahmen
                char_scaled = pygame.transform.scale(char_img, (img_size, img_size))
                self.screen.blit(char_scaled, img_rect)

        # Text Infos
        text_start_x = img_size + 30
        header_text = snap['room_name']
        header_col = COLOR_ACCENT
        
        if snap['dialogue_active']:
            header_text = snap['dialogue_header']
            header_col = COLOR_DIALOGUE_BORDER
            
        surf_header = self.font_main.render(header_text.upper(), True, header_col)
        self.screen.blit(surf_header, (text_start_x, 20))
        
        stats = []
        stats.append(f"ZEIT: {snap['time']}")
        stats.append(f"INTEGRITÄT: {snap['stability']}%")
        if 'weight_info' in snap:
            stats.append(f"LAST: {snap['weight_info']}")
            
        stats_str = " | ".join(stats)
        surf_stats = self.font_log.render(stats_str, True, (150, 150, 150))
        self.screen.blit(surf_stats, (text_start_x, 50))
        
        exits_str = "AUSGÄNGE: " + ", ".join([e.upper() for e in snap['exits']])
        if not snap['exits']: exits_str = "AUSGÄNGE: KEINE"
        surf_exits = self.font_log.render(exits_str, True, (150, 150, 150))
        self.screen.blit(surf_exits, (text_start_x, 75))

        inv_count = len(snap['inventory'])
        surf_inv = self.font_log.render(f"ITEMS: {inv_count}", True, (150, 150, 150))
        self.screen.blit(surf_inv, (text_start_x, 100))

    def draw_log_area(self, rect, snap):
        self.screen.set_clip(rect)
        padding = 15
        line_height = FONT_SIZE_LOG + 4
        
        logs = snap['logs']
        y_pos = rect.bottom - padding - (line_height * self.scroll_offset)
        
        for log in reversed(logs):
            text = log['text']
            cat = log['type']
            
            col = COLOR_TEXT
            if cat == 'user': col = (150, 150, 150)
            elif cat == 'error': col = COLOR_ALERT
            elif cat == 'success': col = (100, 255, 100)
            elif cat == 'info': col = (180, 180, 200)
            elif cat == 'character': col = COLOR_DIALOGUE_BORDER
            elif cat == 'story': col = (255, 255, 200)
            
            words = text.split(' ')
            lines = []
            current_line = []
            
            for word in words:
                test_line = " ".join(current_line + [word])
                if self.font_log.size(test_line)[0] < (rect.width - 2*padding):
                    current_line.append(word)
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
            lines.append(" ".join(current_line))
            
            for line in reversed(lines):
                if y_pos < rect.top: break
                surf = self.font_log.render(line, True, col)
                self.screen.blit(surf, (rect.left + padding, y_pos - line_height))
                y_pos -= line_height
                
            y_pos -= 5
            if y_pos < rect.top: break

        self.screen.set_clip(None)
        
        if self.scroll_offset > 0:
            surf = self.font_log.render(f"^ SCROLL {self.scroll_offset} ^", True, COLOR_ACCENT)
            self.screen.blit(surf, (rect.right - 150, rect.bottom - 25))

    def draw_input_area(self, rect, snap):
        pygame.draw.rect(self.screen, COLOR_INPUT_BG, rect)
        pygame.draw.line(self.screen, COLOR_BORDER, rect.topleft, rect.topright, 2)
        
        prompt = "> "
        txt_surf = self.font_main.render(prompt + self.input_text, True, COLOR_ACCENT)
        self.screen.blit(txt_surf, (rect.left + 20, rect.centery - txt_surf.get_height()//2))
        
        if self.cursor_visible:
            cursor_x = rect.left + 20 + txt_surf.get_width()
            cursor_h = txt_surf.get_height()
            cursor_y = rect.centery - cursor_h//2
            pygame.draw.rect(self.screen, COLOR_ACCENT, (cursor_x, cursor_y, 10, cursor_h))

if __name__ == "__main__":
    gui = NarratrixGUI()
    gui.run()
