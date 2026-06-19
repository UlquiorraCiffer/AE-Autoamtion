import json
import logging

import httpx

from app.ai.base import AIProvider
from app.ai.utils import (
    ProviderError,
    RateLimitError,
    TimeoutError_,
    retry_async,
)
from app.models.schemas import Action

logger = logging.getLogger(__name__)

_OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
_SYSTEM_PROMPT = (
    "You are an After Effects anime editing assistant. "
    "Given a natural-language edit description, output a JSON array of actions. "
    "Each action has: type (string), label (string), params (object). "
    "Available types: beat_detect, scene_detect, zoom, shake, flash. "
    "Respond with valid JSON only, no markdown, no explanation."
)


class OpenRouterProvider(AIProvider):
    name = "openrouter"

    async def complete(
        self,
        prompt: str,
        model: str,
        api_key: str,
    ) -> list[Action]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        async def _request():
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                resp = await client.post(_OPENROUTER_BASE, json=body, headers=headers)

            if resp.status_code == 429:
                raise RateLimitError("OpenRouter rate limit hit", 429)
            if resp.status_code == 401:
                raise ProviderError("OpenRouter authentication failed — check your API key", 401)
            if resp.status_code == 402:
                raise ProviderError("OpenRouter insufficient credits", 402)
            if resp.status_code >= 500:
                raise ProviderError(f"OpenRouter server error ({resp.status_code})", 500)

            resp.raise_for_status()
            return resp.json()

        try:
            data = await retry_async(_request)
        except ProviderError as e:
            logger.error("OpenRouter request failed: %s", e.message)
            raise

        return _parse_response(data, prompt)


def _parse_response(data: dict, fallback_prompt: str) -> list[Action]:
    try:
        text = data["choices"][0]["message"]["content"]
        raw = text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        actions_data = json.loads(raw)
        return [Action(**a) for a in actions_data]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        logger.warning("Failed to parse OpenRouter response (%s), falling back", exc)
        from app.services.analyzer import parse_prompt_locally

        return parse_prompt_locally(fallback_prompt)
