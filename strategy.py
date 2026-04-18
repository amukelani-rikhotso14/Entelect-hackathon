import math


class LevelOneStrategyBuilder:
    def __init__(self, race_data, physics_engine):
        self.race_data = race_data
        self.physics_engine = physics_engine

    # ---------------------------
    # Weather + tyre helpers
    # ---------------------------

    def get_weather_name(self) -> str:
        """
        Returns the starting weather name for Level 1.
        Falls back to 'dry' if not found.
        """
        start_id = self.race_data.race.starting_weather_condition_id

        for condition in self.race_data.weather_conditions:
            if condition.id == start_id:
                return condition.name

        return "dry"

    def get_tyre_compound_by_id(self, tyre_id: int) -> str:
        """
        Finds the tyre compound name from a tyre id.
        """
        for tyre_set in self.race_data.available_tyre_sets:
            if tyre_id in tyre_set.ids:
                return tyre_set.compound

        raise ValueError(f"Tyre id {tyre_id} not found.")

    def get_tyre_friction(self, tyre_compound: str, weather_name: str) -> float:
        """
        Returns tyre friction for Level 1.

        Assumes tyre_properties is shaped like:
        {
            "Soft": {
                "base_friction": 1.8,
                "dry_friction_multiplier": 1.18,
                ...
            }
        }
        """
        props = self.race_data.tyre_properties[tyre_compound]
        base_friction = props["base_friction"]
        multiplier_key = f"{weather_name}_friction_multiplier"

        if multiplier_key not in props:
            raise ValueError(f"Missing friction multiplier '{multiplier_key}' for {tyre_compound}")

        return base_friction * props[multiplier_key]

    def compute_safe_corner_speed(self, radius_m: float, tyre_friction: float) -> float:
        """
        Computes the max safe corner speed using the problem formula:
        sqrt(tyre_friction * gravity * radius) + crawl_constant
        """
        gravity = 9.8
        crawl_constant = self.race_data.car.crawl_speed

        return math.sqrt(tyre_friction * gravity * radius_m) + crawl_constant

    def compute_corner_time(self, length_m: float, corner_speed_mps: float) -> float:
        """
        Time through a corner at constant speed.
        """
        if corner_speed_mps <= 0:
            raise ValueError("Corner speed must be greater than 0.")

        return length_m / corner_speed_mps

    def choose_initial_tyre(self) -> int:
        """
        For Level 1, choose the tyre with the best friction
        for the starting weather.
        """
        weather_name = self.get_weather_name()

        best_tyre_id = None
        best_friction = -1.0

        for tyre_set in self.race_data.available_tyre_sets:
            compound = tyre_set.compound
            friction = self.get_tyre_friction(compound, weather_name)

            if friction > best_friction:
                best_friction = friction
                best_tyre_id = tyre_set.ids[0]

        if best_tyre_id is None:
            raise ValueError("No tyre sets available.")

        return best_tyre_id

    def precompute_corner_speeds(self, tyre_id: int) -> dict:
        """
        Precomputes safe corner speeds for all corners on the track.
        Returns: {segment_id: safe_speed}
        """
        weather_name = self.get_weather_name()
        tyre_compound = self.get_tyre_compound_by_id(tyre_id)
        tyre_friction = self.get_tyre_friction(tyre_compound, weather_name)

        corner_speeds = {}

        for segment in self.race_data.track_segments:
            if segment.type == "corner":
                corner_speeds[segment.id] = self.compute_safe_corner_speed(
                    radius_m=segment.radius,
                    tyre_friction=tyre_friction,
                )

        return corner_speeds

    # ---------------------------
    # Straight strategy helpers
    # ---------------------------

    def find_next_corner_speed_requirement(self, current_index: int, corner_speeds: dict) -> float:
        """
        For a straight at track_segments[current_index],
        return the safe speed required for the next corner.
        """
        next_segment = self.race_data.track_segments[current_index + 1]

        if next_segment.type != "corner":
            raise ValueError("Expected next segment after straight to be a corner.")

        return corner_speeds[next_segment.id]

    def generate_target_speed_candidates(self, entry_speed: float, step: float = 5.0) -> list[float]:
        """
        Generates target speed candidates from high to low.
        """
        if step <= 0:
            raise ValueError("Step must be greater than 0.")

        max_speed = self.race_data.car.max_speed
        entry_speed = self.physics_engine.clamp_speed(entry_speed)

        candidates = []
        current_speed = max_speed

        while current_speed >= entry_speed:
            candidates.append(float(current_speed))
            current_speed -= step

        if not candidates or abs(candidates[-1] - entry_speed) > 1e-6:
            candidates.append(float(entry_speed))

        return candidates

    def choose_best_target_speed(
        self,
        entry_speed: float,
        exit_speed_required: float,
        straight_segment,
        step: float = 5.0,
    ) -> dict:
        """
        Chooses the first feasible target speed from fastest to slower.
        Returns the full straight simulation result plus chosen target.
        """
        candidates = self.generate_target_speed_candidates(entry_speed, step=step)

        best_result = None

        for target_speed in candidates:
            result = self.physics_engine.simulate_straight(
                entry_speed=entry_speed,
                target_speed=target_speed,
                exit_speed_required=exit_speed_required,
                length_m=straight_segment.length,
            )

            if result["feasible"]:
                best_result = result
                best_result["chosen_target_mps"] = target_speed
                return best_result

        raise ValueError(f"No feasible target speed found for straight segment {straight_segment.id}")

    # ---------------------------
    # Output helpers
    # ---------------------------

    def build_straight_output(self, segment_id: int, target_mps: float, brake_distance: float) -> dict:
        """
        Builds one straight segment output entry.
        """
        return {
            "id": segment_id,
            "type": "straight",
            "target_m/s": round(target_mps, 3),
            "brake_start_m_before_next": round(brake_distance, 3),
        }

    def build_corner_output(self, segment_id: int) -> dict:
        """
        Builds one corner segment output entry.
        """
        return {
            "id": segment_id,
            "type": "corner",
        }

    # ---------------------------
    # Lap + race simulation
    # ---------------------------

    def simulate_one_lap(self, lap_number: int, starting_speed: float, corner_speeds: dict) -> dict:
        """
        Simulates one lap and returns:
        - lap number
        - lap time
        - ending speed
        - segment outputs
        """
        current_speed = starting_speed
        lap_time_s = 0.0
        segment_outputs = []

        segments = self.race_data.track_segments

        for index, segment in enumerate(segments):
            if segment.type == "straight":
                exit_speed_required = self.find_next_corner_speed_requirement(index, corner_speeds)

                straight_result = self.choose_best_target_speed(
                    entry_speed=current_speed,
                    exit_speed_required=exit_speed_required,
                    straight_segment=segment,
                )

                lap_time_s += straight_result["time_s"]
                current_speed = straight_result["end_speed_mps"]

                segment_outputs.append(
                    self.build_straight_output(
                        segment_id=segment.id,
                        target_mps=straight_result["chosen_target_mps"],
                        brake_distance=straight_result["brake_start_m_before_next"],
                    )
                )

            elif segment.type == "corner":
                corner_speed = corner_speeds[segment.id]
                corner_time = self.compute_corner_time(segment.length, corner_speed)

                lap_time_s += corner_time
                current_speed = corner_speed

                segment_outputs.append(self.build_corner_output(segment.id))

            else:
                raise ValueError(f"Unknown segment type: {segment.type}")

        return {
            "lap_number": lap_number,
            "lap_time_s": lap_time_s,
            "ending_speed": current_speed,
            "segments": segment_outputs,
        }

    def build_strategy(self) -> dict:
        """
        Builds the full Level 1 submission strategy.
        """
        initial_tyre_id = self.choose_initial_tyre()
        corner_speeds = self.precompute_corner_speeds(initial_tyre_id)

        laps_output = []
        current_speed = 0.0
        total_time_s = 0.0

        for lap_number in range(1, self.race_data.race.laps + 1):
            lap_result = self.simulate_one_lap(
                lap_number=lap_number,
                starting_speed=current_speed,
                corner_speeds=corner_speeds,
            )

            total_time_s += lap_result["lap_time_s"]
            current_speed = lap_result["ending_speed"]

            laps_output.append(
                {
                    "lap": lap_number,
                    "segments": lap_result["segments"],
                    "pit": {
                        "enter": False
                    }
                }
            )

        return {
            "initial_tyre_id": initial_tyre_id,
            "laps": laps_output,
            "_meta": {
                "total_time_s": round(total_time_s, 3)
            }
        }

    # ---------------------------
    # Final export helper
    # ---------------------------

    def strip_debug_meta(self, strategy: dict) -> dict:
        """
        Removes debug metadata before submission.
        """
        clean_strategy = dict(strategy)
        clean_strategy.pop("_meta", None)
        return clean_strategy