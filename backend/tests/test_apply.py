from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestApply:
    def test_apply_valid_actions(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "zoom", "label": "Add zoom", "params": {}}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "ae.addZoom()" in data["applied"]

    def test_apply_empty_actions_returns_400(self):
        response = client.post("/apply-edit", json={"actions": []})
        assert response.status_code == 400
        assert "No actions provided" in response.json()["detail"]
