from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Force

@dataclass
class FootingSectionForces:
    V_u: Force # Cortante Último
    M_u: Force # Momento Flector Último
    M_serv: Force # Momento bajo cargas de servicio
    V_c: Force # Capacidad nominal al corte
    phi_V_c: Force # Capacidad factorada (phi=0.75)
    is_shear_safe: bool

@dataclass
class FootingDesignResult:
    toe: FootingSectionForces
    heel: FootingSectionForces
    key: Optional[FootingSectionForces] = None
