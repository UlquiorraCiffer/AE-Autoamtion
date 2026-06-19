from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestApply:
    def test_apply_zoom_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "zoom", "label": "Zoom", "params": {"magnitude": 1.3}}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "ae.applyZoom" in data["applied"][0]

    def test_apply_shake_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "shake", "label": "Shake", "params": {"frequency": 15}}]},
        )
        assert response.status_code == 200
        assert "ae.applyShake" in response.json()["applied"][0]

    def test_apply_flash_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "flash", "label": "Flash", "params": {}}]},
        )
        assert response.status_code == 200
        assert "ae.applyFlash" in response.json()["applied"][0]

    def test_apply_glow_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "glow", "label": "Glow", "params": {}}]},
        )
        assert response.status_code == 200
        assert "ae.applyGlow" in response.json()["applied"][0]

    def test_apply_velocity_ramp_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "velocity_ramp", "label": "Ramp", "params": {}}]},
        )
        assert response.status_code == 200
        assert "ae.applyVelocityRamp" in response.json()["applied"][0]

    def test_apply_split_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "split", "label": "Split", "params": {"layerIndex": 1, "time": 5.0}}]},
        )
        assert response.status_code == 200
        assert "ae.splitLayer" in response.json()["applied"][0]

    def test_apply_trim_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "trim", "label": "Trim", "params": {"layerIndex": 1, "inTime": 0, "outTime": 10}}]},
        )
        assert response.status_code == 200
        assert "ae.trimLayer" in response.json()["applied"][0]

    def test_apply_markers_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "add_markers", "label": "Markers", "params": {"beats": [{"time_seconds": 0.0}]}}]},
        )
        assert response.status_code == 200
        assert "ae.addMarkers" in response.json()["applied"][0]

    def test_apply_reorder_generates_script(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "reorder", "label": "Reorder", "params": {"order": [3, 1, 2]}}]},
        )
        assert response.status_code == 200
        assert "ae.reorderLayers" in response.json()["applied"][0]

    def test_apply_multiple_actions(self):
        response = client.post(
            "/apply-edit",
            json={
                "actions": [
                    {"type": "zoom", "label": "Zoom", "params": {}},
                    {"type": "shake", "label": "Shake", "params": {}},
                ]
            },
        )
        assert response.status_code == 200
        assert len(response.json()["applied"]) == 2

    def test_apply_empty_actions_returns_400(self):
        response = client.post("/apply-edit", json={"actions": []})
        assert response.status_code == 400
        assert "No actions provided" in response.json()["detail"]

    def test_actions_params_are_escaped(self):
        response = client.post(
            "/apply-edit",
            json={"actions": [{"type": "zoom", "label": "Zoom", "params": {"magnitude": 1.5, "direction": "in"}}]},
        )
        assert response.status_code == 200
        script = response.json()["applied"][0]
        assert "1.5" in script
        assert "in" in script
