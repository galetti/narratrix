from __future__ import annotations

from typing import Any

MODULE_CONFIG: dict[str, Any] = {
    "id": "test_lab",
    "title": "Testlabor (Mechanik-Sandbox)",
    "description": "Modulare Testumgebung für Physik-, Akustik-, Kletter-, KI- und Dialogmechaniken.",
    "start_chapter": "data.modules.test_lab.chapters.sandbox.config",
    "chapters": [
        "data.modules.test_lab.chapters.sandbox.config",
    ],
    "theme": "lab",
    "common_module": None,
    "asset_dir": "data/modules/test_lab/assets/images",
}
