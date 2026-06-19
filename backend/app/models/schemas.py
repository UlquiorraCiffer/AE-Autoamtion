from pydantic import BaseModel, Field


# ─── Analyze ───

class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    provider: str = "openrouter"
    model: str = "gpt-4o-mini"
    api_key: str | None = None


class Action(BaseModel):
    type: str
    label: str
    params: dict = {}


class AnalyzeResponse(BaseModel):
    prompt: str
    actions: list[Action]


# ─── Scene Detection ───

class SceneBoundary(BaseModel):
    time_seconds: float
    frame: int


class DetectScenesResponse(BaseModel):
    scenes: list[SceneBoundary]
    total_scenes: int


# ─── Beat Detection ───

class Beat(BaseModel):
    time_seconds: float
    bpm: float
    confidence: float = 1.0


class DetectBeatsResponse(BaseModel):
    beats: list[Beat]
    bpm: float
    total_beats: int


# ─── Apply Edit ───

class ApplyRequest(BaseModel):
    actions: list[Action]


class ApplyResponse(BaseModel):
    applied: list[str]
    status: str = "ok"


# ─── Health ───

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
