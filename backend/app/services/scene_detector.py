import logging

import cv2
import numpy as np

from app.exceptions import DetectionError
from app.models.schemas import DetectScenesResponse, SceneSegment
from app.services.ffmpeg_utils import extract_frames

logger = logging.getLogger(__name__)

_BLACK_THRESHOLD = 25
_MOTION_THRESHOLD = 30.0
_HIST_METHOD = cv2.HISTCMP_CORREL


def _histogram(frame: np.ndarray) -> cv2.Mat:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist(
        [hsv],
        [0, 1],
        None,
        [50, 60],
        [0, 180, 0, 256],
    )
    cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
    return hist


def _is_black(frame: np.ndarray) -> bool:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(gray.mean()) < _BLACK_THRESHOLD


def _motion_score(prev: np.ndarray, curr: np.ndarray) -> float:
    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(prev_gray, curr_gray)
    return float(diff.mean())


def _classify_confidence(hist_diff: float, is_black_change: bool) -> float:
    if is_black_change:
        return 0.85
    if hist_diff < 0.1:
        return 0.95
    if hist_diff < 0.25:
        return 0.80
    if hist_diff < 0.4:
        return 0.60
    return 0.40


def detect_scenes_from_frames(
    frames: list[np.ndarray],
    fps: float = 1.0,
    threshold: float = 0.3,
) -> list[SceneSegment]:
    if len(frames) < 2:
        return [SceneSegment(start_time=0.0, end_time=len(frames) / fps, motion_score=0.0, confidence=1.0)]

    histograms = [_histogram(f) for f in frames]
    black_flags = [_is_black(f) for f in frames]
    motion_scores = [0.0] + [_motion_score(frames[i - 1], frames[i]) for i in range(1, len(frames))]

    segments: list[SceneSegment] = []
    seg_start = 0.0
    seg_motion_sum = 0.0
    seg_motion_count = 0

    for i in range(1, len(frames)):
        current_time = i / fps
        seg_motion_sum += motion_scores[i]
        seg_motion_count += 1

        hist_diff = 1.0 - cv2.compareHist(histograms[i - 1], histograms[i], _HIST_METHOD)
        is_black_change = black_flags[i - 1] != black_flags[i]
        confidence = _classify_confidence(hist_diff, is_black_change)

        if (is_black_change and black_flags[i]) or hist_diff > threshold:
            avg_motion = seg_motion_sum / max(seg_motion_count, 1)
            segments.append(
                SceneSegment(
                    start_time=round(seg_start, 3),
                    end_time=round(current_time, 3),
                    motion_score=round(avg_motion, 2),
                    confidence=round(confidence, 2),
                )
            )
            seg_start = current_time
            seg_motion_sum = 0.0
            seg_motion_count = 0

    total_duration = len(frames) / fps
    avg_motion = seg_motion_sum / max(seg_motion_count, 1)
    segments.append(
        SceneSegment(
            start_time=round(seg_start, 3),
            end_time=round(total_duration, 3),
            motion_score=round(avg_motion, 2),
            confidence=1.0,
        )
    )

    return segments


async def detect_scenes(
    video_path: str,
    fps: float = 1.0,
    threshold: float = 0.3,
) -> DetectScenesResponse:
    logger.info("Scene detection on %s (fps=%.1f, threshold=%.2f)", video_path, fps, threshold)

    try:
        frames = extract_frames(video_path, fps=fps)
    except (ValueError, RuntimeError) as exc:
        raise DetectionError(str(exc))

    segments = detect_scenes_from_frames(frames, fps=fps, threshold=threshold)

    logger.info("Detected %d scene segments", len(segments))

    return DetectScenesResponse(
        video_path=video_path,
        segments=segments,
        total_scenes=len(segments),
        analysis_fps=fps,
    )
