from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestScenes:
    def test_detect_scenes_returns_scenes(self):
        response = client.post("/detect-scenes")
        assert response.status_code == 200
        data = response.json()
        assert "scenes" in data
        assert data["total_scenes"] > 0
        for s in data["scenes"]:
            assert "time_seconds" in s
            assert "frame" in s
