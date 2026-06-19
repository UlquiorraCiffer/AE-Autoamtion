import logging

from fastapi import APIRouter

from app.models.schemas import ApplyRequest, ApplyResponse
from app.services.edit_applier import apply_edit

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Apply Edit"])


@router.post("/apply-edit", response_model=ApplyResponse)
async def apply_edit_endpoint(body: ApplyRequest):
    return await apply_edit(body)
