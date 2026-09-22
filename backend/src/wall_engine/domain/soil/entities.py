from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Density, Angle, Pressure

@dataclass(frozen=True)
class Soil:
    name: str

    unit_weight: Density
    saturated_unit_weight: Optional[Density]

    friction_angle: Angle
    cohesion: Pressure

    interface_friction_angle: Optional[Angle]

    bearing_capacity: Optional[Pressure]
