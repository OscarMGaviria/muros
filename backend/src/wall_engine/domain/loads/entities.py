from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Length, Pressure, Q_

@dataclass(frozen=True)
class Surcharge:
    name: str
    magnitude: Pressure
    distribution: str
    offset: Optional[Length]
    width: Optional[Length]

@dataclass(frozen=True)
class TrafficSurcharge:
    orientation: str = "PARALLEL"
    distance_from_back: Length = Q_(0, "mm")
