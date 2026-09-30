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
    Si kh>0, el empuje sísmico debe ser mayor al estático, y la resultante total
    P_AE se ubica a H/3 por defecto (CCP-14 11.6.5.3).
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
    
    # H = fuste 10.0 + zapata 0.5 = 10.5 m
    # El estático es Ka = 1/3, Pa = 0.5 * 18 * 10.5^2 * 1/3 = 330.75 kN/m
    assert result.soil_active_force.magnitude.magnitude == pytest.approx(330.75, abs=0.01)
    
    # El incremento dinámico debe existir
    assert result.seismic_active_force.magnitude.magnitude > 0
    
    # Con P_AE total a H/3 (y P_A a H/3), el incremento también queda a H/3 = 3.5 m
    assert result.seismic_active_force.application_height.magnitude == pytest.approx(3.5, abs=0.01)
    assert result.coefficient_seismic_active > result.coefficient_active
    assert result.warnings == []



def _soil(phi=30.0, gamma_sat=None):
    return Soil("Relleno", Q_(18, "kN/m**3"), Q_(gamma_sat, "kN/m**3") if gamma_sat else None,
                Q_(phi, "degrees"), Q_(0, "kPa"), Q_(0.0, "degrees"), None)


def _geom(beta=0.0):
    return WallGeometry(
        stem_height=Q_(10.0, "m"), stem_thickness_base=Q_(1.0, "m"), stem_thickness_top=Q_(0.5, "m"),
        footing_width=Q_(5.0, "m"), footing_thickness=Q_(0.5, "m"), toe_cover_soil=Q_(0.0, "m"),
        toe_length=Q_(1.0, "m"), heel_length=Q_(3.0, "m"), key_depth=None, key_width=None,
        backfill_slope=Q_(beta, "degrees"), stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )


def test_pae_height_option():
    """Con la opción 0.5h, la resultante total P_AE = P_A + ΔP_AE queda a 0.5h."""
    seismic = SeismicParameters(ag=0.2, kh=0.2, kv=0.0, pae_height_ratio=0.5)
    r = MononobeOkabeEarthPressure().calculate(_soil(), _geom(), seismic)
    pa = r.soil_active_force.magnitude.to("kN/m").magnitude
    dpae = r.seismic_active_force.magnitude.to("kN/m").magnitude
    y_total = (pa * 10.5 / 3 + dpae * r.seismic_active_force.application_height.to("m").magnitude) / (pa + dpae)
    assert y_total == pytest.approx(0.5 * 10.5)


def test_mononobe_not_applicable_warns():
    """φ − β − θMO < 0: la norma pide otro método; el motor avisa (CCP-14 11.6.5.3)."""
    seismic = SeismicParameters(ag=0.4, kh=0.4, kv=0.0)
    r = MononobeOkabeEarthPressure().calculate(_soil(phi=30), _geom(beta=15), seismic)
    assert len(r.warnings) == 1
    assert "GLE" in r.warnings[0]


def test_hydrodynamic_pressure_free_draining_backfill():
    """Relleno de drenaje libre: P_wd = 7/12·kh·γw·hw² a 0.4·hw (Westergaard)."""
    from wall_engine.domain.water.entities import Groundwater
    water = Groundwater(elevation=Q_(4.0, "m"), drainage_enabled=False, drainage_type=None,
                        free_draining_backfill=True)
    seismic = SeismicParameters(ag=0.2, kh=0.2, kv=0.0)
    r = MononobeOkabeEarthPressure().calculate(_soil(gamma_sat=20), _geom(), seismic, groundwater=water)
    hd = r.hydrodynamic_force
    assert hd.magnitude.to("kN/m").magnitude == pytest.approx(7 / 12 * 0.2 * 9.80665 * 16)
    assert hd.application_height.to("m").magnitude == pytest.approx(1.6)


def test_saturated_backfill_uses_total_unit_weight():
    """Relleno que no drena libremente: el agua se mueve con el suelo (peso total) y no hay hidrodinámica."""
    from wall_engine.domain.water.entities import Groundwater
    seismic = SeismicParameters(ag=0.2, kh=0.2, kv=0.0)
    impermeable = Groundwater(elevation=Q_(4.0, "m"), drainage_enabled=False, drainage_type=None)
    free = Groundwater(elevation=Q_(4.0, "m"), drainage_enabled=False, drainage_type=None, free_draining_backfill=True)
    r_imp = MononobeOkabeEarthPressure().calculate(_soil(gamma_sat=20), _geom(), seismic, groundwater=impermeable)
    r_free = MononobeOkabeEarthPressure().calculate(_soil(gamma_sat=20), _geom(), seismic, groundwater=free)
    assert r_imp.hydrodynamic_force is None
    # El incremento con peso total es mayor que con peso sumergido
    assert r_imp.seismic_active_force.magnitude > r_free.seismic_active_force.magnitude
