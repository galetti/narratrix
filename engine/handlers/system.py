import os
import json
import re
from engine.constants import *

class SystemHandler:
    @staticmethod
    def _save_filename(args):
        stem = args[0] if args else "savegame"
        stem = stem[:-5] if stem.lower().endswith(".json") else stem
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", stem):
            raise ValueError("Save-Name darf nur Buchstaben, Zahlen, '_' und '-' enthalten.")
        return f"{stem}.json"
    
    @staticmethod
    def save(game, args):
        """Speichert den aktuellen Spielstand."""
        try:
            filename = SystemHandler._save_filename(args)
        except ValueError as exc:
            return game.log('error', str(exc))
        
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        filepath = os.path.join(save_dir, filename)
        
        try:
            data = game.serialize_state()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            game.log('success', f"Spiel gespeichert unter: {filename}")
        except Exception as e:
            game.log('error', f"Fehler beim Speichern: {e}")

    @staticmethod
    def load(game, args):
        """Lädt einen Spielstand."""
        try:
            filename = SystemHandler._save_filename(args)
        except ValueError as exc:
            return game.log('error', str(exc))
        
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")
        filepath = os.path.join(save_dir, filename)
        
        if not os.path.exists(filepath):
            return game.log('error', f"Spielstand '{filename}' nicht gefunden.")
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            success = game.deserialize_state(data)
            if success:
                game.log('success', "Spielstand geladen.")
                from engine.handlers.exploration import ExplorationHandler
                ExplorationHandler.look(game, [])
            else:
                game.log('error', "Fehler beim Verarbeiten des Spielstands.")
                
        except Exception as e:
            game.log('error', f"Kritischer Fehler beim Laden: {e}")

    @staticmethod
    def help(game, args):
        """Zeigt verfügbare Befehle."""
        help_text = """
VERFÜGBARE BEFEHLE

BEWEGUNG:
  gehe <richtung> (n, s, e, w, u, d, out)
  klettere <objekt> (climb)
  verstecke <objekt> (hide in)

INTERAKTION:
  schaue / l [objekt]
  nimm <objekt>
  benutze <objekt> [mit <objekt>]
  öffne <objekt>
  schließe <objekt>
  lege <objekt> in/auf <objekt>
  zerstöre / break <objekt>

SYSTEM:
  inv / i       - Inventar zeigen
  journal / j   - Aufgaben ansehen
  save [name]   - Speichern
  load [name]   - Laden
  map           - Karte anzeigen
"""
        game.log('info', help_text.strip())

    @staticmethod
    def oracle(game, args):
        """Debug / Story Helper Tool: Zeigt interne Zustände an."""
        game.log('info', "--- ORACLE SYSTEM STATUS ---")
        game.log('info', f"Zeit: T+{game.time}m | Stabilität: {game.stability}%")
        
        # Quest Status
        active_quests = game.quests.get_active_quests()
        if active_quests:
            game.log('info', f"Aktive Quests: {len(active_quests)}")
        else:
            game.log('info', "Keine aktiven Quests.")

        pending_count = 0
        if hasattr(game, 'events'):
            for e in game.events.events:
                if not e.get('triggered', False) and e.get('trigger') == 'time' and e.get('trigger_time', 0) > game.time:
                    pending_count += 1
        
        game.log('info', f"Ausstehende Zeit-Events: {pending_count}")
        
        npc_info = []
        for npc in game.npcs:
            state = npc.get('state', 'default')
            loc = npc.get('location', 'unknown')
            room_name = loc
            if loc in game.rooms:
                room_name = game.rooms[loc].get('name', loc)
            npc_info.append(f"{npc[ATTR_NAME]} ({state}) @ {room_name}")
        
        if npc_info:
            game.log('info', "NPCs:\n  " + "\n  ".join(npc_info))

        warnings = []
        if game.stability < 50: warnings.append("KRITISCH: Stations-Integrität gefährdet!")
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
        visited_ids = [r_id for r_id, r in game.rooms.items() if r.get('visited')]
        
        if not visited_ids:
            game.log('info', "Keine Kartendaten verfügbar.")
            return

        for r_id in visited_ids:
            room = game.rooms[r_id]
            name = room.get(ATTR_NAME, "Unbekannt")
            marker = " [HIER]" if r_id == game.location else ""
            
            exits = room.get('exits', {})
            exit_strs = []
            for direction, target_id in exits.items():
                target_name = "???"
                if target_id in visited_ids:
                    target_room = game.rooms[target_id]
                    target_name = target_room.get(ATTR_NAME, "Unbekannt")
                
                short_dir = direction[0].upper() if len(direction) > 2 else direction.upper()
                exit_strs.append(f"{short_dir} -> {target_name}")
            
            exits_display = ", ".join(exit_strs) if exit_strs else "Sackgasse"
            log_type = 'location' if r_id == game.location else 'info'
            game.log(log_type, f"> {name}{marker}\n  Verbindungen: {exits_display}")

    @staticmethod
    def journal(game, args):
        """Zeigt aktive und erledigte Quests an."""
        # Wir nutzen 'header' oder 'system' als Typ, je nachdem was im Renderer definiert ist.
        # 'event' ist meist Orange/Gelb und gut sichtbar.
        game.log('event', "--- PERSÖNLICHES LOGBUCH ---")
        
        # Aktive Quests
        active = game.quests.get_active_quests()
        if active:
            game.log('info', "AKTUELLE ZIELE:")
            for q in active:
                # Titel hervorheben
                game.log('success', f"[*] {q['title']}")
                # Beschreibung einrücken
                stage_desc = q.get('stage_desc', "")
                if stage_desc:
                    game.log('story', f"    > {stage_desc}")
        else:
            game.log('info', "Keine aktiven Aufgaben.")
            
        # Erledigte Quests (Optional: Nur wenn Argument 'all' oder so, aber hier immer gut)
        completed = game.quests.get_completed_quests()
        if completed:
            game.log('info', "")
            game.log('info', "ERLEDIGT:")
            for title in completed:
                # Erledigt in Grau/Story-Farbe
                game.log('story', f"[x] {title}")

        failed = game.quests.get_failed_quests()
        if failed:
            game.log('info', "")
            game.log('info', "FEHLGESCHLAGEN:")
            for title in failed:
                game.log('error', f"[!] {title}")
