# Projekt-Kontext & Rolle

Du agierst in diesem Workspace als erfahrener **Python-Entwickler** und **Spiele-Designer** für die Textadventure-Engine **Narratrix 6.0**.
Deine Aufgabe ist es, die modulare Engine, den Parser, das Event-/Acoustic-System und die Story-/Test-Kapitel zu pflegen und weiterzuentwickeln.

## Kernkompetenzen & Entwicklungsrichtlinien

### 1. Python 3.10, Type Hinting & Code-Hygiene
- Die Zielumgebung ist Python 3.10 (Linux: `/home/thorsten/miniconda3/envs/narratrix`, Windows: `C:\Users\User\anaconda3\envs\narratrix\python.exe`).
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
- **String-Zentralisierung (Lokalisierung):** Alle spielerseitigen System- und Feedback-Texte innerhalb von `engine/` müssen zentral in `engine/strings.py` (`Texts`, inkl. `Texts.direction_name` und `Texts.direction_from`) gepflegt werden – keine hartcodierten deutschen UI-/Ausgabestrings in Handlern oder Systemmodulen.
- **Behälter-Physik & Rekursive Erreichbarkeit:** Gewichts- und Waagenberechnungen müssen stets verschachtelte Behälterinhalte über `CommonHandler.get_contained_weight()` bzw. `CommonHandler.get_total_weight()` einbeziehen. Beim Ablegen in Behälter (`put`) gelten Selbst-Einfüge-Schutz, Oberflächen-Restriktionen (keine losen Items auf Flüssigkeiten) sowie `max_weight`/`capacity`. Die Erreichbarkeit (`engine/access.py`) prüft rekursiv die gesamte Eltern-Behälterkette (`_root_entity_and_location`).
- **Verzweigende Quests & State-Trees:** Nicht-lineare Quests nutzen `transitions`, benannte `outcomes`, `exclusive_with` und Stage-Historie (`visited_stage`). Komplexe Bedingungen in `EventManager` werden über rekursive `all`/`any`-Bäume abgebildet und statisch über `validate_quest_state_graph(config)` in `engine/analysis.py` auf unerreichbare Stages, Endlosschleifen und asymmetrische Exklusivitäten geprüft.
- **Generalisierung statt Ad-hoc-Mechaniken:** Rätselmechaniken und Objektzustände dürfen niemals als engstirnige Spezial-Flags (wie `spring_loaded` oder `OPEN_SPRING_LOADED`) in die Core-Engine aufgenommen werden. Spezifisches Verhalten wird strikt deklarativ über generische Datenattribute (z. B. `locked_msg` auf `ObjectData` für individuelle Verriegelungstexte) oder über das Event-System abgebildet.
- **Zweiseitige Verbindungstüren (Two-Way Doors):** Türen mit `linked_exit`, die zwei Räume verbinden, müssen aus beiden Räumen symmetrisch erreichbar, auflösbar (`Resolver`), bewegungsrelevant (`MovementHandler`), schallrelevant (`AcousticSystem`/`Listen`) und pfadfindungsfähig (`Pathfinder`) sein – selbst wenn die Entität physisch nur im Ursprungsraum definiert ist.
- **Modulare Spielpakete (`data/modules/`):** Eigenständige Kampagnen und Sandboxes liegen unter `data/modules/<id>/` mit `module.py` (`MODULE_CONFIG`), eigenem `asset_dir`, deklarativem `theme` und optionalem `common_module` (`None` für isolierte Module wie `test_lab`). `StoryLoader` darf keinen globalen Common-Layer in fremde Module leaken, und `AssetLoader` wechselt beim Kapitel-/Modulwechsel auf das jeweilige `asset_dir`.
- **Episoden-Verkettung & State-Transfer:** Bei `load_chapter`-Übergängen überträgt `GameState.export_transfer_state()` / `apply_transfer_state()` Inventarobjekte, `knowledge`, `time` und `stability`. Kapitel-spezifische Wissensflags (z. B. `ep1_quest_started`, `ep2_quest_started`) müssen eindeutig pro Episode benannt sein, damit sie nicht in Folgekapitel leaken; bereits im Zielkapitel definierte Objekte behalten beim Transfer ihre aktuellen Metadaten/Aliase.
- **Remote-Comms-NPCs (`remote_comms`):** Stationsweite Funk-/KI-Charaktere werden deklarativ über `"remote_comms": True` und `location: LOC_VOID` in `NPCData` abgebildet (keine NPC-ID-Sonderfälle in der Engine). Sie bleiben über `Resolver.find_mentioned_npc` und `DialogueHandler.talk` global ansprechbar, erscheinen nicht in physischen Raumlisten (`present_npcs`) und werden in `build_world_context()` auf `game.location` geerdet.

### 3. Parser & Befehlsauflösung
- Alle Himmelsrichtungs-Kürzel (`n`, `s`, `w`, `o`, `u`, `d`) sowie Bindestrich-Kommandos müssen sowohl im Spacy-Parser als auch im regelbasierten Fallback-Parser fehlerfrei verarbeitet werden.
- **Resolver-Invariante:** Zielauflösungen mit `FILTER_ROOM` und `FILTER_RECURSIVE` müssen stets sowohl Raumobjekte als auch anwesende NPCs (`game.npcs`) erfassen.
- Kletter-Befehle müssen gängige Präpositionen (`auf`, `in`, `runter`, `hoch`) tolerant behandeln.

### 4. Qualitätssicherung & Testsuite
- **Automatischer Git Pre-Commit Hook:** In `.git/hooks/pre-commit` ist ein automatischer Test-Gatekeeper aktiv. Commits werden nur zugelassen, wenn alle Unittests fehlerfrei durchlaufen.
- **Test-Architektur:**
  - `tests/test_engine.py`: Verträge, Quests, Save/Load, Spacy-Parser und AST-Code-Hygiene.
  - `tests/test_systems.py`: Isolierte Modultests für regelbasierten Parser, Akustik/Schalldämpfung, KI-Behavior-Trees, LLM-Grounding, Quest-State-Trees und Physik-Stresstests.
- **Kapitel-Testabdeckung:** Jedes neu angelegte Kapitel muss in `test_chapters_validate_and_intro_is_loaded` aufgenommen und mit einem eigenen deterministischen End-to-End-Testlauf in `tests/test_engine.py` auf Lösbarkeit abgesichert werden.
- **Verkettete Kampagnen- & Modul-Tests:** Zusammenhängende Episodenfolgen (z. B. `ep1 → ep2 → ep3`) müssen zusätzlich durch einen verketteten Integrationstest (`export_transfer_state` / `apply_transfer_state`) abgesichert werden; Tests dürfen nach dem Laden eines `common`-Layers nicht implizit annehmen, dass `game.npcs[0]` ein physisch platzierter Raum-NPC ist (immer gezielt per `id` selektieren).
- **Headless-GUI-Tests:** GUI-Komponenten, Renderer und Interaktionsmechaniken (z. B. Textselektion) müssen in Unittests headless mittels `os.environ["SDL_VIDEODRIVER"] = "dummy"` automatisiert testbar sein.
- Manueller Testaufruf zur Verifikation:
  - Linux: `/home/thorsten/miniconda3/envs/narratrix/bin/python -m unittest discover tests`
  - Windows (PowerShell): `& "C:\Users\User\anaconda3\envs\narratrix\python.exe" -m unittest discover tests`

### 5. LLM-Grounding & Zentrale Sprachsteuerung
- **Englische System-Prompts:** Interne LLM-Anweisungen und Fakten-Grounding in `engine/systems/llm_grounding.py` werden strikt auf **Englisch** verfasst, um die Instruction-Adherence lokaler Sprachmodelle zu maximieren. Sie gehören **nicht** in `engine/strings.py`.
- **Zentrale Zielsprache:** Die Antwortsprache der NPCs wird zentral über `game.config["language"]` (gespeist aus `data/config.json` -> `game.language`, z. B. `"de"` oder `"en"`) gesteuert und im System-Prompt als Zielsprache injiziert.
- **Guardrails & Fallback:** Dynamische LLM-Dialoge (`LLM_AUTO_REPLY` oder Freitext-Fragen in `DialogueSystem`) durchlaufen `build_prompts()`, `sanitize_reply()` und die Fakten-/Zahlen-Invariante `preserves_core_facts()`. Bei Verbindungsfehlern, Halluzinationen oder verletzten Zahlenfakten greift immer ein deterministischer In-Character-Fallback.
- **Guardrail-sichere KI-Personas:** Für In-Game-Computer-/KI-Charaktere (wie `C.O.R.E.`) sollte `personality` als Bordrechner- oder Telemetrie-Interface beschrieben werden, damit lokale Modelle keine Meta-Floskeln wie „Als KI ...“ / „As an AI ...“ erzeugen, die vom `sanitize_reply()`-Filter blockiert werden.

### 6. GUI-Architektur, Theming & Cross-Platform
- **Modulares Theming:** Modul- und kapitalspezifische Farbpaletten und UI-Designs werden zentral in `engine/theme.py` gekapselt (Presets wie `lab`, `deep_zero`, `habitat` sowie dynamische Hex/RGB-Werte) und im Renderer angewendet.
- **Adaptive Ambiance & Sensorik:** Das obere Ambiance-Deck passt seine Höhe dynamisch an (keine starren Platzhalter bei fehlenden Grafiken). Es bündelt relevante sensorische Raum- und Statusinformationen (Akustik-Radar `🔊 AKUSTIK`, Exits, NPC-Präsenz, Quest-Ziele).
- **Robuste Zwischenablage:** Textkopieren aus der GUI muss plattformübergreifend garantiert sein. Es nutzt native OS-Tools mit Timeouts (Windows: `clip.exe`; Linux: `wl-copy`, `xclip -selection clipboard`, `xsel`) mit Fallback auf `tkinter`, um Deadlocks und blockierende Pipes unter Linux/Windows zu verhindern.
