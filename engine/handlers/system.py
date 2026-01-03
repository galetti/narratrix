import os
import json
import time
from engine.constants import *
# Wir brauchen hier keinen InteractionHandler mehr.
# Für Save/Load nutzen wir die GameState Methoden direkt oder json.

class SystemHandler:
    
    @staticmethod
    def save(game, args):
        """Speichert den aktuellen Spielstand."""
        filename = "savegame.json"
        if args: filename = f"{args[0]}.json"
        
        # Sicherstellen, dass der Ordner existiert
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        filepath = os.path.join(save_dir, filename)
        
        try:
            # Wir holen uns den Snapshot vom GameState
            data = game.serialize_state()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            game.log('success', f"Spiel gespeichert unter: {filename}")
        except Exception as e:
            game.log('error', f"Fehler beim Speichern: {e}")

    @staticmethod
    def load(game, args):
        """Lädt einen Spielstand."""
        filename = "savegame.json"
        if args: filename = f"{args[0]}.json"
        
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")
        filepath = os.path.join(save_dir, filename)
        
        if not os.path.exists(filepath):
            return game.log('error', f"Spielstand '{filename}' nicht gefunden.")
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Wir setzen ein Flag, damit die GUI den State beim nächsten Tick neu lädt/überschreibt
            # oder wir laden es direkt in den game state.
            # Da GameState serialization komplex sein kann, nutzen wir hier eine einfache Methode:
            success = game.deserialize_state(data)
            if success:
                game.log('success', "Spielstand geladen.")
                # Force Look nach dem Laden
                from engine.handlers.exploration import ExplorationHandler
                ExplorationHandler.look(game, [])
            else:
                game.log('error', "Fehler beim Verarbeiten des Spielstands.")
                
        except Exception as e:
            game.log('error', f"Kritischer Fehler beim Laden: {e}")

    @staticmethod
    def help(game, args):
        """Zeigt verfügbare Befehle."""
        # Da wir nun modulare Handler haben, geben wir eine statische Übersicht
        help_text = """
<header>VERFÜGBARE BEFEHLE</header>

<accent>BEWEGUNG:</accent>
  gehe <richtung> (n, s, e, w, u, d, out)
  verstecke <objekt> (hide in)

<accent>INTERAKTION:</accent>
  schaue / l [objekt]
  nimm <objekt>
  benutze <objekt> [mit <objekt>]
  öffne <objekt>
  lege <objekt> in/auf <objekt>

<accent>SYSTEM:</accent>
  inv / i       - Inventar zeigen
  save [name]   - Speichern
  load [name]   - Laden
  map           - Karte anzeigen
  oracle        - Log-Analyse
"""
        game.log('info', help_text.strip())

    @staticmethod
    def oracle(game, args):
        """Debug / Story Helper Tool: Zeigt interne Zustände an."""
        game.log('system', "--- ORACLE SYSTEM STATUS ---")
        
        # 1. Globale Variablen
        game.log('info', f"Zeit: T+{game.time}m | Stabilität: {game.stability}%")
        
        # 2. Event-Queue Status
        pending_events = len([e for e in game.event_queue if e['time'] > game.time])
        game.log('info', f"Ausstehende Events: {pending_events}")
        
        # 3. NPC Status
        npc_info = []
        for npc in game.npcs:
            state = npc.get('state', 'default')
            loc = npc.get('location', 'unknown')
            # Hole den Namen des Raums für bessere Lesbarkeit
            room_name = loc
            if loc in game.rooms:
                room_name = game.rooms[loc].get('name', loc)
            npc_info.append(f"{npc[ATTR_NAME]} ({state}) @ {room_name}")
        
        if npc_info:
            game.log('info', "NPCs:\n  " + "\n  ".join(npc_info))
        else:
            game.log('info', "NPCs: Keine aktiv.")

        # 4. Aktive Gefahren/Probleme
        warnings = []
        if game.stability < 50: warnings.append("KRITISCH: Stations-Integrität gefährdet!")
        
        # Suche nach sabotierten Räumen
        sabotaged_rooms = [r.get('name', r_id) for r_id, r in game.rooms.items() if r.get('state') == STATE_SABOTAGED]
        if sabotaged_rooms:
            warnings.append(f"Sabotage entdeckt in: {', '.join(sabotaged_rooms)}")
            
        if warnings:
            game.log('alarm', "\n".join(warnings))
        else:
            game.log('success', "Systemdiagnose: Nominal.")

    @staticmethod
    def map(game, args):
        """Zeigt eine dynamisch generierte Karte der besuchten Räume."""
        game.log('info', "--- TAKTISCHE KARTE (Bekannte Sektoren) ---")
        
        # Wir sammeln alle besuchten Räume
        visited_ids = [r_id for r_id, r in game.rooms.items() if r.get('visited')]
        
        if not visited_ids:
            game.log('info', "Keine Kartendaten verfügbar.")
            return

        # Einfache Visualisierung (Liste mit Verbindungen)
        # Eine echte 2D-Grid Map wäre im Text-Log schwer, daher eine strukturierte Liste.
        
        for r_id in visited_ids:
            room = game.rooms[r_id]
            name = room.get(ATTR_NAME, "Unbekannt")
            
            # Marker für aktuelle Position
            marker = " [HIER]" if r_id == game.location else ""
            
            # Ausgänge formatieren
            exits = room.get('exits', {})
            exit_strs = []
            for direction, target_id in exits.items():
                target_name = "???"
                # Zeige Zielname nur, wenn Ziel auch besucht wurde
                if target_id in visited_ids:
                    target_room = game.rooms[target_id]
                    target_name = target_room.get(ATTR_NAME, "Unbekannt")
                
                # Kurze Richtungsnamen
                short_dir = direction[0].upper() if len(direction) > 2 else direction.upper()
                exit_strs.append(f"{short_dir} -> {target_name}")
            
            exits_display = ", ".join(exit_strs) if exit_strs else "Sackgasse"
            
            # Farbige Ausgabe je nach Status
            log_type = 'location' if r_id == game.location else 'info'
            game.log(log_type, f"> {name}{marker}\n  Verbindungen: {exits_display}")