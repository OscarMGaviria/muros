from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Length, Angle

@dataclass(frozen=True)
class WallGeometry:
    stem_height: Length
    stem_thickness_base: Length
    stem_thickness_top: Length

    footing_width: Length
    footing_thickness: Length
    toe_length: Length
    heel_length: Length
    toe_cover_soil: Length

    key_depth: Optional[Length]
    key_width: Optional[Length]

    backfill_slope: Angle
    stem_batter: Angle
    back_face_angle: Angle # Angulo theta de la cara trasera (90 si es vertical)
