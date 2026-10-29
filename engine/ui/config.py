from __future__ import annotations

import json
import logging
from pathlib import Path
import subprocess
from typing import Any

try:
    import pygame
    import pygame.scrap
except ImportError:  # Allow headless imports without pygame installed.
    pygame = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def load_system_config(config_path: Path | None = None) -> dict[str, dict[str, Any]]:
    default_conf: dict[str, dict[str, Any]] = {
        "game": {
            "start_chapter": "data.chapters.ep1_deep_zero.config",
            "title": "Narratrix",
            "language": "de",
        },
        "system": {
            "resolution_width": 1024,
            "resolution_height": 768,
            "parser_mode": "SPACY",
            "llm_enabled": False,
            "llm_url": "http://localhost:1234/v1/chat/completions",
        },
    }

    target_path = config_path or (PROJECT_ROOT / "data" / "config.json")
    if target_path.exists():
        try:
            with target_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data.get("game"), dict):
                default_conf["game"].update(data["game"])
            if isinstance(data.get("system"), dict):
                default_conf["system"].update(data["system"])
            logger.info("Config geladen von: %s", target_path)
            return default_conf
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Konnte %s nicht lesen: %s", target_path, exc)
    else:
        logger.info("Keine Config gefunden unter %s, nutze Defaults.", target_path)

    return default_conf


def copy_to_clipboard(text_dump: str) -> bool:
    """Kopiert Text in die Zwischenablage mit X11-Fallbacks (xclip/xsel)."""
    payload = text_dump.encode("utf-8")
    if pygame is not None:
        try:
            pygame.scrap.put(pygame.SCRAP_TEXT, payload)
            return True
        except pygame.error:
            pass

    for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "-b", "-i"]):
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            process.communicate(input=payload)
            if process.returncode == 0:
                return True
        except OSError:
            continue

    logger.warning(
        "Zwischenablage nicht verfügbar (bitte unter Linux xclip oder xsel installieren)."
    )
    return False
