import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import GenericLoad, LoadType
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.calculations.structural.stem_calculator import StemCalculator

def test_stem_calculator():
    # Zapata de 0.5m de espesor, Fuste de 0.5m de espesor en la base
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
    cover = Q_(0.075, "m") # 7.5 cm
    
    # Fuerzas de prueba
    # 1. Empuje horizontal aplicado a 2m desde la base de la zapata
    # (Por lo tanto, actúa a 1.5m sobre la base del fuste)
    load_eh = GenericLoad(
        name="Empuje Activo",
        load_type=LoadType.EH,
        force_x=Q_(100, "kN/m"),
        force_y=Q_(0, "kN/m"),
        x_application=Q_(2.5, "m"),
        y_application=Q_(2.0, "m")
    )
    
    # 2. Fuerza horizontal aplicada por debajo de la base del fuste (Ej. empuje sobre zapata)
    # No debería afectar al fuste.
    load_eh_zapata = GenericLoad(
        name="Empuje Zapata",
        load_type=LoadType.EH,
        force_x=Q_(50, "kN/m"),
        force_y=Q_(0, "kN/m"),
        x_application=Q_(2.5, "m"),
        y_application=Q_(0.25, "m")
    )
    
    loads = [load_eh, load_eh_zapata]
    
    # Factores LRFD
    factors = {
        LoadType.EH: 1.5,
        LoadType.DC: 1.25
    }
    
    calc = StemCalculator()
    res = calc.calculate(loads, factors, geom, concrete, cover)
    
    # Cortante: Solo la fuerza sobre el fuste (100 * 1.5 = 150 kN)
    assert res.V_u.to("kN/m").magnitude == pytest.approx(150.0)
    
    # Momento: Fuerza * Brazo = 150 kN * (2.0 - 0.5)m = 150 * 1.5 = 225 kN-m
    assert res.M_u.to("kN*m/m").magnitude == pytest.approx(225.0)
    
    # Capacidad a cortante (AASHTO / CCP-14 5.8.3.3, beta = 2):
    # d = 0.5m - 0.075m = 425 mm; dv = max(0.9*425, 0.72*500) = 382.5 mm
    # Vc = 0.083 * 2 * sqrt(28) * 1000 * 382.5 / 1000 = 336.0 kN
    # phi_Vc = 0.90 * 336.0 = 302.4 kN
    assert res.V_c.to("kN/m").magnitude == pytest.approx(336.0, abs=0.1)
    assert res.phi_V_c.to("kN/m").magnitude == pytest.approx(302.4, abs=0.1)
    
    # 150 <= 302.4 -> True
    assert res.is_shear_safe == True


def test_stem_ignores_load_types_absent_from_limit_state():
    """Una carga sísmica no debe entrar en un estado límite que no la incluye."""
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
    load_eh = GenericLoad("Empuje", LoadType.EH, Q_(100, "kN/m"), Q_(0, "kN/m"), Q_(2.5, "m"), Q_(2.0, "m"))
    load_eq = GenericLoad("Inercia fuste", LoadType.EQ_I, Q_(40, "kN/m"), Q_(0, "kN/m"), Q_(0.7, "m"), Q_(3.0, "m"))
    
    res = StemCalculator().calculate([load_eh, load_eq], {LoadType.EH: 1.5}, geom, concrete, Q_(0.075, "m"))
    
    assert res.V_u.to("kN/m").magnitude == pytest.approx(150.0)
    assert res.M_u.to("kN*m/m").magnitude == pytest.approx(225.0)
