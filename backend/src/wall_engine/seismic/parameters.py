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
    # Factor de carga viva en Evento Extremo I (Tabla 3.4.1-1): 0.0, 0.5 o 1.0
    gamma_eq: float = 0.0
    # Altura de la resultante de P_AE sobre la base, como fracción de h (11.6.5.3):
    # H/3 por defecto; la norma permite 0.4h a 0.5h
    pae_height_ratio: float = 1.0 / 3.0
