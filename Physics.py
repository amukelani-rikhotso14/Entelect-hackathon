import math


class StraightPhysicsEngine:
    def __init__(
        self,
        accel_mps2: float,
        brake_mps2: float,
        max_speed_mps: float,
        min_speed_mps: float = 0.0,
    ):
        self.accel_mps2 = accel_mps2
        self.brake_mps2 = brake_mps2
        self.max_speed_mps = max_speed_mps
        self.min_speed_mps = min_speed_mps  # ✅ FIXED

    def clamp_speed(self, speed: float) -> float:
        """
        Ensures the speed stays within valid bounds.

        Why:
        - The car cannot exceed max_speed (rule from problem).
        - The car should never go below a minimum speed.
        - In Level 1, min_speed is 0.0.
        - In later levels, this could represent crawl speed or other limits.
        """
        return max(self.min_speed_mps, min(speed, self.max_speed_mps))

    def time_to_change_speed(self, v_from: float, v_to: float, rate: float) -> float:
        """
        Returns the time needed to change speed at a constant rate.

        Why:
        - Used for both acceleration and braking.
        - We use the magnitude of the speed difference.
        - The rate must be positive.
        - If speeds are the same, time is 0.

        Example:
        - from 20 m/s to 60 m/s at 10 m/s² -> 4 seconds
        - from 60 m/s to 20 m/s at 20 m/s² -> 2 seconds
        """
        if rate <= 0:
            raise ValueError("Rate must be greater than 0.")

        return abs(v_to - v_from) / rate

    def distance_to_change_speed(self, v_from: float, v_to: float, rate: float) -> float:
            """
            Returns the distance needed to change speed at a constant rate.

            Why:
            - Used for both acceleration and braking.
            - Uses the standard motion formula:
            d = (v_to^2 - v_from^2) / (2 * rate)
            - We use abs(...) so the distance is always positive.
            - The rate must be positive.
            """
            if rate <= 0:
                raise ValueError("Rate must be greater than 0.")

            return abs((v_to ** 2 - v_from ** 2) / (2 * rate))

    def compute_accel_phase(self, entry_speed: float, peak_speed: float) -> dict:
        """
        Computes the acceleration phase from entry_speed to peak_speed.

        Why:
        - If peak_speed is greater than entry_speed, the car accelerates.
        - If peak_speed is less than or equal to entry_speed, there is no acceleration phase.
        - Returns both distance and time so the next functions can reuse it.
        """
        entry_speed = self.clamp_speed(entry_speed)
        peak_speed = self.clamp_speed(peak_speed)

        if peak_speed <= entry_speed:
            return {
                "distance_m": 0.0,
                "time_s": 0.0,
            }

        return {
            "distance_m": self.distance_to_change_speed(entry_speed, peak_speed, self.accel_mps2),
            "time_s": self.time_to_change_speed(entry_speed, peak_speed, self.accel_mps2),
        }

    def compute_brake_phase(self, peak_speed: float, exit_speed: float) -> dict:
        """
        Computes the braking phase from peak_speed down to exit_speed.
        """
        peak_speed = self.clamp_speed(peak_speed)
        exit_speed = self.clamp_speed(exit_speed)

        if peak_speed <= exit_speed:
            return {
                "distance_m": 0.0,
                "time_s": 0.0,
            }

        return {
            "distance_m": self.distance_to_change_speed(peak_speed, exit_speed, self.brake_mps2),
            "time_s": self.time_to_change_speed(peak_speed, exit_speed, self.brake_mps2),
        }

    def compute_cruise_phase(self, distance_m: float, speed_mps: float) -> dict:
        """
        Computes the cruise phase at constant speed.
        """
        distance_m = max(0.0, distance_m)
        speed_mps = self.clamp_speed(speed_mps)

        if distance_m == 0.0:
            return {
                "distance_m": 0.0,
                "time_s": 0.0,
            }

        if speed_mps <= 0:
            raise ValueError("Cruise speed must be greater than 0 when distance is positive.")

        return {
            "distance_m": distance_m,
            "time_s": distance_m / speed_mps,
        }

    def can_reach_target_and_brake(
        self,
        entry_speed: float,
        target_speed: float,
        exit_speed: float,
        length_m: float,
    ) -> bool:
        """
        Checks whether the car can:
        1. accelerate from entry_speed to target_speed
        2. then brake from target_speed to exit_speed
        all within the available straight length.

        Why:
        - This is the first feasibility check for a straight.
        - If accel distance + brake distance fits, then the target is valid.
        - Any leftover distance can be used for cruising.
        """
        entry_speed = self.clamp_speed(entry_speed)
        target_speed = self.clamp_speed(target_speed)
        exit_speed = self.clamp_speed(exit_speed)

        # Per the spec, if target speed is lower than entry speed,
        # the car simply continues at entry speed until braking.
        effective_target_speed = max(entry_speed, target_speed)

        accel_phase = self.compute_accel_phase(entry_speed, effective_target_speed)
        brake_phase = self.compute_brake_phase(effective_target_speed, exit_speed)

        total_required_distance = accel_phase["distance_m"] + brake_phase["distance_m"]

        return total_required_distance <= length_m

    def can_reach_target_and_brake(
        self,
        entry_speed: float,
        target_speed: float,
        exit_speed: float,
        length_m: float,
    ) -> bool:
        """
        Checks whether the car can:
        1. accelerate from entry_speed to target_speed
        2. then brake from target_speed to exit_speed
        all within the available straight length.

        Why:
        - This is the first feasibility check for a straight.
        - If accel distance + brake distance fits, then the target is valid.
        - Any leftover distance can be used for cruising.
        """
        entry_speed = self.clamp_speed(entry_speed)
        target_speed = self.clamp_speed(target_speed)
        exit_speed = self.clamp_speed(exit_speed)

        # Per the spec, if target speed is lower than entry speed,
        # the car simply continues at entry speed until braking.
        effective_target_speed = max(entry_speed, target_speed)

        accel_phase = self.compute_accel_phase(entry_speed, effective_target_speed)
        brake_phase = self.compute_brake_phase(effective_target_speed, exit_speed)

        total_required_distance = accel_phase["distance_m"] + brake_phase["distance_m"]

        return total_required_distance <= length_m

    def simulate_straight(
        self,
        entry_speed: float,
        target_speed: float,
        exit_speed_required: float,
        length_m: float,
    ) -> dict:
        """
        Simulates a straight segment.

        It handles two cases:
        1. Target speed is reachable -> accelerate, maybe cruise, then brake
        2. Target speed is not reachable -> accelerate to best possible peak speed, then brake

        Returns a dictionary with full phase details for strategy use.
        """
        if length_m < 0:
            raise ValueError("Straight length cannot be negative.")

        entry_speed = self.clamp_speed(entry_speed)
        target_speed = self.clamp_speed(target_speed)
        exit_speed_required = self.clamp_speed(exit_speed_required)

        # Spec rule: if target is lower than entry speed, car keeps going at entry speed
        effective_target_speed = max(entry_speed, target_speed)

        # First check: if we cannot even brake from entry speed to exit speed in this length, impossible
        min_brake_phase = self.compute_brake_phase(entry_speed, exit_speed_required)
        if entry_speed > exit_speed_required and min_brake_phase["distance_m"] > length_m:
            return {
                "feasible": False,
                "reason": "Not enough distance to brake from entry speed to required exit speed."
            }

        # Case 1: target is reachable
        if self.can_reach_target_and_brake(
            entry_speed=entry_speed,
            target_speed=effective_target_speed,
            exit_speed=exit_speed_required,
            length_m=length_m,
        ):
            accel_phase = self.compute_accel_phase(entry_speed, effective_target_speed)
            brake_phase = self.compute_brake_phase(effective_target_speed, exit_speed_required)

            cruise_distance = length_m - accel_phase["distance_m"] - brake_phase["distance_m"]
            cruise_phase = self.compute_cruise_phase(cruise_distance, effective_target_speed)

            total_time = (
                accel_phase["time_s"]
                + cruise_phase["time_s"]
                + brake_phase["time_s"]
            )

            return {
                "feasible": True,
                "time_s": total_time,
                "entry_speed_mps": entry_speed,
                "target_speed_mps": target_speed,
                "peak_speed_mps": effective_target_speed,
                "end_speed_mps": exit_speed_required,
                "distance_accel_m": accel_phase["distance_m"],
                "distance_cruise_m": cruise_phase["distance_m"],
                "distance_brake_m": brake_phase["distance_m"],
                "time_accel_s": accel_phase["time_s"],
                "time_cruise_s": cruise_phase["time_s"],
                "time_brake_s": brake_phase["time_s"],
                "brake_start_m_before_next": brake_phase["distance_m"],
            }

        # Case 2: target not reachable, solve no-cruise peak
        peak_speed = self.solve_peak_speed_no_cruise(
            entry_speed=entry_speed,
            exit_speed=exit_speed_required,
            length_m=length_m,
        )

        accel_phase = self.compute_accel_phase(entry_speed, peak_speed)
        brake_phase = self.compute_brake_phase(peak_speed, exit_speed_required)

        total_distance = accel_phase["distance_m"] + brake_phase["distance_m"]

        # small floating point tolerance
        if total_distance > length_m + 1e-6:
            return {
                "feasible": False,
                "reason": "Numerical inconsistency: no-cruise solution exceeds straight length."
            }

        total_time = accel_phase["time_s"] + brake_phase["time_s"]

        return {
            "feasible": True,
            "time_s": total_time,
            "entry_speed_mps": entry_speed,
            "target_speed_mps": target_speed,
            "peak_speed_mps": peak_speed,
            "end_speed_mps": exit_speed_required,
            "distance_accel_m": accel_phase["distance_m"],
            "distance_cruise_m": 0.0,
            "distance_brake_m": brake_phase["distance_m"],
            "time_accel_s": accel_phase["time_s"],
            "time_cruise_s": 0.0,
            "time_brake_s": brake_phase["time_s"],
            "brake_start_m_before_next": brake_phase["distance_m"],
        }

    def solve_peak_speed_no_cruise(
        self,
        entry_speed: float,
        exit_speed: float,
        length_m: float,
    ) -> float:
        """
        Computes the highest reachable peak speed when there is no cruise phase.
        """
        entry_speed = self.clamp_speed(entry_speed)
        exit_speed = self.clamp_speed(exit_speed)

        if length_m < 0:
            raise ValueError("Straight length cannot be negative.")

        a = self.accel_mps2
        b = self.brake_mps2

        numerator = (
            length_m
            + (entry_speed ** 2) / (2 * a)
            + (exit_speed ** 2) / (2 * b)
        )

        denominator = (1 / (2 * a)) + (1 / (2 * b))

        peak_speed_squared = numerator / denominator
        peak_speed = math.sqrt(max(0.0, peak_speed_squared))

        return self.clamp_speed(peak_speed)
