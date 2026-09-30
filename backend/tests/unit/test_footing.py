import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import GenericLoad, LoadType
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.calculations.structural.footing_calculator import FootingCalculator
from wall_engine.domain.soil.entities import Soil

SOIL = Soil("Base", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)

def test_footing_calculator():
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
    
    concrete = Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None)
    cover = Q_(0.075, "m")
    
    # Simular presión uniforme de 100 kPa
    stab = StabilityResult("TEST", 1, Q_(0, "m"), True, Q_(0, "kN/m"), Q_(100, "kN/m"), 0.0, 100.0, 100.0)
    
    # Fuerzas hacia abajo en el talón:
    # Peso de la tierra = 200 kN aplicado en el centro del talón (x = 0.5 + 0.5 + 1.0 = 2.0m)
    # Convención del motor: force_y > 0 es carga hacia abajo (pesos).
    # Factor LRFD = 1.0 para simplificar
    load_soil = GenericLoad("Soil Heel", LoadType.EV, Q_(0, "kN/m"), Q_(200, "kN/m"), Q_(2.0, "m"), Q_(2.5, "m"))
    
    # Fuerzas hacia abajo en la punta:
    # Peso del concreto de la punta = 6 kN (0.5m x 0.5m x 24 kN/m3) aplicado en x = 0.25m
    load_toe = GenericLoad("Toe Concrete", LoadType.DC, Q_(0, "kN/m"), Q_(6, "kN/m"), Q_(0.25, "m"), Q_(0.25, "m"))
    
    loads = [load_soil, load_toe]
    factors = {LoadType.EV: 1.0, LoadType.DC: 1.0}
    
    calc = FootingCalculator()
    res = calc.calculate(loads, factors, geom, concrete, cover, stab, SOIL)
    
    # ==========================
    # PUNTA (Toe)
    # ==========================
    # Presión uniforme 100 kPa sobre 0.5m -> 50 kN hacia arriba
    # Centro de la presión = 0.25m (A 0.25m del corte en x=0.5m)
    # V_up = 50 kN. V_down = 6 kN -> Vu = 44 kN
    assert res.toe.V_u.to("kN/m").magnitude == pytest.approx(44.0)
    
    # M_up = 50 * 0.25 = 12.5 kN-m
    # M_down = 6 * 0.25 = 1.5 kN-m -> Mu = 11.0 kN-m
    assert res.toe.M_u.to("kN*m/m").magnitude == pytest.approx(11.0)
    
    # ==========================
    # TALÓN (Heel)
    # ==========================
    # Presión uniforme 100 kPa sobre 2.0m -> 200 kN hacia arriba
    # V_down = 200 kN (Tierra)
    # Vu = 200 - 200 = 0
    assert res.heel.V_u.to("kN/m").magnitude == pytest.approx(0.0)
    
    # Centro de presión del suelo a 1.0m del corte en x=1.0m
    # M_up = 200 * 1.0 = 200 kN-m
    # Brazo de la tierra = 2.0m (pos) - 1.0m (corte) = 1.0m
    # M_down = 200 * 1.0 = 200 kN-m -> Mu = 0.0
    assert res.heel.M_u.to("kN*m/m").magnitude == pytest.approx(0.0)

def test_footing_calculator_with_key():
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(3.0, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_length=Q_(0.5, "m"),
        heel_length=Q_(2.0, "m"),
        toe_cover_soil=Q_(0, "m"),
        key_depth=Q_(0.5, "m"),
        key_width=Q_(0.4, "m"),
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    
    concrete = Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None)
    cover = Q_(0.075, "m")
    stab = StabilityResult("TEST", 1, Q_(0, "m"), True, Q_(0, "kN/m"), Q_(100, "kN/m"), 0.0, 100.0, 100.0)
    
    calc = FootingCalculator()
    res = calc.calculate([], {}, geom, concrete, cover, stab, SOIL)
    
    assert res.key is not None
    # Pasivo sobre la franja del dentellón (Kp = 3 para phi = 30):
    # y1 = 0 (sin relleno sobre la punta) + 0.5 (zapata); p1 = 18 * 3 * 0.5 = 27 kPa
    # Rep = 27 * 0.5 + 0.5 * 27 * 0.5 = 20.25 kN/m
    assert res.key.V_u.to("kN/m").magnitude == pytest.approx(20.25)
    # z = (27 * 0.5^2 / 2 + 6.75 * 2 * 0.5 / 3) / 20.25 = 0.2778 m -> Mu = 5.625 kN-m/m
    assert res.key.M_u.to("kN*m/m").magnitude == pytest.approx(5.625)
    # d = 0.4 - 0.075 = 325 mm; dv = max(0.9*325, 0.72*400) = 292.5 mm
    # Vc = 0.083 * 2 * sqrt(28) * 1000 * 292.5 / 1000 = 256.9; phi_Vc = 0.90 * 256.9 = 231.2
    assert res.key.phi_V_c.to("kN/m").magnitude == pytest.approx(231.2, abs=0.2)
    assert res.key.is_shear_safe == True


def test_footing_ignores_load_types_absent_from_limit_state():
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
    concrete = Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None)
    stab = StabilityResult("TEST", 1, Q_(0, "m"), True, Q_(0, "kN/m"), Q_(100, "kN/m"), 0.0, 0.0, 0.0)
    load_soil = GenericLoad("Soil Heel", LoadType.EV, Q_(0, "kN/m"), Q_(200, "kN/m"), Q_(2.0, "m"), Q_(2.5, "m"))
    
    # EV no está en los factores: no debe cargar el talón
    res = FootingCalculator().calculate([load_soil], {LoadType.DC: 1.25}, geom, concrete, Q_(0.075, "m"), stab, SOIL)
    assert res.heel.M_u.to("kN*m/m").magnitude == pytest.approx(0.0)
    
    # Con EV = 1.35 y sin reacción del suelo: M = 1.35 * 200 * 1.0
    res = FootingCalculator().calculate([load_soil], {LoadType.EV: 1.35}, geom, concrete, Q_(0.075, "m"), stab, SOIL)
    assert res.heel.M_u.to("kN*m/m").magnitude == pytest.approx(270.0)
