import logging

from fastapi import APIRouter

from app.models.schemas import GeneratePlanRequest, GeneratePlanResponse
from app.services.decision_engine import generate_plan

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Edit Plan"])


@router.post("/generate-plan", response_model=GeneratePlanResponse)
async def generate_plan_endpoint(body: GeneratePlanRequest):
    return await generate_plan(
        prompt=body.prompt,
        segments=body.segments,
        beats=body.beats,
        bpm=body.bpm,
    )
