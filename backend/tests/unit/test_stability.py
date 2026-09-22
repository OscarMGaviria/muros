import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import FactoredResult
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.calculations.stability.calculator import StabilityCalculator

def test_stability_middle_third():
    """Prueba cuando la resultante cae en el tercio medio (toda la zapata en compresión)"""
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
    soil = Soil("Base", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    
    # Fuerzas ficticias
    fy = Q_(300, "kN/m")
    fx = Q_(50, "kN/m")
    # Para que e = 0, el momento respecto a la punta debe ser Fy * (B/2) = 300 * 1.5 = 450
    # Pondremos un momento levemente mayor para tener algo de excentricidad.
    # M = 300 * 1.2 = 360 (Cae a 1.2m de la punta). 
    # e = B/2 - x0 = 1.5 - 1.2 = 0.3m. 
    # Tercio medio de B=3 es B/6 = 0.5m. Por tanto cae dentro.
    factored_load = FactoredResult("TEST", 1, fx, fy, Q_(-360, "kN*m/m"), {})
    
    calc = StabilityCalculator()
    res = calc.calculate(factored_load, geom, soil, is_rock=False)
    
    # Excentricidad
    assert res.eccentricity.to("m").magnitude == pytest.approx(0.3)
    assert res.is_eccentricity_safe == True # 0.3 <= 3/3 (1.0)
    
    # Presiones
    # q = (Fy/B) * (1 +/- 6e/B) = (300/3) * (1 +/- 6*0.3/3) = 100 * (1 +/- 0.6)
    # q_toe = 100 * 1.6 = 160
    # q_heel = 100 * 0.4 = 40
    assert res.q_toe == pytest.approx(160)
    assert res.q_heel == pytest.approx(40)

def test_stability_meyerhof():
    """Prueba cuando la resultante sale del tercio medio (levantamiento del talón)"""
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
    soil = Soil("Base", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    
    fy = Q_(300, "kN/m")
    fx = Q_(50, "kN/m")
    # Cae a x0 = 0.8m de la punta.
    # M = 300 * 0.8 = 240
    # e = 1.5 - 0.8 = 0.7m. Es mayor a B/6 (0.5m), por tanto sale del tercio medio hacia la punta.
    factored_load = FactoredResult("TEST", 1, fx, fy, Q_(-240, "kN*m/m"), {})
    
    calc = StabilityCalculator()
    res = calc.calculate(factored_load, geom, soil, is_rock=False)
    
    assert res.eccentricity.to("m").magnitude == pytest.approx(0.7)
    
    # Presión Meyerhof
    # q_max = 2*Fy / (3 * (B/2 - e)) = 2*300 / (3 * (1.5 - 0.7)) = 600 / (3 * 0.8) = 600 / 2.4 = 250
    assert res.q_toe == pytest.approx(250)
    assert res.q_heel == 0.0
