from engine.resolver import Resolver
from engine.constants import *

class InteractionHandler:
    @staticmethod
    def _is_reachable(game, obj):
        current = obj
        while True:
            loc_id = current.get('location')
            if loc_id == game.location: return True 
            if loc_id == LOC_INVENTORY: return True 
            if loc_id == LOC_VOID: return False     
            parent = game.objects.get(loc_id)
            if not parent: return False 
            if parent.get('type') == TYPE_CONTAINER and not parent.get('is_open'):
                return False 
            current = parent

    @staticmethod
    def look(game, args):
        if not args:
            InteractionHandler._look_room_overview(game)
            return
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='look')
        InteractionHandler._examine_target(game, target)

    @staticmethod
    def _look_room_overview(game):
        room = game.get_room(game.location)
        game.log('location', room[ATTR_NAME])
        
        # Beschreibung holen
        raw_desc = game.render_room_desc(game.location)
        
        # Formatierung:
        desc = raw_desc
        
        # 1. Versuch: Standard Python Format
        try:
            format_map = {oid: o.get(ATTR_NAME, oid) for oid, o in game.objects.items()}
            desc = raw_desc.format(**format_map)
        except:
            # 2. Versuch: Manuelles Ersetzen von {id}
            for oid, obj in game.objects.items():
                placeholder = "{" + oid + "}"
                if placeholder in raw_desc:
                    real_name = obj.get(ATTR_NAME, oid)
                    desc = desc.replace(placeholder, real_name)
            
            if "{chair}" in desc:
                chair_obj = game.objects.get("chair")
                if chair_obj:
                    desc = desc.replace("{chair}", chair_obj.get(ATTR_NAME, "Sessel"))

        game.log('story', desc)
        
        exits = room.get('exits', {})
        if exits:
            trans = {"north": "Norden", "south": "Süden", "east": "Osten", "west": "Westen", "up": "Oben", "down": "Unten"}
            exit_names = [trans.get(d, d.capitalize()) for d in exits.keys()]
            game.log('info', f"Ausgänge: {', '.join(exit_names)}")
        else: 
            game.log('info', "Es gibt keinen sichtbaren Ausweg.")

        InteractionHandler._list_visible_objects(game)

    @staticmethod
    def _list_visible_objects(game):
        # Nur Objekte direkt im Raum
        local_objects = [o for o in game.objects.values() if o['location'] == game.location]
        
        items_ground = []
        scenery = []
        
        for obj in local_objects:
            obj_type = obj.get('type')
            name = obj.get(ATTR_NAME, "Unbekanntes Objekt")

            if obj_type == TYPE_SURFACE:
                contents = [sub[ATTR_NAME] for sub in game.objects.values() if sub['location'] == obj[ATTR_ID]]
                desc = name
                if contents: desc += f" (darauf: {', '.join(contents)})"
                scenery.append(desc)
                
            elif obj_type == TYPE_CONTAINER:
                desc = name
                if obj.get('is_open'):
                    contents = [sub[ATTR_NAME] for sub in game.objects.values() if sub['location'] == obj[ATTR_ID]]
                    if contents: desc += f" (offen, enthält: {', '.join(contents)})"
                    else: desc += " (offen, leer)"
                else:
                    desc += " (geschlossen)"
                scenery.append(desc)
            
            elif obj_type == TYPE_SCENERY: 
                scenery.append(name)
                
            elif obj_type == TYPE_ITEM or (not obj_type and obj.get(ATTR_MOVABLE)):
                items_ground.append(name)

        if scenery:
            game.log('info', f"Du siehst hier: {', '.join(scenery)}")
            
        if items_ground: 
            game.log('info', f"Am Boden liegt: {', '.join(items_ground)}")
        
        visible_npcs = [n[ATTR_NAME] for n in game.npcs if n['location'] == game.location]
        if visible_npcs: game.log('character', f"Personen: {', '.join(visible_npcs)}")

    @staticmethod
    def _examine_target(game, target):
        if not target:
            game.log('error', "Das siehst du hier nicht.")
            return
        
        if not InteractionHandler._is_reachable(game, target):
            game.log('error', "Du kannst das von hier aus nicht genau sehen (verdeckt).")
            return

        desc = target.get(ATTR_DESC, "Nichts Besonderes.")
        status = []
        
        # Schätzung des Gewichts statt exakter Angabe
        if target.get(ATTR_MOVABLE):
            real_weight = game.get_real_weight(target)
            weight_desc = "sehr leicht"
            pronomen = "Er" # Vereinfacht, eigentlich müsste man Genus prüfen (Der Becher -> Er, Die Flasche -> Sie)
                            # Für eine erste Version nutzen wir neutrale Formulierungen oder "Es"
                            
            if real_weight > 10.0: weight_desc = "extrem schwer"
            elif real_weight > 5.0: weight_desc = "sehr schwer"
            elif real_weight > 2.0: weight_desc = "schwer"
            elif real_weight > 0.5: weight_desc = "handlich"
            
            # Bessere Formulierung: "Es sieht ... aus"
            status.append(f"Das Objekt wirkt {weight_desc}.")

        temp = target.get(ATTR_TEMP, 20)
        if temp > 50: status.append("Es ist HEISS.")
        elif temp < 5: status.append("Es ist eiskalt.")
        
        if target.get(ATTR_MATTER) == MATTER_LIQUID: status.append("Es ist flüssig.")

        if target.get('type') == TYPE_CONTAINER:
            # Kapazität nur grob schätzen? Nein, Füllstand ist visuell erkennbar.
            cap = target.get(ATTR_CAPACITY, 0)
            
            if target.get('is_locked'): status.append("Verschlossen.")
            elif target.get('is_open'):
                contents = [o for o in game.objects.values() if o['location'] == target[ATTR_ID]]
                names = [o[ATTR_NAME] for o in contents]
                
                current_load = sum(game.get_real_weight(c) for c in contents)
                
                # Füllstandsanzeige
                if cap > 0:
                    fill_ratio = current_load / cap
                    if fill_ratio > 0.9: status.append("(Fast voll)")
                    elif fill_ratio > 0.5: status.append("(Halb voll)")
                    elif fill_ratio > 0.1: status.append("(Fast leer)")
                    else: status.append("(Leer)")

                if names: status.append(f"Inhalt: {', '.join(names)}")
                else: status.append("Leer.")
            else: status.append("Geschlossen.")
        
        if target.get('state') == STATE_SABOTAGED: status.append("[ZUSTAND: SABOTIERT]")
        if target.get('state') == STATE_BROKEN: status.append("[ZUSTAND: DEFEKT]")
        
        if status: desc += " " + " ".join(status)
        game.log('story', desc)

    @staticmethod
    def take(game, args):
        if any(w in args for w in ["all", "alles", "alle"]):
            candidates = [o for o in game.objects.values() if o.get(ATTR_MOVABLE)]
            taken = []
            
            current_load = game.get_inventory_weight()
            
            for item in candidates:
                if item.get(ATTR_MATTER) == MATTER_LIQUID: continue 
                
                if InteractionHandler._is_reachable(game, item) and item['location'] != LOC_INVENTORY:
                    item_weight = game.get_real_weight(item)
                    
                    if current_load + item_weight <= game.max_carry_weight:
                        item['location'] = LOC_INVENTORY
                        taken.append(item[ATTR_NAME])
                        current_load += item_weight 
                    else:
                        game.log('error', f"Zu schwer! {item[ATTR_NAME]} passt nicht mehr ins Inventar.")
                        break 

            if taken:
                game.log('success', f"Genommen: {', '.join(taken)}")
                game.tick(len(taken))
            else:
                if not any(o.get(ATTR_MOVABLE) for o in game.objects.values() if o['location'] == game.location):
                    game.log('info', "Hier gibt es nichts Greifbares zum Mitnehmen.")
            return

        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='take')
        
        if target:
            if target['location'] == LOC_INVENTORY: return game.log('info', "Hast du schon.")
            
            if not InteractionHandler._is_reachable(game, target):
                game.log('error', "Du kommst da nicht heran (Container geschlossen?).")
                return

            if not target.get(ATTR_MOVABLE): return game.log('error', "Das ist fest verankert.")
            if target.get(ATTR_MATTER) == MATTER_LIQUID: return game.log('error', "Du brauchst einen Behälter.")

            item_weight = game.get_real_weight(target)
            current_load = game.get_inventory_weight()
            
            if current_load + item_weight > game.max_carry_weight:
                return game.log('error', f"Das ist zu schwer! ({item_weight}kg). Du trägst bereits {current_load}kg.")

            target['location'] = LOC_INVENTORY
            game.log('success', f"{target[ATTR_NAME]} genommen.")
            game.tick(1)
        else:
            game.log('error', "Nicht gefunden.")

    @staticmethod
    def give(game, args):
        separators = game.config.get('vocabulary', {}).get('prepositions', {}).get('give', ["an", "to"])
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        if sep_indices:
            idx = sep_indices[0]; item_words = args[:idx]; npc_words = args[idx+1:]
        else:
            if len(args) < 2: return game.log('error', "Was an wen?")
            item_words = args[:-1]; npc_words = [args[-1]]
            
        item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='give_item')
        if not item: return game.log('error', "Das hast du nicht.")
        
        npc = Resolver.find_mentioned_npc(game, npc_words)
        if not npc: return game.log('error', "Diese Person ist nicht hier.")
        
        game.log('success', f"Du gibst {item[ATTR_NAME]} an {npc[ATTR_NAME]}.")
        item['location'] = LOC_VOID 
        
        trigger_id = f"received_{item[ATTR_ID]}"
        game.add_knowledge(trigger_id)
        
        from engine.handlers.dialogue import DialogueHandler
        
        dialogue_active = False
        current_state = npc.get('state', 'default')
        state_db = npc.get('dialogue', {}).get(current_state, {})
        
        reaction_topic = None
        if trigger_id in state_db:
            reaction_topic = state_db[trigger_id]
        if not reaction_topic:
            for topic, entry in state_db.items():
                if isinstance(entry, dict) and 'condition' in entry:
                    cond = entry['condition']
                    if cond == trigger_id or (isinstance(cond, dict) and cond.get('value') == trigger_id):
                        reaction_topic = entry
                        break
        
        if reaction_topic:
            game.dialogue_active = True
            game.dialogue_partner = npc
            game.log('event', f"--- REAKTION VON {npc[ATTR_NAME].upper()} ---")
            DialogueHandler._print_dialogue(game, npc, reaction_topic)
            DialogueHandler.process_effects(game, reaction_topic, npc)
        else:
            DialogueHandler.talk(game, [npc[ATTR_NAME]])

    @staticmethod
    def open(game, args):
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='open')
        
        if not target: return game.log('error', "Das sehe ich hier nicht.")
        
        if not InteractionHandler._is_reachable(game, target):
             game.log('error', "Du kommst da nicht heran.")
             return

        if target.get('type') == TYPE_SURFACE: return game.log('info', "Das ist offen sichtbar.")
        if target.get('type') != TYPE_CONTAINER: return game.log('error', "Das lässt sich nicht öffnen.")
        
        if target.get('is_locked'):
            key_id = target.get('key_id')
            if key_id:
                has_key = any(o[ATTR_ID] == key_id and o['location'] == LOC_INVENTORY for o in game.objects.values())
                if has_key:
                    key_obj = game.objects[key_id]; game.log('info', f"(Ich schließe mit {key_obj[ATTR_NAME]} auf...)"); target['is_locked'] = False
                else: return game.log('error', "Verschlossen. Du brauchst einen Schlüssel.")
            else: return game.log('error', "Verschlossen.")
        
        if target.get('is_open'): return game.log('info', "Ist schon offen.")

        target['is_open'] = True
        game.log('success', f"{target[ATTR_NAME]} geöffnet.")
        InteractionHandler.look(game, clean_args)

    @staticmethod
    def put(game, args):
        separators = game.config.get('vocabulary', {}).get('prepositions', {}).get('put', ["in", "auf"])
        sep_indices = [i for i, w in enumerate(args) if w.lower() in separators]
        
        item_words = args[:sep_indices[0]] if sep_indices else args[:-1]
        container_words = args[sep_indices[0]+1:] if sep_indices else [args[-1]]
        
        item = Resolver.resolve_target(game, item_words, location_filter=FILTER_INVENTORY, verb='put_item')
        if not item: return game.log('error', "Das hast du nicht.")
        
        container = Resolver.resolve_target(game, container_words, location_filter=FILTER_RECURSIVE, verb='put_container')
        if not container: return game.log('error', "Das sehe ich hier nicht.")
        
        if not InteractionHandler._is_reachable(game, container):
            game.log('error', "Du kommst an den Behälter nicht ran.")
            return
        
        if container == item: return game.log('error', "Geht nicht.")
        if container.get('type') not in [TYPE_CONTAINER, TYPE_SURFACE]: return game.log('error', "Da passt nichts rein.")
        if container.get('type') == TYPE_CONTAINER and not container.get('is_open'): return game.log('error', f"Der {container[ATTR_NAME]} ist geschlossen.")
        
        capacity = container.get(ATTR_CAPACITY, 9999) 
        
        contents = [o for o in game.objects.values() if o['location'] == container[ATTR_ID]]
        current_content_weight = sum(game.get_real_weight(c) for c in contents)
        
        item_weight = game.get_real_weight(item)
        
        if current_content_weight + item_weight > capacity:
            return game.log('error', f"Passt nicht! Der Behälter ist voll ({current_content_weight}/{capacity}kg).")

        item['location'] = container[ATTR_ID]; prep = "auf" if container.get('type') == TYPE_SURFACE else "in"
        game.log('success', f"Du legst {item[ATTR_NAME]} {prep} {container[ATTR_NAME]}."); game.tick(2)

    @staticmethod
    def inventory(game, args):
        items = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY]
        display_list = []
        for item in items:
            name = item.get(ATTR_NAME, "Unbekannt")
            # Gewicht wird hier nicht mehr angezeigt
            
            if item.get('type') in [TYPE_CONTAINER, TYPE_SURFACE]:
                if item.get('type') == TYPE_SURFACE or item.get('is_open', True):
                    contents = [o[ATTR_NAME] for o in game.objects.values() if o['location'] == item[ATTR_ID]]
                    if contents: name += f" (enthält: {', '.join(contents)})"
                else: name += " (geschlossen)"
            
            # Nur Name anzeigen
            display_list.append(f"{name}")
            
        current_load = game.get_inventory_weight()
        max_load = game.max_carry_weight
        
        if not display_list: 
            game.log('info', f"Inventar: Leer ({current_load:.1f}/{max_load}kg)")
        else: 
            game.log('info', f"Inventar ({current_load:.1f}/{max_load}kg): {', '.join(display_list)}")

    @staticmethod
    def use(game, args):
        separators = game.config.get('vocabulary', {}).get('prepositions', {}).get('use', ["mit", "with"])
        separator_indices = [i for i, word in enumerate(args) if word.lower() in separators]
        
        item1_name = ""; item2_name = ""
        if separator_indices:
            idx = separator_indices[0]
            item1_name = " ".join(args[:idx]); item2_name = " ".join(args[idx+1:])
        elif len(args) >= 2:
            mid = len(args) // 2; item1_name = " ".join(args[:mid]); item2_name = " ".join(args[mid:])
        else:
            game.log('info', f"Womit möchtest du {' '.join(args)} benutzen?")
            game.pending_interaction = {'verb': 'use', 'args': args}
            return

        result_msg = game.perform_combine(item1_name, item2_name)
        if "Fehler" in result_msg or "nicht" in result_msg.lower(): game.log('error', result_msg)
        else: game.log('success', result_msg); game.tick(5)

    @staticmethod
    def break_(game, args): 
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='break')
        if not target: return game.log('error', "Was aufbrechen?")
        
        if not target.get('is_locked'): return game.log('info', "Das ist nicht verschlossen.")
        
        tools = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY and 
                 ("brecheisen" in o[ATTR_NAME].lower() or o.get('tool_type') == 'force')]
        
        if not tools:
            game.log('error', "Du kannst das nicht mit bloßen Händen aufbrechen. Du brauchst ein Brecheisen.")
            return

        tool = tools[0]
        game.log('success', f"Mit einem lauten Krachen brichst du das Schloss mit dem {tool[ATTR_NAME]} auf.")
        target['is_locked'] = False
        target['is_open'] = True
        target['state'] = STATE_BROKEN
        game.tick(10)

    @staticmethod
    def fix(game, args):
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_RECURSIVE, verb='fix')
        if not target: return game.log('error', "Was reparieren?")
        
        if target.get('state') not in [STATE_SABOTAGED, STATE_BROKEN]:
            return game.log('info', "Das sieht intakt aus.")

        tools = [o for o in game.objects.values() if o['location'] == LOC_INVENTORY and 
                 ("werkzeug" in o[ATTR_NAME].lower() or "kit" in o[ATTR_NAME].lower() or o.get('tool_type') == 'repair')]

        if not tools:
            game.log('error', "Du hast kein geeignetes Werkzeug, um das zu reparieren.")
            return

        tool = tools[0]
        game.log('success', f"Du arbeitest mit dem {tool[ATTR_NAME]} daran...")
        target['state'] = STATE_NORMAL
        game.log('success', f"{target[ATTR_NAME]} ist wieder funktionstüchtig.")
        game.tick(20)
    
    @staticmethod
    def drop_item(game, args):
        clean_args = Resolver.clean_args(args)
        target = Resolver.resolve_target(game, clean_args, location_filter=FILTER_INVENTORY, verb='drop')
        if target: target['location'] = game.location; game.log('success', f"{target[ATTR_NAME]} abgelegt."); game.tick(1)
        
    @staticmethod
    def wait(game, args):
        game.log('info', "Du wartest eine Weile..."); game.tick(10)
