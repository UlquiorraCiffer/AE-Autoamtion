import logging

from app.ai import ProviderRegistry
from app.exceptions import AnalysisError
from app.models.schemas import Action, AnalyzeResponse

logger = logging.getLogger(__name__)


def parse_prompt_locally(text: str) -> list[Action]:
    lower = text.lower()
    actions: list[Action] = []

    if "beat" in lower or "bpm" in lower:
        actions.append(Action(type="beat_detect", label="Detect beats"))
    if "scene" in lower or "cut" in lower:
        actions.append(Action(type="scene_detect", label="Detect scene cuts"))
    if "zoom" in lower or "punch" in lower:
        actions.append(Action(type="zoom", label="Add zoom effect"))
    if "shake" in lower or "wiggle" in lower:
        actions.append(Action(type="shake", label="Add shake effect"))
    if "flash" in lower:
        actions.append(Action(type="flash", label="Add flash effect"))
    if "glow" in lower:
        actions.append(Action(type="glow", label="Add glow effect"))
    if "speed ramp" in lower or "velocity" in lower or "speed_ramp" in lower:
        actions.append(Action(type="velocity_ramp", label="Add velocity ramp"))
    if "remove low" in lower or "remove slow" in lower:
        actions.append(Action(type="remove_low_energy", label="Remove low-energy segments"))

    if not actions:
        actions.append(
            Action(type="unknown", label="Unrecognised prompt — try describing cuts, beats, or effects")
        )

    return actions


async def analyze_prompt(
    prompt: str,
    provider: str = "openrouter",
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
) -> AnalyzeResponse:
    if not prompt.strip():
        raise AnalysisError("Prompt cannot be empty")

    logger.info("Analyzing prompt (provider=%s, model=%s, len=%d)", provider, model, len(prompt))

    if api_key:
        try:
            instance = ProviderRegistry.get(provider)
            actions = await instance.complete(prompt=prompt, model=model, api_key=api_key)
            logger.info("LLM returned %d actions via %s", len(actions), provider)
        except Exception as exc:
            logger.warning("LLM analysis failed (%s), falling back to local parser", exc)
            actions = parse_prompt_locally(prompt)
    else:
        logger.info("No API key provided — using local parser")
        actions = parse_prompt_locally(prompt)

    return AnalyzeResponse(prompt=prompt, actions=actions)
