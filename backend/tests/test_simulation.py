"""Simulation ticks, scenarios, and the single background loop."""

from sqlalchemy import select

from app.models.entities import Alarm, Machine
from app.services.simulator import engine


def test_running_machine_produces_and_updates(db_session):
    machine = db_session.get(Machine, "MCH-A")
    assert machine is not None
    before_count = machine.production_count
    before_update = machine.last_update
    db_session.commit()

    assert engine.tick(5, force=True) is True

    db_session.expire_all()
    machine = db_session.get(Machine, "MCH-A")
    assert machine is not None
    assert machine.production_count > before_count
    assert machine.good_count + machine.defect_count == machine.production_count
    assert machine.last_update >= before_update
    assert machine.running_seconds > 0


def test_idle_machine_does_not_produce(db_session):
    machine = db_session.get(Machine, "MCH-B")
    assert machine is not None
    machine.status = "IDLE"
    machine.active_scenario = "idle"
    before_count = machine.production_count
    before_idle = machine.idle_seconds
    db_session.commit()

    engine.tick(10, force=True)

    db_session.expire_all()
    machine = db_session.get(Machine, "MCH-B")
    assert machine is not None
    assert machine.production_count == before_count
    assert machine.idle_seconds == before_idle + 10


def test_high_temperature_scenario_rises_and_alarms_once(db_session):
    machine = db_session.get(Machine, "MCH-A")
    assert machine is not None
    machine.status = "RUNNING"
    machine.active_scenario = "high_temperature"
    machine.temperature = machine.temp_warning + 1
    db_session.commit()

    engine.tick(2.5, force=True)
    engine.tick(2.5, force=True)

    db_session.expire_all()
    machine = db_session.get(Machine, "MCH-A")
    assert machine is not None
    assert machine.temperature > machine.temp_warning
    alarms = list(
        db_session.scalars(
            select(Alarm).where(
                Alarm.machine_id == "MCH-A",
                Alarm.alarm_type == "HIGH_TEMPERATURE",
                Alarm.active.is_(True),
            )
        ).all()
    )
    assert len(alarms) == 1


def test_paused_tick_does_not_apply(db_session):
    machine = db_session.get(Machine, "MCH-D")
    assert machine is not None
    before = machine.production_count
    db_session.commit()
    engine._paused = True
    assert engine.tick(5, force=False) is False
    db_session.expire_all()
    machine = db_session.get(Machine, "MCH-D")
    assert machine is not None
    assert machine.production_count == before
    engine._paused = False


def test_only_one_simulator_thread_is_started(db_session):
    assert db_session.get(Machine, "MCH-A") is not None
    engine.start()
    first = engine._thread
    engine.start()
    assert engine._thread is first
    assert first is not None and first.is_alive()
    engine.shutdown()
    assert engine.state() == "stopped"
    engine.start()
    assert engine._thread is not first
    assert engine.state() == "running"
    engine.shutdown()
