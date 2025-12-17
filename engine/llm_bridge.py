# engine/llm_bridge.py
import requests
import json

class LLMBridge:
    API_URL = "http://localhost:1234/v1/chat/completions"
    HEADERS = {"Content-Type": "application/json"}
    
    @staticmethod
    def call(system_prompt, user_message, max_tokens=100, temperature=0.7):
        """
        Sendet einen Request an den lokalen LLM Server.
        Gibt None zurück, wenn der Server nicht erreichbar ist.
        """
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(LLMBridge.API_URL, headers=LLMBridge.HEADERS, json=payload, timeout=4)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"[LLM Error] Status: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError:
            print("[LLM Error] Server nicht erreichbar.")
            return None
        except Exception as e:
            print(f"[LLM Error] {e}")
            return None