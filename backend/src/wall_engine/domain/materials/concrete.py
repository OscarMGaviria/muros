from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Pressure, Density

@dataclass(frozen=True)
class Concrete:
    fc: Pressure
    density: Density
    elastic_modulus: Optional[Pressure]
