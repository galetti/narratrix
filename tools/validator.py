import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from data.story_config import CONFIG
    from engine.constants import *
except ImportError as e:
    print(f"KRITISCHER FEHLER: Konnte Konfiguration nicht laden. {e}")
    sys.exit(1)

def validate_integrity():
    print(f"--- Starte Deep-Scan für '{CONFIG['meta']['title']}' v{CONFIG['meta']['version']} ---\n")
    
    errors = []
    warnings = []
    
    rooms = CONFIG['rooms']
    items = CONFIG['objects']
    npcs = CONFIG['npcs']
    matrix = CONFIG['narrative_matrix']
    combos = CONFIG['combinations']

    # --- ASSET PATH SETUP (NEU: in data/assets) ---
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

    # 1. RÄUME
    print(f"Prüfe {len(rooms)} Räume...")
    for r_id, room in rooms.items():
        for d, t_id in room.get('exits', {}).items():
            if t_id not in rooms:
                errors.append(f"[ROOM] '{r_id}': Exit '{d}' führt ins Nichts ('{t_id}').")
        
        if 'map_x' not in room or 'map_y' not in room:
            warnings.append(f"[MAP] Raum '{r_id}' hat keine Koordinaten.")
            
        check_image(room.get('img'), f"Raum {r_id}")

    # 2. ITEMS & PHYSIK
    print(f"Prüfe {len(items)} Objekte...")
    for o_id, obj in items.items():
        loc = obj.get('location')
        if not (loc in rooms or loc in items or loc in [LOC_INVENTORY, LOC_VOID]):
            errors.append(f"[ITEM] '{o_id}': Ungültige Location '{loc}'.")
        
        matter = obj.get(ATTR_MATTER, MATTER_SOLID)
        is_container = obj.get('type') == TYPE_CONTAINER
        
        if matter == MATTER_LIQUID and not is_container and obj.get('movable'):
            warnings.append(f"[PHYSICS] '{o_id}' ist flüssig und beweglich, aber kein Container.")

        if obj.get('type') == TYPE_CONTAINER and 'is_open' not in obj:
            warnings.append(f"[LOGIC] Container '{o_id}' hat keinen 'is_open' Status.")

        if obj.get('is_locked'):
            key = obj.get('key_id')
            if key and key not in items:
                errors.append(f"[ITEM] '{o_id}': Schlüssel '{key}' existiert nicht.")

    # 3. NPCs & DIALOGE
    print(f"Prüfe {len(npcs)} NPCs...")
    for npc in npcs:
        n_name = npc['name']
        if npc['start_loc'] not in rooms:
            errors.append(f"[NPC] '{n_name}': Start '{npc['start_loc']}' ungültig.")
            
        check_image(npc.get('img'), f"NPC {n_name} (Basis)")
        
        dialogue = npc.get('dialogue', {})
        for state, data in dialogue.items():
            if isinstance(data, dict) and 'img' in data:
                check_image(data['img'], f"NPC {n_name} (State: {state})")
                
            def scan_effects(node, path):
                if isinstance(node, dict):
                    if 'effect' in node:
                        eff = node['effect']
                        if eff['type'] == 'move_npc' and eff.get('target') not in rooms:
                            errors.append(f"[DIALOG] '{n_name}' ({path}): Move-Target '{eff.get('target')}' ungültig.")
                    for k, v in node.items():
                        if isinstance(v, dict): scan_effects(v, f"{path}->{k}")

            scan_effects(data, state)

    # 4. EVENTS & MATRIX
    print(f"Prüfe {len(matrix)} Events...")
    event_ids = [e['id'] for e in matrix]
    for evt in matrix:
        if 'origin_id' in evt and evt['origin_id'] not in rooms:
             errors.append(f"[EVENT] '{evt['id']}': Origin '{evt['origin_id']}' ungültig.")
        if evt.get('trigger') == 'relative' and evt.get('parent_id') not in event_ids:
             errors.append(f"[EVENT] '{evt['id']}': Parent '{evt.get('parent_id')}' fehlt.")

    # 5. CRAFTING
    print(f"Prüfe {len(combos)} Rezepte...")
    for i, recipe in enumerate(combos):
        for item in recipe['items']:
            if item not in items: errors.append(f"[CRAFT] Rezept #{i}: Zutat '{item}' fehlt.")
        if recipe.get('result') not in items:
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

if __name__ == "__main__":
    validate_integrity()