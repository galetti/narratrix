from __future__ import annotations

from typing import TYPE_CHECKING

from engine.constants import (
    ATTR_CLIMBABLE,
    ATTR_ID,
    ATTR_NAME,
    FILTER_ROOM,
    TYPE_CONTAINER,
    TYPE_SCENERY,
)
from engine.resolver import Resolver, ResolutionError
from engine.strings import Texts
from engine.handlers.common import CommonHandler

if TYPE_CHECKING:
    from engine.game_state import GameState


class MovementHandler:
    @staticmethod
    def _list_room_items(game: GameState, room_id: str) -> None:
        visible_items: list[str] = []
        for obj in game.objects.values():
            if obj['location'] == room_id:
                if obj.get('type') == TYPE_SCENERY: continue
                
                obj_level = obj.get('level', 0)
                level_info = ""
                
                if obj_level != game.elevation:
                    if obj_level > game.elevation: level_info = Texts.LEVEL_INFO_UP.format(level=obj_level)
                    else: level_info = Texts.LEVEL_INFO_DOWN.format(level=obj_level)

                name = obj[ATTR_NAME]
                
                if obj.get('type') == TYPE_CONTAINER:
                    if obj.get('is_open'): name += Texts.CONTAINER_OPEN
                    else: name += Texts.CONTAINER_CLOSED
                
                if obj.get('is_resource') and obj.get('count', 1) > 1:
                    name = f"{obj['count']}x {name}"

                visible_items.append(f"{name}{level_info}")
        
        if visible_items:
            game.log('info', Texts.MOVE_SEE_ITEMS.format(', '.join(visible_items)))

        visible_npcs = CommonHandler.format_visible_npcs(game, room_id)
        if visible_npcs:
            game.log('character', Texts.LOOK_PERSONS.format(', '.join(visible_npcs)))

    @staticmethod
    def handle(game: GameState, args: list[str]) -> None:
        if game.hidden_in:
            if any(w in args for w in ["raus", "out", "verlasse", "exit"]):
                game.hidden_in = None
                game.log('success', Texts.MOVE_LEAVE_HIDE)
                game.log('location', game.rooms[game.location][ATTR_NAME])
                desc = game.render_room_desc(game.location)
                game.log('story', desc)
                MovementHandler._list_room_items(game, game.location)
                return
            else:
                return game.log('error', Texts.MOVE_STILL_HIDDEN)

        if not args:
            return game.log('error', Texts.MOVE_NO_DEST)

        vocab_dirs = game.config.get('vocabulary', {}).get('directions', {})
        target_dir: str | None = None
        filler_preps = {"nach", "in", "gen", "richtung", "zum", "zur", "den", "dem", "der", "die", "das"}
        filtered_args = [w.lower() for w in args if w.lower() not in filler_preps]
        candidate_words = filtered_args if filtered_args else [args[0].lower()]

        for word in candidate_words:
            for canonical, synonyms in vocab_dirs.items():
                if word == canonical or word in synonyms:
                    target_dir = canonical
                    break
            if target_dir:
                break

        if not target_dir:
            target_dir = candidate_words[0] 
        
        room = game.rooms[game.location]
        exits = room.get('exits', {})
        
        if target_dir in exits:
            target_id = exits[target_dir]
            
            blocked = False
            blocker_name = ""
            room_objs = [o for o in game.objects.values() if o['location'] == game.location]
            for obj in room_objs:
                if obj.get('linked_exit') == target_dir:
                    if not obj.get('is_open', True): 
                        blocked = True
                        blocker_name = obj[ATTR_NAME]
                        break
            
            if blocked:
                game.log('error', Texts.MOVE_BLOCKED.format(blocker=blocker_name))
            else:
                game.location = target_id
                game.elevation = 0 
                game.visit_room(target_id)
                
                game.log('location', game.rooms[target_id][ATTR_NAME])
                desc = game.render_room_desc(target_id)
                game.log('story', desc)
                
                visible_exits = [k for k in game.rooms[target_id].get('exits', {}).keys()]
                exit_names = [Texts.direction_name(d) for d in visible_exits]
                if exit_names: game.log('info', Texts.LOOK_EXITS.format(', '.join(exit_names)))
                
                MovementHandler._list_room_items(game, target_id)
                game.tick(1) 
        elif target_dir == "down" and game.elevation > 0:
            MovementHandler.climb(game, ["down"])
        elif target_dir == "up" and game.elevation == 0:
            climbables = [
                obj
                for obj in game.objects.values()
                if obj.get("location") == game.location and obj.get(ATTR_CLIMBABLE, False)
            ]
            if climbables:
                MovementHandler.climb(game, [climbables[0][ATTR_NAME]])
            else:
                game.log('error', Texts.MOVE_NO_WAY.format(target=target_dir))
        else:
            try:
                climb_candidate = Resolver.resolve_target(
                    game, candidate_words, location_filter=FILTER_ROOM, verb="climb"
                )
            except ResolutionError:
                climb_candidate = None
            if climb_candidate and climb_candidate.get(ATTR_CLIMBABLE, False):
                MovementHandler.climb(game, candidate_words)
            else:
                game.log('error', Texts.MOVE_NO_WAY.format(target=target_dir))

    @staticmethod
    def climb(game: GameState, args: list[str]) -> None:
        if game.hidden_in: return game.log('error', Texts.ERR_HIDDEN)
        
        if not args:
            return game.log('error', Texts.MOVE_CLIMB_WHAT)

        # Filter Präpositionen aus den Argumenten für sauberes Resolver-Matching
        clean_args = [
            w
            for w in args
            if w.lower() not in ["auf", "on", "up", "hoch", "in", "im", "an", "den", "die", "das"]
        ]
        
        # Fallback: Wenn nur "klettere auf" eingegeben wurde, ist clean_args leer
        if not clean_args:
             if args[0].lower() not in ["up", "hoch", "rauf", "oben"]:
                 return game.log('error', Texts.MOVE_CLIMB_WHAT)

        # "Climb down" logic
        if args[0].lower() in ["down", "runter", "ab", "unten", "boden"]:
            if game.elevation > 0:
                game.elevation = 0
                game.log('success', Texts.MOVE_CLIMB_DOWN)
                MovementHandler._list_room_items(game, game.location)
                game.tick(1)
                return
            else:
                MovementHandler.handle(game, ["down"])
                return

        # "Climb up" logic (ohne Zielobjekt)
        if args[0].lower() in ["up", "hoch", "rauf", "oben"]:
            if game.elevation == 0:
                if 'up' in game.rooms[game.location].get('exits', {}):
                    MovementHandler.handle(game, ["up"])
                else:
                    game.log('error', Texts.MOVE_CLIMB_CANNOT_SIMPLE)
                return
            else:
                game.log('error', Texts.MOVE_CLIMB_ALREADY_UP)
                return

        try:
            # WICHTIG: Nutze die bereinigten Argumente
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_ROOM, verb='climb')
            if not target:
                return
            
            if not target.get(ATTR_CLIMBABLE, False):
                game.log('info', Texts.MOVE_CLIMB_CANNOT.format(target=target[ATTR_NAME]))
                return

            if 'target_elevation' in target:
                new_level = target['target_elevation']
                if new_level == game.elevation:
                    game.log(
                        'info',
                        Texts.MOVE_CLIMB_ALREADY_THERE.format(
                            target=target[ATTR_NAME], level=new_level
                        ),
                    )
                    MovementHandler._list_room_items(game, game.location)
                else:
                    game.elevation = new_level
                    game.log(
                        'success',
                        Texts.MOVE_CLIMB_SUCCESS_LEVEL.format(
                            target=target[ATTR_NAME], level=new_level
                        ),
                    )
                    MovementHandler._list_room_items(game, game.location)
                    game.tick(1)
                return

            if 'destination' in target:
                dest = target['destination']
                game.location = dest
                game.elevation = 0
                game.visit_room(dest)
                game.log('success', Texts.MOVE_CLIMB_SUCCESS_DEST.format(target=target[ATTR_NAME]))
                game.tick(1)
                
                game.log('location', game.rooms[dest][ATTR_NAME])
                game.log('story', game.render_room_desc(dest))
                MovementHandler._list_room_items(game, dest)
                return

            current_room = game.rooms[game.location]
            climb_targets = current_room.get('climb_targets', {})
            target_id = target[ATTR_ID]
            
            if target_id in climb_targets:
                dest_room_id = climb_targets[target_id]
                game.log(
                    'success',
                    Texts.MOVE_CLIMB_SUCCESS_PASSAGE.format(target=target[ATTR_NAME]),
                )
                game.location = dest_room_id
                game.elevation = 0
                game.visit_room(dest_room_id)
                game.tick(1)
                
                game.log('location', game.rooms[dest_room_id][ATTR_NAME])
                game.log('story', game.render_room_desc(dest_room_id))
                MovementHandler._list_room_items(game, dest_room_id)
            else:
                game.log(
                    'success',
                    Texts.MOVE_CLIMB_NO_HEIGHT.format(target=target[ATTR_NAME]),
                )
        
        except ResolutionError as e:
            game.log('error', str(e))
