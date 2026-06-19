import logging

from app.exceptions import ApplyError
from app.models.schemas import Action, ApplyRequest, ApplyResponse

logger = logging.getLogger(__name__)

_ACTION_MAP = {
    "beat_detect": "ae.beatDetect()",
    "scene_detect": "ae.sceneDetect()",
    "zoom": "ae.addZoom()",
    "shake": "ae.addShake()",
    "flash": "ae.addFlash()",
}


async def apply_edit(request: ApplyRequest) -> ApplyResponse:
    if not request.actions:
        raise ApplyError("No actions provided")

    applied: list[str] = []
    for action in request.actions:
        script = _ACTION_MAP.get(action.type)
        if script:
            applied.append(script)
            logger.debug("Queued action: %s", script)
        else:
            logger.warning("Unknown action type: %s", action.type)

    return ApplyResponse(applied=applied)
