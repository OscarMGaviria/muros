"""
Coeficiente sísmico horizontal para muros (CCP-14 11.6.5.2).

kh0 = Fpga · PGA; en perfiles A o B (roca) kh0 = 1.2 · Fpga · PGA.
Si el muro puede desplazarse de 25 a 50 mm durante el sismo, kh puede reducirse
a 0.5 · kh0 sin análisis de Newmark (11.6.5.2.2).
"""
from dataclasses import dataclass
from typing import Optional

# Tabla 3.10.3.2-1: Fpga por tipo de perfil y PGA (interpolación lineal)
_PGA_POINTS = [0.1, 0.2, 0.3, 0.4, 0.5]
_FPGA_TABLE = {
    "A": [0.8, 0.8, 0.8, 0.8, 0.8],
    "B": [1.0, 1.0, 1.0, 1.0, 1.0],
    "C": [1.2, 1.2, 1.1, 1.0, 1.0],
    "D": [1.6, 1.4, 1.2, 1.1, 1.0],
    "E": [2.5, 1.7, 1.2, 0.9, 0.9],
}


def site_factor_fpga(site_class: str, pga: float) -> float:
    site_class = site_class.upper()
    if site_class == "F":
        raise ValueError("Perfil de suelo F: se requiere un estudio de respuesta de sitio (Tabla 3.10.3.2-1, nota 2); ingrese Fpga.")
    if site_class not in _FPGA_TABLE:
        raise ValueError(f"Tipo de perfil de suelo desconocido: {site_class}")
    values = _FPGA_TABLE[site_class]
    if pga <= _PGA_POINTS[0]:
        return values[0]
    if pga >= _PGA_POINTS[-1]:
        return values[-1]
    for i in range(len(_PGA_POINTS) - 1):
        x0, x1 = _PGA_POINTS[i], _PGA_POINTS[i + 1]
        if x0 <= pga <= x1:
            return values[i] + (pga - x0) / (x1 - x0) * (values[i + 1] - values[i])
    return values[-1]


@dataclass(frozen=True)
class SeismicCoefficient:
    fpga: float
    kh0: float
    kh: float


def horizontal_seismic_coefficient(
    pga: float,
    site_class: str,
    fpga: Optional[float] = None,
    allow_displacement: bool = False,
) -> SeismicCoefficient:
    """Calcula kh0 y kh. Si no se da Fpga, se toma de la Tabla 3.10.3.2-1."""
    f = fpga if fpga is not None else site_factor_fpga(site_class, pga)
    kh0 = f * pga
    if site_class.upper() in ("A", "B"):
        kh0 *= 1.2
    kh = 0.5 * kh0 if allow_displacement else kh0
    return SeismicCoefficient(fpga=f, kh0=kh0, kh=kh)
