import logging

from fastapi import APIRouter

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.analyzer import analyze_prompt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest):
    return await analyze_prompt(
        prompt=body.prompt,
        provider=body.provider,
        model=body.model,
        api_key=body.api_key,
    )
