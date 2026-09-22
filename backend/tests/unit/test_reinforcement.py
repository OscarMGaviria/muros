import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.results.stem_design import StemForcesResult
from wall_engine.domain.results.footing_design import FootingDesignResult, FootingSectionForces
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.calculations.structural.reinforcement_calculator import ReinforcementCalculator

def test_reinforcement_calculator():
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
    steel = ReinforcementSteel(Q_(420, "MPa"), None, Q_(200000, "MPa"))
    cover = Q_(0.075, "m")
    
    # Stem ficticio: Mu = 200 kN-m
    stem_forces = StemForcesResult(
        V_u=Q_(100, "kN/m"),
        M_u=Q_(200, "kN*m/m"),
        M_serv=Q_(133.3, "kN*m/m"),
        V_c=Q_(200, "kN/m"),
        phi_V_c=Q_(150, "kN/m"),
        is_shear_safe=True
    )
    
    # Footing ficticio:
    # Toe: Mu = 50
    # Heel: Mu = 10
    footing_forces = FootingDesignResult(
        toe=FootingSectionForces(Q_(50, "kN/m"), Q_(50, "kN*m/m"), Q_(33.3, "kN*m/m"), Q_(200, "kN/m"), Q_(150, "kN/m"), True),
        heel=FootingSectionForces(Q_(50, "kN/m"), Q_(10, "kN*m/m"), Q_(6.7, "kN*m/m"), Q_(200, "kN/m"), Q_(150, "kN/m"), True),
        key=None
    )
    
    calc = ReinforcementCalculator()
    res = calc.calculate(stem_forces, footing_forces, geom, concrete, steel, cover)
    
    # ==========================
    # STEM (Mu = 200 kN-m)
    # ==========================
    # b = 1000, d = 425 mm, fc = 28, fy = 420
    # Rn = 200e6 / (0.9 * 1000 * 425^2) = 1.23 MPa
    # rho = (0.85*28/420) * [1 - sqrt(1 - 2*1.23/(0.85*28))] = 0.0566 * [1 - sqrt(1 - 0.1033)] = 0.0030
    # As_req = 0.0030 * 1000 * 425 = 1275 mm2 = 12.75 cm2
    assert res.stem.A_s_required == pytest.approx(12.8, abs=0.2)
    
    # As_min = Max entre Temp (9.0 cm2) y Flexión Normativa 5.7.3.3.2 (M_cr = 148.8 kN-m -> As = 9.45 cm2)
    assert res.stem.A_s_min == pytest.approx(9.45, abs=0.05)
    
    # Final = max(12.75, 9.45) = 12.75
    assert res.stem.A_s_final == pytest.approx(12.8, abs=0.2)
    
    # ==========================
    # HEEL (Mu = 10 kN-m) - Caso de cuantía mínima
    # ==========================
    # As_req debe ser muy bajo, por lo que dominará As_min = 9.0 cm2
    assert res.heel.A_s_required < 9.0
    assert res.heel.A_s_final == pytest.approx(9.0)
