from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestAnalyze:
    def test_analyze_with_beat_prompt(self):
        response = client.post("/analyze", json={"prompt": "cut on every beat with zoom"})
        assert response.status_code == 200
        data = response.json()
        assert data["prompt"] == "cut on every beat with zoom"
        assert len(data["actions"]) > 0
        types = {a["type"] for a in data["actions"]}
        assert "beat_detect" in types

    def test_analyze_empty_prompt_returns_422(self):
        response = client.post("/analyze", json={"prompt": ""})
        assert response.status_code == 422

    def test_analyze_with_scene_prompt(self):
        response = client.post("/analyze", json={"prompt": "detect scenes and cut"})
        assert response.status_code == 200
        data = response.json()
        types = {a["type"] for a in data["actions"]}
        assert "scene_detect" in types
