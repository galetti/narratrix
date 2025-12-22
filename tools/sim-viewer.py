import pygame
import sys
import os

# Pfad-Hack, damit wir engine und data importieren können
# (Fügt das Parent-Directory 'narratrix' zum Python-Pfad hinzu)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.story_loader import StoryLoader
from engine.game_state import GameState
from engine.analysis import generate_future_matrix
from engine.constants import ATTR_NAME

# Farben
COL_BG = (20, 20, 30)
COL_NODE = (50, 50, 80)
COL_NODE_ACTIVE = (100, 100, 150)
COL_LINK = (100, 100, 100)
COL_NPC = (255, 200, 0)
COL_EVENT = (255, 50, 50)
COL_TEXT = (200, 200, 200)
COL_ACCENT = (0, 255, 136) 

SCREEN_W, SCREEN_H = 800, 600

def run_viewer():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Narratrix Simulation Viewer v5.0")
    try:
        font = pygame.font.SysFont("Arial", 16)
    except:
        font = pygame.font.Font(None, 24)
        
    clock = pygame.time.Clock()

    # 1. Initiale Simulation mit neuem Loader
    print("Lade Kapiteldaten...")
    # Wir laden standardmäßig Episode 1 für die Simulation
    config = StoryLoader.load_chapter("data.chapters.ep1_station.config")
    
    if not config:
        print("[ERROR] Konnte Config nicht laden. Abbruch.")
        return

    print("Starte Simulation...")
    initial_game = GameState(config, silent=True)
    
    # Simuliere 120 Minuten in 5-Minuten-Schritten
    # WICHTIG: Das Klonen im Analysis-Tool muss mit der neuen GameState-Logik kompatibel sein
    timeline = generate_future_matrix(initial_game, minutes_to_simulate=120, step_size=5)
    print(f"Simulation abgeschlossen. {len(timeline)} Snapshots generiert.")

    slider_val = 0 # Index in der Timeline
    dragging = False

    # Map Offset berechnen (Zentrieren)
    center_x, center_y = SCREEN_W // 2, SCREEN_H // 2
    scale = 100 # Pixel pro Map-Einheit

    running = True
    while running:
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Slider Hitbox (Unten)
                if my > SCREEN_H - 60:
                    dragging = True
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mx = event.pos[0]
                    # Map x to slider index
                    # Slider Area: 50 to Width-50
                    ratio = (mx - 50) / (SCREEN_W - 100)
                    ratio = max(0, min(1, ratio))
                    slider_val = int(ratio * (len(timeline) - 1))

        # Draw
        screen.fill(COL_BG)
        
        # A. MAP ZEICHNEN
        current_snap = timeline[slider_val]
        
        # Wir holen die Räume aus der Config (die ist statisch für die Map-Struktur)
        rooms = config['rooms']
        
        # Verbindungen zeichnen
        for r_id, room in rooms.items():
            x1 = center_x + room.get('map_x', 0) * scale
            y1 = center_y + room.get('map_y', 0) * scale
            
            for exit_dir, target_id in room.get('exits', {}).items():
                target = rooms.get(target_id)
                if target:
                    x2 = center_x + target.get('map_x', 0) * scale
                    y2 = center_y + target.get('map_y', 0) * scale
                    pygame.draw.line(screen, COL_LINK, (x1, y1), (x2, y2), 2)

        # Räume & Inhalte zeichnen
        for r_id, room in rooms.items():
            rx = center_x + room.get('map_x', 0) * scale
            ry = center_y + room.get('map_y', 0) * scale
            
            # Raum Node
            col = COL_NODE
            # Wenn Events in diesem Raum im aktuellen Tick aktiv sind, pulsieren
            room_data = current_snap["rooms"].get(r_id)
            if room_data and room_data["events"]:
                col = COL_EVENT
            
            pygame.draw.circle(screen, col, (rx, ry), 30)
            
            # Label
            lbl = font.render(room[ATTR_NAME], True, COL_TEXT)
            screen.blit(lbl, (rx - lbl.get_width()//2, ry - 45))
            
            # Inhalte aus Snapshot
            if room_data:
                # NPCs
                for i, npc_name in enumerate(room_data["npcs"]):
                    pygame.draw.circle(screen, COL_NPC, (rx - 10 + (i*10), ry), 8)
                    # Kürzel für NPC Name
                    short_name = npc_name[:2]
                    n_lbl = font.render(short_name, True, (0,0,0)) 
                    screen.blit(n_lbl, (rx - 10 + (i*10) - 3, ry - 5))
                
                # Events Text
                if room_data["events"]:
                    # Zeige Event-Namen unter dem Raum
                    y_off = 35
                    for ev_name in room_data["events"]:
                        ev_lbl = font.render(ev_name, True, COL_EVENT)
                        screen.blit(ev_lbl, (rx - ev_lbl.get_width()//2, ry + y_off))
                        y_off += 15

        # B. UI / SLIDER
        time_lbl = font.render(f"ZEIT: T+{current_snap['time']} min", True, COL_TEXT)
        screen.blit(time_lbl, (50, SCREEN_H - 80))
        
        # Slider Leiste
        pygame.draw.rect(screen, (50, 50, 50), (50, SCREEN_H - 40, SCREEN_W - 100, 10))
        # Slider Knopf
        slider_x = 50 + (slider_val / (len(timeline) - 1)) * (SCREEN_W - 100)
        pygame.draw.circle(screen, COL_ACCENT, (int(slider_x), SCREEN_H - 35), 10)

        # Legende
        legend = ["Gelb: NPC", "Rot: Event"]
        for i, l in enumerate(legend):
            t = font.render(l, True, COL_TEXT)
            screen.blit(t, (SCREEN_W - 150, 20 + i*20))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    run_viewer()
