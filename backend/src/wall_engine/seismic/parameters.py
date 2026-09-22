from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SeismicParameters:
    ag: Optional[float]
    kh: float
    kv: float

    soil_factor: Optional[float]
    seismic_zone: Optional[str]
