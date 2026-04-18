import math


def time_to_change_speed(v_initial, v_final, rate):
    """t = (v_final - v_initial) / rate  (rate always positive)"""
    return (v_final - v_initial) / rate


def distance_to_change_speed(v_initial, v_final, rate):
    """d = (v_final^2 - v_initial^2) / (2 * rate)  (rate always positive)"""
    return (v_final ** 2 - v_initial ** 2) / (2 * rate)


def time_at_constant_speed(distance, speed):
    """t = distance / speed"""
    return distance / speed


def simulate_straight(entry_v, target_v, corner_entry_v, length, accel_rate, brake_rate, max_speed=float("inf")):
    """
    Simulate a straight segment with up to 3 phases:
      Phase 1 — accelerate from entry_v to cruise speed
      Phase 2 — cruise at constant speed
      Phase 3 — brake from cruise speed to corner_entry_v

    Returns (total_time, exit_speed) where exit_speed == corner_entry_v.
    """
    target_v = min(target_v, max_speed)
    # Phase 1: acceleration
    if target_v <= entry_v:
        cruise_v = entry_v
        accel_dist = 0.0
        accel_time = 0.0
    else:
        cruise_v = target_v
        accel_dist = distance_to_change_speed(entry_v, cruise_v, accel_rate)
        accel_time = time_to_change_speed(entry_v, cruise_v, accel_rate)

    # Phase 3: braking (backward from end of straight)
    brake_dist = abs(distance_to_change_speed(corner_entry_v, cruise_v, brake_rate))
    brake_time = abs(time_to_change_speed(cruise_v, corner_entry_v, brake_rate))

    # Phase 2: cruise
    cruise_dist = length - accel_dist - brake_dist

    if cruise_dist < 0:
        # Too short — find max achievable speed analytically:
        # (v^2 - entry_v^2)/(2*accel) + (v^2 - corner_entry_v^2)/(2*brake) = length
        # v^2 * (1/(2*a) + 1/(2*b)) = length + entry_v^2/(2*a) + corner_entry_v^2/(2*b)
        inv_sum = 1 / (2 * accel_rate) + 1 / (2 * brake_rate)
        rhs = length + entry_v ** 2 / (2 * accel_rate) + corner_entry_v ** 2 / (2 * brake_rate)
        max_v = math.sqrt(rhs / inv_sum)

        cruise_v = max_v
        accel_dist = distance_to_change_speed(entry_v, cruise_v, accel_rate)
        accel_time = time_to_change_speed(entry_v, cruise_v, accel_rate)
        brake_dist = abs(distance_to_change_speed(corner_entry_v, cruise_v, brake_rate))
        brake_time = abs(time_to_change_speed(cruise_v, corner_entry_v, brake_rate))
        cruise_dist = 0.0
        cruise_time = 0.0
    else:
        cruise_time = time_at_constant_speed(cruise_dist, cruise_v) if cruise_dist > 0 else 0.0

    total_time = accel_time + cruise_time + brake_time
    return total_time, corner_entry_v


def find_optimal_brake_point(
    entry_v,
    target_v,
    corner_entry_v,
    length,
    accel_rate,
    brake_rate,
    max_speed=float("inf"),
):
    """
    Returns where braking should start (distance from the start of the straight),
    plus the achieved cruise speed and total time.

    Returns a dict:
      - brake_start_m: distance from start of straight to begin braking
      - cruise_speed: achieved peak/cruise speed (m/s)
      - total_time: total time through the straight (s)
      - exit_speed: speed at end of straight (m/s) == corner_entry_v
    """
    target_v = min(target_v, max_speed)

    cruise_v = entry_v if target_v <= entry_v else target_v
    accel_dist = distance_to_change_speed(entry_v, cruise_v, accel_rate) if cruise_v > entry_v else 0.0
    accel_time = time_to_change_speed(entry_v, cruise_v, accel_rate) if cruise_v > entry_v else 0.0

    brake_dist = abs(distance_to_change_speed(corner_entry_v, cruise_v, brake_rate))
    brake_time = abs(time_to_change_speed(cruise_v, corner_entry_v, brake_rate))

    cruise_dist = length - accel_dist - brake_dist
    if cruise_dist < 0:
        inv_sum = 1 / (2 * accel_rate) + 1 / (2 * brake_rate)
        rhs = length + entry_v ** 2 / (2 * accel_rate) + corner_entry_v ** 2 / (2 * brake_rate)
        cruise_v = math.sqrt(max(0.0, rhs / inv_sum))

        accel_dist = distance_to_change_speed(entry_v, cruise_v, accel_rate) if cruise_v > entry_v else 0.0
        accel_time = time_to_change_speed(entry_v, cruise_v, accel_rate) if cruise_v > entry_v else 0.0
        brake_dist = abs(distance_to_change_speed(corner_entry_v, cruise_v, brake_rate))
        brake_time = abs(time_to_change_speed(cruise_v, corner_entry_v, brake_rate))
        cruise_dist = 0.0
        cruise_time = 0.0
    else:
        cruise_time = time_at_constant_speed(cruise_dist, cruise_v) if cruise_dist > 0 else 0.0

    return {
        "brake_start_m": max(0.0, length - brake_dist),
        "cruise_speed": cruise_v,
        "total_time": accel_time + cruise_time + brake_time,
        "exit_speed": corner_entry_v,
    }


def is_straight_feasible(entry_v, target_v, corner_entry_v, length, accel_rate, brake_rate, max_speed=float("inf")):
    """
    Returns True if the car can reach target_v and still brake to corner_entry_v
    within the straight length.
    """
    target_v = min(target_v, max_speed)
    cruise_v = target_v if target_v > entry_v else entry_v
    accel_dist = distance_to_change_speed(entry_v, cruise_v, accel_rate) if cruise_v > entry_v else 0.0
    brake_dist = abs(distance_to_change_speed(corner_entry_v, cruise_v, brake_rate))
    return accel_dist + brake_dist <= length
