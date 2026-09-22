import pint

# Inicializar el registro de unidades
ureg = pint.UnitRegistry()

# Definir unidades de uso frecuente en ingeniería estructural y geotécnica
Length = ureg.Quantity
Pressure = ureg.Quantity
Force = ureg.Quantity
Density = ureg.Quantity
Angle = ureg.Quantity
Moment = ureg.Quantity
Area = ureg.Quantity

# Helper para parsear de manera segura
def Q_(value: float, unit: str) -> pint.Quantity:
    return ureg.Quantity(value, unit)
