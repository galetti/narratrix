import sys
import os
import importlib

# Füge das Projekt-Root zum Pfad hinzu, damit Importe funktionieren
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.constants import *

def validate_integrity(chapter_module_path="data.chapters.ep1_station.config"):
    print(f"--- Starte Deep-Scan für Kapitel: '{chapter_module_path}' ---\n")
    
    errors = []
    warnings = []

    # 1. Lade Common Layer
    try:
        common_mod = importlib.import_module("data.common.config")
        common_data = common_mod.COMMON_CONFIG
        print("✅ Common Layer geladen.")
    except ImportError as e:
        errors.append(f"[FATAL] Common Layer nicht gefunden: {e}")
        common_data = {"rooms": {}, "objects": {}, "npcs": [], "matrix": [], "combinations": []}

    # 2. Lade Chapter Layer
    try:
        chapter_mod = importlib.import_module(chapter_module_path)
        chapter_data = chapter_mod.CHAPTER_CONFIG
        print(f"✅ Chapter Layer geladen: {chapter_data['meta']['title']}\n")
    except ImportError as e:
        print(f"❌ KRITISCHER FEHLER: Konnte Kapitel '{chapter_module_path}' nicht laden. {e}")
        sys.exit(1)

    # --- NAMESPACE KOLLISIONSPRÜFUNG ---
    print("Prüfe auf ID-Konflikte zwischen Common und Chapter...")
    
    def check_collision(dict_common, dict_chapter, type_label):
        common_keys = set(dict_common.keys())
        chapter_keys = set(dict_chapter.keys())
        intersection = common_keys.intersection(chapter_keys)
        
        for duplicate in intersection:
            errors.append(f"[COLLISION] {type_label} ID '{duplicate}' existiert sowohl in Common als auch im Chapter! (Chapter überschreibt Common)")

    check_collision(common_data.get('rooms', {}), chapter_data.get('rooms', {}), "ROOM")
    check_collision(common_data.get('objects', {}), chapter_data.get('objects', {}), "ITEM")
    
    # NPCs sind Listen, hier müssen wir IDs manuell extrahieren
    common_npc_ids = {n['id'] for n in common_data.get('npcs', []) if 'id' in n}
    chapter_npc_ids = {n['id'] for n in chapter_data.get('npcs', []) if 'id' in n}
    npc_intersection = common_npc_ids.intersection(chapter_npc_ids)
    for dup in npc_intersection:
        errors.append(f"[COLLISION] NPC ID '{dup}' existiert doppelt!")

    # --- MERGE FÜR TIEFENPRÜFUNG ---
    # Wir simulieren den Merge, den der StoryLoader macht, um Referenzen zu prüfen
    merged_rooms = common_data.get('rooms', {}).copy()
    merged_rooms.update(chapter_data.get('rooms', {}))
    
    merged_items = common_data.get('objects', {}).copy()
    merged_items.update(chapter_data.get('objects', {}))
    
    merged_npcs = common_data.get('npcs', []) + chapter_data.get('npcs', [])
    
    # --- ASSET PATH SETUP ---
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    asset_dir = os.path.join(project_root, "data", "assets", "images")
    
    def check_image(img_id, context):
        if not img_id: return
        found = False
        for ext in [".png", ".jpg", ".jpeg"]:
            if os.path.exists(os.path.join(asset_dir, img_id + ext)):
                found = True
                break
        if not found:
            warnings.append(f"[ASSET] {context}: Bild '{img_id}' fehlt in data/assets/images/")

    # 1. RÄUME & EXITS
    print(f"Prüfe {len(merged_rooms)} Räume (Merged)...")
    for r_id, room in merged_rooms.items():
        for d, t_id in room.get('exits', {}).items():
            # Spezialfall: Dynamische Exits (wie 'out' im Schiff) werden evtl. erst zur Laufzeit gesetzt.
            # Wenn sie hier hardcoded sind, prüfen wir sie.
            if t_id not in merged_rooms:
                # Ist es vielleicht ein Tag-basierter Exit, der noch nicht aufgelöst ist?
                # Nein, hier prüfen wir statische Configs.
                errors.append(f"[ROOM] '{r_id}': Exit '{d}' führt ins Nichts ('{t_id}').")
        
        if 'map_x' not in room or 'map_y' not in room:
            warnings.append(f"[MAP] Raum '{r_id}' hat keine Koordinaten.")
            
        check_image(room.get('img'), f"Raum {r_id}")

    # 2. ITEMS & PHYSIK
    print(f"Prüfe {len(merged_items)} Objekte...")
    for o_id, obj in merged_items.items():
        loc = obj.get('location')
        if not (loc in merged_rooms or loc in merged_items or loc in [LOC_INVENTORY, LOC_VOID]):
            errors.append(f"[ITEM] '{o_id}': Ungültige Location '{loc}'.")
        
        matter = obj.get(ATTR_MATTER, MATTER_SOLID)
        is_container = obj.get('type') == TYPE_CONTAINER
        
        if matter == MATTER_LIQUID and not is_container and obj.get('movable'):
            warnings.append(f"[PHYSICS] '{o_id}' ist flüssig und beweglich, aber kein Container.")

        if obj.get('type') == TYPE_CONTAINER and 'is_open' not in obj:
            warnings.append(f"[LOGIC] Container '{o_id}' hat keinen 'is_open' Status.")

        if obj.get('is_locked'):
            key = obj.get('key_id')
            if key and key not in merged_items:
                errors.append(f"[ITEM] '{o_id}': Schlüssel '{key}' existiert nicht.")

    # 3. NPCs & DIALOGE (Inklusive neuer Struktur)
    print(f"Prüfe {len(merged_npcs)} NPCs...")
    for npc in merged_npcs:
        n_name = npc.get('name', 'UNKNOWN')
        n_id = npc.get('id', 'UNKNOWN_ID')
        
        if 'start_loc' in npc and npc['start_loc'] not in merged_rooms:
            errors.append(f"[NPC] '{n_name}' ({n_id}): Start '{npc['start_loc']}' ungültig.")
            
        # Check Bilder (Flat Structure Fallback)
        if 'img' in npc: check_image(npc['img'], f"NPC {n_name} (Basis)")
        
        # Neue Struktur: States
        if 'states' in npc:
            for state_name, state_data in npc['states'].items():
                # Visuals Check
                if 'visuals' in state_data and 'img' in state_data['visuals']:
                    check_image(state_data['visuals']['img'], f"NPC {n_name} (State: {state_name})")
                
                # Behavior Check
                if 'behavior' in state_data:
                    route = state_data['behavior'].get('route', [])
                    for stop in route:
                        if stop not in merged_rooms:
                            errors.append(f"[NPC] '{n_name}' ({n_id}): Route-Punkt '{stop}' existiert nicht.")
                
                # Dialogue Effects Check
                if 'dialogue' in state_data:
                    scan_dialogue_effects(state_data['dialogue'], n_name, f"{state_name}", merged_rooms, merged_items, errors)

        # Alte Struktur (Fallback Check)
        if 'dialogue' in npc and not 'states' in npc:
             for state, data in npc['dialogue'].items():
                 scan_dialogue_effects(data, n_name, state, merged_rooms, merged_items, errors)

    # 4. EVENTS & MATRIX
    # (Merge Matrix fehlt noch, aber wir prüfen das Kapitel und Common separat wenn nötig)
    # Hier prüfen wir einfach die Listen aus den Configs
    all_events = common_data.get('matrix', []) + chapter_data.get('matrix', [])
    print(f"Prüfe {len(all_events)} Events...")
    event_ids = [e['id'] for e in all_events]
    
    for evt in all_events:
        if 'origin_id' in evt and evt['origin_id'] not in merged_rooms:
             errors.append(f"[EVENT] '{evt['id']}': Origin '{evt['origin_id']}' ungültig.")
        if evt.get('trigger') == 'relative' and evt.get('parent_id') not in event_ids:
             errors.append(f"[EVENT] '{evt['id']}': Parent '{evt.get('parent_id')}' fehlt.")

    # 5. CRAFTING
    all_combos = common_data.get('combinations', []) + chapter_data.get('combinations', [])
    print(f"Prüfe {len(all_combos)} Rezepte...")
    for i, recipe in enumerate(all_combos):
        for item in recipe['items']:
            if item not in merged_items: errors.append(f"[CRAFT] Rezept #{i}: Zutat '{item}' fehlt.")
        if recipe.get('result') not in merged_items:
             errors.append(f"[CRAFT] Rezept #{i}: Ergebnis '{recipe.get('result')}' fehlt.")

    print("\n" + "="*30)
    if warnings:
        print(f"⚠️  {len(warnings)} WARNUNGEN:")
        for w in warnings: print(f"  - {w}")
    else:
        print("✨ Keine Warnungen.")

    if errors:
        print(f"\n❌ {len(errors)} KRITISCHE FEHLER:")
        for e in errors: print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n✅ DATEN-INTEGRITÄT BESTÄTIGT.")
        sys.exit(0)

def scan_dialogue_effects(node, npc_name, path, rooms, items, errors):
    """Rekursive Funktion zum Prüfen von Dialog-Effekten."""
    if isinstance(node, dict):
        if 'effect' in node:
            effects = node['effect']
            if not isinstance(effects, list): effects = [effects]
            
            for eff in effects:
                e_type = eff.get('type')
                if e_type == 'move_npc':
                    if eff.get('target') not in rooms:
                        errors.append(f"[DIALOG] '{npc_name}' ({path}): Move-Target '{eff.get('target')}' ungültig.")
                elif e_type == 'receive_item':
                    if eff.get('item_id') not in items:
                        errors.append(f"[DIALOG] '{npc_name}' ({path}): Item-Reward '{eff.get('item_id')}' ungültig.")
        
        for k, v in node.items():
            if isinstance(v, dict): scan_dialogue_effects(v, npc_name, f"{path}->{k}", rooms, items, errors)

if __name__ == "__main__":
    # Optional: Kapitel per Argument übergeben
    if len(sys.argv) > 1:
        validate_integrity(sys.argv[1])
    else:
        validate_integrity()
