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

    def calculate_ls_load(self, wall: Wall, k_a: float):
        """
        Calcula la sobrecarga viva vehicular (LS) según CCP-14 / AASHTO LRFD 3.11.6.4.
        La altura equivalente de suelo (heq) se interpola de la Tabla 3.11.6.4-1/2
        según la altura del muro y la orientación respecto al tráfico. La presión
        de sobrecarga se obtiene como qs = heq * gamma_relleno, y el empuje LS
        resultante es puramente horizontal (no se descompone por fricción muro-suelo):
        LS = qs * K_a * H_total
        Retorna (loads, heq_m, qs_kPa).
        """
        orientation = wall.traffic.orientation if wall.traffic else "PARALLEL"
        distance_mm = wall.traffic.distance_from_back.to('mm').magnitude if wall.traffic else 0.0

        h_m = wall.geometry.stem_height.to('m').magnitude + wall.geometry.footing_thickness.to('m').magnitude
        height_mm = h_m * 1000.0

        heq_mm = self.interpolate_heq(height_mm, orientation, distance_mm)
        heq_m = heq_mm / 1000.0

        gamma_fill = wall.backfill.unit_weight.to('kN/m**3').magnitude
        qs_kPa = heq_m * gamma_fill

        if qs_kPa <= 0:
            return [], heq_m, qs_kPa

        # LS = qs * H_total * K_a (fuerza horizontal pura, sin componente vertical)
        p_ls = qs_kPa * h_m * k_a
        y_app = h_m / 2.0

        load = GenericLoad(
            name="Sobrecarga Vehicular (LS)",
            load_type=LoadType.LS,
            force_x=Q_(p_ls, "kN/m"),
            force_y=Q_(0.0, "kN/m"),
            y_application=Q_(y_app, "m"),
            x_application=wall.geometry.toe_length + wall.geometry.stem_thickness_base
        )
        return [load], heq_m, qs_kPa