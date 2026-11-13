from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, TypedDict

try:
    import requests
except ImportError:  # LLM support is optional.
    requests = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class LLMProviderSpec(TypedDict, total=False):
    url: str
    model: str
    api_key: str


class LLMBridge:
    DEFAULT_URL: str = "http://127.0.0.1:11434/v1/chat/completions"
    DEFAULT_MODEL: str = "gemma4:12b"
    CONNECT_TIMEOUT: float = 2.0
    TIMEOUT: float = 30.0
    COOLDOWN_SECONDS: float = 30.0
    _unreachable_until: dict[str, float] = {}

    @classmethod
    def reset_cooldowns(cls) -> None:
        """Clear cached provider failure cooldowns."""
        cls._unreachable_until.clear()

    @staticmethod
    def get_api_url(configured_url: str | None = None) -> str:
        return configured_url or os.getenv("NARRATRIX_LLM_URL", LLMBridge.DEFAULT_URL)

    @staticmethod
    def _resolve_api_key(
        configured_key: str | None = None,
        env_var: str | None = None,
    ) -> str:
        if configured_key and configured_key.strip():
            return configured_key.strip()
        if env_var:
            env_val = os.getenv(env_var, "").strip()
            if env_val:
                return env_val
        return ""

    @classmethod
    def resolve_providers(
        cls,
        *,
        api_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        fallback_url: str | None = None,
        fallback_model: str | None = None,
        fallback_api_key: str | None = None,
        providers: list[dict[str, Any]] | None = None,
    ) -> list[LLMProviderSpec]:
        """Build ordered OpenAI-compatible provider chain (primary -> fallbacks)."""
        ordered: list[LLMProviderSpec] = []

        if providers:
            for entry in providers:
                if not isinstance(entry, dict):
                    continue
                url = str(entry.get("url") or "").strip()
                if not url:
                    continue
                spec: LLMProviderSpec = {
                    "url": url,
                    "model": str(entry.get("model") or cls.DEFAULT_MODEL).strip(),
                }
                key = cls._resolve_api_key(
                    entry.get("api_key"), entry.get("api_key_env")
                )
                if key:
                    spec["api_key"] = key
                ordered.append(spec)
        else:
            primary_url = str(cls.get_api_url(api_url) or "").strip()
            if primary_url:
                primary_spec: LLMProviderSpec = {
                    "url": primary_url,
                    "model": str(
                        model or os.getenv("NARRATRIX_LLM_MODEL", cls.DEFAULT_MODEL)
                    ).strip(),
                }
                primary_key = cls._resolve_api_key(api_key, "NARRATRIX_LLM_API_KEY")
                if primary_key:
                    primary_spec["api_key"] = primary_key
                ordered.append(primary_spec)

        fb_url = str(
            fallback_url or os.getenv("NARRATRIX_LLM_FALLBACK_URL", "")
        ).strip()
        if fb_url:
            fb_model = str(
                fallback_model
                or os.getenv("NARRATRIX_LLM_FALLBACK_MODEL", cls.DEFAULT_MODEL)
            ).strip()
            fb_spec: LLMProviderSpec = {"url": fb_url, "model": fb_model}
            fb_key = cls._resolve_api_key(
                fallback_api_key, "NARRATRIX_LLM_FALLBACK_KEY"
            ) or cls._resolve_api_key(None, "NARRATRIX_LLM_FALLBACK_API_KEY")
            if fb_key:
                fb_spec["api_key"] = fb_key
            ordered.append(fb_spec)

        deduped: list[LLMProviderSpec] = []
        seen: set[tuple[str, str, str]] = set()
        for spec in ordered:
            marker = (
                spec.get("url", ""),
                spec.get("model", ""),
                spec.get("api_key", ""),
            )
            if marker[0] and marker not in seen:
                seen.add(marker)
                deduped.append(spec)
        return deduped

    @classmethod
    def _post_completion(
        cls,
        provider: LLMProviderSpec,
        messages: list[dict[str, str]],
    ) -> str | None:
        if requests is None:
            return None
        url = provider["url"]
        headers: dict[str, str] = {"Content-Type": "application/json"}
        api_key = provider.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload: dict[str, Any] = {
            "model": provider.get("model", cls.DEFAULT_MODEL),
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
        }
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=(cls.CONNECT_TIMEOUT, cls.TIMEOUT),
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                cls._unreachable_until.pop(url, None)
                return str(choices[0]["message"]["content"]).strip().strip('"')
        except requests.exceptions.ConnectionError:
            cls._unreachable_until[url] = time.monotonic() + cls.COOLDOWN_SECONDS
        except requests.exceptions.Timeout:
            logger.warning("LLM Timeout (%s) - Server antwortet zu langsam.", url)
            cls._unreachable_until[url] = time.monotonic() + cls.COOLDOWN_SECONDS
        except (ValueError, KeyError, requests.RequestException) as exc:
            logger.warning("LLM Fehler (%s): %s", url, exc)
            cls._unreachable_until[url] = time.monotonic() + cls.COOLDOWN_SECONDS
        return None

    @staticmethod
    def call(
        system_prompt: str,
        user_message: str,
        api_url: str | None = None,
        model: str | None = None,
        history: list[dict[str, str]] | None = None,
        *,
        api_key: str | None = None,
        fallback_url: str | None = None,
        fallback_model: str | None = None,
        fallback_api_key: str | None = None,
        providers: list[dict[str, Any]] | None = None,
        response_filter: Callable[[str], str | None] | None = None,
    ) -> str | None:
        if requests is None:
            return None
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if history:
            for turn in history:
                role = turn.get("role")
                content = turn.get("content", "")
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        chain = LLMBridge.resolve_providers(
            api_url=api_url,
            model=model,
            api_key=api_key,
            fallback_url=fallback_url,
            fallback_model=fallback_model,
            fallback_api_key=fallback_api_key,
            providers=providers,
        )
        if not chain:
            return None

        now = time.monotonic()
        active_chain = chain
        if len(chain) > 1:
            healthy = [
                spec
                for spec in chain
                if LLMBridge._unreachable_until.get(spec["url"], 0.0) <= now
            ]
            if healthy:
                active_chain = healthy

        for spec in active_chain:
            raw = LLMBridge._post_completion(spec, messages)
            if not raw:
                continue
            if response_filter is not None:
                filtered = response_filter(raw)
                if not filtered:
                    continue
                return filtered
            return raw
        return None

    @staticmethod
    def check_availability(
        api_url: str | None = None,
        *,
        fallback_url: str | None = None,
        providers: list[dict[str, Any]] | None = None,
    ) -> bool:
        if requests is None:
            return False
        chain = LLMBridge.resolve_providers(
            api_url=api_url,
            fallback_url=fallback_url,
            providers=providers,
        )
        for spec in chain:
            url = spec["url"]
            headers: dict[str, str] = {}
            if spec.get("api_key"):
                headers["Authorization"] = f"Bearer {spec['api_key']}"
            try:
                response = requests.get(
                    url.replace("/chat/completions", "/models"),
                    headers=headers,
                    timeout=1,
                )
                if response.ok:
                    return True
            except requests.RequestException:
                continue
        return False
