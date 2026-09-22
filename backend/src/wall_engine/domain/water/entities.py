from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Length

@dataclass(frozen=True)
class Groundwater:
    elevation: Length
    drainage_enabled: bool
    drainage_type: Optional[str]
