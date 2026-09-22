from dataclasses import dataclass
from typing import Dict, List
from uuid import UUID

from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.results.bearing import BearingCapacityResult
from wall_engine.domain.results.reinforcement import WallReinforcementResult
from wall_engine.domain.loads.combinations import FactoredResult, GenericLoad

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
