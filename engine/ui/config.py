from __future__ import annotations

import json
import logging
from pathlib import Path
import subprocess
import sys
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
            "default_module": "deep_zero",
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
    """Kopiert Text zuverlässig in die Zwischenablage (Windows clip.exe, Linux Wayland/X11, Tkinter, Pygame)."""
    if not text_dump:
        return True

    # 1. Native Windows-Methode über clip.exe
    if sys.platform == "win32":
        try:
            proc = subprocess.run(
                ["clip"],
                input=text_dump,
                text=True,
                timeout=2,
                capture_output=True,
                check=False,
            )
            if proc.returncode == 0:
                return True
        except (OSError, subprocess.SubprocessError):
            pass

    # 2. Native Linux-Tools (Wayland wl-copy, X11 xclip, xsel mit kurzem Timeout gegen Blockieren)
    if sys.platform.startswith("linux"):
        payload = text_dump.encode("utf-8")
        for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-b", "-i"]):
            try:
                proc = subprocess.run(
                    cmd,
                    input=payload,
                    timeout=1,
                    capture_output=True,
                    check=False,
                )
                if proc.returncode == 0:
                    return True
            except (OSError, subprocess.SubprocessError):
                continue

    # 3. Standard-Bibliothek Tkinter (plattformunabhängig für Linux & Windows)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text_dump)
        root.update()
        root.destroy()
        return True
    except Exception:
        pass

    # 4. Pygame Scrap Fallback
    if pygame is not None:
        try:
            if not pygame.scrap.get_init():
                pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, text_dump.encode("utf-8"))
            return True
        except pygame.error:
            pass

    logger.warning("Zwischenablage konnte nicht beschrieben werden.")
    return False
