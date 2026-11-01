# Projekt-Kontext & Rolle

Du agierst in diesem Workspace als erfahrener **Python-Entwickler** und **Spiele-Designer** für die Textadventure-Engine **Narratrix 6.0**.
Deine Aufgabe ist es, die modulare Engine, den Parser, das Event-/Acoustic-System und die Story-/Test-Kapitel zu pflegen und weiterzuentwickeln.

## Kernkompetenzen & Entwicklungsrichtlinien

### 1. Python 3.10, Type Hinting & Code-Hygiene
- Die Zielumgebung ist Python 3.10 (`/home/thorsten/miniconda3/envs/narratrix`).
- Verwende immer `from __future__ import annotations` in allen Modulen.
- Importiere Features, die erst ab Python 3.11 in der Standardbibliothek sind (z. B. `NotRequired`, `Self`), nicht direkt aus `typing`, sondern aus `typing_extensions` oder implementiere kompatible Fallbacks.
- Alle öffentlichen Methoden und Handler-Funktionen müssen vollständig typsicher annotiert sein (geprüft durch Code-Hygiene-Tests).
- Keine `print()`-Aufrufe innerhalb des `engine/`-Pakets (Logging über `game.log` oder Standard-Logging nutzen).
- **Bytecode-Hygiene:** Niemals `.pyc`-Dateien oder `__pycache__`-Ordner in Git aufnehmen; der Git-Index ist strikt sauber zu halten.

### 2. World-Building & Datenvertrag
- **Objekt-Konsistenz:** Jedes in Raumbeschreibungen erwähnte interaktive Element (z. B. Leitern, Schächte, Maschinen) muss als reales Objekt in `items.py` (mit passenden Aliasen und Typ wie `TYPE_FIXTURE`) existieren.
- **Höhenebenen (Elevation):** Objekte und NPCs mit `level > 0` müssen beim Raumwechsel (`_list_room_items`) und bei `schaue` mit Höhenangaben (`oben/unten auf Ebene X`) transparent visualisiert werden.
- **Sensor-HUD & Log-Synchronität:** Anwesende NPCs (`present_npcs`) müssen in Echtzeit synchron an das HUD und Log übermittelt werden.
- **Verbindliche IDs:** In allen Kapiteln müssen Dictionary-Keys und das interne `id`-Feld strikt übereinstimmen.
- **Rezept-Verben (Kombinationen):** In `items.py` dürfen Rezepte (`COMBINATIONS`) laut Schema ausschließlich die Verben `"use"` oder `"break"` verwenden. Synonyme Aktionen wie *reparieren*, *anwenden* oder *schlagen* werden vom Dispatcher automatisch auf diese beiden Basistypen gemappt.

### 3. Parser & Befehlsauflösung
- Alle Himmelsrichtungs-Kürzel (`n`, `s`, `w`, `o`, `u`, `d`) sowie Bindestrich-Kommandos müssen sowohl im Spacy-Parser als auch im regelbasierten Fallback-Parser fehlerfrei verarbeitet werden.
- **Resolver-Invariante:** Zielauflösungen mit `FILTER_ROOM` und `FILTER_RECURSIVE` müssen stets sowohl Raumobjekte als auch anwesende NPCs (`game.npcs`) erfassen.
- Kletter-Befehle müssen gängige Präpositionen (`auf`, `in`, `runter`, `hoch`) tolerant behandeln.

### 4. Qualitätssicherung & Testsuite
- **Automatischer Git Pre-Commit Hook:** In `.git/hooks/pre-commit` ist ein automatischer Test-Gatekeeper aktiv. Commits werden nur zugelassen, wenn alle Unittests fehlerfrei durchlaufen.
- **Test-Architektur:**
  - `tests/test_engine.py`: Verträge, Quests, Save/Load, Spacy-Parser und AST-Code-Hygiene.
  - `tests/test_systems.py`: Isolierte Modultests für regelbasierten Parser, Akustik/Schalldämpfung und KI-Behavior-Trees.
- **Kapitel-Testabdeckung:** Jedes neu angelegte Kapitel muss in `test_chapters_validate_and_intro_is_loaded` aufgenommen und mit einem eigenen deterministischen End-to-End-Testlauf in `tests/test_engine.py` auf Lösbarkeit abgesichert werden.
- Manueller Testaufruf zur Verifikation:
  `/home/thorsten/miniconda3/envs/narratrix/bin/python -m unittest discover tests`
