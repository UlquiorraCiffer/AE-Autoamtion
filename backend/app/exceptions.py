from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, status_code: int = HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code


class AnalysisError(AppError):
    pass


class DetectionError(AppError):
    pass


class ApplyError(AppError):
    pass


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("AppError: %s", exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
