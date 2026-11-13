from __future__ import annotations

import logging
import os
from typing import Any

try:
    import requests
except ImportError:  # LLM support is optional.
    requests = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class LLMBridge:
    DEFAULT_URL: str = "http://127.0.0.1:11434/v1/chat/completions"
    DEFAULT_MODEL: str = "gemma4:12b"
    TIMEOUT: int = 30

    @staticmethod
    def get_api_url(configured_url: str | None = None) -> str:
        return configured_url or os.getenv("NARRATRIX_LLM_URL", LLMBridge.DEFAULT_URL)

    @staticmethod
    def call(
        system_prompt: str,
        user_message: str,
        api_url: str | None = None,
        model: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str | None:
        if requests is None:
            return None
        url = LLMBridge.get_api_url(api_url)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            for turn in history:
                role = turn.get("role")
                content = turn.get("content", "")
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})
        payload: dict[str, Any] = {
            "model": model or os.getenv("NARRATRIX_LLM_MODEL", LLMBridge.DEFAULT_MODEL),
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=LLMBridge.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return str(choices[0]["message"]["content"]).strip().strip('"')
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            logger.warning("LLM Timeout - Server antwortet zu langsam.")
        except (ValueError, KeyError, requests.RequestException) as exc:
            logger.warning("LLM Fehler: %s", exc)
        return None

    @staticmethod
    def check_availability(api_url: str | None = None) -> bool:
        if requests is None:
            return False
        url = LLMBridge.get_api_url(api_url)
        try:
            response = requests.get(
                url.replace("/chat/completions", "/models"),
                timeout=1,
            )
            return bool(response.ok)
        except requests.RequestException:
            return False
