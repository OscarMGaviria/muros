from dataclasses import dataclass
from wall_engine.units.registry import Pressure

@dataclass
class BearingCapacityResult:
    q_nominal: Pressure
    effective_width: float # m
    # En LRFD puro, el factor de resistencia phi_b se aplica en la capa del código normativo
    # pero aquí podemos reportar la nominal para que luego sea factorada.
    N_c: float
    N_q: float
    N_gamma: float
    i_c: float
    i_q: float
    i_gamma: float

    # Verificación LRFD (AASHTO 11.6.3.2 y Tabla 11.5.7-1)
    q_demand: float = 0.0        # kPa, sigma_V = V / B'
    phi_b: float = 0.55
    q_resistance: float = 0.0    # kPa, phi_b * q_n
    bearing_ratio: float = 0.0   # demanda / resistencia (<= 1.0 cumple)
    is_safe: bool = True
    uses_geotechnical_q_n: bool = False  # q_n tomado del estudio geotécnico

    # Detalle para la memoria de cálculo
    q_n_computed: float = 0.0     # kPa, ecuación general (aunque gobierne el valor geotécnico)
    embedment_depth: float = 0.0  # m, D_f
    q_overburden: float = 0.0     # kPa, gamma·D_f
    cohesion: float = 0.0         # kPa
    friction_angle_deg: float = 0.0
    unit_weight: float = 0.0      # kN/m³
    sum_V: float = 0.0            # kN/m
    sum_H: float = 0.0            # kN/m
    eccentricity: float = 0.0     # m
    footing_width: float = 0.0    # m
    limit_state: str = ""
