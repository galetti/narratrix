from engine.resolver import Resolver, ResolutionError
from engine.constants import *

class InteractionHandler:
    
    # ... Helper (is_open_container, is_held_by_player, format_contents) bleiben gleich ...
    @staticmethod
    def _is_open_container(obj):
        if obj.get('type') == TYPE_SURFACE: return True
        if obj.get('type') == TYPE_CONTAINER and obj.get('is_open', True): return True
        return False

    @staticmethod
    def _is_held_by_player(game, obj):
        current = obj
        while True:
            loc = current['location']
            if loc == LOC_INVENTORY: return True
            if loc in game.rooms: return False 
            parent = game.objects.get(loc)
            if not parent: return False
            current = parent

    @staticmethod
    def _format_contents_recursive(game, obj_id, depth=0):
        if depth > 2: return "" 
        contents = [sub for sub in game.objects.values() if sub['location'] == obj_id]
        if not contents: return ""
        names = []
        for item in contents:
            name = item[ATTR_NAME]
            if InteractionHandler._is_open_container(item):
                sub_text = InteractionHandler._format_contents_recursive(game, item[ATTR_ID], depth+1)
                if sub_text: name += f" ({sub_text})"
            names.append(name)
        return ", ".join(names)

    @staticmethod
    def look(game, args):
        # Wenn versteckt, sieht man nur eingeschränkt
        if game.hidden_in:
            container = game.objects.get(game.hidden_in)
            game.log('info', f"Du versteckst dich in {container[ATTR_NAME]}.")
            game.log('info', "Befehle: 'raus' (move out), 'warte'.")
            
            # Optional: Eingeschränkter Blick in den Raum
            room = game.get_room(game.location)
            visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
            if visible_npcs: game.log('character', f"Durch den Spalt siehst du: {', '.join(visible_npcs)}")
            return

        room = game.get_room(game.location)
        if not args:
            game.log('location', room[ATTR_NAME])
            game.log('story', game.render_room_desc(game.location))
            exits = room.get('exits', {})
            if exits:
                trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten", "out": "Ausgang"}
                exit_names = [trans.get(d, d.capitalize()) for d in exits.keys()]
                game.log('info', f"Ausgänge: {', '.join(exit_names)}")
            else: game.log('info', "Es gibt keinen sichtbaren Ausweg.")

            visible_objs = []
            local_objects = [o for o in game.objects.values() if o['location'] == game.location]
            for obj in local_objects:
                if InteractionHandler._is_open_container(obj):
                    content_str = InteractionHandler._format_contents_recursive(game, obj[ATTR_ID])
                    prep = "Auf dem" if obj.get('type') == TYPE_SURFACE else "Im offenen"
                    if content_str: game.log('info', f"{prep} {obj[ATTR_NAME]}: {content_str}")
                elif obj.get('type') == TYPE_ITEM or (not obj.get('type') and obj.get(ATTR_WEIGHT, float('inf')) < float('inf')):
                     visible_objs.append(obj[ATTR_NAME])
            if visible_objs: game.log('info', f"Am Boden: {', '.join(visible_objs)}")
            visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
            if visible_npcs: game.log('character', f"Personen: {', '.join(visible_npcs)}")
            return

        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='look')
            if target:
                desc = target.get(ATTR_DESC, "Nichts Besonderes.")
                status = []
                
                temp = target.get(ATTR_TEMP, 20)
                if temp > 50: status.append("Es ist HEISS.")
                elif temp > 30: status.append("Es ist warm.")
                elif temp < 5: status.append("Es ist eiskalt.")
                if target.get(ATTR_MATTER) == MATTER_LIQUID: status.append("Es ist flüssig.")

                if target.get('is_scale'):
                    contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    total_weight = sum(o.get('weight', 0) for o in contents)
                    status.append(f"Display: {total_weight:.2f} kg")

                if target.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                    if target.get('type') == TYPE_CONTAINER and target.get('is_locked'): 
                        status.append("Verschlossen.")
                    elif InteractionHandler._is_open_container(target):
                        content_str = InteractionHandler._format_contents_recursive(game, target[ATTR_ID])
                        if content_str: status.append(f"Inhalt: {content_str}")
                        else: status.append("Leer.")
                    elif target.get('type') == TYPE_CONTAINER:
                        status.append("Geschlossen.")
                
                if target.get('state') == STATE_SABOTAGED: status.append("[WARNUNG: SABOTIERT]")
                if target.get('state') == STATE_BROKEN: status.append("[DEFEKT]")
                
                if status: desc += " " + " ".join(status)
                game.log('story', desc)
        except ResolutionError as e: game.log('error', str(e))

    # NEU: HIDE MECHANIK
    @staticmethod
    def hide(game, args):
        if game.hidden_in:
            return game.log('info', "Du bist bereits versteckt. Benutze 'raus' um das Versteck zu verlassen.")
            
        clean_args = Resolver.clean_args(args)
        try:
            # Wir suchen nur Container im aktuellen Raum (nicht im Inventar!)
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_ROOM, verb='hide')
            
            if target:
                if target.get('type') != TYPE_CONTAINER:
                    return game.log('error', "Darin kannst du dich nicht verstecken.")
                
                # Check Size/Capacity? Vorerst nehmen wir an, alle Container sind groß genug (Schränke etc.)
                # Außer Items wie "Becher". Wir bräuchten ein Property 'can_hide_player'.
                # Fallback: Alles was nicht movable ist und Container ist.
                if target.get(ATTR_WEIGHT, 0) < 100: # Willkürliche Grenze: Nur große Dinge
                     return game.log('error', "Das ist zu klein für dich.")
                
                if not target.get('is_open', True):
                    return game.log('error', "Es ist geschlossen.")

                game.hidden_in = target[ATTR_ID]
                game.log('success', f"Du kriechst in {target[ATTR_NAME]} und ziehst die Tür leise zu.")
                
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def take(game, args):
        if game.hidden_in: return game.log('error', "Du bist versteckt. Komm erst raus.")
        # ... Rest von take (identisch) ...
        if any(w in args for w in ["all", "alles", "alle"]):
            candidates = Resolver._collect_candidates(game, FILTER_RECURSIVE)
            candidates = [o for o in candidates if o['location'] != LOC_INVENTORY and o.get(ATTR_WEIGHT, float('inf')) < float('inf')]
            taken = []
            for item in candidates:
                if item.get(ATTR_MATTER) == MATTER_LIQUID: continue 
                item['location'] = LOC_INVENTORY
                taken.append(item[ATTR_NAME])
            if taken:
                game.log('success', f"Genommen: {', '.join(taken)}")
                game.tick(len(taken))
            else: game.log('info', "Hier gibt es nichts zum Mitnehmen.")
            return

        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='take')
            if target:
                if target['location'] == LOC_INVENTORY: return game.log('info', "Hast du schon.")
                weight = target.get(ATTR_WEIGHT, float('inf'))
                if weight == float('inf'): return game.log('error', "Das ist viel zu schwer oder fest verankert.")
                if target.get(ATTR_MATTER) == MATTER_LIQUID: return game.log('error', "Das kannst du nicht mit den bloßen Händen nehmen. Du brauchst einen Behälter.")

                target['location'] = LOC_INVENTORY
                game.log('success', f"{target[ATTR_NAME]} genommen.")
                
                if target.get('type') == TYPE_SURFACE:
                    contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                    if contents:
                        names = []
                        for item in contents:
                            item['location'] = LOC_INVENTORY
                            names.append(item[ATTR_NAME])
                        if names: game.log('info', f"Du verstaust auch: {', '.join(names)}.")
                game.tick(1)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def give(game, args):
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        # ... Rest von give ...
        if not args: return game.log('error', "Was an wen?")
        separators = ["an", "to", "dem", "der"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        item_words = args[:sep_indices[0]] if sep_indices else args[:-1]
        npc_words = args[idx+1:] if sep_indices else [args[-1]]
        try:
            item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='give_item')
            if item:
                npc = Resolver.find_mentioned_npc(game, npc_words)
                if not npc: return game.log('error', "Diese Person ist nicht hier.")
                trigger_ids = [f"received_{item[ATTR_ID]}"]
                if item.get('type') == TYPE_CONTAINER:
                    contents = [o for o in game.objects.values() if o['location'] == item[ATTR_ID]]
                    for c in contents: trigger_ids.append(f"received_{c[ATTR_ID]}")
                current_state = npc.get('state', 'default')
                dialogue_root = npc.get('dialogue', {})
                state_db = dialogue_root.get(current_state, {})
                reaction_entry = None
                for topic, entry in state_db.items():
                    if isinstance(entry, dict) and 'condition' in entry:
                        cond = entry['condition']
                        if isinstance(cond, dict) and cond.get('type') == 'knowledge' and cond.get('value') in trigger_ids: reaction_entry = entry; break
                        elif isinstance(cond, str) and cond in trigger_ids: reaction_entry = entry; break
                if reaction_entry:
                    game.log('success', f"Du gibst {item[ATTR_NAME]} an {npc[ATTR_NAME]}.")
                    item['location'] = LOC_VOID 
                    for t_id in trigger_ids: game.add_knowledge(t_id)
                    from engine.handlers.dialogue import DialogueHandler
                    game.dialogue_active = True
                    game.dialogue_partner = npc
                    game.log('event', f"--- GESPRÄCH MIT {npc[ATTR_NAME].upper()} ---")
                    DialogueHandler._print_dialogue(game, npc, reaction_entry)
                    DialogueHandler.process_effects(game, reaction_entry, npc)
                else: game.log('character', f"{npc[ATTR_NAME]} lehnt ab: \"Das brauche ich gerade nicht.\"")
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def open(game, args):
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='open')
            if target: 
                if target.get('type') == TYPE_SURFACE: return game.log('info', "Das ist offen sichtbar.")
                if target.get('type') != TYPE_CONTAINER: return game.log('error', "Das lässt sich nicht öffnen.")
                
                mechanism = target.get('mechanism')
                if mechanism:
                    mech_type = mechanism.get('type')
                    if mech_type == 'rusty':
                        if not mechanism.get('solved', False): return game.log('error', mechanism.get('fail_msg', "Es klemmt."))
                    elif mech_type == 'electronic':
                        if not mechanism.get('powered', True): return game.log('error', "Kein Strom.")
                        if not mechanism.get('unlocked', False): return game.log('error', mechanism.get('fail_msg', "Zugriff verweigert."))

                if target.get('is_locked'):
                    key_id = target.get('key_id')
                    if key_id:
                        has_key = any(o[ATTR_ID] == key_id and o['location'] == LOC_INVENTORY for o in game.objects.values())
                        if has_key: key_obj = game.objects[key_id]; game.log('info', f"(Ich schließe mit {key_obj[ATTR_NAME]} auf...)"); target['is_locked'] = False
                        else: return game.log('error', "Verschlossen. Du brauchst einen Schlüssel.")
                    else: return game.log('error', "Verschlossen.")
                if target.get('is_open'): return game.log('info', "Ist schon offen.")
                target['is_open'] = True
                game.log('success', f"{target[ATTR_NAME]} geöffnet.")
                InteractionHandler.look(game, clean_args)
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def put(game, args):
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        # ... Rest von put ...
        if not args: return game.log('error', "Was wohin legen?")
        separators = ["in", "auf", "on", "into", "an"]
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        item_words = args[:sep_indices[0]] if sep_indices else args[:-1]
        container_words = args[sep_indices[0]+1:] if sep_indices else [args[-1]]
        try:
            item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='put_item')
            if item: 
                container = Resolver.resolve_target(game, container_words, location_filter=FILTER_RECURSIVE, verb='put_container')
                if container:
                    if container == item: return game.log('error', "Geht nicht.")
                    if container.get('type') not in [TYPE_CONTAINER, TYPE_SURFACE]: return game.log('error', "Da kannst du nichts reinlegen.")
                    if container.get('type') == TYPE_CONTAINER and not container.get('is_open'): return game.log('error', f"Der {container[ATTR_NAME]} ist geschlossen.")
                    
                    if container.get('is_scale'):
                        if InteractionHandler._is_held_by_player(game, container):
                            return game.log('error', "Die Waage muss auf einem stabilen Untergrund stehen.")

                    item['location'] = container[ATTR_ID]; prep = "auf" if container.get('type') == TYPE_SURFACE else "in"
                    game.log('success', f"Du legst {item[ATTR_NAME]} {prep} {container[ATTR_NAME]}."); game.tick(2)
                    
                    if container.get('is_scale'):
                        contents = [o for o in game.objects.values() if o['location'] == container[ATTR_ID]]
                        total_weight = sum(o.get('weight', 0) for o in contents)
                        game.log('info', f"Das Display der Waage springt an: {total_weight:.2f} kg")
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def inventory(game, args):
        items = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        display_list = []
        for item in items:
            name = item[ATTR_NAME]
            if InteractionHandler._is_open_container(item):
                content_str = InteractionHandler._format_contents_recursive(game, item[ATTR_ID])
                if content_str: name += f" (enthält: {content_str})"
                else: name += " (leer)"
            elif item.get('type') == TYPE_CONTAINER: name += " (geschlossen)"
            display_list.append(name)
        if not display_list: game.log('info', "Inventar: Leer")
        else: game.log('info', f"Inventar: {', '.join(display_list)}")

    @staticmethod
    def use(game, args):
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        if not args: return game.log('error', "Was benutzen?")
        separator_indices = [i for i, word in enumerate(args) if word.lower() in ["mit", "with", "und", "an"]]
        item1_name = ""
        item2_name = ""
        if separator_indices:
            idx = separator_indices[0]
            item1_name = " ".join(args[:idx])
            item2_name = " ".join(args[idx+1:])
        elif len(args) >= 2:
            item1_name = args[0]; item2_name = args[-1]
            if len(args) > 2: mid = len(args) // 2; item1_name = " ".join(args[:mid]); item2_name = " ".join(args[mid:])
        else:
            game.log('info', f"Womit möchtest du {' '.join(args)} benutzen?")
            game.pending_interaction = {'verb': 'use', 'args': args}
            return
        result_msg = game.perform_combine(item1_name, item2_name)
        if "Fehler" in result_msg or "nicht" in result_msg.lower(): game.log('error', result_msg)
        else: game.log('success', result_msg); game.tick(2)

    @staticmethod
    def break_(game, args): 
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='break')
            if target: 
                if not target.get('type') == TYPE_CONTAINER or not target.get('is_locked'): return game.log('error', "Nicht nötig.")
                key_id = target.get('key_id'); key_obj = game.objects.get(key_id) if key_id else None
                if key_obj and key_obj['location'] == LOC_INVENTORY:
                     game.log('success', f"Du brichst das Schloss mit dem {key_obj[ATTR_NAME]} auf."); target['is_locked'] = False; target['is_open'] = True; game.tick(5); InteractionHandler.look(game, clean_args)
                else: game.log('error', "Du brauchst Werkzeug.")
        except ResolutionError as e: game.log('error', str(e))

    @staticmethod
    def fix(game, args):
        if game.hidden_in: return game.log('error', "Nicht während du versteckt bist.")
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='fix')
            if target: 
                if target.get('state') in [STATE_SABOTAGED, STATE_BROKEN]: target['state'] = STATE_NORMAL; game.log('success', f"Repariert."); game.tick(15)
                else: game.log('info', "Scheint intakt zu sein.")
        except ResolutionError as e: game.log('error', str(e))
    
    @staticmethod
    def drop_item(game, args):
        if game.hidden_in: return game.log('error', "Nicht im Versteck.")
        clean_args = Resolver.clean_args(args)
        try:
            target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_INVENTORY, verb='drop')
            if target: target['location'] = game.location; game.log('success', f"{target[ATTR_NAME]} fallen gelassen."); game.tick(1)
        except ResolutionError as e: game.log('error', str(e))
        
    @staticmethod
    def wait(game, args):
        game.log('info', "Du wartest eine Weile..."); game.tick(10)