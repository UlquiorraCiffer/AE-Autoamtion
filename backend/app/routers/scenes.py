import logging

from fastapi import APIRouter

from app.models.schemas import DetectScenesRequest, DetectScenesResponse
from app.services.scene_detector import detect_scenes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scene Detection"])


@router.post("/detect-scenes", response_model=DetectScenesResponse)
async def detect_scenes_endpoint(body: DetectScenesRequest):
    return await detect_scenes(
        video_path=body.video_path,
        fps=body.fps,
        threshold=body.threshold,
    )
