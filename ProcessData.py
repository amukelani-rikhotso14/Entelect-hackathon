import json
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Car:
    max_speed_m_s: float
    accel_m_s2: float
    brake_m_s2: float
    limp_constant_m_s: float
    crawl_constant_m_s: float
    fuel_tank_capacity_l: float
    initial_fuel_l: float
    fuel_consumption_l_m: float

@dataclass
class Race:
    name: str
    laps: int
    base_pit_stop_time_s: float
    pit_tyre_swap_time_s: float
    pit_refuel_rate_l_s: float
    corner_crash_penalty_s: float
    pit_exit_speed_m_s: float
    fuel_soft_cap_limit_l: float
    starting_weather_condition_id: int
    time_reference_s: float

@dataclass
class Segment:
    id: int
    type: str
    length_m: float
    radius_m: Optional[float] = None  # Radius only exists on 'corner' types

@dataclass
class Track:
    name: str
    segments: List[Segment]

@dataclass
class TyreProperties:
    life_span: int
    dry_friction_multiplier: float
    cold_friction_multiplier: float
    light_rain_friction_multiplier: float
    heavy_rain_friction_multiplier: float
    dry_degradation: float
    cold_degradation: float
    light_rain_degradation: float
    heavy_rain_degradation: float

@dataclass
class AvailableSet:
    ids: List[int]
    compound: str

@dataclass
class WeatherCondition:
    id: int
    condition: str
    duration_s: float
    acceleration_multiplier: float
    deceleration_multiplier: float

class GameData:
    """Main class to encapsulate all parsed data representing the game state/configurations."""
    def __init__(self, json_data: dict):
        # Map car data explicitly to handle slashes in JSON keys
        c = json_data['car']
        self.car = Car(
            max_speed_m_s=c['max_speed_m/s'],
            accel_m_s2=c['accel_m/se2'],
            brake_m_s2=c['brake_m/se2'],
            limp_constant_m_s=c['limp_constant_m/s'],
            crawl_constant_m_s=c['crawl_constant_m/s'],
            fuel_tank_capacity_l=c['fuel_tank_capacity_l'],
            initial_fuel_l=c['initial_fuel_l'],
            fuel_consumption_l_m=c['fuel_consumption_l/m']
        )

        # Map race data
        r = json_data['race']
        self.race = Race(
            name=r['name'],
            laps=r['laps'],
            base_pit_stop_time_s=r['base_pit_stop_time_s'],
            pit_tyre_swap_time_s=r['pit_tyre_swap_time_s'],
            pit_refuel_rate_l_s=r['pit_refuel_rate_l/s'],
            corner_crash_penalty_s=r['corner_crash_penalty_s'],
            pit_exit_speed_m_s=r['pit_exit_speed_m/s'],
            fuel_soft_cap_limit_l=r['fuel_soft_cap_limit_l'],
            starting_weather_condition_id=r['starting_weather_condition_id'],
            time_reference_s=r['time_reference_s']
        )

        # Map track and segments
        self.track = Track(
            name=json_data['track']['name'],
            segments=[Segment(**s) for s in json_data['track']['segments']]
        )

        # Map tyres, sets, and weather conditions using dictionary unpacking
        self.tyre_properties = {compound: TyreProperties(**props) 
                                for compound, props in json_data['tyres']['properties'].items()}
        self.available_sets = [AvailableSet(**a) for a in json_data['available_sets']]
        self.weather_conditions = [WeatherCondition(**w) for w in json_data['weather']['conditions']]

    @classmethod
    def from_file(cls, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data)

if __name__ == "__main__":
    filepath = r"c:\Users\Mathiane karabo\OneDrive - University of Cape Town\Entelect-hackathon\1.txt"
    game_data = GameData.from_file(filepath)
    print(f"Loaded Race: {game_data.race.name} ({game_data.race.laps} Laps)")
    print(f"Track: {game_data.track.name} with {len(game_data.track.segments)} segments")
    print(f"Car Max Speed: {game_data.car.max_speed_m_s} m/s")
    print(f"Available Tyre Compounds: {', '.join(game_data.tyre_properties.keys())}")