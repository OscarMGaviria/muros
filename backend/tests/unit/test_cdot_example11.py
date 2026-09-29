"""
Validación contra el Design Example 11 del CDOT Bridge Design Manual
(example/document.md): muro en voladizo de concreto vaciado en sitio, empuje de
Coulomb sobre el plano virtual del talón.

Se omiten las cargas que el motor no modela (baranda DC4, colisión CT, LS
vertical sobre el talón). En el ejemplo el fuste tiene la cara inclinada atrás
(EV2), mientras el motor la asume adelante; por eso se comparan los componentes
que no dependen de esa diferencia.
"""
import math
import uuid
from dataclasses import replace
import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.domain.wall.entities import Wall, WallMaterials
from wall_engine.domain.loads.combinations import LoadType
from wall_engine.domain.loads.entities import TrafficSurcharge
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.codes.ccp14.orchestrator import CCP14Orchestrator


def kip_ft(v):
    return Q_(v, "kip/ft").to("kN/m").magnitude


def kip_ft_ft(v):
    return Q_(v, "kip*ft/ft").to("kN*m/m").magnitude


def ft(v):
    return Q_(v, "ft").to("m").magnitude


def make_cdot_wall(kh=0.0, key_depth_ft=None):
    geom = WallGeometry(
        stem_height=Q_(15.0, "ft"),
        stem_thickness_base=Q_(1.75, "ft"),
        stem_thickness_top=Q_(1.50, "ft"),
        footing_width=Q_(10.0, "ft"),
        footing_thickness=Q_(1.25, "ft"),
        toe_length=Q_(2.75, "ft"),
        heel_length=Q_(5.50, "ft"),
        toe_cover_soil=Q_(2.0, "ft"),
        key_depth=Q_(key_depth_ft, "ft") if key_depth_ft else None,
        key_width=Q_(1.5, "ft") if key_depth_ft else None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees"),
    )
    backfill = Soil("Class 1 Backfill", Q_(0.130, "kip/ft**3"), None, Q_(34, "degrees"),
                    Q_(0, "kPa"), Q_(22.67, "degrees"), None)
    subgrade = Soil("Subgrade", Q_(0.130, "kip/ft**3"), None, Q_(20, "degrees"),
                    Q_(0, "kPa"), None, None)
    return Wall(
        id=uuid.uuid4(),
        name="CDOT Example 11",
        geometry=geom,
        materials=WallMaterials(
            concrete=Concrete(Q_(4.5, "ksi"), Q_(0.150, "kip/ft**3"), None),
            reinforcement=ReinforcementSteel(Q_(60, "ksi"), None, Q_(29000, "ksi")),
            cover=Q_(2.0, "inch"),
        ),
        backfill=backfill,
        foundation_soil=subgrade,
        groundwater=None,
        surcharges=[],
        seismic=SeismicParameters(ag=kh, kh=kh, kv=0.0),
        # Tráfico a 2 ft de la cara trasera: heq = 600 mm (CDOT usa 2.00 ft)
        traffic=TrafficSurcharge(orientation="PARALLEL", distance_from_back=Q_(2.0, "ft")),
    )


@pytest.fixture(scope="module")
def report():
    return CCP14Orchestrator().design_wall(make_cdot_wall())


def load(report, name):
    return next(ld for ld in report.unfactored_loads if ld.name == name)


def test_active_coefficient(report):
    assert report.earth_pressure.coefficient_active == pytest.approx(0.254, abs=0.001)


def test_earth_pressure_on_virtual_back(report):
    """EHH = 4.03 kip/ft a 5.42 ft (H total / 3); EHV = 1.68 kip/ft estabilizante en x = B."""
    eh = load(report, "Empuje Activo Estático")
    assert eh.force_x.to("kN/m").magnitude == pytest.approx(kip_ft(4.03), rel=0.01)
    assert eh.y_application.to("m").magnitude == pytest.approx(ft(5.42), rel=0.01)
    assert eh.force_y.to("kN/m").magnitude == pytest.approx(kip_ft(1.68), rel=0.01)
    assert eh.x_application.to("m").magnitude == pytest.approx(ft(10.0))
    # La componente vertical debe reducir el momento de vuelco
    assert eh.overturning_moment.to("kN*m/m").magnitude < (eh.force_x * eh.y_application).to("kN*m/m").magnitude


def test_vertical_loads(report):
    dc = sum(ld.force_y.to("kN/m").magnitude for ld in report.unfactored_loads if ld.load_type == LoadType.DC)
    # DC1 + DC2 + DC3 = 3.38 + 0.28 + 1.88
    assert dc == pytest.approx(kip_ft(5.54), rel=0.01)
    ev1 = load(report, "Soil over Heel (Rectangular)")
    assert ev1.force_y.to("kN/m").magnitude == pytest.approx(kip_ft(10.73), rel=0.01)
    assert ev1.x_application.to("m").magnitude == pytest.approx(ft(7.25))
    ev3 = load(report, "Soil over Toe")
    assert ev3.force_y.to("kN/m").magnitude == pytest.approx(kip_ft(0.72), rel=0.01)


def test_sliding_strength_ia(report):
    """Deslizamiento: gobierna Strength Ia (DC 0.90, EV 1.00, EH 1.50, LS 1.75); pasivo despreciado."""
    stab = report.stability_results["Strength I"]
    # ΣH = 1.50 (4.03) + 1.75 (1.07) = 7.92 kip/ft
    assert stab.sliding_demand.to("kN/m").magnitude == pytest.approx(kip_ft(7.92), rel=0.02)
    # ΣV sin baranda ni EV2 = 0.90 (5.54) + 1.00 (10.73 + 0.72) + 1.50 (1.68) = 18.95 kip/ft
    expected_cap = kip_ft(18.95) * math.tan(math.radians(20))
    assert stab.sliding_capacity.to("kN/m").magnitude == pytest.approx(expected_cap, rel=0.01)
    # Igual que en el ejemplo: sin dentellón no cumple (RR < ΣH)
    assert stab.sliding_ratio > 1.0


def test_stem_design_forces(report):
    """Base del fuste, Strength Ib: Vu = 6.88 kip/ft, Mu = 38.75 kip-ft/ft."""
    stem = report.structural_design.stem
    assert stem.V_u.to("kN/m").magnitude == pytest.approx(kip_ft(6.88), rel=0.02)
    assert stem.M_u.to("kN*m/m").magnitude == pytest.approx(kip_ft_ft(38.75), rel=0.02)
    # El control de fisuración usa el momento de Service I: 24.59 kip-ft/ft
    assert stem.M_serv.to("kN*m/m").magnitude == pytest.approx(kip_ft_ft(24.59), rel=0.02)


def test_extreme_event_governs_reinforcement_when_larger():
    # Con kh = 0.3 aún gobierna Strength I en el fuste (el estático no se mayora en sismo);
    # con kh = 0.4 gobierna el sismo.
    static = CCP14Orchestrator().design_wall(make_cdot_wall(kh=0.0))
    moderate = CCP14Orchestrator().design_wall(make_cdot_wall(kh=0.3))
    strong = CCP14Orchestrator().design_wall(make_cdot_wall(kh=0.4))
    assert moderate.structural_design.stem.M_u.magnitude == pytest.approx(static.structural_design.stem.M_u.magnitude)
    assert strong.structural_design.stem.M_u > static.structural_design.stem.M_u


def test_key_passive_resistance_is_factored():
    """Con dentellón se suma φep · Rep (φep = 0.50) sobre la franja del dentellón."""
    no_key = CCP14Orchestrator().design_wall(make_cdot_wall())
    with_key = CCP14Orchestrator().design_wall(make_cdot_wall(key_depth_ft=1.0))
    cap_no_key = no_key.stability_results["Strength I"].sliding_capacity.to("kN/m").magnitude
    cap_key = with_key.stability_results["Strength I"].sliding_capacity.to("kN/m").magnitude
    assert cap_key > cap_no_key

    phi = math.radians(20)
    kp = (1 + math.sin(phi)) / (1 - math.sin(phi))
    gamma = Q_(0.130, "kip/ft**3").to("kN/m**3").magnitude
    y1, y2 = ft(2.0 + 1.25), ft(2.0 + 1.25 + 1.0)
    rep = gamma * kp * (y1 + y2) / 2 * (y2 - y1)
    friction = with_key.stability_results["Strength I"].sliding_capacity.to("kN/m").magnitude - 0.5 * rep
    assert friction > 0
    assert friction < cap_no_key  # el bloque inerte reduce la fricción del tramo R1


def ksf(v):
    return Q_(v, "kip/ft**2").to("kPa").magnitude


def test_bearing_check_with_geotechnical_q_n():
    """qn = 7.50 ksf del estudio geotécnico: qR = 0.55 qn = 4.13 ksf; en evento extremo qR = qn."""
    wall = make_cdot_wall(kh=0.1)
    wall.foundation_soil = replace(wall.foundation_soil, bearing_capacity=Q_(7.5, "kip/ft**2"))
    rep = CCP14Orchestrator().design_wall(wall)

    assert "Service I" not in rep.bearing_results
    strength = rep.bearing_results["Strength I"]
    assert strength.uses_geotechnical_q_n
    assert strength.q_resistance == pytest.approx(ksf(0.55 * 7.5))
    assert rep.bearing_results["Extreme Event I-a"].q_resistance == pytest.approx(ksf(7.5))
    assert rep.bearing_results["Extreme Event I-b"].q_resistance == pytest.approx(ksf(7.5))

    # Strength IV: sigma_V = 2.74 ksf en el ejemplo
    assert rep.bearing_results["Strength IV"].q_demand == pytest.approx(ksf(2.74), rel=0.02)
    # Strength Ib: 2.94 ksf en el ejemplo, que además incluye la baranda y LS vertical
    assert ksf(2.5) < strength.q_demand < ksf(2.94)
    assert all(br.is_safe for br in rep.bearing_results.values())


def test_strength_iv_is_evaluated(report):
    assert "Strength IV" in report.stability_results
    assert report.governing_loads["Strength IV"].factors_used[LoadType.DC] in (1.50, 0.90)


def test_heel_design_option_ignores_soil_reaction():
    """
    CDOT 2.2: talón diseñado con su peso y el suelo encima, sin reacción del suelo.
    Strength IV: Vu = 16.03 kip/ft, Mu = 44.07 kip-ft/ft; Service I: 32.33 kip-ft/ft.
    El motor suma además la componente vertical del empuje en el extremo del
    talón (EHV = 1.68 kip/ft a 5.5 ft), que el ejemplo no carga sobre el talón.
    """
    from wall_engine.domain.wall.entities import DesignOptions
    with_reaction = CCP14Orchestrator().design_wall(make_cdot_wall()).structural_design.heel

    wall = make_cdot_wall()
    wall.options = DesignOptions(ignore_heel_soil_reaction=True)
    heel = CCP14Orchestrator().design_wall(wall).structural_design.heel

    ehv, arm = 1.68, 5.5
    assert heel.V_u.to("kN/m").magnitude == pytest.approx(kip_ft(16.03 + 1.5 * ehv), rel=0.01)
    assert heel.M_u.to("kN*m/m").magnitude == pytest.approx(kip_ft_ft(44.07 + 1.5 * ehv * arm), rel=0.01)
    assert heel.M_serv.to("kN*m/m").magnitude == pytest.approx(kip_ft_ft(32.33 + ehv * arm), rel=0.01)
    assert heel.M_u > with_reaction.M_u
