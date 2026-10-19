"""HTTP contract for the monitoring API."""

from fastapi.testclient import TestClient


def test_health_and_demo_machines(client: TestClient):
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["database"] == "sqlite"

    machines = client.get("/api/machines")
    assert machines.status_code == 200
    body = machines.json()
    assert [machine["id"] for machine in body] == ["MCH-A", "MCH-B", "MCH-C", "MCH-D"]
    assert {machine["name"] for machine in body} == {
        "Conveyor System",
        "Packaging Machine",
        "Electric Motor",
        "Inspection Station",
    }
    for machine in body:
        assert machine["status"] in {"RUNNING", "IDLE", "STOPPED", "FAULT"}
        assert "temperature" in machine
        assert "oee" in machine

    missing = client.get("/api/machines/NOPE")
    assert missing.status_code == 404
    docs = client.get("/docs")
    assert docs.status_code == 200


def test_start_stop_reset_and_fault_recovery(client: TestClient):
    before = client.get("/api/machines/MCH-A").json()
    stopped = client.post("/api/machines/MCH-A/stop")
    assert stopped.status_code == 200
    assert stopped.json()["machine"]["status"] == "STOPPED"
    assert stopped.json()["machine"]["stop_count"] == before["stop_count"] + 1

    started = client.post("/api/machines/MCH-A/start")
    assert started.status_code == 200
    assert started.json()["machine"]["status"] == "RUNNING"

    fault = client.post("/api/simulation/scenarios/machine_fault", json={"machine_id": "MCH-A"})
    assert fault.status_code == 200
    assert fault.json()["machine"]["status"] == "FAULT"
    again = client.post("/api/simulation/scenarios/machine_fault", json={"machine_id": "MCH-A"})
    assert again.status_code == 200

    blocked = client.post("/api/machines/MCH-A/start")
    assert blocked.status_code == 409

    alarms = client.get("/api/alarms", params={"machine_id": "MCH-A", "acknowledged": False}).json()
    fault_alarms = [alarm for alarm in alarms if alarm["alarm_type"] == "MACHINE_FAULT" and alarm["active"]]
    assert len(fault_alarms) == 1
    acknowledged = client.post(f"/api/alarms/{fault_alarms[0]['id']}/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["acknowledged"] is True
    assert client.get("/api/machines/MCH-A").json()["status"] == "FAULT"

    reset = client.post("/api/machines/MCH-A/reset")
    assert reset.status_code == 200
    assert reset.json()["machine"]["status"] == "IDLE"
    assert reset.json()["machine"]["active_scenario"] is None
    stored = client.get("/api/alarms", params={"machine_id": "MCH-A"}).json()
    same = next(alarm for alarm in stored if alarm["id"] == fault_alarms[0]["id"])
    assert same["acknowledged"] is True
    assert same["active"] is False

    recovered = client.post("/api/machines/MCH-A/start")
    assert recovered.json()["machine"]["status"] == "RUNNING"


def test_reset_does_not_acknowledge_a_new_fault(client: TestClient):
    client.post("/api/simulation/scenarios/machine_fault", json={"machine_id": "MCH-C"})
    alarms = client.get("/api/alarms", params={"machine_id": "MCH-C", "acknowledged": False}).json()
    fault_alarm = next(alarm for alarm in alarms if alarm["alarm_type"] == "MACHINE_FAULT")
    client.post("/api/machines/MCH-C/reset")
    stored = client.get(f"/api/alarms").json()
    same = next(alarm for alarm in stored if alarm["id"] == fault_alarm["id"])
    assert same["acknowledged"] is False
    assert same["active"] is False
    assert client.get("/api/machines/MCH-C").json()["status"] == "IDLE"


def test_alarm_filters_history_reports_and_exports(client: TestClient):
    critical = client.get("/api/alarms", params={"severity": "CRITICAL", "machine_id": "MCH-B"})
    assert critical.status_code == 200
    assert critical.json()
    assert all(alarm["severity"] == "CRITICAL" and alarm["machine_id"] == "MCH-B" for alarm in critical.json())

    invalid = client.get("/api/alarms", params={"severity": "URGENT"})
    assert invalid.status_code == 422

    history = client.get("/api/machines/MCH-A/history")
    assert history.status_code == 200
    assert len(history.json()["readings"]) > 10
    assert "temperature" in history.json()["readings"][0]
    assert history.json()["status_history"]

    report = client.get("/api/reports/summary")
    assert report.status_code == 200
    body = report.json()
    assert body["simulated"] is True
    assert len(body["machines"]) == 4
    assert body["trends"][0]["points"]
    assert body["machines"][0]["production_count"] > 0

    bad_range = client.get("/api/reports/summary", params={"from": "2026-10-18T00:00:00Z", "to": "2026-10-17T00:00:00Z"})
    assert bad_range.status_code == 422

    alarm_csv = client.get("/api/alarms/export")
    assert alarm_csv.status_code == 200
    assert "text/csv" in alarm_csv.headers["content-type"]
    assert "machine_name" in alarm_csv.text

    production_csv = client.get("/api/production/export")
    assert production_csv.status_code == 200
    assert "oee" in production_csv.text


def test_production_summary_matches_oee_factors(client: TestClient):
    summary = client.get("/api/production/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["simulated"] is True
    assert "verified production" in body["disclaimer"]
    for machine in body["machines"]:
        oee = machine["oee"]
        assert abs(oee["oee"] - (oee["availability"] * oee["performance"] * oee["quality"])) < 1e-9
        assert 0 <= oee["oee"] <= 1


def test_simulation_pause_resume_and_unknown_scenario(client: TestClient):
    paused = client.post("/api/simulation/pause")
    assert paused.status_code == 200
    assert paused.json()["state"] == "paused"
    assert client.get("/api/health").json()["simulation"] == "paused"

    resumed = client.post("/api/simulation/resume")
    assert resumed.status_code == 200
    assert resumed.json()["state"] == "running"

    unknown = client.post("/api/simulation/scenarios/explode", json={"machine_id": "MCH-A"})
    assert unknown.status_code == 404
    missing = client.post("/api/alarms/99999/acknowledge")
    assert missing.status_code == 404
