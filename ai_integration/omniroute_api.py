"""OmniRoute API client following the OpenAI-compatible chat endpoint.

This client uses the OmniRoute local endpoint with the provided API key,
enabling access to 150+ free AI tiers through a single OpenAI-compatible
endpoint. Auto-fallback and token compression are handled by OmniRoute.
"""

from __future__ import annotations

from typing import Any, Dict, List

import requests


class OmniRouteAPI:
    """OpenAI-compatible client for OmniRoute AI gateway.

    Uses one endpoint (http://localhost:20128/v1) to access 352+ providers
    including 150+ free tiers. The Smart Router automatically falls back
    when a provider has quota issues or fails.

    API key format: sk-... provided by OmniRoute dashboard.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "auto",
        base_url: str = "http://localhost:20128/v1",
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
        max_tokens: int = 1100,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """Send a chat completion request to OmniRoute.

        Same interface as an OpenAI-compatible client for maximum compatibility.
        OmniRoute handles auto-fallback across 1100+ providers.
        """
        if not self.api_key:
            return {"error": "Falta la API key de OmniRoute."}

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
                f"{self.base_url}/chat/completions",
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
            return {"error": f"OmniRoute API error: {description}"}
        except requests.RequestException as exc:  # pragma: no cover - network issues
            return {"error": f"No se pudo contactar a OmniRoute: {exc}"}

    @staticmethod
    def _parse_response(response: Dict[str, Any]) -> Dict[str, Any]:
        if "error" in response:
            error = response["error"]
            if isinstance(error, dict):
                return {"error": error.get("message", "Error desconocido de OmniRoute")}
            return {"error": str(error)}

        choices = response.get("choices", [])
        if not choices:
            return {"error": "OmniRoute devolvió una respuesta vacía."}

        message = choices[0].get("message", {})
        content = message.get("content", "").strip()
        if not content:
            return {"error": "OmniRoute no generó contenido."}

        usage = response.get("usage", {})
        return {
            "text": content,
            "usage": usage,
        }