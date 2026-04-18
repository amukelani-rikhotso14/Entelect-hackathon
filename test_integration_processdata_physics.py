import math
from pathlib import Path

import pytest

from ProcessData import GameData
from straight_physics import find_optimal_brake_point, simulate_straight


APPROX = pytest.approx


def _fixture_path() -> Path:
    return Path(__file__).with_name("1.txt")


class TestProcessDataLoads:
    def test_can_load_example_json(self):
        gd = GameData.from_file(str(_fixture_path()))
        assert gd.race.name
        assert isinstance(gd.race.laps, int)
        assert gd.car.max_speed_m_s > 0
        assert gd.car.accel_m_s2 > 0
        assert gd.car.brake_m_s2 > 0
        assert len(gd.track.segments) > 0


class TestStraightPhysicsIntegration:
    def test_straight_time_uses_parsed_car_rates(self):
        gd = GameData.from_file(str(_fixture_path()))

        # Use the first straight in the sample track.
        straight = next(s for s in gd.track.segments if s.type == "straight")
        length = straight.length_m

        entry_v = gd.race.pit_exit_speed_m_s
        corner_entry_v = gd.race.pit_exit_speed_m_s  # placeholder: corner model not implemented yet

        # Ask for an unrealistically high target speed, but clamp it to the car max.
        t, v_exit = simulate_straight(
            entry_v=entry_v,
            target_v=1e9,
            corner_entry_v=corner_entry_v,
            length=length,
            accel_rate=gd.car.accel_m_s2,
            brake_rate=gd.car.brake_m_s2,
            max_speed=gd.car.max_speed_m_s,
        )

        assert t >= 0
        assert v_exit == APPROX(corner_entry_v)

    def test_find_optimal_brake_point_output_is_sane(self):
        gd = GameData.from_file(str(_fixture_path()))
        straight = next(s for s in gd.track.segments if s.type == "straight")
        length = straight.length_m

        entry_v = gd.race.pit_exit_speed_m_s
        corner_entry_v = gd.race.pit_exit_speed_m_s  # placeholder: corner model not implemented yet

        out = find_optimal_brake_point(
            entry_v=entry_v,
            target_v=gd.car.max_speed_m_s,
            corner_entry_v=corner_entry_v,
            length=length,
            accel_rate=gd.car.accel_m_s2,
            brake_rate=gd.car.brake_m_s2,
            max_speed=gd.car.max_speed_m_s,
        )

        assert set(out.keys()) == {"brake_start_m", "cruise_speed", "total_time", "exit_speed"}
        assert 0.0 <= out["brake_start_m"] <= length
        assert 0.0 < out["cruise_speed"] <= gd.car.max_speed_m_s
        assert out["total_time"] >= 0.0
        assert out["exit_speed"] == APPROX(corner_entry_v)

    def test_brake_start_matches_brake_distance_geometry(self):
        gd = GameData.from_file(str(_fixture_path()))
        straight = next(s for s in gd.track.segments if s.type == "straight")
        length = straight.length_m

        entry_v = 20.0
        corner_entry_v = 10.0
        accel_rate = gd.car.accel_m_s2
        brake_rate = gd.car.brake_m_s2
        max_speed = gd.car.max_speed_m_s

        out = find_optimal_brake_point(
            entry_v=entry_v,
            target_v=max_speed,
            corner_entry_v=corner_entry_v,
            length=length,
            accel_rate=accel_rate,
            brake_rate=brake_rate,
            max_speed=max_speed,
        )

        # If cruise_speed is the peak speed, the braking distance should be:
        # d = (v^2 - v_corner^2) / (2*brake_rate), and brake starts at length - d.
        v_peak = out["cruise_speed"]
        brake_dist = (v_peak**2 - corner_entry_v**2) / (2 * brake_rate)
        expected_start = max(0.0, length - brake_dist)
        assert out["brake_start_m"] == APPROX(expected_start, rel=1e-7, abs=1e-7)

