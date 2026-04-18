import json
import math
from dataclasses import dataclass
from ProcessData import *

# ── Constants ─────────────────────────────────────────────────────────────────
GRAVITY = 9.8

BASE_FRICTION = {
    "Soft": 1.8, "Medium": 1.7, "Hard": 1.6,
    "Intermediate": 1.2, "Wet": 1.1
}


# ── Level 1 Strategy ──────────────────────────────────────────────────────────
class Level1Strategy:
    """
    Generates an optimal Level 1 race strategy.

    Level 1 rules:
      - Tyres do NOT degrade
      - No fuel management needed
      - Goal: complete all laps as fast as possible without crashing corners
    """

    def __init__(self, game_data: GameData):
        self.gd = game_data
        self.car = game_data.car
        self.race = game_data.race
        self.segments = game_data.track.segments

        # Level 1 is always dry, so use dry weather multipliers
        self.weather = "dry"

        # Pick best tyre for dry Level 1 = Soft (highest dry friction)
        self.tyre_compound = "Soft"
        self.tyre_id = self._get_tyre_id(self.tyre_compound)
        self.tyre_props = game_data.tyre_properties[self.tyre_compound]
        self.friction_mult = self.tyre_props.dry_friction_multiplier

    # ── Tyre helpers ──────────────────────────────────────────────────────────

    def _get_tyre_id(self, compound: str) -> int:
        """Return the first available tyre ID for the given compound."""
        for s in self.gd.available_sets:
            if s.compound == compound:
                return s.ids[0]
        raise ValueError(f"No tyre set found for compound: {compound}")

    def tyre_friction(self, degradation: float = 0.0) -> float:
        """
        tyre_friction = (base_friction - degradation) × weather_multiplier
        Level 1: degradation is always 0.
        """
        return (BASE_FRICTION[self.tyre_compound] - degradation) * self.friction_mult

    def max_corner_speed(self, radius_m: float, degradation: float = 0.0) -> float:
        """
        max_corner_speed = sqrt(tyre_friction × gravity × radius) + crawl_speed
        """
        friction = self.tyre_friction(degradation)
        return math.sqrt(friction * GRAVITY * radius_m) + self.car.crawl_constant_m_s

    # ── Straight helpers ──────────────────────────────────────────────────────

    def brake_distance(self, v_from: float, v_to: float) -> float:
        """Distance required to brake from v_from down to v_to."""
        if v_to >= v_from:
            return 0.0
        return (v_from**2 - v_to**2) / (2 * self.car.brake_m_s2)

    def accel_distance(self, v_from: float, v_to: float) -> float:
        """Distance required to accelerate from v_from up to v_to."""
        if v_to <= v_from:
            return 0.0
        return (v_to**2 - v_from**2) / (2 * self.car.accel_m_s2)

    def plan_straight(self, seg: Segment, v_entry: float, v_exit_needed: float):
        """
        For a straight segment, decide:
          - target_speed  : the speed to aim for along the straight
          - brake_start   : metres before the END of the straight to start braking

        Strategy: go as fast as possible (max speed), then brake just in time
        to hit the required corner entry speed.
        """
        target = self.car.max_speed_m_s  # always aim for max speed
        length = seg.length_m

        # How far we need to brake from target speed down to v_exit_needed
        d_brake = self.brake_distance(target, v_exit_needed)

        # Clamp so braking doesn't start before the beginning of the straight
        brake_before = min(d_brake, length)
        brake_before = max(brake_before, 0.0)

        return round(target, 2), round(brake_before, 2)

    # ── Main strategy builder ─────────────────────────────────────────────────

    def build(self) -> dict:
        """Build and return the full race submission JSON as a Python dict."""
        laps_out = []

        for lap_num in range(1, self.race.laps + 1):
            segments_out = []

            # Entry speed: 0 on first segment of lap 1, pit exit speed otherwise
            v_entry = 0.0 if lap_num == 1 else self.race.pit_exit_speed_m_s

            for i, seg in enumerate(self.segments):

                if seg.type == "straight":
                    # Determine the speed we must arrive at the END of this straight.
                    # That is the max safe speed for the NEXT segment if it's a corner.
                    next_seg = self.segments[i + 1] if i + 1 < len(self.segments) else None

                    if next_seg and next_seg.type == "corner":
                        v_exit = min(
                            self.max_corner_speed(next_seg.radius_m),
                            self.car.max_speed_m_s
                        )
                    else:
                        # Next is another straight or end of lap — no need to slow down
                        v_exit = self.car.max_speed_m_s

                    target, brake_before = self.plan_straight(seg, v_entry, v_exit)

                    segments_out.append({
                        "id": seg.id,
                        "type": "straight",
                        "target_m/s": target,
                        "brake_start_m_before_next": brake_before
                    })

                    v_entry = v_exit  # carry speed into next segment

                elif seg.type == "corner":
                    safe_speed = self.max_corner_speed(seg.radius_m)
                    # Entry speed must not exceed safe corner speed
                    v_entry = min(v_entry, safe_speed)

                    segments_out.append({
                        "id": seg.id,
                        "type": "corner"
                    })
                    # Exit corner at the same speed (no acceleration inside corners)

            # Level 1: no pit stops needed
            laps_out.append({
                "lap": lap_num,
                "segments": segments_out,
                "pit": {"enter": False}
            })

        return {
            "initial_tyre_id": self.tyre_id,
            "laps": laps_out
        }

    # ── Simulator (estimates your race time so you can tune) ──────────────────

    def simulate(self, plan: dict) -> float:
        """
        Simulate the race plan and return an estimated total race time in seconds.
        Useful for checking your score before submitting.
        """
        total_time = 0.0
        v = 0.0

        for lap_data in plan["laps"]:
            for s in lap_data["segments"]:
                seg = next(x for x in self.segments if x.id == s["id"])

                if s["type"] == "straight":
                    target      = s["target_m/s"]
                    brake_before = s["brake_start_m_before_next"]
                    length      = seg.length_m

                    # Effective target (can't go slower than entry speed)
                    eff_target = max(v, target)
                    eff_target = min(eff_target, self.car.max_speed_m_s)

                    # Next corner exit speed
                    seg_idx = self.segments.index(seg)
                    next_seg = self.segments[seg_idx + 1] if seg_idx + 1 < len(self.segments) else None
                    v_exit = (min(self.max_corner_speed(next_seg.radius_m), self.car.max_speed_m_s)
                              if next_seg and next_seg.type == "corner"
                              else eff_target)

                    # Phase 1 — accelerate
                    if eff_target > v:
                        t_accel = (eff_target - v) / self.car.accel_m_s2
                        total_time += t_accel

                    # Phase 2 — cruise
                    brake_pos = length - brake_before
                    d_accel = self.accel_distance(v, eff_target)
                    d_cruise = max(0.0, brake_pos - d_accel)
                    if eff_target > 0:
                        total_time += d_cruise / eff_target

                    # Phase 3 — brake
                    if eff_target > v_exit:
                        t_brake = (eff_target - v_exit) / self.car.brake_m_s2
                        total_time += t_brake

                    v = v_exit

                elif s["type"] == "corner":
                    safe = self.max_corner_speed(seg.radius_m)
                    spd  = min(v, safe)
                    spd  = max(spd, self.car.crawl_constant_m_s)
                    total_time += seg.length_m / spd
                    v = spd

        return total_time


# ── Run it ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    filepath = "1.txt"   # ← change to your full path if needed

    gd       = GameData.from_file(filepath)
    strategy = Level1Strategy(gd)
    plan     = strategy.build()

    # Save submission file
    with open("output.txt", "w") as f:
        json.dump(plan, f, indent=2)

    # Estimate race time & score
    est_time = strategy.simulate(plan)
    ref_time = gd.race.time_reference_s
    score    = 500_000 * (ref_time / est_time) ** 3

    print(f"Race     : {gd.race.name}")
    print(f"Track    : {gd.track.name}  ({len(gd.track.segments)} segments, {gd.race.laps} laps)")
    print(f"Tyre     : {strategy.tyre_compound} (ID {strategy.tyre_id})")
    print(f"Est time : {est_time:.1f}s  ({est_time/60:.1f} min)")
    print(f"Ref time : {ref_time}s")
    print(f"Est score: {score:,.0f}")
    print(f"Output   : output.txt")