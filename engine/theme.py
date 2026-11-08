# narratrix/engine/theme.py
from __future__ import annotations

import copy
from typing import Any

ColorTuple = tuple[int, int, int]

DEFAULT_THEME: dict[str, Any] = {
    "name": "default",
    "color_bg": (10, 12, 18),
    "color_panel": (16, 20, 28),
    "color_ui_border": (40, 50, 70),
    "color_text": (210, 215, 225),
    "color_text_dim": (130, 140, 155),
    "color_accent": (0, 255, 136),
    "color_accent_dim": (0, 160, 90),
    "color_alert": (255, 60, 60),
    "color_input": (255, 255, 255),
    "color_loading": (255, 200, 0),
    "color_user_echo": (150, 160, 180),
    "color_dialogue_border": (0, 160, 255),
    "color_info": (170, 185, 210),
    "color_selection": (35, 75, 130),
    "color_game_over_bg": (50, 10, 10),
    "color_game_over_text": (255, 255, 255),
    "font_size_log": 18,
    "font_size_header": 28,
    "font_size_game_over": 64,
    "scene_height_ratio": 0.28,
    "input_height": 50,
    "padding": 12,
    "cursor_blink_speed": 15,
    "scroll_speed_mouse": 40,
    "scroll_speed_key": 200,
}

THEME_PRESETS: dict[str, dict[str, Any]] = {
    "default": copy.deepcopy(DEFAULT_THEME),
    "lab": {
        **DEFAULT_THEME,
        "name": "lab",
        "color_bg": (14, 18, 26),
        "color_panel": (20, 26, 38),
        "color_ui_border": (50, 75, 110),
        "color_text": (220, 230, 240),
        "color_text_dim": (140, 155, 175),
        "color_accent": (0, 215, 255),
        "color_accent_dim": (0, 140, 180),
        "color_dialogue_border": (0, 190, 255),
        "color_selection": (30, 80, 140),
    },
    "deep_zero": {
        **DEFAULT_THEME,
        "name": "deep_zero",
        "color_bg": (10, 14, 20),
        "color_panel": (18, 22, 30),
        "color_ui_border": (50, 65, 85),
        "color_text": (205, 215, 225),
        "color_text_dim": (130, 140, 150),
        "color_accent": (255, 170, 50),
        "color_accent_dim": (180, 110, 30),
        "color_dialogue_border": (255, 180, 50),
        "color_selection": (75, 55, 30),
    },
    "habitat": {
        **DEFAULT_THEME,
        "name": "habitat",
        "color_bg": (12, 18, 15),
        "color_panel": (18, 26, 22),
        "color_ui_border": (45, 75, 60),
        "color_text": (210, 230, 215),
        "color_text_dim": (135, 160, 145),
        "color_accent": (60, 240, 150),
        "color_accent_dim": (40, 160, 100),
        "color_dialogue_border": (60, 220, 180),
        "color_selection": (30, 75, 55),
    },
    "reactor": {
        **DEFAULT_THEME,
        "name": "reactor",
        "color_bg": (18, 12, 12),
        "color_panel": (28, 18, 18),
        "color_ui_border": (75, 45, 45),
        "color_text": (235, 215, 215),
        "color_text_dim": (160, 135, 135),
        "color_accent": (255, 130, 20),
        "color_accent_dim": (180, 80, 10),
        "color_dialogue_border": (255, 100, 50),
        "color_selection": (85, 40, 25),
    },
}

# Module-Level Variablen für direkte Abwärtskompatibilität
COLOR_BG: ColorTuple = DEFAULT_THEME["color_bg"]
COLOR_PANEL_BG: ColorTuple = DEFAULT_THEME["color_panel"]
COLOR_UI_BORDER: ColorTuple = DEFAULT_THEME["color_ui_border"]
COLOR_TEXT: ColorTuple = DEFAULT_THEME["color_text"]
COLOR_TEXT_DIM: ColorTuple = DEFAULT_THEME["color_text_dim"]
COLOR_ACCENT: ColorTuple = DEFAULT_THEME["color_accent"]
COLOR_ACCENT_DIM: ColorTuple = DEFAULT_THEME["color_accent_dim"]
COLOR_ALERT: ColorTuple = DEFAULT_THEME["color_alert"]
COLOR_INPUT: ColorTuple = DEFAULT_THEME["color_input"]
COLOR_LOADING: ColorTuple = DEFAULT_THEME["color_loading"]
COLOR_USER_ECHO: ColorTuple = DEFAULT_THEME["color_user_echo"]
COLOR_DIALOGUE_BORDER: ColorTuple = DEFAULT_THEME["color_dialogue_border"]
COLOR_INFO: ColorTuple = DEFAULT_THEME["color_info"]
COLOR_SELECTION: ColorTuple = DEFAULT_THEME["color_selection"]
COLOR_GAME_OVER_BG: ColorTuple = DEFAULT_THEME["color_game_over_bg"]
COLOR_GAME_OVER_TEXT: ColorTuple = DEFAULT_THEME["color_game_over_text"]

FONT_SIZE_LOG: int = DEFAULT_THEME["font_size_log"]
FONT_SIZE_HEADER: int = DEFAULT_THEME["font_size_header"]
FONT_SIZE_GAME_OVER: int = DEFAULT_THEME["font_size_game_over"]

SCENE_HEIGHT_RATIO: float = DEFAULT_THEME["scene_height_ratio"]
INPUT_HEIGHT: int = DEFAULT_THEME["input_height"]
PADDING: int = DEFAULT_THEME["padding"]
CURSOR_BLINK_SPEED: int = DEFAULT_THEME["cursor_blink_speed"]
SCROLL_SPEED_MOUSE: int = DEFAULT_THEME["scroll_speed_mouse"]
SCROLL_SPEED_KEY: int = DEFAULT_THEME["scroll_speed_key"]

ACTIVE_THEME: dict[str, Any] = copy.deepcopy(DEFAULT_THEME)


def _parse_color(val: Any, default: ColorTuple) -> ColorTuple:
    if isinstance(val, (tuple, list)) and len(val) >= 3:
        return (int(val[0]), int(val[1]), int(val[2]))
    if isinstance(val, str) and val.startswith("#") and len(val) in (7, 4):
        if len(val) == 7:
            return (int(val[1:3], 16), int(val[3:5], 16), int(val[5:7], 16))
        return (int(val[1] * 2, 16), int(val[2] * 2, 16), int(val[3] * 2, 16))
    return default


def set_active_theme(custom: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """Lädt und aktiviert ein Theme (Preset-Name oder Custom-Dictionary)."""
    global COLOR_BG, COLOR_PANEL_BG, COLOR_UI_BORDER, COLOR_TEXT, COLOR_TEXT_DIM
    global COLOR_ACCENT, COLOR_ACCENT_DIM, COLOR_ALERT, COLOR_INPUT, COLOR_LOADING
    global COLOR_USER_ECHO, COLOR_DIALOGUE_BORDER, COLOR_INFO, COLOR_SELECTION
    global COLOR_GAME_OVER_BG, COLOR_GAME_OVER_TEXT
    global FONT_SIZE_LOG, FONT_SIZE_HEADER, FONT_SIZE_GAME_OVER
    global SCENE_HEIGHT_RATIO, INPUT_HEIGHT, PADDING, CURSOR_BLINK_SPEED
    global SCROLL_SPEED_MOUSE, SCROLL_SPEED_KEY, ACTIVE_THEME

    base: dict[str, Any]
    if isinstance(custom, str):
        base = copy.deepcopy(THEME_PRESETS.get(custom, DEFAULT_THEME))
    elif isinstance(custom, dict):
        preset_name = custom.get("preset") or custom.get("name")
        if isinstance(preset_name, str) and preset_name in THEME_PRESETS:
            base = copy.deepcopy(THEME_PRESETS[preset_name])
        else:
            base = copy.deepcopy(DEFAULT_THEME)

        for key, val in custom.items():
            if key in ("preset",):
                continue
            color_key = key if key.startswith("color_") else f"color_{key}"
            if color_key in base and isinstance(base[color_key], tuple):
                base[color_key] = _parse_color(val, base[color_key])
            elif key in base:
                base[key] = val
    else:
        base = copy.deepcopy(DEFAULT_THEME)

    ACTIVE_THEME = base

    COLOR_BG = base["color_bg"]
    COLOR_PANEL_BG = base["color_panel"]
    COLOR_UI_BORDER = base["color_ui_border"]
    COLOR_TEXT = base["color_text"]
    COLOR_TEXT_DIM = base["color_text_dim"]
    COLOR_ACCENT = base["color_accent"]
    COLOR_ACCENT_DIM = base["color_accent_dim"]
    COLOR_ALERT = base["color_alert"]
    COLOR_INPUT = base["color_input"]
    COLOR_LOADING = base["color_loading"]
    COLOR_USER_ECHO = base["color_user_echo"]
    COLOR_DIALOGUE_BORDER = base["color_dialogue_border"]
    COLOR_INFO = base["color_info"]
    COLOR_SELECTION = base["color_selection"]
    COLOR_GAME_OVER_BG = base["color_game_over_bg"]
    COLOR_GAME_OVER_TEXT = base["color_game_over_text"]

    FONT_SIZE_LOG = int(base["font_size_log"])
    FONT_SIZE_HEADER = int(base["font_size_header"])
    FONT_SIZE_GAME_OVER = int(base["font_size_game_over"])

    SCENE_HEIGHT_RATIO = float(base["scene_height_ratio"])
    INPUT_HEIGHT = int(base["input_height"])
    PADDING = int(base["padding"])
    CURSOR_BLINK_SPEED = int(base["cursor_blink_speed"])
    SCROLL_SPEED_MOUSE = int(base["scroll_speed_mouse"])
    SCROLL_SPEED_KEY = int(base["scroll_speed_key"])

    return ACTIVE_THEME
