from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SeismicParameters:
    ag: Optional[float]
    kh: float
    kv: float
    q_surcharge: float = 0.0
    soil_factor: Optional[float] = None
    seismic_zone: Optional[str] = None
