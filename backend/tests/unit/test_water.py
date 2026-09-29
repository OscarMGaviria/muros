import pytest
import math
import uuid
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.water.entities import Groundwater
from wall_engine.domain.wall.entities import Wall, WallMaterials
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.calculations.water.calculator import WaterPressureCalculator

def create_mock_wall(gw_elevation: float, drainage_enabled: bool) -> Wall:
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(3.5, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(1.0, "m"),
        heel_length=Q_(2.0, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )
    water = Groundwater(
        elevation=Q_(gw_elevation, "m"),
        drainage_enabled=drainage_enabled,
        drainage_type=None
    )
    # Mock materials and soil to satisfy Wall entity (not used in water calc)
    concrete = Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None)
    steel = ReinforcementSteel(Q_(420, "MPa"), None, Q_(200000, "MPa"))
    materials = WallMaterials(concrete, steel, Q_(7.5, "cm"))
    soil = Soil("dummy", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    
    return Wall(
        id=uuid.uuid4(),
        name="Test Wall",
        geometry=geom,
        materials=materials,
        backfill=soil,
        foundation_soil=soil,
        groundwater=water,
        surcharges=[],
        seismic=None
    )

def test_water_pressure_drained():
    wall = create_mock_wall(gw_elevation=3.0, drainage_enabled=True)
    calc = WaterPressureCalculator()
    result = calc.calculate(wall)
    
    # Drenado = No hay fuerzas de agua
    assert result.horizontal_force.magnitude.magnitude == 0
    assert result.uplift.magnitude.magnitude == 0

def test_water_pressure_undrained():
    # Agua a 2m de altura. Gamma_w = 9.80665 kN/m3
    wall = create_mock_wall(gw_elevation=2.0, drainage_enabled=False)
    calc = WaterPressureCalculator()
    result = calc.calculate(wall)
    
    gamma_w = 9.80665
    
    # 1. Fuerza horizontal = 0.5 * gamma_w * hw^2 = 0.5 * 9.80665 * 4 = 19.6133 kN/m
    expected_horizontal = 0.5 * gamma_w * (2**2)
    assert result.horizontal_force.magnitude.to("kN/m").magnitude == pytest.approx(expected_horizontal, abs=0.01)
    assert result.horizontal_force.application_height.to("m").magnitude == pytest.approx(2/3, abs=0.01)
    
    # 2. El agua sobre el talón ya está en el peso saturado del suelo: no se suma aparte
    assert result.vertical_force.magnitude.to("kN/m").magnitude == 0
    
    # 3. Subpresión = 0.5 * (gamma_w * hw) * B = 0.5 * (9.80665 * 2) * 3.5 = 34.323 kN/m (negativo)
    expected_uplift = -0.5 * (gamma_w * 2.0) * 3.5
    assert result.uplift.magnitude.to("kN/m").magnitude == pytest.approx(expected_uplift, abs=0.01)
    assert result.uplift.application_height.to("m").magnitude == pytest.approx(2 * 3.5 / 3)
    assert result.uplift_pressure_at_heel.to("kPa").magnitude == pytest.approx(gamma_w * 2.0)


def test_water_limited_to_total_retained_height():
    # Altura total = fuste 5.0 + zapata 0.5 = 5.5 m; el agua no puede superarla
    wall = create_mock_wall(gw_elevation=8.0, drainage_enabled=False)
    result = WaterPressureCalculator().calculate(wall)
    assert result.water_height.to("m").magnitude == pytest.approx(5.5)
