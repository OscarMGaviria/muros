from dataclasses import dataclass
from wall_engine.units.registry import Force

@dataclass
class StemForcesResult:
    V_u: Force # Cortante último (Demanda)
    M_u: Force # Momento flector último (Demanda)
    M_serv: Force # Momento bajo cargas de servicio
    
    V_c: Force # Capacidad nominal al corte del concreto
    phi_V_c: Force # Capacidad al corte factorada (phi = 0.75)
    is_shear_safe: bool # V_u <= phi_V_c
