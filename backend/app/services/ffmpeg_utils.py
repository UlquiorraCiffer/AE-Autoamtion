import logging
import subprocess
import tempfile
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_FFMPEG_CMD = "ffmpeg"


def _check_ffmpeg() -> bool:
    try:
        subprocess.run(
            [_FFMPEG_CMD, "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


_HAS_FFMPEG = _check_ffmpeg()


def has_ffmpeg() -> bool:
    return _HAS_FFMPEG


def extract_frames_ffmpeg(
    video_path: str,
    fps: float = 1.0,
) -> list[np.ndarray]:
    if not _HAS_FFMPEG:
        raise RuntimeError("FFmpeg not found on PATH")

    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = str(Path(tmpdir) / "frame_%06d.png")

        subprocess.run(
            [
                _FFMPEG_CMD,
                "-i", video_path,
                "-vf", f"fps={fps}",
                "-vsync", "vfr",
                "-q:v", "2",
                pattern,
            ],
            capture_output=True,
            check=True,
        )

        frame_paths = sorted(Path(tmpdir).glob("frame_*.png"))
        frames: list[np.ndarray] = []
        for path in frame_paths:
            import cv2
            frame = cv2.imread(str(path))
            if frame is not None:
                frames.append(frame)

        logger.info("Extracted %d frames with FFmpeg at %.1f fps", len(frames), fps)
        return frames


def extract_frames_opencv(
    video_path: str,
    fps: float = 1.0,
) -> list[np.ndarray]:
    import cv2

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if source_fps <= 0:
        source_fps = 30.0

    step = max(1, int(round(source_fps / fps)))

    frames: list[np.ndarray] = []
    pos = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if pos % step == 0:
            frames.append(frame)
        pos += 1

    cap.release()
    logger.info("Extracted %d frames with OpenCV at %.1f fps (source %.1f fps)", len(frames), fps, source_fps)
    return frames


def extract_frames(
    video_path: str,
    fps: float = 1.0,
) -> list[np.ndarray]:
    if _HAS_FFMPEG:
        try:
            return extract_frames_ffmpeg(video_path, fps)
        except Exception as exc:
            logger.warning("FFmpeg extraction failed (%s), falling back to OpenCV", exc)

    return extract_frames_opencv(video_path, fps)
