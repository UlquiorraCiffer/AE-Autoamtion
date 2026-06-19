import math
import struct
import tempfile
import wave
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.beat_detector import analyze_audio

client = TestClient(app)
SAMPLE_RATE = 22050


@pytest.fixture(scope="session", autouse=True)
def _warm_librosa():
    """Trigger numba JIT compilation on first import so tests don't time out."""
    import librosa
    y = np.zeros(int(SAMPLE_RATE * 0.5))
    librosa.beat.beat_track(y=y, sr=SAMPLE_RATE)
    librosa.onset.onset_strength(y=y, sr=SAMPLE_RATE)
    yield


def _make_click_track(
    duration_secs: float = 10.0,
    bpm: float = 128.0,
    sr: int = SAMPLE_RATE,
) -> np.ndarray:
    num_samples = int(sr * duration_secs)
    y = np.zeros(num_samples)
    beat_interval = 60.0 / bpm
    beat_samples = int(sr * beat_interval)

    for i in range(int(duration_secs / beat_interval)):
        start = i * beat_samples
        if start >= num_samples:
            break
        click_len = int(sr * 0.02)
        end = min(start + click_len, num_samples)
        t = np.arange(end - start) / sr
        envelope = np.exp(-t * 80)
        y[start:end] = envelope * 0.9

    return y


def _generate_wav(path: str, y: np.ndarray, sr: int = SAMPLE_RATE):
    scaled = np.clip(y * 32767, -32768, 32767).astype(np.int16)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(scaled.tobytes())


class TestBeatAnalyzerUnit:
    def test_detect_beats_returns_reasonable_bpm(self):
        sr = SAMPLE_RATE
        y = _make_click_track(duration_secs=8.0, bpm=128.0, sr=sr)
        bpm, times, drops, confs = analyze_audio(y, sr)
        assert bpm > 60
        assert len(times) > 0

    def test_all_outputs_have_same_length(self):
        sr = SAMPLE_RATE
        y = _make_click_track(duration_secs=5.0, bpm=140.0, sr=sr)
        _, times, drops, confs = analyze_audio(y, sr)
        assert len(times) == len(drops) == len(confs)

    def test_drop_intensity_in_range(self):
        sr = SAMPLE_RATE
        y = _make_click_track(duration_secs=5.0, bpm=100.0, sr=sr)
        _, _, drops, _ = analyze_audio(y, sr)
        for d in drops:
            assert 0 <= d <= 1

    def test_confidence_in_range(self):
        sr = SAMPLE_RATE
        y = _make_click_track(duration_secs=5.0, bpm=120.0, sr=sr)
        _, _, _, confs = analyze_audio(y, sr)
        for c in confs:
            assert 0 <= c <= 1

    def test_beat_times_are_ascending(self):
        sr = SAMPLE_RATE
        y = _make_click_track(duration_secs=6.0, bpm=128.0, sr=sr)
        _, times, _, _ = analyze_audio(y, sr)
        for i in range(1, len(times)):
            assert times[i] > times[i - 1]

    def test_duration_affects_beat_count(self):
        sr = SAMPLE_RATE
        short = _make_click_track(duration_secs=3.0, bpm=120.0, sr=sr)
        long = _make_click_track(duration_secs=6.0, bpm=120.0, sr=sr)
        _, short_times, _, _ = analyze_audio(short, sr)
        _, long_times, _, _ = analyze_audio(long, sr)
        assert len(long_times) >= len(short_times)


class TestBeatsEndpoint:
    def test_missing_audio_path_returns_422(self):
        response = client.post("/detect-beats", json={})
        assert response.status_code == 422

    def test_nonexistent_audio_returns_400(self):
        response = client.post("/detect-beats", json={"audio_path": "nonexistent.wav"})
        assert response.status_code == 400
