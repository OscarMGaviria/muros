import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.calculations.earth_pressure.mononobe_okabe import MononobeOkabeEarthPressure

def test_mononobe_okabe_zero_seismic():
    """
    Si kh=0 y kv=0, el incremento dinámico debe ser nulo y K_AE == K_a.
    """
    soil = Soil(
        name="Relleno Arena",
        unit_weight=Q_(18, "kN/m**3"),
        saturated_unit_weight=None,
        friction_angle=Q_(30.0, "degrees"),
        cohesion=Q_(0, "kPa"),
        interface_friction_angle=Q_(0.0, "degrees"),
        bearing_capacity=None
    )
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(3.0, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(0.5, "m"),
        heel_length=Q_(2.0, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    seismic = SeismicParameters(
        ag=0.0,
        kh=0.0,
        kv=0.0,
        soil_factor=None,
        seismic_zone=None
    )
    
    calc = MononobeOkabeEarthPressure()
    result = calc.calculate(soil, geom, seismic)
    
    # El incremento dinámico debe ser 0
    assert result.seismic_active_force.magnitude.magnitude == pytest.approx(0, abs=0.001)

def test_mononobe_okabe_active():
    """
    Si kh>0, el empuje sísmico debe ser mayor al estático,
    y el incremento debe aplicarse a 0.6H.
    """
    soil = Soil(
        name="Relleno",
        unit_weight=Q_(18, "kN/m**3"),
        saturated_unit_weight=None,
        friction_angle=Q_(30.0, "degrees"),
        cohesion=Q_(0, "kPa"),
        interface_friction_angle=Q_(0.0, "degrees"),
        bearing_capacity=None
    )
    geom = WallGeometry(
        stem_height=Q_(10.0, "m"), # h_ret = 10m
        stem_thickness_base=Q_(1.0, "m"),
        stem_thickness_top=Q_(0.5, "m"),
        footing_width=Q_(5.0, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(1.0, "m"),
        heel_length=Q_(0.0, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    seismic = SeismicParameters(
        ag=0.2,
        kh=0.2,
        kv=0.0,
        soil_factor=None,
        seismic_zone=None
    )
    
    calc = MononobeOkabeEarthPressure()
    result = calc.calculate(soil, geom, seismic)
    
    # El estático era Ka = 1/3, Pa = 0.5 * 18 * 100 * 1/3 = 300 kN/m
    assert result.soil_active_force.magnitude.magnitude == pytest.approx(300, abs=0.01)
    
    # El incremento dinámico debe existir
    assert result.seismic_active_force.magnitude.magnitude > 0
    
    # Debe aplicarse a 0.6H = 6m
    assert result.seismic_active_force.application_height.magnitude == pytest.approx(6.0, abs=0.01)
