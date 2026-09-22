from dataclasses import dataclass
from wall_engine.units.registry import Force, Length
from wall_engine.domain.results.earth_pressure import ForceComponent

@dataclass
class WaterPressureResult:
    horizontal_force: ForceComponent
    vertical_force: ForceComponent
    uplift: ForceComponent
    
    # Fuerzas resultantes netas de agua
    resultant_horizontal: Force
    resultant_vertical: Force
