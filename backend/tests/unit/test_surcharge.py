import pytest
from wall_engine.calculations.loads.surcharge_calculator import LSSurchargeCalculator


@pytest.mark.parametrize("height_mm, distance_mm, expected", [
    (1500, 0, 1500), (3000, 0, 1050), (6000, 0, 600), (9000, 0, 600),
    (1500, 300, 600), (3000, 300, 600),
    (4500, 0, 825),  # interpolación entre 1050 y 600
])
def test_parallel_table(height_mm, distance_mm, expected):
    """AASHTO / CCP-14 Tabla 3.11.6.4-2 (muros paralelos al tráfico)."""
    calc = LSSurchargeCalculator()
    assert calc.interpolate_heq(height_mm, "PARALLEL", distance_mm) == pytest.approx(expected)


@pytest.mark.parametrize("height_mm, expected", [(1500, 1200), (3000, 900), (6000, 600)])
def test_perpendicular_table(height_mm, expected):
    """AASHTO / CCP-14 Tabla 3.11.6.4-1 (estribos perpendiculares al tráfico)."""
    assert LSSurchargeCalculator().interpolate_heq(height_mm, "PERPENDICULAR") == pytest.approx(expected)
