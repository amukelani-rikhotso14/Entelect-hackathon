from Physics import StraightPhysicsEngine


def assert_almost_equal(actual, expected, test_name: str, tol=1e-6) -> None:
    if abs(actual - expected) <= tol:
        print(f"[PASS] {test_name}: {actual}")
    else:
        print(f"[FAIL] {test_name}: got {actual}, expected {expected}")


def test_clamp_speed(engine: StraightPhysicsEngine) -> None:
    print("Testing clamp_speed...")

    assert_almost_equal(engine.clamp_speed(120), 90, "Clamp above max speed")
    assert_almost_equal(engine.clamp_speed(-5), 0.0, "Clamp below min speed")
    assert_almost_equal(engine.clamp_speed(70), 70, "Clamp valid speed")

    print()


def test_time_to_change_speed(engine: StraightPhysicsEngine) -> None:
    print("Testing time_to_change_speed...")

    assert_almost_equal(
        engine.time_to_change_speed(20, 60, 10),
        4.0,
        "Acceleration time"
    )

    assert_almost_equal(
        engine.time_to_change_speed(60, 20, 20),
        2.0,
        "Braking time"
    )

    assert_almost_equal(
        engine.time_to_change_speed(50, 50, 10),
        0.0,
        "No speed change"
    )

    print()


def test_time_invalid_rate(engine: StraightPhysicsEngine) -> None:
    print("Testing invalid rate handling...")

    try:
        engine.time_to_change_speed(20, 60, 0)
        print("[FAIL] Did not raise error for zero rate")
    except ValueError:
        print("[PASS] Correctly raised error for zero rate")

    print()


def test_distance_to_change_speed(engine: StraightPhysicsEngine) -> None:
    print("Testing distance_to_change_speed...")

    assert_almost_equal(
        engine.distance_to_change_speed(20, 60, 10),
        160.0,
        "Acceleration distance"
    )

    assert_almost_equal(
        engine.distance_to_change_speed(60, 20, 20),
        80.0,
        "Braking distance"
    )

    assert_almost_equal(
        engine.distance_to_change_speed(50, 50, 10),
        0.0,
        "No speed change distance"
    )

    print()


def test_distance_invalid_rate(engine: StraightPhysicsEngine) -> None:
    print("Testing invalid distance rate handling...")

    try:
        engine.distance_to_change_speed(20, 60, 0)
        print("[FAIL] Did not raise error for zero rate in distance")
    except ValueError:
        print("[PASS] Correctly raised error for zero rate in distance")

    print()

def test_compute_accel_phase(engine: StraightPhysicsEngine) -> None:
    print("Testing compute_accel_phase...")

    result = engine.compute_accel_phase(20, 60)

    assert_almost_equal(result["distance_m"], 160.0, "Accel phase distance")
    assert_almost_equal(result["time_s"], 4.0, "Accel phase time")

    no_accel_result = engine.compute_accel_phase(60, 20)
    assert_almost_equal(no_accel_result["distance_m"], 0.0, "No accel distance when peak <= entry")
    assert_almost_equal(no_accel_result["time_s"], 0.0, "No accel time when peak <= entry")

    same_speed_result = engine.compute_accel_phase(50, 50)
    assert_almost_equal(same_speed_result["distance_m"], 0.0, "No accel distance when speeds equal")
    assert_almost_equal(same_speed_result["time_s"], 0.0, "No accel time when speeds equal")

    print()

def test_compute_cruise_phase(engine: StraightPhysicsEngine) -> None:
    print("Testing compute_cruise_phase...")

    result = engine.compute_cruise_phase(100, 50)
    assert_almost_equal(result["distance_m"], 100.0, "Cruise phase distance")
    assert_almost_equal(result["time_s"], 2.0, "Cruise phase time")

    zero_distance_result = engine.compute_cruise_phase(0, 50)
    assert_almost_equal(zero_distance_result["distance_m"], 0.0, "Zero cruise distance")
    assert_almost_equal(zero_distance_result["time_s"], 0.0, "Zero cruise time")

    print()
def test_compute_cruise_phase_invalid_speed(engine: StraightPhysicsEngine) -> None:
    print("Testing invalid cruise speed handling...")

    try:
        engine.compute_cruise_phase(100, 0)
        print("[FAIL] Did not raise error for zero cruise speed")
    except ValueError:
        print("[PASS] Correctly raised error for zero cruise speed")

    print()
def test_simulate_straight_with_cruise(engine: StraightPhysicsEngine) -> None:
    print("Testing simulate_straight with reachable target and cruise...")

    result = engine.simulate_straight(
        entry_speed=20,
        target_speed=60,
        exit_speed_required=20,
        length_m=300,
    )

    if result["feasible"]:
        print("[PASS] Straight correctly marked feasible")
    else:
        print("[FAIL] Straight incorrectly marked infeasible")

    assert_almost_equal(result["peak_speed_mps"], 60.0, "Reachable target peak speed")
    assert_almost_equal(result["distance_accel_m"], 160.0, "Straight accel distance")
    assert_almost_equal(result["distance_brake_m"], 80.0, "Straight brake distance")
    assert_almost_equal(result["distance_cruise_m"], 60.0, "Straight cruise distance")
    assert_almost_equal(result["brake_start_m_before_next"], 80.0, "Brake start before next")

    print()



def main() -> None:
    engine = StraightPhysicsEngine(
        accel_mps2=10,
        brake_mps2=20,
        max_speed_mps=90,
        min_speed_mps=0.0,
    )

    test_clamp_speed(engine)
    test_time_to_change_speed(engine)
    test_time_invalid_rate(engine)
    test_distance_to_change_speed(engine)
    test_distance_invalid_rate(engine)
    test_compute_accel_phase(engine)
    test_compute_cruise_phase(engine)
    test_compute_cruise_phase_invalid_speed(engine)
    test_simulate_straight_with_cruise(engine)


if __name__ == "__main__":
    main()