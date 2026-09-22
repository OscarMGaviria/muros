from dataclasses import dataclass
from wall_engine.units.registry import Force, Length, Q_

@dataclass
class StabilityResult:
    limit_state: str
    permutation_id: int
    
    # Volcamiento (Eccentricity)
    eccentricity: Length
    is_eccentricity_safe: bool
    
    # Deslizamiento (Sliding)
    sliding_demand: Force
    sliding_capacity: Force
    sliding_ratio: float # Demand / Capacity (<= 1.0 es seguro)
    
    # Presiones de contacto (Bearing Pressures)
    q_toe: float # Presión en la punta (ej. en kPa o kN/m2)
    q_heel: float # Presión en el talón
