import json
import logging

from app.exceptions import ApplyError
from app.models.schemas import Action, ApplyRequest, ApplyResponse

logger = logging.getLogger(__name__)

_ACTION_MAP: dict[str, str] = {
    "zoom": "ae.applyZoom({layerIndex}, '{params}')",
    "shake": "ae.applyShake({layerIndex}, '{params}')",
    "flash": "ae.applyFlash('{params}')",
    "glow": "ae.applyGlow({layerIndex}, '{params}')",
    "velocity_ramp": "ae.applyVelocityRamp({layerIndex}, '{params}')",
    "split": "ae.splitLayer({layerIndex}, {time})",
    "trim": "ae.trimLayer({layerIndex}, {inTime}, {outTime})",
    "add_markers": "ae.addMarkers('{params}')",
    "reorder": "ae.reorderLayers('{params}')",
    "execute_plan": "ae.executePlan('{params}')",
    "beat_detect": None,
    "scene_detect": None,
}


async def apply_edit(request: ApplyRequest) -> ApplyResponse:
    if not request.actions:
        raise ApplyError("No actions provided")

    applied: list[str] = []
    for action in request.actions:
        script = _build_script(action)
        if script:
            applied.append(script)
            logger.debug("Queued script: %s", script)
        else:
            logger.info("Skipping action (no AE script): %s", action.type)

    return ApplyResponse(applied=applied)


def _build_script(action: Action) -> str | None:
    template = _ACTION_MAP.get(action.type)
    if template is None:
        return None

    params = action.params or {}
    params_json = _escape_js(json.dumps(params))

    layer_index = params.get("layerIndex", 1)

    return template.format(
        layerIndex=layer_index,
        params=params_json,
        time=params.get("time", 0),
        inTime=params.get("inTime", 0),
        outTime=params.get("outTime", 0),
    )


def _escape_js(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
