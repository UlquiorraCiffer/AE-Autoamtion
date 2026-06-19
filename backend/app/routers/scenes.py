import logging

from fastapi import APIRouter

from app.models.schemas import DetectScenesResponse
from app.services.scene_detector import detect_scenes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scene Detection"])


@router.post("/detect-scenes", response_model=DetectScenesResponse)
async def detect_scenes_endpoint():
    return await detect_scenes()
