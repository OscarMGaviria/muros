import pytest
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import LimitState, LoadFactor, LoadType, GenericLoad
from wall_engine.calculations.loads.combinator import CombinationEngine

def test_combination_permutations():
    # 1. Definir un estado límite simulado (STRENGTH I)
    strength_i = LimitState(
        name="STRENGTH_I",
        factors={
            LoadType.DC: LoadFactor(gamma_max=1.25, gamma_min=0.90),
            LoadType.EH: LoadFactor(gamma_max=1.50, gamma_min=0.90)
        }
    )
    
    # 2. Crear algunas cargas genéricas
    # Carga muerta del muro (DC): Va hacia abajo (-Y), genera un momento resistente negativo
    dc_load = GenericLoad(
        name="Wall Weight",
        load_type=LoadType.DC,
        force_x=Q_(0, "kN/m"),
        force_y=Q_(100, "kN/m"), # Hacia abajo la sumamos como positiva en compresión
        x_application=Q_(1.5, "m"),
        y_application=Q_(2.0, "m")
    )
    
    # Carga de empuje (EH): Va hacia la izquierda (+X), genera momento volcador positivo
    eh_load = GenericLoad(
        name="Earth Pressure",
        load_type=LoadType.EH,
        force_x=Q_(50, "kN/m"),
        force_y=Q_(0, "kN/m"),
        x_application=Q_(0, "m"), # X no importa para fuerzas puramente horizontales
        y_application=Q_(3.0, "m")
    )
    
    engine = CombinationEngine()
    results = engine.generate_permutations([dc_load, eh_load], strength_i)
    
    # Como tenemos 2 tipos de carga y ambos tienen max != min, esperamos 4 permutaciones
    assert len(results) == 4
    
    # Verificamos si los factores permutados son correctos
    expected_factor_sets = [
        {LoadType.DC: 1.25, LoadType.EH: 1.50},
        {LoadType.DC: 1.25, LoadType.EH: 0.90},
        {LoadType.DC: 0.90, LoadType.EH: 1.50},
        {LoadType.DC: 0.90, LoadType.EH: 0.90},
    ]
    
    # Para comparar sin preocuparnos por el orden:
    actual_factor_sets = [res.factors_used for res in results]
    
    for expected in expected_factor_sets:
        assert expected in actual_factor_sets
        
    # Verificar aritméticamente el caso más desfavorable para volcamiento:
    # Máximo empuje (EH = 1.50) y mínimo peso retenedor (DC = 0.90)
    worst_overturning = next(r for r in results if r.factors_used[LoadType.EH] == 1.5 and r.factors_used[LoadType.DC] == 0.9)
    
    # Fuerzas resultantes
    assert worst_overturning.sum_force_x.to("kN/m").magnitude == pytest.approx(50 * 1.5) # 75
    assert worst_overturning.sum_force_y.to("kN/m").magnitude == pytest.approx(100 * 0.9) # 90
    
    # Momento = Fx*Y - Fy*X
    # EH: 50 * 3.0 = 150 (positivo) * 1.5 = 225
    # DC: -100 * 1.5 = -150 (negativo) * 0.9 = -135
    # Sum = 225 - 135 = 90
    assert worst_overturning.sum_moment.magnitude == pytest.approx(90)
