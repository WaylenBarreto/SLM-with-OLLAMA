import json
from collections.abc import AsyncIterator
from typing import Any
import httpx
from .schemas import ModelInfo


class OllamaUnavailable(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")

    async def _get(self, path: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}{path}")
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaUnavailable(str(exc)) from exc

    async def version(self) -> str:
        return (await self._get("/api/version")).get("version", "unknown")

    async def models(self) -> list[ModelInfo]:
        data = await self._get("/api/tags")
        models = []
        for item in data.get("models", []):
            details = item.get("details", {})
            models.append(ModelInfo(
                name=item["name"], size=item.get("size"),
                parameter_size=details.get("parameter_size"),
                quantization=details.get("quantization_level"),
                modified_at=item.get("modified_at"),
            ))
        return models

    async def generate(self, model: str, prompt: str, options: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        payload = {"model": model, "prompt": prompt, "stream": True, "options": options}
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            yield json.loads(line)
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise OllamaUnavailable(str(exc)) from exc
