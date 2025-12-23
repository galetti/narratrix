# Objekt-Zustände
STATE_NORMAL = "normal"
STATE_SABOTAGED = "sabotaged"
STATE_BROKEN = "broken"

# Objekt-Typen
TYPE_CONTAINER = "container"
TYPE_SURFACE = "surface"
TYPE_ITEM = "item"
TYPE_SCENERY = "scenery"

# Aggregatzustände
MATTER_SOLID = "solid"
MATTER_LIQUID = "liquid"
MATTER_GAS = "gas"

# Orte
LOC_INVENTORY = "inventory"
LOC_VOID = "void" # Aus dem Spiel entfernt

# Attribute
ATTR_AFFINITY = "affinity"
# ATTR_MOVABLE ist obsolet -> Logik prüft nun auf weight < inf
ATTR_WEIGHT = "weight" # NEU
ATTR_ALIASES = "aliases"
ATTR_DESC = "desc"
ATTR_ID = "id"
ATTR_NAME = "name"
ATTR_TEMP = "temp" 
ATTR_MATTER = "matter" 

# Dialog & AI
AI_CHANCE_MOVE_DEFAULT = 20
AI_CHANCE_STAY = 80

# Filter für Resolver
FILTER_ROOM = "room"
FILTER_INVENTORY = "inventory"
FILTER_RECURSIVE = "recursive_room"
