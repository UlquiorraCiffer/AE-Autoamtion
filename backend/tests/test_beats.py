from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestBeats:
    def test_detect_beats_returns_beats(self):
        response = client.post("/detect-beats")
        assert response.status_code == 200
        data = response.json()
        assert "beats" in data
        assert data["total_beats"] > 0
        assert data["bpm"] > 0
        for b in data["beats"]:
            assert "time_seconds" in b
            assert "bpm" in b
