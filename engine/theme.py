# narratrix/engine/theme.py
from __future__ import annotations

ColorTuple = tuple[int, int, int]

# Farben
COLOR_BG: ColorTuple = (10, 10, 15)
COLOR_UI_BORDER: ColorTuple = (40, 40, 60)
COLOR_TEXT: ColorTuple = (200, 200, 200)
COLOR_ACCENT: ColorTuple = (0, 255, 136)
COLOR_ALERT: ColorTuple = (255, 50, 50)
COLOR_INPUT: ColorTuple = (255, 255, 255)
COLOR_LOADING: ColorTuple = (255, 200, 0)
COLOR_USER_ECHO: ColorTuple = (150, 150, 150)
COLOR_DIALOGUE_BORDER: ColorTuple = (0, 150, 255)
COLOR_INFO: ColorTuple = (180, 180, 180)
COLOR_GAME_OVER_BG: ColorTuple = (50, 10, 10)
COLOR_GAME_OVER_TEXT: ColorTuple = (255, 255, 255)

# Schriftgrößen
FONT_SIZE_LOG: int = 18
FONT_SIZE_HEADER: int = 32
FONT_SIZE_GAME_OVER: int = 64

# Layout
SCENE_HEIGHT_RATIO: float = 0.4
INPUT_HEIGHT: int = 50
PADDING: int = 10
CURSOR_BLINK_SPEED: int = 15
SCROLL_SPEED_MOUSE: int = 40
SCROLL_SPEED_KEY: int = 200
