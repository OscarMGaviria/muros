import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.wall.rules import GeometryValidator, InvalidGeometryError

def create_valid_geometry() -> WallGeometry:
    return WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.45, "m"),
        stem_thickness_top=Q_(0.25, "m"),
        footing_width=Q_(3.20, "m"),  # 0.8 + 0.45 + 1.95 = 3.20
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(0.80, "m"),
        heel_length=Q_(1.95, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )

def test_valid_geometry():
    geom = create_valid_geometry()
    # No debería lanzar ninguna excepción
    GeometryValidator.validate(geom)

def test_invalid_negative_height():
    geom = WallGeometry(
        stem_height=Q_(-1.0, "m"),
        stem_thickness_base=Q_(0.45, "m"),
        stem_thickness_top=Q_(0.25, "m"),
        footing_width=Q_(3.20, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(0.80, "m"),
        heel_length=Q_(1.95, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )
    with pytest.raises(InvalidGeometryError, match="altura del fuste"):
        GeometryValidator.validate(geom)

def test_inconsistent_footing_width():
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.45, "m"),
        stem_thickness_top=Q_(0.25, "m"),
        footing_width=Q_(4.00, "m"), # Inconsistente, debería ser 3.20
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(0.80, "m"),
        heel_length=Q_(1.95, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )
    with pytest.raises(InvalidGeometryError, match="Inconsistencia geométrica"):
        GeometryValidator.validate(geom)
