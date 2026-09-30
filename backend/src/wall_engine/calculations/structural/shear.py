import math
from typing import Optional

# Resistencia al corte del concreto sin refuerzo transversal, método simplificado
# de AASHTO LRFD / CCP-14 5.8.3.3 y 5.8.3.4.1 (beta = 2.0), por metro de ancho.
BETA = 2.0
PHI_V = 0.90  # CCP-14 5.5.4.2: corte y torsión en concreto de peso normal


def concrete_shear_capacity(fc_mpa: float, thickness_m: float, d_m: float, a_m: Optional[float] = None) -> tuple[float, float]:
    """
    Vc = 0.083 · β · √f'c · bv · dv (N, MPa, mm), con dv = max(d − a/2, 0.9·d, 0.72·h).
    Si aún no se conoce el refuerzo (a_m None), dv = max(0.9·d, 0.72·h).
    Retorna (Vc, φVc) en kN/m.
    """
    b_mm = 1000.0
    d_mm = max(d_m, 0.001) * 1000.0
    h_mm = thickness_m * 1000.0
    dv_mm = max(0.9 * d_mm, 0.72 * h_mm)
    if a_m is not None:
        dv_mm = max(dv_mm, d_mm - a_m * 1000.0 / 2.0)
    vc_kn = 0.083 * BETA * math.sqrt(fc_mpa) * b_mm * dv_mm / 1000.0
    return vc_kn, PHI_V * vc_kn
