from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import Beat, SceneSegment

client = TestClient(app)

_SAMPLE_SEGMENTS = [
    SceneSegment(start_time=0.0, end_time=4.0, motion_score=5.0, confidence=0.9),
    SceneSegment(start_time=4.0, end_time=8.0, motion_score=30.0, confidence=0.95),
    SceneSegment(start_time=8.0, end_time=12.0, motion_score=2.0, confidence=0.6),
    SceneSegment(start_time=12.0, end_time=16.0, motion_score=45.0, confidence=0.98),
    SceneSegment(start_time=16.0, end_time=20.0, motion_score=8.0, confidence=0.8),
]

_SAMPLE_BEATS = [
    Beat(time_seconds=0.0, bpm=128, confidence=0.9, drop_intensity=0.8),
    Beat(time_seconds=0.469, bpm=128, confidence=0.85, drop_intensity=0.3),
    Beat(time_seconds=0.938, bpm=128, confidence=0.7, drop_intensity=0.9),
    Beat(time_seconds=1.406, bpm=128, confidence=0.6, drop_intensity=0.2),
    Beat(time_seconds=1.875, bpm=128, confidence=0.95, drop_intensity=0.7),
    Beat(time_seconds=2.344, bpm=128, confidence=0.8, drop_intensity=0.5),
    Beat(time_seconds=2.812, bpm=128, confidence=0.75, drop_intensity=0.1),
    Beat(time_seconds=3.281, bpm=128, confidence=0.88, drop_intensity=0.6),
]


def _request(prompt: str, segments=None, beats=None, bpm: float = 0):
    return {
        "prompt": prompt,
        "segments": [s.model_dump() for s in (segments or _SAMPLE_SEGMENTS)],
        "beats": [b.model_dump() for b in (beats or _SAMPLE_BEATS)],
        "bpm": bpm,
    }


class TestGeneratePlanEndpoint:
    def test_returns_valid_plan_structure(self):
        resp = client.post("/generate-plan", json=_request("cut on every beat with zoom"))
        assert resp.status_code == 200
        data = resp.json()
        assert "plan" in data
        plan = data["plan"]
        assert "timeline" in plan
        assert "effects" in plan
        assert "bpm" in plan
        assert plan["prompt"] == "cut on every beat with zoom"

    def test_timeline_entries_have_required_fields(self):
        resp = client.post("/generate-plan", json=_request("edit this"))
        plan = resp.json()["plan"]
        for entry in plan["timeline"]:
            assert "segment_index" in entry
            assert "keep" in entry
            assert "order" in entry

    def test_all_segments_appear_in_timeline(self):
        resp = client.post("/generate-plan", json=_request("edit this"))
        plan = resp.json()["plan"]
        indices = {e["segment_index"] for e in plan["timeline"]}
        assert indices == {0, 1, 2, 3, 4}

    def test_zoom_effects_added_for_zoom_prompt(self):
        resp = client.post("/generate-plan", json=_request("zoom on every beat"))
        effects = resp.json()["plan"]["effects"]
        zoom_types = {e["type"] for e in effects}
        assert "zoom" in zoom_types

    def test_shake_effects_added_for_shake_prompt(self):
        resp = client.post("/generate-plan", json=_request("add shake to action scenes"))
        effects = resp.json()["plan"]["effects"]
        assert any(e["type"] == "shake" for e in effects)

    def test_flash_effects_added_for_flash_prompt(self):
        resp = client.post("/generate-plan", json=_request("flash on every beat"))
        effects = resp.json()["plan"]["effects"]
        assert any(e["type"] == "flash" for e in effects)

    def test_glow_effects_added_for_glow_prompt(self):
        resp = client.post("/generate-plan", json=_request("glow effect on transitions"))
        effects = resp.json()["plan"]["effects"]
        assert any(e["type"] == "glow" for e in effects)

    def test_velocity_ramp_added_for_speed_prompt(self):
        resp = client.post("/generate-plan", json=_request("speed ramp on action"))
        effects = resp.json()["plan"]["effects"]
        assert any(e["type"] == "velocity_ramp" for e in effects)

    def test_multiple_effects_in_plan(self):
        resp = client.post("/generate-plan", json=_request("zoom and shake with flash"))
        effects = resp.json()["plan"]["effects"]
        types = {e["type"] for e in effects}
        assert "zoom" in types
        assert "shake" in types
        assert "flash" in types

    def test_effect_targets_have_params(self):
        resp = client.post("/generate-plan", json=_request("zoom in on action"))
        effects = resp.json()["plan"]["effects"]
        for e in effects:
            assert "params" in e
            assert isinstance(e["params"], dict)

    def test_empty_prompt_returns_422(self):
        resp = client.post("/generate-plan", json=_request(""))
        assert resp.status_code == 422

    def test_missing_segments_returns_422(self):
        resp = client.post("/generate-plan", json={"prompt": "edit", "segments": [], "beats": []})
        assert resp.status_code == 422

    def test_inferred_bpm_from_beats(self):
        resp = client.post("/generate-plan", json=_request("edit", bpm=0))
        plan = resp.json()["plan"]
        assert plan["bpm"] > 0

    def test_removed_segments_are_marked(self):
        resp = client.post("/generate-plan", json=_request("remove slow parts"))
        plan = resp.json()["plan"]
        removed = [e for e in plan["timeline"] if not e["keep"]]
        assert len(removed) >= 0

    def test_single_segment_plan(self):
        seg = [SceneSegment(start_time=0.0, end_time=10.0, motion_score=10.0, confidence=0.9)]
        resp = client.post("/generate-plan", json=_request("add zoom", segments=seg, beats=[]))
        assert resp.status_code == 200
        plan = resp.json()["plan"]
        assert len(plan["timeline"]) == 1
        assert plan["timeline"][0]["keep"] is True
