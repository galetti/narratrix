import importlib
import copy

class ChapterManager:
    """
    Verwaltet das Laden und Zusammenfügen von globalen Daten und Kapitel-Daten.
    """
    
    @staticmethod
    def load_chapter(chapter_module_path, global_data_module):
        """
        Lädt ein Kapitel und verschmilzt es mit den globalen Daten.
        """
        # 1. Kapitel-Modul dynamisch laden
        try:
            chapter = importlib.import_module(chapter_module_path)
            # Reload erzwingen, falls wir im selben Prozess das Kapitel wechseln
            importlib.reload(chapter) 
        except ImportError as e:
            print(f"[ERROR] Konnte Kapitel '{chapter_module_path}' nicht laden: {e}")
            return None

        # 2. Basis-Config aus globalen Daten erstellen
        # Wir starten mit der globalen Konfiguration als Basis
        final_config = copy.deepcopy(global_data_module.GLOBAL_CONFIG)
        
        # 3. Daten mergen (Chapter überschreibt/ergänzt Global)
        
        # A) Räume zusammenfügen (Dicts)
        global_rooms = final_config.get('rooms', {})
        chapter_rooms = getattr(chapter, 'ROOMS', {})
        final_config['rooms'] = {**global_rooms, **chapter_rooms}
        
        # B) Objekte/Items zusammenfügen (Dicts)
        global_items = final_config.get('objects', {})
        chapter_items = getattr(chapter, 'ITEMS', {})
        final_config['objects'] = {**global_items, **chapter_items}
        
        # C) NPCs zusammenfügen (Listen)
        global_npcs = final_config.get('npcs', [])
        chapter_npcs = getattr(chapter, 'NPCS', [])
        final_config['npcs'] = global_npcs + chapter_npcs
        
        # D) Events/Matrix zusammenfügen (Listen)
        global_matrix = final_config.get('narrative_matrix', [])
        chapter_matrix = getattr(chapter, 'NARRATIVE_MATRIX', [])
        final_config['narrative_matrix'] = global_matrix + chapter_matrix
        
        # E) Kombinationen (Typ-sicherer Merge)
        global_combos = final_config.get('combinations', [])
        chapter_combos = getattr(chapter, 'COMBINATIONS', [])
        
        if isinstance(global_combos, list) and isinstance(chapter_combos, list):
            # Wenn beide Listen sind (dein Fall), einfach addieren
            final_config['combinations'] = global_combos + chapter_combos
        elif isinstance(global_combos, dict) and isinstance(chapter_combos, dict):
            # Wenn beide Dicts sind
            final_config['combinations'] = {**global_combos, **chapter_combos}
        elif isinstance(global_combos, list) and isinstance(chapter_combos, dict):
             # Mischfall abfangen (Fehlertoleranz)
             if not chapter_combos: # Wenn Chapter leer ist, ist der Typ egal
                 final_config['combinations'] = global_combos
             else:
                 print("[WARNUNG] Combinations Typ-Konflikt: Global=List, Chapter=Dict. Chapter-Combos ignoriert.")
                 final_config['combinations'] = global_combos
        else:
            # Fallback
            final_config['combinations'] = global_combos

        # Meta-Daten aktualisieren
        final_config['meta']['current_chapter_module'] = chapter_module_path
        if hasattr(chapter, 'CHAPTER_META'):
            final_config['meta'].update(chapter.CHAPTER_META)
            
        print(f"[SYSTEM] Kapitel geladen: {final_config['meta'].get('chapter_title', 'Unbekannt')}")
        
        return final_config
