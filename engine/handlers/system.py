from __future__ import annotations

import json
import logging
import os
import re
from typing import TYPE_CHECKING

from engine.constants import ATTR_NAME, STATE_SABOTAGED
from engine.strings import Texts

if TYPE_CHECKING:
    from engine.game_state import GameState

logger = logging.getLogger(__name__)


class SystemHandler:
    @staticmethod
    def _save_filename(args: list[str]) -> str:
        stem = args[0] if args else "savegame"
        stem = stem[:-5] if stem.lower().endswith(".json") else stem
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", stem):
            raise ValueError(Texts.SAVE_INVALID_NAME)
        return f"{stem}.json"
    
    @staticmethod
    def save(game: GameState, args: list[str]) -> None:
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
            game.log('success', Texts.SAVE_SUCCESS.format(filename=filename))
        except (OSError, TypeError, ValueError) as e:
            logger.error("Fehler beim Speichern von '%s': %s", filename, e)
            game.log('error', Texts.SAVE_ERROR.format(error=e))

    @staticmethod
    def load(game: GameState, args: list[str]) -> None:
        """Lädt einen Spielstand."""
        try:
            filename = SystemHandler._save_filename(args)
        except ValueError as exc:
            return game.log('error', str(exc))
        
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")
        filepath = os.path.join(save_dir, filename)
        
        if not os.path.exists(filepath):
            return game.log('error', Texts.LOAD_NOT_FOUND.format(filename=filename))
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            success = game.deserialize_state(data)
            if success:
                game.log('success', Texts.LOAD_SUCCESS)
                from engine.handlers.exploration import ExplorationHandler
                ExplorationHandler.look(game, [])
            else:
                game.log('error', Texts.LOAD_PROCESS_ERROR)
                
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error("Kritischer Fehler beim Laden von '%s': %s", filename, e)
            game.log('error', Texts.LOAD_CRITICAL_ERROR.format(error=e))

    @staticmethod
    def help(game: GameState, args: list[str]) -> None:
        """Zeigt verfügbare Befehle."""
        game.log('info', Texts.HELP_TEXT)

    @staticmethod
    def oracle(game: GameState, args: list[str]) -> None:
        """Debug / Story Helper Tool: Zeigt interne Zustände an."""
        game.log('info', Texts.ORACLE_HEADER)
        game.log('info', Texts.ORACLE_TIME_STABILITY.format(time=game.time, stability=game.stability))
        
        # Quest Status
        active_quests = game.quests.get_active_quests()
        if active_quests:
            game.log('info', Texts.ORACLE_ACTIVE_QUESTS.format(count=len(active_quests)))
        else:
            game.log('info', Texts.ORACLE_NO_ACTIVE_QUESTS)

        pending_count = 0
        if hasattr(game, 'events'):
            for e in game.events.events:
                if not e.get('triggered', False) and e.get('trigger') == 'time' and e.get('trigger_time', 0) > game.time:
                    pending_count += 1
        
        game.log('info', Texts.ORACLE_PENDING_EVENTS.format(count=pending_count))
        
        npc_info: list[str] = []
        for npc in game.npcs:
            state = npc.get('state', 'default')
            loc = npc.get('location', 'unknown')
            room_name = loc
            if loc in game.rooms:
                room_name = game.rooms[loc].get('name', loc)
            npc_info.append(f"{npc[ATTR_NAME]} ({state}) @ {room_name}")
        
        if npc_info:
            game.log('info', "NPCs:\n  " + "\n  ".join(npc_info))

        warnings: list[str] = []
        if game.stability < 50: warnings.append(Texts.ORACLE_CRITICAL_STABILITY)
        sabotaged_rooms = [r.get('name', r_id) for r_id, r in game.rooms.items() if r.get('state') == STATE_SABOTAGED]
        if sabotaged_rooms:
            warnings.append(Texts.ORACLE_SABOTAGE_IN.format(rooms=', '.join(sabotaged_rooms)))
            
        if warnings:
            game.log('alarm', "\n".join(warnings))
        else:
            game.log('success', Texts.ORACLE_NOMINAL)

    @staticmethod
    def map(game: GameState, args: list[str]) -> None:
        """Zeigt eine dynamisch generierte Karte der besuchten Räume."""
        game.log('info', Texts.MAP_HEADER)
        visited_ids = [r_id for r_id, r in game.rooms.items() if r.get('visited')]
        
        if not visited_ids:
            game.log('info', Texts.MAP_NO_DATA)
            return

        for r_id in visited_ids:
            room = game.rooms[r_id]
            name = room.get(ATTR_NAME, Texts.MAP_UNKNOWN_ROOM)
            marker = Texts.MAP_HERE_MARKER if r_id == game.location else ""
            
            exits = room.get('exits', {})
            exit_strs: list[str] = []
            for direction, target_id in exits.items():
                target_name = "???"
                if target_id in visited_ids:
                    target_room = game.rooms[target_id]
                    target_name = target_room.get(ATTR_NAME, Texts.MAP_UNKNOWN_ROOM)
                
                short_dir = direction[0].upper() if len(direction) > 2 else direction.upper()
                exit_strs.append(f"{short_dir} -> {target_name}")
            
            exits_display = ", ".join(exit_strs) if exit_strs else Texts.MAP_DEAD_END
            log_type = 'location' if r_id == game.location else 'info'
            game.log(
                log_type,
                Texts.MAP_CONNECTIONS.format(
                    name=name, marker=marker, exits=exits_display
                ),
            )

    @staticmethod
    def journal(game: GameState, args: list[str]) -> None:
        """Zeigt aktive und erledigte Quests an."""
        game.log('event', Texts.JOURNAL_HEADER)
        
        # Aktive Quests
        active = game.quests.get_active_quests()
        if active:
            game.log('info', Texts.JOURNAL_ACTIVE_TITLE)
            for q in active:
                # Titel hervorheben
                game.log('success', f"[*] {q['title']}")
                # Beschreibung einrücken
                stage_desc = q.get('stage_desc', "")
                if stage_desc:
                    game.log('story', f"    > {stage_desc}")
        else:
            game.log('info', Texts.JOURNAL_NO_ACTIVE)
            
        # Erledigte Quests (Optional: Nur wenn Argument 'all' oder so, aber hier immer gut)
        completed = game.quests.get_completed_quests()
        if completed:
            game.log('info', "")
            game.log('info', Texts.JOURNAL_DONE_TITLE)
            for title in completed:
                # Erledigt in Grau/Story-Farbe
                game.log('story', f"[x] {title}")

        failed = game.quests.get_failed_quests()
        if failed:
            game.log('info', "")
            game.log('info', Texts.JOURNAL_FAILED_TITLE)
            for title in failed:
                game.log('error', f"[!] {title}")
