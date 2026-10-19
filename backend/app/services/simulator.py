"""Background simulator. One thread updates every machine on a fixed tick."""

from __future__ import annotations

import logging
import random
import threading
import time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.timeutil import now_ts
from app.database import get_session
from app.models.entities import Machine, MetricSample
from app.services import alarms, machines
from app.services.catalog import BASE_TICK_SECONDS, SCENARIO_NAMES

logger = logging.getLogger(__name__)

_SENSOR_SCENARIOS = {"high_temperature", "excessive_vibration", "motor_overload"}


class SimulationEngine:
    def __init__(self) -> None:
        self.write_lock = threading.Lock()
        self._life_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._paused = False
        self._rng = random.Random()
        self._ticks = 0

    def reset_runtime(self) -> None:
        self.shutdown()
        self._paused = False
        self._stop = threading.Event()
        self._ticks = 0

    def state(self) -> str:
        thread = self._thread
        if thread is None or not thread.is_alive():
            return "stopped"
        if self._paused:
            return "paused"
        return "running"

    def ensure_background(self) -> None:
        with self._life_lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._paused = self._read_paused()
            self._stop = threading.Event()
            self._thread = threading.Thread(target=self._loop, name="machine-simulator", daemon=True)
            self._thread.start()

    def start(self) -> str:
        already = self.state() == "running"
        self._set_paused(False)
        self.ensure_background()
        if already:
            return "Simulation is already running."
        return "Simulation started."

    def pause(self) -> str:
        already = self.state() == "paused"
        self._set_paused(True)
        self.ensure_background()
        if already:
            return "Simulation is already paused."
        return "Simulation paused. Sensor values and production counters will hold until resume."

    def resume(self) -> str:
        already = self.state() == "running"
        self._set_paused(False)
        self.ensure_background()
        if already:
            return "Simulation is already running."
        return "Simulation resumed."

    def shutdown(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=3)
        self._thread = None

    def tick(self, sim_dt: float = BASE_TICK_SECONDS, force: bool = False) -> bool:
        if self._paused and not force:
            return False
        with self.write_lock:
            db = get_session()
            try:
                self._tick_locked(db, sim_dt)
                db.commit()
                return True
            except Exception:
                db.rollback()
                logger.exception("Simulation tick failed")
                raise
            finally:
                db.close()

    def trigger(self, db: Session, scenario_name: str, machine_id: str) -> tuple[str, Machine]:
        if scenario_name not in SCENARIO_NAMES:
            known = ", ".join(SCENARIO_NAMES)
            raise AppError(f"Unknown scenario '{scenario_name}'. Choose one of: {known}.", 404)
        machine = machines.get_machine(db, machine_id)
        if scenario_name == "clear":
            machine.active_scenario = None
            return f"Cleared the active scenario on {machine.name}. A fault still requires Reset.", machine
        if scenario_name == "machine_fault":
            machine.active_scenario = "machine_fault"
            if machine.status != "FAULT":
                machines.set_status(db, machine, "FAULT", "Simulated machine fault was triggered.")
            alarms.ensure_fault_alarm(db, machine)
            return f"{machine.name} is in FAULT. Acknowledge the alarm, then reset the machine to recover.", machine
        if machine.status == "FAULT":
            raise AppError("Machine is in fault. Reset it before triggering another scenario.", 409)
        if scenario_name == "idle":
            machine.active_scenario = "idle"
            machines.set_status(db, machine, "IDLE", "Simulated idle operation was triggered.")
            return f"{machine.name} is idle. It stays available but does not produce items.", machine
        if machine.status != "RUNNING":
            machines.set_status(db, machine, "RUNNING", f"Started {machine.name} for the {scenario_name} scenario.")
        machine.active_scenario = scenario_name
        labels = {
            "high_temperature": "high temperature",
            "excessive_vibration": "excessive vibration",
            "motor_overload": "motor overload",
        }
        return (
            f"{labels[scenario_name].capitalize()} scenario started on {machine.name}. "
            "Readings will rise above the configured threshold.",
            machine,
        )

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self._paused:
                if self._stop.wait(0.25):
                    break
                continue
            speed = self._read_speed()
            interval = machines.tick_interval(speed)
            started = time.monotonic()
            try:
                self.tick(BASE_TICK_SECONDS, force=False)
            except Exception:
                logger.exception("Simulator loop recovered from a tick error")
            elapsed = time.monotonic() - started
            remaining = interval - elapsed
            if remaining > 0 and self._stop.wait(remaining):
                break

    def _tick_locked(self, db: Session, sim_dt: float) -> None:
        moment = now_ts()
        rows = list(db.scalars(select(Machine).order_by(Machine.id)).all())
        for machine in rows:
            self._apply_dynamics(machine)
            produced, good, defect = self._account(machine, sim_dt)
            alarms.evaluate_sensor_alarms(db, machine, moment)
            if machine.status == "FAULT":
                alarms.ensure_fault_alarm(db, machine, moment)
            machine.last_update = moment
            db.add(
                MetricSample(
                    machine_id=machine.id,
                    timestamp=moment,
                    status=machine.status,
                    temperature=machine.temperature,
                    vibration=machine.vibration,
                    motor_current=machine.motor_current,
                    dt_seconds=sim_dt,
                    total_delta=produced,
                    good_delta=good,
                    defect_delta=defect,
                )
            )
        self._ticks += 1
        if self._ticks % 25 == 0:
            self._prune(db)

    def _apply_dynamics(self, machine: Machine) -> None:
        scenario = machine.active_scenario
        if machine.status == "FAULT" or scenario == "machine_fault":
            machine.motor_current = self._move_toward(machine.motor_current, 0.1, 0.45)
            machine.vibration = self._move_toward(machine.vibration, 0.15, 0.2)
            machine.temperature = self._move_toward(machine.temperature, 30.0, 0.35)
            return
        if machine.status == "STOPPED":
            machine.temperature = self._move_toward(machine.temperature, 27.0, 0.6)
            machine.vibration = self._move_toward(machine.vibration, 0.05, 0.25)
            machine.motor_current = self._move_toward(machine.motor_current, 0.05, 0.6)
            return
        if machine.status == "IDLE" or scenario == "idle":
            temp_high = machine.temp_min + 0.35 * (machine.temp_max - machine.temp_min)
            vib_high = machine.vib_min + 0.35 * (machine.vib_max - machine.vib_min)
            machine.temperature = self._wander(machine.temperature, machine.temp_min, temp_high)
            machine.vibration = self._wander(machine.vibration, machine.vib_min, vib_high)
            machine.motor_current = self._wander(machine.motor_current, machine.current_min * 0.25, machine.current_min)
            return
        if scenario == "high_temperature":
            machine.temperature = self._rise(machine.temperature, machine.temp_critical + 1.5)
            machine.vibration = self._wander(machine.vibration, machine.vib_min, machine.vib_max)
            machine.motor_current = self._wander(machine.motor_current, machine.current_min, machine.current_max)
            return
        if scenario == "excessive_vibration":
            machine.temperature = self._wander(machine.temperature, machine.temp_min, machine.temp_max)
            machine.vibration = self._rise(machine.vibration, machine.vib_critical + 0.3)
            machine.motor_current = self._wander(machine.motor_current, machine.current_min, machine.current_max)
            return
        if scenario == "motor_overload":
            machine.temperature = self._wander(machine.temperature, machine.temp_min, machine.temp_max)
            machine.vibration = self._wander(machine.vibration, machine.vib_min, machine.vib_max)
            machine.motor_current = self._rise(machine.motor_current, machine.current_critical + 0.6)
            return
        if scenario in _SENSOR_SCENARIOS:
            return
        machine.temperature = self._wander(machine.temperature, machine.temp_min, machine.temp_max)
        machine.vibration = self._wander(machine.vibration, machine.vib_min, machine.vib_max)
        machine.motor_current = self._wander(machine.motor_current, machine.current_min, machine.current_max)

    def _account(self, machine: Machine, sim_dt: float) -> tuple[int, int, int]:
        produced = good = defect = 0
        if machine.status == "RUNNING":
            machine.running_seconds += sim_dt
            machine.cycle_accumulator += sim_dt
            while machine.cycle_accumulator >= machine.ideal_cycle_time:
                machine.cycle_accumulator -= machine.ideal_cycle_time
                produced += 1
                if self._rng.random() < machine.defect_rate:
                    defect += 1
                else:
                    good += 1
            machine.production_count += produced
            machine.good_count += good
            machine.defect_count += defect
        elif machine.status == "IDLE":
            machine.idle_seconds += sim_dt
        elif machine.status == "FAULT":
            machine.fault_seconds += sim_dt
        elif machine.status == "STOPPED":
            machine.stopped_seconds += sim_dt
        return produced, good, defect

    def _wander(self, value: float, low: float, high: float) -> float:
        if high <= low:
            return low
        span = high - low
        mid = (low + high) / 2
        step = self._rng.uniform(-0.08, 0.08) * span
        updated = value + step + (mid - value) * 0.08
        floor = low - 0.02 * span
        ceiling = high + 0.02 * span
        return max(floor, min(ceiling, updated))

    def _rise(self, value: float, target: float) -> float:
        gap = target - value
        if gap <= 0:
            return target + self._rng.uniform(-0.15, 0.15)
        return value + max(abs(target) * 0.04, gap * 0.45)

    def _move_toward(self, value: float, target: float, portion: float) -> float:
        updated = value + (target - value) * portion
        return max(0.0, updated)

    def _prune(self, db: Session) -> None:
        machine_ids = list(db.scalars(select(Machine.id)).all())
        for machine_id in machine_ids:
            cutoff = db.scalar(
                select(MetricSample.timestamp)
                .where(MetricSample.machine_id == machine_id)
                .order_by(MetricSample.timestamp.desc())
                .offset(1200)
                .limit(1)
            )
            if cutoff is not None:
                db.execute(
                    delete(MetricSample).where(
                        MetricSample.machine_id == machine_id,
                        MetricSample.timestamp < cutoff,
                    )
                )

    def _read_paused(self) -> bool:
        db = get_session()
        try:
            row = machines.get_settings_row(db)
            db.commit()
            return bool(row.paused)
        finally:
            db.close()

    def _read_speed(self) -> float:
        db = get_session()
        try:
            row = machines.get_settings_row(db)
            return float(row.simulation_speed)
        finally:
            db.close()

    def _set_paused(self, paused: bool) -> None:
        self._paused = paused
        with self.write_lock:
            db = get_session()
            try:
                row = machines.get_settings_row(db)
                row.paused = paused
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()


engine = SimulationEngine()
