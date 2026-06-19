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

class DetectScenesRequest(BaseModel):
    video_path: str = Field(..., min_length=1)
    fps: float = 1.0
    threshold: float = 0.3


class SceneSegment(BaseModel):
    start_time: float
    end_time: float
    motion_score: float = 0.0
    confidence: float = 1.0


class DetectScenesResponse(BaseModel):
    video_path: str
    segments: list[SceneSegment]
    total_scenes: int
    analysis_fps: float


# ─── Beat Detection ───

class DetectBeatsRequest(BaseModel):
    audio_path: str = Field(..., min_length=1)


class Beat(BaseModel):
    time_seconds: float
    bpm: float
    confidence: float = 1.0
    drop_intensity: float = 0.0


class DetectBeatsResponse(BaseModel):
    audio_path: str
    beats: list[Beat]
    bpm: float
    total_beats: int
    duration_seconds: float


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
