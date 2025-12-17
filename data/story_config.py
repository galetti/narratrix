# data/story_config.py
# DIES IST JETZT DER BOOTSTRAPPER FÜR DAS KAPITEL-SYSTEM

import data.global_data as global_data
from engine.chapter_manager import ChapterManager

# Standardmäßig laden wir Kapitel 1
# Später kann der Savegame-Loader entscheiden, ein anderes Kapitel zu laden,
# indem er ChapterManager.load_chapter aufruft.

# Hier definieren wir, welches Kapitel beim "Neuen Spiel" geladen wird.
START_CHAPTER = "data.chapters.chapter_1"

# Wir laden die Konfiguration initial
CONFIG = ChapterManager.load_chapter(START_CHAPTER, global_data)

if CONFIG is None:
    raise RuntimeError("Kritischer Fehler: Start-Kapitel konnte nicht geladen werden!")

# Hilfsfunktion für Savegames/Engine, um Kapitel zu wechseln
def reload_config_for_chapter(chapter_module_str):
    """
    Lädt die globale CONFIG neu basierend auf dem gewünschten Kapitel.
    Wird vom SystemHandler beim Laden eines Spielstands aufgerufen.
    """
    global CONFIG
    new_config = ChapterManager.load_chapter(chapter_module_str, global_data)
    if new_config:
        CONFIG.clear()
        CONFIG.update(new_config)
        return True
    return False
