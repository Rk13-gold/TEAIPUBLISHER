from typing import Any, Dict
import requests

class LMStudioClient:
    def __init__(self, api_url: str, api_key: str = "", model: str = "qwen/qwen3-4b"):
        self.api_url = api_url
        self.api_key = api_key
        self.model = model

    def chat(self, prompt: str, max_tokens: int = 512, temperature: float = 0.8) -> dict:
        """
        Envía un mensaje al modelo LM Studio usando el endpoint /v1/chat/completions y espera indefinidamente la respuesta.
        """
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        data = {
            'model': self.model,
            'messages': [
                {"role": "user", "content": prompt}
            ],
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        for attempt in range(3):
            try:
                print(f"[LMStudioClient] Enviando solicitud a {self.api_url} (intento {attempt+1}/3)")
                print(f"[LMStudioClient] Payload: {data}")
                # timeout=None hace que requests espere indefinidamente
                response = requests.post(self.api_url, json=data, headers=headers, timeout=None)
                print(f"[LMStudioClient] Código de estado: {response.status_code}")
                print(f"[LMStudioClient] Respuesta cruda: {response.text}")
                response.raise_for_status()
                return self._parse_response(response.json())
            except requests.Timeout:
                print(f"Timeout al conectar con LM Studio. Intento {attempt+1}/3")
                if attempt == 2:
                    return {"error": "Timeout al conectar con LM Studio."}
            except requests.RequestException as e:
                print(f"Error al conectar con LM Studio (intento {attempt+1}/3):", e)
                if attempt == 2:
                    return {"error": str(e)}
        return {"error": "No se pudo conectar con LM Studio tras varios intentos."}

    def _parse_response(self, response: Dict[str, Any]) -> dict:
        if "error" in response:
            return response
        try:
            choices = response.get("choices", [])
            if not choices or "message" not in choices[0]:
                return {"error": "Respuesta inesperada del modelo.", "raw": response}
            text = choices[0]["message"].get("content", "").strip()
            if not text:
                # Si content está vacío, intenta usar reasoning_content
                text = choices[0]["message"].get("reasoning_content", "").strip()
            return {"text": text}
        except Exception as e:
            print("Error al parsear la respuesta:", e)
            return {"error": "Error inesperado al parsear la respuesta."}