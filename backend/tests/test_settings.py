"""Settings validation for speed and sensor thresholds."""

from fastapi.testclient import TestClient


def _body(client: TestClient) -> dict:
    current = client.get("/api/settings").json()
    return {
        "simulation_speed": current["simulation_speed"],
        "machines": [
            {
                "machine_id": machine["machine_id"],
                "temp_warning": machine["temp_warning"],
                "temp_critical": machine["temp_critical"],
                "vib_warning": machine["vib_warning"],
                "vib_critical": machine["vib_critical"],
                "current_warning": machine["current_warning"],
                "current_critical": machine["current_critical"],
            }
            for machine in current["machines"]
        ],
    }


def test_speed_and_threshold_update(client: TestClient):
    body = _body(client)
    body["simulation_speed"] = 2
    updated = client.put("/api/settings", json=body)
    assert updated.status_code == 200
    assert updated.json()["simulation_speed"] == 2
    assert updated.json()["tick_interval_seconds"] == 1.25


def test_warning_must_be_below_critical(client: TestClient):
    body = _body(client)
    body["machines"][0]["temp_warning"] = 90
    body["machines"][0]["temp_critical"] = 70
    response = client.put("/api/settings", json=body)
    assert response.status_code == 422


def test_warning_must_be_at_or_above_normal_maximum(client: TestClient):
    current = client.get("/api/settings").json()
    normal_max = current["machines"][0]["temp_max"]
    body = _body(client)
    body["machines"][0]["temp_warning"] = normal_max - 1
    body["machines"][0]["temp_critical"] = normal_max + 20
    response = client.put("/api/settings", json=body)
    assert response.status_code == 422
    assert "normal maximum" in response.json()["detail"]


def test_speed_out_of_range_is_rejected(client: TestClient):
    body = _body(client)
    body["simulation_speed"] = 9
    response = client.put("/api/settings", json=body)
    assert response.status_code == 422


def test_sensor_scenario_is_rejected_during_a_fault(client: TestClient):
    client.post("/api/simulation/scenarios/machine_fault", json={"machine_id": "MCH-D"})
    response = client.post("/api/simulation/scenarios/motor_overload", json={"machine_id": "MCH-D"})
    assert response.status_code == 409
    cleared = client.post("/api/machines/MCH-D/reset")
    assert cleared.status_code == 200
    started = client.post(
        "/api/simulation/scenarios/excessive_vibration",
        json={"machine_id": "MCH-D"},
    )
    assert started.status_code == 200
    assert started.json()["machine"]["active_scenario"] == "excessive_vibration"
