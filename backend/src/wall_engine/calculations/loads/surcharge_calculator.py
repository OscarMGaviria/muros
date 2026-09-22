from typing import List

from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import GenericLoad, LoadType
from wall_engine.domain.wall.entities import Wall

def _linear_interp(x: float, xs: List[float], ys: List[float]) -> float:
    if x <= xs[0]: return ys[0]
    if x >= xs[-1]: return ys[-1]
    for i in range(len(xs)-1):
        if xs[i] <= x <= xs[i+1]:
            fraction = (x - xs[i]) / (xs[i+1] - xs[i])
            return ys[i] + fraction * (ys[i+1] - ys[i])
    return ys[-1]

class LSSurchargeCalculator:
    """
    Calculates Live Load Surcharge (LS) based on CCP-14 / AASHTO LRFD Table 3.11.6.4.
    """
    def __init__(self):
        # Table 3.11.6.4-1: Abutments perpendicular to traffic (Height in mm, heq in mm)
        self.table_perpendicular_h = [1500, 3000, 6000]
        self.table_perpendicular_heq = [1200, 900, 600]
        
        # Table 3.11.6.4-2: Walls parallel to traffic (Distance 0.0 mm)
        self.table_parallel_0_h = [1500, 3000, 6000]
        self.table_parallel_0_heq = [1500, 1000, 600]
        
        # Table 3.11.6.4-2: Walls parallel to traffic (Distance >= 300 mm)
        self.table_parallel_300_h = [1500, 3000, 6000]
        self.table_parallel_300_heq = [600, 600, 600]

    def interpolate_heq(self, height_mm: float, orientation: str, distance_mm: float = 0.0) -> float:
        """
        Interpolates the equivalent height of soil (h_eq) based on wall height and orientation.
        """
        if orientation == "PERPENDICULAR":
            return _linear_interp(height_mm, self.table_perpendicular_h, self.table_perpendicular_heq)
            
        elif orientation == "PARALLEL":
            heq_0 = _linear_interp(height_mm, self.table_parallel_0_h, self.table_parallel_0_heq)
            heq_300 = _linear_interp(height_mm, self.table_parallel_300_h, self.table_parallel_300_heq)
            
            if distance_mm <= 0.0:
                return heq_0
            elif distance_mm >= 300.0:
                return heq_300
            else:
                fraction = distance_mm / 300.0
                return heq_0 - fraction * (heq_0 - heq_300)
        else:
            raise ValueError(f"Unknown orientation: {orientation}")

    def calculate_ls_load(self, wall: Wall, k_a: float, traffic_orientation: str = "PARALLEL", distance_from_back_mm: float = 300.0) -> List[GenericLoad]:
        h_m = wall.geometry.total_height.to("m").magnitude
        h_mm = h_m * 1000.0
        
        h_eq_mm = self.interpolate_heq(h_mm, traffic_orientation, distance_from_back_mm)
        h_eq_m = h_eq_mm / 1000.0
        
        gamma_s = wall.backfill.unit_weight.to("kN/m**3").magnitude
        delta_p = k_a * gamma_s * h_eq_m
        p_ls = delta_p * h_m
        y_app = h_m / 2.0
        
        load = GenericLoad(
            name="Traffic Surcharge (LS)",
            type=LoadType.LS,
            force_x=Q_(p_ls, "kN/m"),
            force_y=Q_(0, "kN/m"),
            application_y=Q_(y_app, "m"),
            application_x=wall.geometry.base_width
        )
        return [load]
