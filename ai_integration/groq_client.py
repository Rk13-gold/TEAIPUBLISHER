"""Simple Groq API client following the OpenAI-compatible chat endpoint."""
from __future__ import annotations

from typing import Any, Dict, List

import requests


class GroqClient:
    """HTTP client for the Groq Chat Completions API."""

    def __init__(
        self,
        api_key: str,
        model: str = "mixtral-8x7b-32768",
        base_url: str = "https://api.groq.com/openai/v1/chat/completions",
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.8,
        max_tokens: int = 1024,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """Send a chat completion request to Groq."""
        if not self.api_key:
            return {"error": "Falta la API key de Groq."}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data)
        except requests.HTTPError as exc:
            try:
                error_payload = response.json()
                description = error_payload.get("error", {}).get("message", str(exc))
            except Exception:  # pragma: no cover - fallback best effort
                description = str(exc)
            return {"error": f"Groq API error: {description}"}
        except requests.RequestException as exc:  # pragma: no cover - network issues
            return {"error": f"No se pudo contactar a Groq: {exc}"}

    @staticmethod
    def _parse_response(response: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in response:
            error = response["error"]
            if isinstance(error, dict):
                return {"error": error.get("message", "Error desconocido de Groq")}
            return {"error": str(error)}

        choices = response.get("choices", [])
        if not choices:
            return {"error": "Groq devolvió una respuesta vacía."}

        message = choices[0].get("message", {})
        content = message.get("content", "").strip()
        if not content:
            return {"error": "Groq no generó contenido."}

        usage = response.get("usage", {})
        return {
            "text": content,
            "usage": usage,
        }
