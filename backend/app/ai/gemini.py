import json
import logging

import httpx

from app.ai.base import AIProvider
from app.ai.utils import (
    ProviderError,
    RateLimitError,
    retry_async,
)
from app.models.schemas import Action

logger = logging.getLogger(__name__)

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_SYSTEM_PROMPT = (
    "You are an After Effects anime editing assistant. "
    "Given a natural-language edit description, output a JSON array of actions. "
    "Each action has: type (string), label (string), params (object). "
    "Available types: beat_detect, scene_detect, zoom, shake, flash. "
    "Respond with valid JSON only, no markdown, no explanation."
)

_MODEL_MAP = {
    "gemini-2.0-flash": "gemini-2.0-flash",
    "gemini-2.0-pro": "gemini-2.0-pro-exp-02-05",
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-1.5-flash": "gemini-1.5-flash",
}


class GeminiProvider(AIProvider):
    name = "gemini"

    async def complete(
        self,
        prompt: str,
        model: str,
        api_key: str,
    ) -> list[Action]:
        resolved = _MODEL_MAP.get(model, model)
        url = f"{_GEMINI_BASE}/{resolved}:generateContent?key={api_key}"

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
            "generation_config": {
                "temperature": 0.2,
                "top_p": 0.95,
                "max_output_tokens": 1024,
            },
        }

        async def _request():
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                resp = await client.post(url, json=body)

            if resp.status_code == 429:
                raise RateLimitError("Gemini rate limit hit", 429)
            if resp.status_code == 403:
                raise ProviderError("Gemini authentication failed — check your API key", 403)
            if resp.status_code >= 500:
                raise ProviderError(f"Gemini server error ({resp.status_code})", 500)

            resp.raise_for_status()
            return resp.json()

        try:
            data = await retry_async(_request)
        except ProviderError as e:
            logger.error("Gemini request failed: %s", e.message)
            raise

        return _parse_response(data, prompt)


def _parse_response(data: dict, fallback_prompt: str) -> list[Action]:
    try:
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        raw = text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        actions_data = json.loads(raw)
        return [Action(**a) for a in actions_data]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Failed to parse Gemini response (%s), falling back", exc)
        from app.services.analyzer import parse_prompt_locally

        return parse_prompt_locally(fallback_prompt)
