import logging

from app.exceptions import DetectionError
from app.models.schemas import DetectScenesResponse, SceneBoundary

logger = logging.getLogger(__name__)


async def detect_scenes() -> DetectScenesResponse:
    logger.info("Scene detection requested (placeholder)")
    scenes = [
        SceneBoundary(time_seconds=0.0, frame=0),
        SceneBoundary(time_seconds=5.2, frame=125),
        SceneBoundary(time_seconds=11.8, frame=283),
    ]
    return DetectScenesResponse(scenes=scenes, total_scenes=len(scenes))
