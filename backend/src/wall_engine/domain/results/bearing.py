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
