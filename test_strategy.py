from Physics import StraightPhysicsEngine
from strategy import LevelOneStrategyBuilder
import math


# ---------------------------------
# Mock models
# ---------------------------------

class MockCar:
    def __init__(self, max_speed: float, crawl_speed: float, accel: float, brake: float):
        self.max_speed = max_speed
        self.crawl_speed = crawl_speed
        self.accel = accel
        self.brake = brake


class MockRace:
    def __init__(self, laps: int, starting_weather_condition_id: int):
        self.laps = laps
        self.starting_weather_condition_id = starting_weather_condition_id


class MockSegment:
    def __init__(self, segment_id: int, segment_type: str, length: float, radius: float = None):
        self.id = segment_id
        self.type = segment_type
        self.length = length
        self.radius = radius


class MockTyreSet:
    def __init__(self, ids: list[int], compound: str):
        self.ids = ids
        self.compound = compound


class MockWeatherCondition:
    def __init__(self, condition_id: int, name: str):
        self.id = condition_id
        self.name = name


class MockRaceData:
    def __init__(self):
        self.car = MockCar(
            max_speed=90.0,
            crawl_speed=10.0,
            accel=10.0,
            brake=20.0,
        )

        self.race = MockRace(
            laps=2,
            starting_weather_condition_id=1,
        )

        self.track_segments = [
            MockSegment(1, "straight", 300.0),
            MockSegment(2, "corner", 100.0, radius=50.0),
            MockSegment(3, "straight", 250.0),
            MockSegment(4, "corner", 90.0, radius=40.0),
        ]

        self.available_tyre_sets = [
            MockTyreSet([1, 2, 3], "Soft"),
            MockTyreSet([4, 5, 6], "Medium"),
            MockTyreSet([7, 8, 9], "Hard"),
        ]

        self.weather_conditions = [
            MockWeatherCondition(1, "dry"),
            MockWeatherCondition(2, "cold"),
        ]

        # Matches the structure expected by strategy.py
        self.tyre_properties = {
            "Soft": {
                "base_friction": 1.8,
                "dry_friction_multiplier": 1.18,
                "cold_friction_multiplier": 1.00,
            },
            "Medium": {
                "base_friction": 1.7,
                "dry_friction_multiplier": 1.08,
                "cold_friction_multiplier": 0.97,
            },
            "Hard": {
                "base_friction": 1.6,
                "dry_friction_multiplier": 0.98,
                "cold_friction_multiplier": 0.92,
            },
        }


# ---------------------------------
# Tiny helpers
# ---------------------------------

def assert_equal(actual, expected, test_name: str) -> None:
    if actual == expected:
        print(f"[PASS] {test_name}: {actual}")
    else:
        print(f"[FAIL] {test_name}: got {actual}, expected {expected}")


def assert_almost_equal(actual, expected, test_name: str, tol: float = 1e-6) -> None:
    if abs(actual - expected) <= tol:
        print(f"[PASS] {test_name}: {actual}")
    else:
        print(f"[FAIL] {test_name}: got {actual}, expected {expected}")


def assert_true(value: bool, test_name: str) -> None:
    if value:
        print(f"[PASS] {test_name}")
    else:
        print(f"[FAIL] {test_name}")


# ---------------------------------
# Tests
# ---------------------------------

def test_get_weather_name(builder: LevelOneStrategyBuilder) -> None:
    print("Testing get_weather_name...")
    assert_equal(builder.get_weather_name(), "dry", "Starting weather name")
    print()


def test_get_tyre_compound_by_id(builder: LevelOneStrategyBuilder) -> None:
    print("Testing get_tyre_compound_by_id...")
    assert_equal(builder.get_tyre_compound_by_id(1), "Soft", "Tyre id 1 compound")
    assert_equal(builder.get_tyre_compound_by_id(5), "Medium", "Tyre id 5 compound")
    assert_equal(builder.get_tyre_compound_by_id(8), "Hard", "Tyre id 8 compound")
    print()


def test_get_tyre_friction(builder: LevelOneStrategyBuilder) -> None:
    print("Testing get_tyre_friction...")
    friction = builder.get_tyre_friction("Soft", "dry")
    expected = 1.8 * 1.18
    assert_almost_equal(friction, expected, "Soft dry friction")
    print()


def test_compute_safe_corner_speed(builder: LevelOneStrategyBuilder) -> None:
    print("Testing compute_safe_corner_speed...")
    tyre_friction = 1.8 * 1.18
    speed = builder.compute_safe_corner_speed(radius_m=50.0, tyre_friction=tyre_friction)
    assert_true(speed > 0, "Safe corner speed positive")
    print()


def test_choose_initial_tyre(builder: LevelOneStrategyBuilder) -> None:
    print("Testing choose_initial_tyre...")
    chosen = builder.choose_initial_tyre()
    # Soft should win in dry with given mock values
    assert_equal(chosen, 1, "Initial tyre choice")
    print()


def test_precompute_corner_speeds(builder: LevelOneStrategyBuilder) -> None:
    print("Testing precompute_corner_speeds...")
    corner_speeds = builder.precompute_corner_speeds(1)

    assert_true(2 in corner_speeds, "Corner speed exists for segment 2")
    assert_true(4 in corner_speeds, "Corner speed exists for segment 4")
    assert_true(corner_speeds[2] > 0, "Corner 2 speed positive")
    assert_true(corner_speeds[4] > 0, "Corner 4 speed positive")
    print()


def test_generate_target_speed_candidates(builder: LevelOneStrategyBuilder) -> None:
    print("Testing generate_target_speed_candidates...")
    result = builder.generate_target_speed_candidates(entry_speed=20.0, step=10.0)
    expected = [90.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0]
    assert_equal(result, expected, "Target speed candidates")
    print()


def test_find_next_corner_speed_requirement(builder: LevelOneStrategyBuilder) -> None:
    print("Testing find_next_corner_speed_requirement...")
    corner_speeds = builder.precompute_corner_speeds(1)
    req = builder.find_next_corner_speed_requirement(0, corner_speeds)
    assert_almost_equal(req, corner_speeds[2], "Next corner speed requirement")
    print()


def test_choose_best_target_speed(builder: LevelOneStrategyBuilder) -> None:
    print("Testing choose_best_target_speed...")
    corner_speeds = builder.precompute_corner_speeds(1)
    exit_speed_required = builder.find_next_corner_speed_requirement(0, corner_speeds)
    straight_segment = builder.race_data.track_segments[0]

    result = builder.choose_best_target_speed(
        entry_speed=0.0,
        exit_speed_required=exit_speed_required,
        straight_segment=straight_segment,
        step=10.0,
    )

    assert_true(result["feasible"], "Chosen straight plan feasible")
    assert_true("chosen_target_mps" in result, "Chosen target included")
    assert_true("brake_start_m_before_next" in result, "Brake distance included")
    print()


def test_build_straight_output(builder: LevelOneStrategyBuilder) -> None:
    print("Testing build_straight_output...")
    output = builder.build_straight_output(1, 70.0, 120.0)

    assert_equal(output["id"], 1, "Straight output id")
    assert_equal(output["type"], "straight", "Straight output type")
    assert_equal(output["target_m/s"], 70.0, "Straight output target")
    assert_equal(output["brake_start_m_before_next"], 120.0, "Straight output brake")
    print()


def test_build_corner_output(builder: LevelOneStrategyBuilder) -> None:
    print("Testing build_corner_output...")
    output = builder.build_corner_output(2)

    assert_equal(output["id"], 2, "Corner output id")
    assert_equal(output["type"], "corner", "Corner output type")
    print()


def test_simulate_one_lap(builder: LevelOneStrategyBuilder) -> None:
    print("Testing simulate_one_lap...")
    corner_speeds = builder.precompute_corner_speeds(1)

    lap_result = builder.simulate_one_lap(
        lap_number=1,
        starting_speed=0.0,
        corner_speeds=corner_speeds,
    )

    assert_equal(lap_result["lap_number"], 1, "Lap number")
    assert_true(lap_result["lap_time_s"] > 0, "Lap time positive")
    assert_true(len(lap_result["segments"]) == 4, "All segments included")
    print()


def test_build_strategy(builder: LevelOneStrategyBuilder) -> None:
    print("Testing build_strategy...")
    strategy = builder.build_strategy()

    assert_true("initial_tyre_id" in strategy, "Strategy has initial tyre")
    assert_true("laps" in strategy, "Strategy has laps")
    assert_true(len(strategy["laps"]) == 2, "Correct number of laps")
    assert_true(strategy["laps"][0]["pit"]["enter"] is False, "Level 1 no pit")
    assert_true("_meta" in strategy, "Debug meta included")
    print()


def test_strip_debug_meta(builder: LevelOneStrategyBuilder) -> None:
    print("Testing strip_debug_meta...")
    strategy = builder.build_strategy()
    clean = builder.strip_debug_meta(strategy)

    assert_true("_meta" not in clean, "Debug meta removed")
    assert_true("initial_tyre_id" in clean, "Submission still has tyre id")
    print()


# ---------------------------------
# Main
# ---------------------------------

def main() -> None:
    race_data = MockRaceData()

    physics_engine = StraightPhysicsEngine(
        accel_mps2=race_data.car.accel,
        brake_mps2=race_data.car.brake,
        max_speed_mps=race_data.car.max_speed,
        min_speed_mps=0.0,
    )

    builder = LevelOneStrategyBuilder(race_data, physics_engine)

    test_get_weather_name(builder)
    test_get_tyre_compound_by_id(builder)
    test_get_tyre_friction(builder)
    test_compute_safe_corner_speed(builder)
    test_choose_initial_tyre(builder)
    test_precompute_corner_speeds(builder)
    test_generate_target_speed_candidates(builder)
    test_find_next_corner_speed_requirement(builder)
    test_choose_best_target_speed(builder)
    test_build_straight_output(builder)
    test_build_corner_output(builder)
    test_simulate_one_lap(builder)
    test_build_strategy(builder)
    test_strip_debug_meta(builder)


if __name__ == "__main__":
    main()