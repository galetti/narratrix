# data/modules/deep_zero/chapters/ep3_reactor_core/items.py
from __future__ import annotations

from engine.constants import (
    ATTR_ALIASES,
    ATTR_DESC,
    ATTR_ID,
    ATTR_NAME,
    ATTR_WEIGHT,
    LOC_INVENTORY,
    LOC_VOID,
    TYPE_CONTAINER,
    TYPE_FIXTURE,
    TYPE_ITEM,
)
from engine.schema import ObjectData, RecipeData

ITEMS: dict[str, ObjectData] = {
    # --- STARTING INVENTORY (Übernommen aus Episode 1 & 2 / Standalone-Defaults) ---
    "tool_omni": {
        ATTR_ID: "tool_omni",
        ATTR_NAME: "Omni-Tool v1",
        ATTR_DESC: "Das Standard-Wartungswerkzeug von Dr. Sato mit Frequenzsensor und Multi-Interface.",
        ATTR_ALIASES: ["omni", "omnitool", "omni-tool", "werkzeug"],
        "location": LOC_INVENTORY,
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.5,
    },
    "core_access_chip": {
        ATTR_ID: "core_access_chip",
        ATTR_NAME: "Reaktorkern-Zugangschip",
        ATTR_DESC: "Der Autorisierungschip von Dr. Elena Vance für den Reaktor-Leitstand und die Herzkammer.",
        ATTR_ALIASES: ["chip", "zugangschip", "reaktorchip", "freigabechip"],
        "location": LOC_INVENTORY,
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.1,
    },
    "parents_photo": {
        ATTR_ID: "parents_photo",
        ATTR_NAME: "Foto der Eltern",
        ATTR_DESC: "Ein kleines, etwas abgegriffenes Foto aus alten Tagen auf der Erde.",
        ATTR_ALIASES: ["foto", "bild", "eltern"],
        "location": LOC_INVENTORY,
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.0,
    },
    # --- REAKTOR-ZUGANGSBRÜCKE ---
    "security_gate": {
        ATTR_ID: "security_gate",
        ATTR_NAME: "Sicherheitsgitter",
        ATTR_DESC: "Ein schweres Scherengitter mit Magnetverriegelung nach Norden zum Kühllager. Ein Chip-Leser blinkt daneben.",
        ATTR_ALIASES: ["gitter", "sicherheitsgitter", "schranke", "tor"],
        "location": "reactor_bridge",
        "type": TYPE_CONTAINER,
        "linked_exit": "north",
        "is_open": False,
        "is_locked": True,
        "key_id": "core_access_chip",
        "locked_msg": "Das Sicherheitsgitter ist verriegelt. Öffne es mit deinem Reaktorkern-Zugangschip.",
    },
    "radiation_blast_door": {
        ATTR_ID: "radiation_blast_door",
        ATTR_NAME: "Strahlenschutz-Schott",
        ATTR_DESC: "Ein zwei Meter dickes Bleischott zum Reaktorraum. Gelbe Warnstreifen mahnen zur Vorsicht.",
        ATTR_ALIASES: ["schott", "strahlenschutz-schott", "tür", "bleischott"],
        "location": "reactor_bridge",
        "type": TYPE_FIXTURE,
        "linked_exit": "south",
        "is_open": True,
    },
    # --- REAKTOR-LEITSTAND ---
    "control_console": {
        ATTR_ID: "control_console",
        ATTR_NAME: "Steuerkonsole",
        ATTR_DESC: (
            "Das zentrale Bedienpult für das Magnetische Containment. "
            "Die Phasenverschiebung des Felds blinkt rot im kritischen Bereich."
        ),
        ATTR_ALIASES: ["konsole", "steuerkonsole", "pult", "terminal", "hauptpult"],
        "location": "control_room",
        "type": TYPE_FIXTURE,
    },
    "storage_locker": {
        ATTR_ID: "storage_locker",
        ATTR_NAME: "Wandfach",
        ATTR_DESC: "Ein verriegelbares Notfall-Ausrüstungsfach an der Wand des Leitstands.",
        ATTR_ALIASES: ["fach", "wandfach", "schrank", "spind", "lagerfach"],
        "location": "control_room",
        "type": TYPE_CONTAINER,
        "is_open": True,
    },
    "insulating_gloves": {
        ATTR_ID: "insulating_gloves",
        ATTR_NAME: "Isolierhandschuhe",
        ATTR_DESC: "Schwere Thermohandschuhe zum sicheren Ankuppeln kryogener Behälter.",
        ATTR_ALIASES: ["handschuhe", "isolierhandschuhe", "thermohandschuhe"],
        "location": "storage_locker",
        "type": TYPE_ITEM,
        "is_tool": True,
        ATTR_WEIGHT: 0.4,
    },
    # --- KRYO-KÜHLLAGER ---
    "crane": {
        ATTR_ID: "crane",
        ATTR_NAME: "Verladekran",
        ATTR_DESC: "Ein automatischer Deckenkran zum Bewegen tonnenschwerer Brennstäbe.",
        ATTR_ALIASES: ["kran", "verladekran", "deckenkran"],
        "location": "coolant_depot",
        "type": TYPE_FIXTURE,
    },
    "cryo_canister": {
        ATTR_ID: "cryo_canister",
        ATTR_NAME: "Kryo-Kühlkanister",
        ATTR_DESC: "Ein isolierter Druckbehälter gefüllt mit tiefgekühltem flüssigem Helium.",
        ATTR_ALIASES: ["kanister", "kühlkanister", "kryo-kanister", "kühlmittel", "behälter"],
        "location": "coolant_depot",
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 3.0,
    },
    # --- REAKTORKAMMER (CONTAINMENT) ---
    "dark_matter_core": {
        ATTR_ID: "dark_matter_core",
        ATTR_NAME: "Dunkle-Materie-Kern",
        ATTR_DESC: (
            "Die primäre Energiequelle von Deep Zero. Ein schwebender Sphäroid, "
            "umhüllt von violetten Plasmaentladungen und enormem Hitzeflimmern."
        ),
        ATTR_ALIASES: ["kern", "reaktorkern", "dunkle-materie-kern", "reaktor", "sphäroid"],
        "location": "reactor_chamber",
        "type": TYPE_FIXTURE,
        "level": 0,
    },
    "containment_generator": {
        ATTR_ID: "containment_generator",
        ATTR_NAME: "Eindämmungs-Generator",
        ATTR_DESC: "Massive Magnetspulen im Fundament der Kammer, die das Magnetfeld aufrechterhalten.",
        ATTR_ALIASES: ["generator", "feldgenerator", "eindämmungs-generator", "spulen"],
        "location": "reactor_chamber",
        "type": TYPE_FIXTURE,
        "level": 0,
    },
    "coolant_gantry_ladder": {
        ATTR_ID: "coolant_gantry_ladder",
        ATTR_NAME: "Injektor-Leiter",
        ATTR_DESC: "Eine senkrechte Steigleiter aus Karbonstreben, die hinauf zur Injektorbühne auf Ebene 2 führt.",
        ATTR_ALIASES: ["leiter", "injektor-leiter", "steigleiter", "sprossen"],
        "location": "reactor_chamber",
        "type": TYPE_FIXTURE,
        "climbable": True,
        "target_elevation": 2,
    },
    "coolant_manifold": {
        ATTR_ID: "coolant_manifold",
        ATTR_NAME: "Kühlmittel-Verteiler",
        ATTR_DESC: (
            "Ein verzweigtes Ventil- und Injektorsystem auf Ebene 2 direkt über dem Reaktorkern. "
            "Hier kann der Notkühlkanister mit Isolierhandschuhen eingekoppelt werden."
        ),
        ATTR_ALIASES: ["verteiler", "injektor", "kühlmittel-verteiler", "anschluss", "flansch"],
        "location": "reactor_chamber",
        "type": TYPE_FIXTURE,
        "level": 2,
    },
    # --- BELOHNUNG & ENDE ---
    "master_station_key": {
        ATTR_ID: "master_station_key",
        ATTR_NAME: "Stations-Generalschlüssel",
        ATTR_DESC: "Der goldene Generalschlüssel für alle Kommandobereiche von Deep Zero.",
        ATTR_ALIASES: ["generalschlüssel", "schlüssel", "stationsschlüssel"],
        "location": LOC_VOID,
        "type": TYPE_ITEM,
        ATTR_WEIGHT: 0.2,
    },
}

COMBINATIONS: list[RecipeData] = [
    {
        "verb": "use",
        "items": ["cryo_canister", "coolant_manifold"],
        "tools": ["insulating_gloves"],
        "condition": {"type": "knowledge", "value": "core_cooled", "not": True},
        "message": (
            "Geschützt durch die Isolierhandschuhe kuppelst du den Kryo-Kühlkanister mit einem satten Zischen an den Injektor-Flansch auf Ebene 2 an. "
            "Flüssiges Helium schießt mit donnerndem Rauschen in die Überhitzungskanäle des Reaktors! "
            "Die violetten Plasmaentladungen kühlen spürbar auf sichere Betriebstemperaturen ab."
        ),
        "effects": [
            {"type": "trigger_event", "id": "event_core_cooled"},
        ],
    },
    {
        "verb": "use",
        "items": ["tool_omni", "control_console"],
        "condition": {"type": "knowledge", "value": "core_stabilized", "not": True},
        "message": (
            "Du schließt das Omni-Tool an den Diagnoseport der Steuerkonsole an. "
            "Mit präzisen Phasenanpassungen stimmst du die Magnetfeldresonanz ab. "
            "Der Dunkle-Materie-Kern pulsiert in vollkommener Harmonie – Deep Zero ist gerettet!"
        ),
        "effects": [
            {"type": "trigger_event", "id": "event_core_stabilized"},
        ],
    },
]
