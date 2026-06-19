import logging

from app.exceptions import DetectionError
from app.models.schemas import Beat, DetectBeatsResponse

logger = logging.getLogger(__name__)


async def detect_beats() -> DetectBeatsResponse:
    logger.info("Beat detection requested (placeholder)")
    bpm = 128.0
    interval = 60.0 / bpm
    beats = [Beat(time_seconds=i * interval, bpm=bpm) for i in range(32)]
    return DetectBeatsResponse(beats=beats, bpm=bpm, total_beats=len(beats))
