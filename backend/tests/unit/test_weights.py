import pytest
import math
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.domain.wall.entities import Wall, WallMaterials
from wall_engine.calculations.loads.weight_calculator import WeightCalculator
import uuid

def create_test_wall() -> Wall:
    geom = WallGeometry(
        stem_height=Q_(5.0, "m"),
        stem_thickness_base=Q_(0.5, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(3.5, "m"),
        footing_thickness=Q_(0.5, "m"),
        toe_length=Q_(1.0, "m"),
        heel_length=Q_(2.0, "m"),
        toe_cover_soil=Q_(0.5, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    concrete = Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None)
    steel = ReinforcementSteel(Q_(420, "MPa"), None, Q_(200000, "MPa"))
    materials = WallMaterials(concrete, steel, Q_(7.5, "cm"))
    soil = Soil("Relleno", Q_(18, "kN/m**3"), None, Q_(30, "degrees"), Q_(0, "kPa"), None, None)
    
    return Wall(
        id=uuid.uuid4(),
        name="Muro estatico",
        geometry=geom,
        materials=materials,
        backfill=soil,
        foundation_soil=soil,
        groundwater=None,
        surcharges=[],
        seismic=None
    )

def test_concrete_weights():
    wall = create_test_wall()
    calc = WeightCalculator()
    blocks = calc.calculate_concrete_blocks(wall)
    
    # 5 bloques esperados: Zapata (punta, bajo fuste, talón), Fuste Rect, Fuste Triang
    assert len(blocks) == 5
    
    # Peso total del concreto
    total_weight = sum(b.weight.to("kN/m").magnitude for b in blocks)
    
    vol_zapata = 3.5 * 0.5 # 1.75
    vol_rect = 0.3 * 5.0 # 1.50
    vol_tri = 0.5 * 0.2 * 5.0 # 0.50
    expected_vol = 1.75 + 1.50 + 0.50 # 3.75 m3/m
    expected_weight = expected_vol * 24 # 90 kN/m
    
    assert total_weight == pytest.approx(expected_weight)
    
    # Comprobar brazos de palanca (x) desde la punta
    # Zapata: punta (0-1.0), bajo fuste (1.0-1.5), talón (1.5-3.5)
    footing_toe = next(b for b in blocks if b.name == "Footing (Toe)")
    footing_stem = next(b for b in blocks if b.name == "Footing (Under Stem)")
    footing_heel = next(b for b in blocks if b.name == "Footing (Heel)")
    assert footing_toe.x_centroid.to("m").magnitude == pytest.approx(0.5)
    assert footing_stem.x_centroid.to("m").magnitude == pytest.approx(1.25)
    assert footing_heel.x_centroid.to("m").magnitude == pytest.approx(2.5)
    assert footing_heel.weight.to("kN/m").magnitude == pytest.approx(2.0 * 0.5 * 24)
    # El conjunto conserva el centroide de la zapata completa (B/2 = 1.75 m)
    footing_blocks = [footing_toe, footing_stem, footing_heel]
    footing_weight = sum(b.weight.to("kN/m").magnitude for b in footing_blocks)
    x_cg = sum(b.weight.to("kN/m").magnitude * b.x_centroid.to("m").magnitude for b in footing_blocks) / footing_weight
    assert x_cg == pytest.approx(1.75)
    
    # Fuste rect C.G = 1.0 (toe) + 0.5 (base) - 0.15 (mitad tope) = 1.35m
    stem_rect = next(b for b in blocks if "Rectangular" in b.name)
    assert stem_rect.x_centroid.to("m").magnitude == 1.35
    
    # Fuste tri C.G = 1.0 + 2/3*(0.2) = 1.1333m
    stem_tri = next(b for b in blocks if "Triangular" in b.name)
    assert stem_tri.x_centroid.to("m").magnitude == pytest.approx(1.133, abs=0.01)

def test_soil_weights():
    wall = create_test_wall()
    calc = WeightCalculator()
    blocks = calc.calculate_soil_blocks(wall)
    
    # 2 bloques: Talón, Punta
    assert len(blocks) == 2
    
    heel_block = next(b for b in blocks if "Heel" in b.name)
    toe_block = next(b for b in blocks if "Toe" in b.name)
    
    # Peso sobre talón = 2.0 * 5.0 * 18 = 180 kN/m
    assert heel_block.weight.to("kN/m").magnitude == 180
    assert heel_block.x_centroid.to("m").magnitude == 1.0 + 0.5 + 1.0 # 2.5m
    assert heel_block.y_centroid.to("m").magnitude == 0.5 + 2.5 # 3.0m
    
    # Peso sobre punta = 1.0 * 0.5 * 18 = 9 kN/m
    assert toe_block.weight.to("kN/m").magnitude == 9
    assert toe_block.x_centroid.to("m").magnitude == 0.5
    assert toe_block.y_centroid.to("m").magnitude == 0.5 + 0.25 # 0.75m

def test_seismic_inertial_loads():
    from wall_engine.seismic.parameters import SeismicParameters
    from wall_engine.domain.loads.combinations import LoadType
    wall = create_test_wall()
    wall.seismic = SeismicParameters(ag=0.2, kh=0.2, kv=0.0, soil_factor=None, seismic_zone=None)
    calc = WeightCalculator()
    eq_loads = calc.calculate_seismic_inertial_loads(wall)
    
    # 5 bloques de concreto + suelo sobre el talón = 6 cargas EQ.
    # El relleno sobre la punta no forma parte de W_s (CCP-14 11.6.5.1).
    assert len(eq_loads) == 6
    
    total_kh_concrete_weight = sum(b.force_x.to("kN/m").magnitude for b in eq_loads if "PIR" in b.name)
    total_kh_soil_weight = sum(b.force_x.to("kN/m").magnitude for b in eq_loads if "PIS" in b.name)
    
    concrete_weight = 90.0 # From previous test
    soil_weight = 180.0 # Solo el suelo sobre el talón
    
    assert total_kh_concrete_weight == pytest.approx(concrete_weight * 0.2)
    assert total_kh_soil_weight == pytest.approx(soil_weight * 0.2)
    
    # Ensure all are of type EQ and have positive force_x
    for eq_load in eq_loads:
        assert eq_load.load_type == LoadType.EQ_I
        assert eq_load.force_x.magnitude > 0
        assert eq_load.force_y.magnitude == 0


def test_slope_soil_centroid():
    """La cuña del talud crece desde el fuste: su C.G. está a 2/3 del talón desde el fuste."""
    from dataclasses import replace
    wall = create_test_wall()
    wall.geometry = replace(wall.geometry, backfill_slope=Q_(20, "degrees"))
    blocks = WeightCalculator().calculate_soil_blocks(wall)
    slope = next(b for b in blocks if "Slope" in b.name)
    # x = punta 1.0 + fuste 0.5 + 2/3 * talón 2.0
    assert slope.x_centroid.to("m").magnitude == pytest.approx(1.0 + 0.5 + 2.0 * 2 / 3)
    h = 2.0 * math.tan(math.radians(20))
    assert slope.weight.to("kN/m").magnitude == pytest.approx(0.5 * 2.0 * h * 18)



def test_saturated_soil_over_heel():
    """Bajo el nivel freático el suelo sobre el talón pesa con gamma_sat (incluye el agua)."""
    from dataclasses import replace
    from wall_engine.domain.water.entities import Groundwater
    wall = create_test_wall()
    wall.backfill = replace(wall.backfill, saturated_unit_weight=Q_(20, "kN/m**3"))
    # Agua a 2.5 m de la base: 2.0 m saturados sobre la zapata (0.5 m) y 3.0 m secos
    wall.groundwater = Groundwater(elevation=Q_(2.5, "m"), drainage_enabled=False, drainage_type=None)
    blocks = WeightCalculator().calculate_soil_blocks(wall)
    sat = next(b for b in blocks if b.name == "Soil over Heel (Saturated)")
    dry = next(b for b in blocks if b.name == "Soil over Heel (Rectangular)")
    assert sat.weight.to("kN/m").magnitude == pytest.approx(2.0 * 2.0 * 20)
    assert dry.weight.to("kN/m").magnitude == pytest.approx(2.0 * 3.0 * 18)
    assert sat.y_centroid.to("m").magnitude == pytest.approx(1.5)
    
    # Con drenaje no hay suelo saturado
    wall.groundwater = replace(wall.groundwater, drainage_enabled=True)
    names = [b.name for b in WeightCalculator().calculate_soil_blocks(wall)]
    assert "Soil over Heel (Saturated)" not in names
