import logging

from fastapi import APIRouter

from app.models.schemas import DetectBeatsRequest, DetectBeatsResponse
from app.services.beat_detector import detect_beats

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Beat Detection"])


@router.post("/detect-beats", response_model=DetectBeatsResponse)
async def detect_beats_endpoint(body: DetectBeatsRequest):
    return await detect_beats(audio_path=body.audio_path)
