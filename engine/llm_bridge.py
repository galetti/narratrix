# narratrix_engine/engine/llm_bridge.py
import requests
import json
import os

class LLMBridge:
    """
    Verbindung zu einem lokalen LLM Server (z.B. LM Studio oder Ollama).
    Konfiguration erfolgt über Environment Variables.
    """
    
    # Defaults
    DEFAULT_URL = "http://localhost:1234/v1/chat/completions"
    DEFAULT_MODEL = "local-model" # Viele lokale Server ignorieren das Model-Feld eh
    TIMEOUT = 5 # Sekunden Timeout, damit das Spiel nicht hängt

    @staticmethod
    def get_api_url():
        return os.getenv("NARRATRIX_LLM_URL", LLMBridge.DEFAULT_URL)

    @staticmethod
    def call(system_prompt, user_message):
        """
        Sendet einen Request an das LLM.
        Gibt None zurück, wenn der Server nicht erreichbar ist.
        """
        url = LLMBridge.get_api_url()
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": LLMBridge.DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }

        try:
            # Kurzer Timeout für UX
            response = requests.post(url, headers=headers, json=payload, timeout=LLMBridge.TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0]['message']['content']
                    return content.strip().strip('"')
            else:
                print(f"[LLM] Fehler Status Code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            # Das ist normal, wenn kein Server läuft -> Silent Fail
            pass
        except requests.exceptions.Timeout:
            print("[LLM] Timeout - Server antwortet zu langsam.")
        except Exception as e:
            print(f"[LLM] Exception: {e}")

        return None

    @staticmethod
    def check_availability():
        """Prüft beim Start einmalig, ob LLM da ist."""
        url = LLMBridge.get_api_url()
        try:
            # Wir senden einen leeren Dummy-Request an den Root oder Info endpoint wäre besser,
            # aber viele OpenAI-kompatible Server haben nur POST /v1/...
            # Wir machen einfach einen minimalen Call.
            requests.get(url.replace("/chat/completions", "/models"), timeout=1)
            return True
        except:
            return False