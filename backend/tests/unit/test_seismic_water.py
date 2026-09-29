"""Sismo (CCP-14 11.6.5) y nivel freático: coeficientes, combinaciones y cargas de agua."""
import uuid
from dataclasses import replace
import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.domain.wall.entities import Wall, WallMaterials
from wall_engine.domain.water.entities import Groundwater
from wall_engine.domain.loads.combinations import FactoredResult, GenericLoad, LoadType
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.seismic.coefficients import horizontal_seismic_coefficient, site_factor_fpga
from wall_engine.codes.ccp14.combinations import CCP14Combinations
from wall_engine.calculations.stability.calculator import StabilityCalculator
from wall_engine.calculations.structural.footing_calculator import FootingCalculator
from wall_engine.codes.ccp14.orchestrator import CCP14Orchestrator


def geometry(stem_height=6.0):
    return WallGeometry(
        stem_height=Q_(stem_height, "m"), stem_thickness_base=Q_(0.6, "m"), stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(4.0, "m"), footing_thickness=Q_(0.6, "m"), toe_length=Q_(1.0, "m"),
        heel_length=Q_(2.4, "m"), toe_cover_soil=Q_(0.5, "m"), key_depth=None, key_width=None,
        backfill_slope=Q_(0, "degrees"), stem_batter=Q_(0, "degrees"), back_face_angle=Q_(90, "degrees")
    )


def make_wall(kh=0.0, groundwater=None, stem_height=6.0, gamma_eq=0.0):
    return Wall(
        id=uuid.uuid4(), name="Muro", geometry=geometry(stem_height),
        materials=WallMaterials(Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None),
                                ReinforcementSteel(Q_(420, "MPa"), None, Q_(200000, "MPa")), Q_(7.5, "cm")),
        backfill=Soil("Relleno", Q_(19, "kN/m**3"), Q_(21, "kN/m**3"), Q_(32, "degrees"), Q_(0, "kPa"), Q_(21, "degrees"), None),
        foundation_soil=Soil("Fundación", Q_(20, "kN/m**3"), None, Q_(32, "degrees"), Q_(0, "kPa"), None, None),
        groundwater=groundwater, surcharges=[],
        seismic=SeismicParameters(ag=kh, kh=kh, kv=0.0, gamma_eq=gamma_eq),
    )


# ---------------------------------------------------------------- kh (11.6.5.2)

@pytest.mark.parametrize("site, pga, expected", [
    ("A", 0.3, 0.8), ("B", 0.3, 1.0), ("C", 0.35, 1.05), ("D", 0.25, 1.3), ("E", 0.05, 2.5), ("E", 0.6, 0.9),
])
def test_fpga_table(site, pga, expected):
    assert site_factor_fpga(site, pga) == pytest.approx(expected)


def test_kh_from_pga():
    # Perfil D, PGA = 0.25: Fpga = 1.3 -> kh0 = 0.325
    c = horizontal_seismic_coefficient(0.25, "D")
    assert c.kh0 == pytest.approx(0.325) and c.kh == pytest.approx(0.325)
    # Roca (A/B): kh0 = 1.2·Fpga·PGA
    assert horizontal_seismic_coefficient(0.25, "B").kh0 == pytest.approx(1.2 * 0.25)
    # Desplazamiento de 25-50 mm aceptable: kh = 0.5·kh0
    assert horizontal_seismic_coefficient(0.25, "D", allow_displacement=True).kh == pytest.approx(0.1625)
    # Fpga dado por el usuario (p. ej. estudio de sitio)
    assert horizontal_seismic_coefficient(0.25, "F", fpga=1.5).kh0 == pytest.approx(0.375)


def test_site_class_f_requires_fpga():
    with pytest.raises(ValueError):
        horizontal_seismic_coefficient(0.25, "F")


# ----------------------------------------------------- combinaciones (11.6.5.1)

def test_extreme_event_cases():
    # P_A = 100, ΔP_AE = 150 -> P_AE = 250; caso b: max(125, 100) = 125 -> f = 25/150
    cases = CCP14Combinations.extreme_event_I_cases(pa_static=100.0, dpae=150.0, gamma_eq=0.5)
    a, b = cases["Extreme Event I-a"].factors, cases["Extreme Event I-b"].factors
    assert (a[LoadType.EQ_E].gamma_max, a[LoadType.EQ_I].gamma_max) == (1.0, 0.5)
    assert b[LoadType.EQ_E].gamma_max == pytest.approx(25 / 150)
    assert b[LoadType.EQ_I].gamma_max == 1.0
    # P_AE ya incluye el estático: EH con factor 1.0
    assert a[LoadType.EH].gamma_max == a[LoadType.EH].gamma_min == 1.0
    assert a[LoadType.LS].gamma_max == 0.5 and a[LoadType.WA].gamma_max == 1.0


def test_extreme_event_case_b_never_below_static():
    # 0.5·P_AE < P_A: se usa P_A (sin incremento)
    b = CCP14Combinations.extreme_event_I_cases(pa_static=100.0, dpae=50.0)["Extreme Event I-b"]
    assert b.factors[LoadType.EQ_E].gamma_max == 0.0
    assert LoadType.LS not in b.factors  # γEQ = 0


def test_no_extreme_event_without_seismic():
    rep = CCP14Orchestrator().design_wall(make_wall(kh=0.0))
    assert not any("Extreme" in name for name in rep.stability_results)


@pytest.mark.parametrize("gamma_eq, ratio", [(0.0, 1 / 3), (0.5, (1 / 3 + 0.4) / 2), (1.0, 0.4)])
def test_seismic_eccentricity_limit(gamma_eq, ratio):
    """2/3 centrales con γEQ = 0, 8/10 centrales con γEQ = 1 e interpolación."""
    soil = Soil("Base", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    calc = StabilityCalculator()
    b = 4.0
    for e, safe in ((ratio * b - 0.01, True), (ratio * b + 0.01, False)):
        x0 = b / 2 - e
        load = FactoredResult("Extreme Event I-a", 1, Q_(10, "kN/m"), Q_(300, "kN/m"), Q_(-300 * x0, "kN*m/m"), {})
        assert calc.calculate(load, geometry(), soil, gamma_eq=gamma_eq).is_eccentricity_safe == safe


# --------------------------------------------------------------------- agua

def test_footing_uplift_adds_upward_pressure():
    """La subpresión (lineal, u_heel en el talón y 0 en la punta) actúa sobre ambos voladizos."""
    geom = replace(geometry(), toe_length=Q_(1.0, "m"), heel_length=Q_(2.4, "m"))
    stab = StabilityResult("TEST", 1, Q_(0, "m"), True, Q_(0, "kN/m"), Q_(100, "kN/m"), 0.0, 0.0, 0.0)
    soil = Soil("Base", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    concrete = Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None)
    res = FootingCalculator().calculate([], {LoadType.WA: 1.0}, geom, concrete, Q_(0.075, "m"), stab, soil,
                                        uplift_at_heel=40.0)
    # Punta (0 a 1.0 m): u de 0 a 10 kPa -> V = 5 kN/m, M = 5 · (1.0 - 2/3) = 1.667
    assert res.toe.V_u.to("kN/m").magnitude == pytest.approx(5.0)
    assert res.toe.M_u.to("kN*m/m").magnitude == pytest.approx(5.0 / 3)
    # Talón (1.6 a 4.0 m): u de 16 a 40 kPa -> V = 67.2 kN/m
    assert res.heel.V_u.to("kN/m").magnitude == pytest.approx(0.5 * (16 + 40) * 2.4)


def test_wall_with_groundwater():
    dry = CCP14Orchestrator().design_wall(make_wall())
    gw = Groundwater(elevation=Q_(3.0, "m"), drainage_enabled=False, drainage_type=None)
    wet = CCP14Orchestrator().design_wall(make_wall(groundwater=gw))

    names = {ld.name: ld for ld in wet.unfactored_loads}
    hydro = names["Empuje Hidrostático"]
    assert hydro.load_type == LoadType.WA
    assert hydro.force_x.to("kN/m").magnitude == pytest.approx(0.5 * 9.80665 * 9)
    assert hydro.x_application.to("m").magnitude == pytest.approx(4.0)
    uplift = names["Subpresión"]
    assert uplift.force_y.to("kN/m").magnitude == pytest.approx(-0.5 * 9.80665 * 3.0 * 4.0)
    assert "Soil over Heel (Saturated)" in names

    # El agua aumenta la demanda al deslizamiento y la excentricidad
    assert wet.stability_results["Strength I"].sliding_ratio > dry.stability_results["Strength I"].sliding_ratio
    assert wet.stability_results["Strength I"].eccentricity > dry.stability_results["Strength I"].eccentricity
    # y el fuste recibe presión de agua por encima de la zapata
    assert wet.structural_design.stem.M_u > dry.structural_design.stem.M_u


def test_drained_backfill_has_no_water_loads():
    gw = Groundwater(elevation=Q_(3.0, "m"), drainage_enabled=True, drainage_type="Tubo perforado")
    rep = CCP14Orchestrator().design_wall(make_wall(groundwater=gw))
    assert not any(ld.load_type == LoadType.WA for ld in rep.unfactored_loads)


def test_hydrodynamic_load_in_extreme_event():
    gw = Groundwater(elevation=Q_(3.0, "m"), drainage_enabled=False, drainage_type=None, free_draining_backfill=True)
    rep = CCP14Orchestrator().design_wall(make_wall(kh=0.2, groundwater=gw))
    hd = next(ld for ld in rep.unfactored_loads if "Hidrodinámica" in ld.name)
    assert hd.load_type == LoadType.EQ_E
    assert hd.force_x.to("kN/m").magnitude == pytest.approx(7 / 12 * 0.2 * 9.80665 * 9)


def test_tall_wall_seismic_warning():
    rep = CCP14Orchestrator().design_wall(make_wall(kh=0.1, stem_height=18.0))
    assert any("18 m" in w for w in rep.warnings)
