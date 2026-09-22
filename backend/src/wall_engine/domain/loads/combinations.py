from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from wall_engine.units.registry import Force, Length, Q_

class LoadType(str, Enum):
    DC = "DC"  # Dead load of structural components
    EV = "EV"  # Vertical earth pressure
    EH = "EH"  # Horizontal earth pressure
    LS = "LS"  # Live load surcharge
    WA = "WA"  # Water pressure and uplift
    EQ = "EQ"
    EQ_E = "EQ_E"  # Earthquake earth pressure
    EQ_I = "EQ_I"  # Earthquake inertial force

@dataclass
class LoadFactor:
    gamma_max: float
    gamma_min: float

@dataclass
class LimitState:
    name: str
    factors: Dict[LoadType, LoadFactor]

@dataclass
class GenericLoad:
    name: str
    load_type: LoadType
    force_x: Force
    force_y: Force
    x_application: Length  # Distancia horizontal desde la punta (0,0)
    y_application: Length  # Distancia vertical desde la base de la zapata (0,0)
    
    @property
    def overturning_moment(self):
        """Momento desestabilizador (asumiendo punta como pivote).
        Fuerzas X empujan el muro (+ momento). 
        Fuerzas Y resisten o desestabilizan dependiendo de su signo."""
        # Convención estática típica en la base (0,0):
        # M_o = F_x * y_application - F_y * x_application
        # Positivo significa que trata de volcar el muro hacia adelante.
        return (self.force_x * self.y_application) - (self.force_y * self.x_application)

@dataclass
class FactoredResult:
    limit_state_name: str
    permutation_id: int
    sum_force_x: Force
    sum_force_y: Force
    sum_moment: Force # It's a Moment, but Pint handles units. Force * Length.
    factors_used: Dict[LoadType, float]
