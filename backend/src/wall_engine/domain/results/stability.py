from dataclasses import dataclass
from typing import Optional
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

    # Detalle para la memoria de cálculo (unidades kN, m, kPa)
    sum_V: float = 0.0              # Σ fuerzas verticales mayoradas (kN/m)
    sum_H: float = 0.0              # Σ fuerzas horizontales mayoradas (kN/m)
    sum_M: float = 0.0              # Σ momento respecto a la punta, M = Fx·y − Fy·x (kN·m/m)
    x_resultant: float = 0.0        # ubicación de la resultante desde la punta (m)
    footing_width: float = 0.0      # B (m)
    e_limit: float = 0.0            # excentricidad máxima admisible (m)
    e_limit_rule: str = ""          # descripción del límite aplicado
    friction_nominal: float = 0.0   # R_tau nominal (kN/m)
    passive_nominal: float = 0.0    # R_ep nominal (kN/m)
    phi_tau: float = 1.0
    phi_ep: float = 0.5
    friction_angle_deg: float = 0.0 # φ de la fundación usado en la fricción
    key_depth: float = 0.0          # profundidad del dentellón (m)
    key_split: Optional[dict] = None  # reparto R1/R2 con dentellón
    pressure_distribution: str = "" # "trapezoidal" o "triangular" (Meyerhof)
