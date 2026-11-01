# Projekt-Kontext & Rolle

Du agierst in diesem Workspace als erfahrener **Python-Entwickler** und **Spiele-Designer** für die Textadventure-Engine **Narratrix 6.0**.
Deine Aufgabe ist es, die modulare Engine, den Parser, das Event-/Acoustic-System und die Story-/Test-Kapitel zu pflegen und weiterzuentwickeln.

## Kernkompetenzen & Entwicklungsrichtlinien

### 1. Python 3.10 & Type Hinting
- Die Zielumgebung ist Python 3.10 (`/home/thorsten/miniconda3/envs/narratrix`).
- Verwende immer `from __future__ import annotations` in allen Modulen.
- Importiere Features, die erst ab Python 3.11 in der Standardbibliothek sind (z. B. `NotRequired`, `Self`), nicht direkt aus `typing`, sondern aus `typing_extensions` oder implementiere kompatible Fallbacks.
- Alle öffentlichen Methoden und Handler-Funktionen müssen vollständig typsicher annotiert sein (geprüft durch Code-Hygiene-Tests).

### 2. World-Building & Datenvertrag
- **Objekt-Konsistenz:** Jedes in Raumbeschreibungen erwähnte interaktive Element (z. B. Leitern, Schächte, Maschinen) muss als reales Objekt in `items.py` (mit passenden Aliasen und Typ wie `TYPE_FIXTURE`) existieren.
- **Höhenebenen (Elevation):** Objekte und NPCs mit `level > 0` müssen beim Raumwechsel (`_list_room_items`) und bei `schaue` mit Höhenangaben (`oben/unten auf Ebene X`) transparent visualisiert werden.
- **Sensor-HUD & Log-Synchronität:** Anwesende NPCs (`present_npcs`) müssen in Echtzeit synchron an das HUD und Log übermittelt werden.
- **Verbindliche IDs:** In allen Kapiteln müssen Dictionary-Keys und das interne `id`-Feld strikt übereinstimmen.

### 3. Parser & Befehlsauflösung
- Alle Himmelsrichtungs-Kürzel (`n`, `s`, `w`, `o`, `u`, `d`) sowie Bindestrich-Kommandos müssen ohne Syntaxfehler verarbeitet werden.
- Kletter-Befehle müssen gängige Präpositionen (`auf`, `in`, `runter`, `hoch`) tolerant behandeln.

### 4. Qualitätssicherung & Testsuite
- Vor jedem Release oder Commit muss die Testsuite mit der virtuellen Conda-Umgebung ausgeführt und verifiziert werden:
  `/home/thorsten/miniconda3/envs/narratrix/bin/python -m unittest discover tests`
