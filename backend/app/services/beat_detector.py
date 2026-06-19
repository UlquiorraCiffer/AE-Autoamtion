import logging

import numpy as np

from app.exceptions import DetectionError
from app.models.schemas import Beat, DetectBeatsResponse

logger = logging.getLogger(__name__)


def analyze_audio(
    y: np.ndarray,
    sr: int,
) -> tuple[float, list[float], list[float], list[float]]:
    import librosa

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    bpm = float(np.round(np.atleast_1d(tempo)[0], 1))

    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_times = librosa.times_like(onset_env, sr=sr)

    if len(beat_times) > 0 and len(onset_env) > 0:
        drop_values = _compute_drop_intensity(beat_times, onset_env, onset_times)
    else:
        drop_values = [0.0]

    confidences = [
        _confidence_from_onset_distribution(t, onset_env, onset_times)
        for t in beat_times
    ]

    return bpm, beat_times, drop_values, confidences


async def detect_beats(audio_path: str) -> DetectBeatsResponse:
    logger.info("Beat detection on %s", audio_path)

    import librosa

    try:
        y, sr = librosa.load(audio_path, sr=None, mono=True)
    except Exception as exc:
        raise DetectionError(f"Failed to load audio: {exc}")

    if len(y) == 0:
        raise DetectionError("Audio file contains no samples")

    duration = float(len(y)) / sr
    bpm, beat_times, drop_values, confidences = analyze_audio(y, sr)

    beats: list[Beat] = [
        Beat(
            time_seconds=round(t, 3),
            bpm=bpm,
            confidence=round(c, 2),
            drop_intensity=round(d, 3),
        )
        for t, c, d in zip(beat_times, confidences, drop_values)
    ]

    logger.info("Detected %d beats at %.1f BPM from %.1fs audio", len(beats), bpm, duration)

    return DetectBeatsResponse(
        audio_path=audio_path,
        beats=beats,
        bpm=bpm,
        total_beats=len(beats),
        duration_seconds=round(duration, 3),
    )


def _compute_drop_intensity(
    beat_times: list[float],
    onset_env: np.ndarray,
    onset_times: np.ndarray,
) -> list[float]:
    values: list[float] = []
    for bt in beat_times:
        diffs = np.abs(onset_times - bt)
        idx = int(diffs.argmin())
        if idx < len(onset_env):
            values.append(float(onset_env[idx]))
        else:
            values.append(0.0)

    if not values:
        return []

    arr = np.array(values)
    mn, mx = float(arr.min()), float(arr.max())
    if mx - mn < 1e-9:
        return [0.5] * len(values)

    return ((arr - mn) / (mx - mn)).tolist()


def _confidence_from_onset_distribution(
    beat_time: float,
    onset_env: np.ndarray,
    onset_times: np.ndarray,
) -> float:
    diffs = np.abs(onset_times - beat_time)
    idx = int(diffs.argmin())
    if idx < len(onset_env):
        local_slice = onset_env[max(0, idx - 2): min(len(onset_env), idx + 3)]
        local_max = float(local_slice.max()) if local_slice.size > 0 else 0.0
        global_max = float(onset_env.max()) if onset_env.size > 0 else 0.0
        if global_max > 0:
            return local_max / global_max
    return 0.5
