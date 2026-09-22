import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import FactoredResult
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.calculations.foundation.bearing_capacity import BearingCapacityCalculator

def test_bearing_capacity_factors():
    """Prueba los factores Nc, Nq, Ngamma para suelo típico (phi=30)"""
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(3.0, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_length=Q_(0.5, "m"),
        heel_length=Q_(2.0, "m"),
        toe_cover_soil=Q_(0, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    soil = Soil("Foundation", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    
    # Fuerzas sin excentricidad ni corte (H=0)
    factored_load = FactoredResult("TEST", 1, Q_(0, "kN/m"), Q_(300, "kN/m"), Q_(-450, "kN*m/m"), {})
    stab = StabilityResult("TEST", 1, Q_(0.0, "m"), True, Q_(0, "kN/m"), Q_(100, "kN/m"), 0.0, 100, 100)
    
    calc = BearingCapacityCalculator()
    res = calc.calculate(stab, factored_load, geom, soil)
    
    # Valores teóricos aproximados para phi=30
    assert res.N_q == pytest.approx(18.4, abs=0.1)
    assert res.N_c == pytest.approx(30.14, abs=0.1)
    assert res.N_gamma == pytest.approx(22.4, abs=0.1)
    
    # Al no haber H, i = 1.0
    assert res.i_q == 1.0
    assert res.i_c == 1.0
    assert res.i_gamma == 1.0
    
    # Ancho efectivo B' = 3.0 (porque e=0)
    assert res.effective_width == 3.0
    
    # Capacidad: 0.5 * 18 * 3.0 * 22.4 = 604.8
    assert res.q_nominal.to("kPa").magnitude == pytest.approx(604.8, abs=5.0)

def test_bearing_capacity_inclination():
    """Prueba que el empuje H reduzca la capacidad portante"""
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(3.0, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_length=Q_(0.5, "m"),
        heel_length=Q_(2.0, "m"),
        toe_cover_soil=Q_(0, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    soil = Soil("Foundation", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    
    # Con carga horizontal H = 100
    factored_load = FactoredResult("TEST", 1, Q_(100, "kN/m"), Q_(300, "kN/m"), Q_(-450, "kN*m/m"), {})
    stab = StabilityResult("TEST", 1, Q_(0.0, "m"), True, Q_(100, "kN/m"), Q_(150, "kN/m"), 0.66, 100, 100)
    
    calc = BearingCapacityCalculator()
    res = calc.calculate(stab, factored_load, geom, soil)
    
    # i_q = (1 - H/V)^2 = (1 - 100/300)^2 = (2/3)^2 = 0.444
    assert res.i_q == pytest.approx(0.444, abs=0.01)
    
    # i_gamma = (1 - H/V)^3 = (2/3)^3 = 0.296
    assert res.i_gamma == pytest.approx(0.296, abs=0.01)
    
    # La capacidad debe caer drásticamente
    # 604.8 * 0.296 = 179
    assert res.q_nominal.to("kPa").magnitude == pytest.approx(179, abs=5.0)
