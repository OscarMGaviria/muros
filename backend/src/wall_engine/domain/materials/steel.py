from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Pressure

@dataclass(frozen=True)
class ReinforcementSteel:
    fy: Pressure
    fu: Optional[Pressure]
    elastic_modulus: Pressure
