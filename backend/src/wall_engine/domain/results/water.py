from dataclasses import dataclass
from wall_engine.units.registry import Force, Length, Pressure, Q_
from wall_engine.domain.results.earth_pressure import ForceComponent

@dataclass
class WaterPressureResult:
    horizontal_force: ForceComponent
    vertical_force: ForceComponent
    uplift: ForceComponent
    
    # Fuerzas resultantes netas de agua
    resultant_horizontal: Force
    resultant_vertical: Force
    
    water_height: Length = Q_(0, "m")          # hw sobre la base de la zapata
    uplift_pressure_at_heel: Pressure = Q_(0, "kPa")  # gamma_w·hw
