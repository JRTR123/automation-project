"""OEE formula, caps, and zero-denominator behavior."""

from app.services.oee import calculate_oee


def test_zero_denominators_are_safe():
    result = calculate_oee(0, 0, 0, 0, 0, 0, 2)
    assert result["availability"] == 0
    assert result["performance"] == 0
    assert result["quality"] == 0
    assert result["oee"] == 0
    assert result["planned_seconds"] == 0
    assert result["downtime_seconds"] == 0


def test_standard_formula():
    result = calculate_oee(
        running_seconds=50,
        idle_seconds=10,
        fault_seconds=10,
        stopped_seconds=0,
        total_count=20,
        good_count=18,
        ideal_cycle_time=2,
    )
    assert result["availability"] == 50 / 70
    assert result["performance"] == 0.8
    assert result["quality"] == 0.9
    assert result["oee"] == (50 / 70) * 0.8 * 0.9
    assert result["downtime_seconds"] == 10


def test_performance_above_ideal_is_capped_in_oee():
    result = calculate_oee(10, 0, 0, 0, 20, 20, 2)
    assert result["performance_raw"] == 4
    assert result["performance"] == 1
    assert result["quality"] == 1
    assert result["oee"] == 1


def test_negative_time_is_treated_as_zero():
    result = calculate_oee(-5, 0, 0, 0, 0, 0, 1)
    assert result["operating_seconds"] == 0
    assert result["oee"] == 0
