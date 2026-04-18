import math
import pytest
from straight_physics import (
    time_to_change_speed,
    distance_to_change_speed,
    time_at_constant_speed,
    simulate_straight,
    find_optimal_brake_point,
    is_straight_feasible,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
APPROX = pytest.approx


# ---------------------------------------------------------------------------
# time_to_change_speed
# ---------------------------------------------------------------------------
class TestTimeToChangeSpeed:
    def test_acceleration(self):
        # 0 → 30 m/s at 5 m/s²  →  t = 6 s
        assert time_to_change_speed(0, 30, 5) == APPROX(6.0)

    def test_braking(self):
        # 30 → 10 m/s at 10 m/s²  →  t = (10-30)/10 = -2  (negative = braking)
        assert time_to_change_speed(30, 10, 10) == APPROX(-2.0)

    def test_no_change(self):
        assert time_to_change_speed(20, 20, 5) == APPROX(0.0)


# ---------------------------------------------------------------------------
# distance_to_change_speed
# ---------------------------------------------------------------------------
class TestDistanceToChangeSpeed:
    def test_acceleration(self):
        # 0 → 30 at 5 m/s²  →  d = (900-0)/10 = 90 m
        assert distance_to_change_speed(0, 30, 5) == APPROX(90.0)

    def test_braking(self):
        # 30 → 10 at 10 m/s²  →  d = (100-900)/20 = -40  (negative = braking)
        assert distance_to_change_speed(30, 10, 10) == APPROX(-40.0)

    def test_no_change(self):
        assert distance_to_change_speed(20, 20, 5) == APPROX(0.0)


# ---------------------------------------------------------------------------
# time_at_constant_speed
# ---------------------------------------------------------------------------
class TestTimeAtConstantSpeed:
    def test_basic(self):
        # 200 m at 40 m/s  →  t = 5 s
        assert time_at_constant_speed(200, 40) == APPROX(5.0)

    def test_zero_distance(self):
        assert time_at_constant_speed(0, 30) == APPROX(0.0)


# ---------------------------------------------------------------------------
# simulate_straight — hand-calculated reference case
#
# Setup:
#   entry_v=20, target_v=50, corner_entry_v=10, length=500
#   accel_rate=5, brake_rate=10
#
# Phase 1 (0→50 at 5):  d=(2500-400)/10=210 m,  t=(50-20)/5=6 s
# Phase 3 (50→10 at 10): d=(2500-100)/20=120 m,  t=(50-10)/10=4 s
# Phase 2: cruise_dist=500-210-120=170 m,  t=170/50=3.4 s
# total_time = 6+3.4+4 = 13.4 s,  exit_speed = 10
# ---------------------------------------------------------------------------
ENTRY, TARGET, CORNER, LENGTH, ACCEL, BRAKE = 20, 50, 10, 500, 5, 10


class TestSimulateStraight:
    def test_all_three_phases(self):
        t, v_exit = simulate_straight(ENTRY, TARGET, CORNER, LENGTH, ACCEL, BRAKE)
        assert t == APPROX(13.4)
        assert v_exit == APPROX(10.0)

    def test_exit_speed_always_corner_entry_v(self):
        _, v_exit = simulate_straight(ENTRY, TARGET, CORNER, LENGTH, ACCEL, BRAKE)
        assert v_exit == CORNER

    def test_target_v_below_entry_v_stays_at_entry(self):
        # target_v=15 < entry_v=20  →  car cruises at 20, no acceleration phase
        # Phase 3 (20→10 at 10): d=(400-100)/20=15 m,  t=1 s
        # Phase 2: cruise_dist=100-0-15=85 m, t=85/20=4.25 s
        t, v_exit = simulate_straight(20, 15, 10, 100, 5, 10)
        expected_brake_dist = (20**2 - 10**2) / (2 * 10)   # 15 m
        expected_cruise_dist = 100 - 0 - expected_brake_dist  # 85 m
        expected_t = (expected_cruise_dist / 20) + (20 - 10) / 10
        assert t == APPROX(expected_t)
        assert v_exit == APPROX(10.0)

    def test_short_straight_no_cruise_phase(self):
        # Very short straight: the car cannot reach target_v=50 and still brake
        # entry=20, target=50, corner=10, length=100, accel=5, brake=10
        # accel_dist(20→50)=210, brake_dist(50→10)=120  →  330 > 100, so no cruise
        t, v_exit = simulate_straight(20, 50, 10, 100, 5, 10)
        # Analytical max_v:
        inv_sum = 1 / (2 * 5) + 1 / (2 * 10)           # 0.1 + 0.05 = 0.15
        rhs = 100 + 20**2 / (2*5) + 10**2 / (2*10)      # 100 + 40 + 5 = 145
        max_v = math.sqrt(rhs / inv_sum)
        expected_accel_t = (max_v - 20) / 5
        expected_brake_t = (max_v - 10) / 10
        expected_t = expected_accel_t + expected_brake_t
        assert t == APPROX(expected_t)
        assert v_exit == APPROX(10.0)

    def test_zero_cruise_boundary(self):
        # Straight exactly long enough so cruise_dist == 0
        accel_dist = (50**2 - 20**2) / (2 * 5)   # 210
        brake_dist = (50**2 - 10**2) / (2 * 10)  # 120
        exact_length = accel_dist + brake_dist     # 330
        t, v_exit = simulate_straight(20, 50, 10, exact_length, 5, 10)
        expected_t = (50 - 20) / 5 + (50 - 10) / 10   # 6 + 4 = 10
        assert t == APPROX(expected_t)
        assert v_exit == APPROX(10.0)

    def test_respects_max_speed_clamp(self):
        # Clamping should behave the same as passing a lower target_v.
        t1, v1 = simulate_straight(20, 50, 10, 500, 5, 10, max_speed=40)
        t2, v2 = simulate_straight(20, 40, 10, 500, 5, 10)
        assert t1 == APPROX(t2)
        assert v1 == APPROX(v2)


class TestFindOptimalBrakePoint:
    def test_reference_case(self):
        out = find_optimal_brake_point(ENTRY, TARGET, CORNER, LENGTH, ACCEL, BRAKE)
        assert out["cruise_speed"] == APPROX(50.0)
        assert out["total_time"] == APPROX(13.4)
        assert out["exit_speed"] == APPROX(10.0)
        # brake_dist(50->10 at 10) = 120, so start braking at 500-120 = 380
        assert out["brake_start_m"] == APPROX(380.0)


# ---------------------------------------------------------------------------
# is_straight_feasible
# ---------------------------------------------------------------------------
class TestIsStraightFeasible:
    def test_feasible(self):
        # accel_dist+brake_dist=330, length=500 → feasible
        assert is_straight_feasible(ENTRY, TARGET, CORNER, LENGTH, ACCEL, BRAKE) is True

    def test_not_feasible(self):
        # accel_dist+brake_dist=330, length=200 → not feasible
        assert is_straight_feasible(20, 50, 10, 200, 5, 10) is False

    def test_exact_boundary_is_feasible(self):
        accel_dist = (50**2 - 20**2) / (2 * 5)
        brake_dist = (50**2 - 10**2) / (2 * 10)
        exact_length = accel_dist + brake_dist
        assert is_straight_feasible(20, 50, 10, exact_length, 5, 10) is True

    def test_target_below_entry_uses_entry_as_cruise(self):
        # cruise at entry_v=20, brake to 10: brake_dist=15, length=20 → feasible
        assert is_straight_feasible(20, 10, 10, 20, 5, 10) is True

    def test_target_below_entry_too_short(self):
        # brake_dist(20→10)=15, length=10 → not feasible
        assert is_straight_feasible(20, 10, 10, 10, 5, 10) is False
