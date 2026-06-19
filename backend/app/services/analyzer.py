import logging

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

    if not actions:
        actions.append(
            Action(type="unknown", label="Unrecognised prompt — try describing cuts, beats, or effects")
        )

    return actions


async def analyze_prompt(prompt: str, model: str, api_key: str | None = None) -> AnalyzeResponse:
    if not prompt.strip():
        raise AnalysisError("Prompt cannot be empty")

    logger.info("Analyzing prompt (model=%s, len=%d)", model, len(prompt))

    if api_key:
        pass

    actions = parse_prompt_locally(prompt)
    logger.info("Parsed %d actions from prompt", len(actions))

    return AnalyzeResponse(prompt=prompt, actions=actions)
