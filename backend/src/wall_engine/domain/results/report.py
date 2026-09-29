from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.results.bearing import BearingCapacityResult
from wall_engine.domain.results.reinforcement import WallReinforcementResult
from wall_engine.domain.loads.combinations import FactoredResult, GenericLoad
from wall_engine.domain.results.earth_pressure import EarthPressureResult
from wall_engine.domain.results.water import WaterPressureResult

@dataclass
class WallDesignReport:
    wall_id: UUID
    wall_name: str
    
    # Dict de combinaciones (ej. "Strength I", "Service I") -> peor FactoredResult
    unfactored_loads: List[GenericLoad]
    governing_loads: Dict[str, FactoredResult]
    
    # Dict de resultados por estado límite
    stability_results: Dict[str, StabilityResult]
    bearing_results: Dict[str, BearingCapacityResult]
    
    # Resultado final de refuerzo estructural
    structural_design: WallReinforcementResult
    
    # "PASS", "FAIL_STABILITY", "FAIL_BEARING", "FAIL_STRUCTURAL"
    status: str
    earth_pressure: EarthPressureResult = None
    traffic_heq_m: float = 0.0
    traffic_qs_kPa: float = 0.0
    water: Optional[WaterPressureResult] = None
    warnings: List[str] = field(default_factory=list)
