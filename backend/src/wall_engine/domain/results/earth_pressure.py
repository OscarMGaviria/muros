from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Force, Angle, Length

@dataclass
class ForceComponent:
    name: str
    magnitude: Force
    angle_horizontal: Angle
    application_height: Length

@dataclass
class EarthPressureResult:
    coefficient_active: float
    coefficient_passive: float
    
    soil_active_force: ForceComponent
    soil_passive_force: Optional[ForceComponent]
    
    surcharge_force: Optional[ForceComponent]
    seismic_active_force: Optional[ForceComponent] # Incremento dinámico de presión de tierras (ΔP_AE)
    
    horizontal_resultant: Force
    vertical_resultant: Force
