import os

try:
    import requests
except ImportError:  # LLM support is optional.
    requests = None


class LLMBridge:
    DEFAULT_URL = "http://localhost:1234/v1/chat/completions"
    DEFAULT_MODEL = "local-model"
    TIMEOUT = 5

    @staticmethod
    def get_api_url(configured_url=None):
        return configured_url or os.getenv("NARRATRIX_LLM_URL", LLMBridge.DEFAULT_URL)

    @staticmethod
    def call(system_prompt, user_message, api_url=None, model=None):
        if requests is None:
            return None
        url = LLMBridge.get_api_url(api_url)
        payload = {
            "model": model or os.getenv("NARRATRIX_LLM_MODEL", LLMBridge.DEFAULT_MODEL),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.7,
            "max_tokens": 100,
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
                return choices[0]["message"]["content"].strip().strip('"')
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            print("[LLM] Timeout - Server antwortet zu langsam.")
        except (ValueError, KeyError, requests.RequestException) as exc:
            print(f"[LLM] Fehler: {exc}")
        return None

    @staticmethod
    def check_availability(api_url=None):
        if requests is None:
            return False
        url = LLMBridge.get_api_url(api_url)
        try:
            response = requests.get(
                url.replace("/chat/completions", "/models"),
                timeout=1,
            )
            return response.ok
        except requests.RequestException:
            return False
