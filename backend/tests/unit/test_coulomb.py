import pytest
import math
from wall_engine.units.registry import Q_
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.water.entities import Groundwater
from wall_engine.calculations.earth_pressure.coulomb import CoulombEarthPressure

def test_coulomb_ka_matches_aashto_example():
    soil = Soil(
        name="Relleno ejemplo AASHTO",
        unit_weight=Q_(120, "lbf/ft**3"),
        saturated_unit_weight=None,
        friction_angle=Q_(35.0, "degrees"),
        cohesion=Q_(0, "kPa"),
        interface_friction_angle=Q_(23.33, "degrees"),
        bearing_capacity=None
    )
    geom = WallGeometry(
        stem_height=Q_(13.0, "ft"),
        stem_thickness_base=Q_(1.5, "ft"),
        stem_thickness_top=Q_(1.0, "ft"),
        footing_width=Q_(10.0, "ft"),
        footing_thickness=Q_(0.5, "ft"),
        toe_cover_soil=Q_(0.0, "ft"),
        toe_length=Q_(2.58, "ft"),
        heel_length=Q_(5.92, "ft"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(9.46232, "degrees"),
        stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )
    
    calc = CoulombEarthPressure()
    result = calc.calculate(soil, geom, surcharges=[])
    
    assert result.coefficient_active == pytest.approx(0.273, abs=0.001)

def test_coulomb_with_groundwater():
    soil = Soil(
        name="Relleno Arena",
        unit_weight=Q_(18, "kN/m**3"),
        saturated_unit_weight=Q_(20, "kN/m**3"),
        friction_angle=Q_(30.0, "degrees"),
        cohesion=Q_(0, "kPa"),
        interface_friction_angle=Q_(0.0, "degrees"),
        bearing_capacity=None
    )
    geom = WallGeometry(
        stem_height=Q_(6.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(4.0, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(1.0, "m"),
        heel_length=Q_(2.5, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )
    # Nivel freático a 3m de la base.
    water = Groundwater(
        elevation=Q_(3.0, "m"),
        drainage_enabled=False,
        drainage_type=None
    )
    
    calc = CoulombEarthPressure()
    result_dry = calc.calculate(soil, geom, surcharges=[])
    result_wet = calc.calculate(soil, geom, surcharges=[], groundwater=water)
    
    # En estado seco: Pa = 0.5 * 18 * 6^2 * 0.3333 = 108 kN/m
    assert result_dry.soil_active_force.magnitude.to("kN/m").magnitude == pytest.approx(108.0, abs=0.1)
    
    # Con agua a la mitad:
    # Arriba (3m): gamma_dry = 18. Pa1 = 0.5 * 18 * 3^2 * 1/3 = 27 kN/m
    # Rectangulo abajo (3m): p = 18 * 3 * 1/3 = 18. Pa2 = 18 * 3 = 54 kN/m
    # Triangulo abajo (3m): gamma_sub = 20 - 9.80665 = 10.193. Pa3 = 0.5 * 10.193 * 3^2 * 1/3 = 15.29 kN/m
    # Total Pa_wet = 27 + 54 + 15.29 = 96.29 kN/m
    assert result_wet.soil_active_force.magnitude.to("kN/m").magnitude == pytest.approx(96.29, abs=0.1)
    
    # El empuje de la tierra es menor porque el agua le quitó peso efectivo.
    assert result_wet.soil_active_force.magnitude < result_dry.soil_active_force.magnitude
