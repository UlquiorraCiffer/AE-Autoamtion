import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.scene_detector import detect_scenes_from_frames

client = TestClient(app)


def _synthetic_frame(hue: float = 0, brightness: float = 128, width: int = 64, height: int = 64) -> np.ndarray:
    frame = np.full((height, width, 3), brightness, dtype=np.uint8)
    if hue != 0:
        hsv = np.full((height, width, 3), [hue, 200, brightness], dtype=np.uint8)
        import cv2
        frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    return frame


def _black_frame(width: int = 64, height: int = 64) -> np.ndarray:
    return np.zeros((height, width, 3), dtype=np.uint8)


class TestSceneDetectorUnit:
    def test_single_segment_for_identical_frames(self):
        frames = [_synthetic_frame() for _ in range(5)]
        segments = detect_scenes_from_frames(frames, fps=1.0)
        assert len(segments) == 1
        assert segments[0].start_time == 0.0
        assert segments[0].end_time == 5.0

    def test_detects_cut_on_histogram_change(self):
        frames = [_synthetic_frame(hue=0) for _ in range(3)]
        frames += [_synthetic_frame(hue=120) for _ in range(3)]
        segments = detect_scenes_from_frames(frames, fps=1.0, threshold=0.3)
        assert len(segments) >= 2

    def test_detects_black_frame_cut(self):
        frames = [_synthetic_frame(brightness=128) for _ in range(3)]
        frames.append(_black_frame())
        frames.append(_synthetic_frame(brightness=128))
        segments = detect_scenes_from_frames(frames, fps=1.0)
        assert len(segments) >= 2
        assert segments[0].end_time <= 3.0

    def test_motion_score_non_zero_with_different_frames(self):
        frames = [_synthetic_frame(brightness=10), _synthetic_frame(brightness=200)]
        segments = detect_scenes_from_frames(frames, fps=1.0, threshold=0.05)
        assert len(segments) >= 1
        if len(segments) > 1:
            assert segments[0].motion_score > 0

    def test_segments_have_required_fields(self):
        frames = [_synthetic_frame(hue=i * 30) for i in range(10)]
        segments = detect_scenes_from_frames(frames, fps=2.0, threshold=0.3)
        for seg in segments:
            assert seg.start_time >= 0
            assert seg.end_time > seg.start_time
            assert 0 <= seg.confidence <= 1


class TestScenesEndpoint:
    def test_missing_video_path_returns_422(self):
        response = client.post("/detect-scenes", json={})
        assert response.status_code == 422

    def test_nonexistent_video_returns_400(self):
        response = client.post("/detect-scenes", json={"video_path": "nonexistent.mp4"})
        assert response.status_code == 400
