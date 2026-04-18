from Physics import StraightPhysicsEngine
from strategy import LevelOneStrategyBuilder
import json


# ---------------------------------
# Mock models (copied from test_strategy.py)
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
# Main execution
# ---------------------------------

def main():
    # Create mock race data
    race_data = MockRaceData()

    # Create physics engine
    physics_engine = StraightPhysicsEngine(
        max_speed_mps=race_data.car.max_speed,
        accel_mps2=race_data.car.accel,
        brake_mps2=race_data.car.brake,
        min_speed_mps=race_data.car.crawl_speed,
    )

    # Create strategy builder
    builder = LevelOneStrategyBuilder(race_data, physics_engine)

    # Build the strategy
    strategy = builder.build_strategy()

    # Strip debug meta for submission
    clean_strategy = builder.strip_debug_meta(strategy)

    # Output as JSON
    print(json.dumps(clean_strategy, indent=2))


if __name__ == "__main__":
    main()