from dataclasses import dataclass
from wall_engine.units.registry import Force, Length

@dataclass
class SectionReinforcement:
    section_name: str
    M_u: Force # kN-m/m
    M_serv: Force # kN-m/m (Momento de servicio para fisuración)
    thickness: Length # m
    d: Length # m
    
    A_s_required: float # cm2/m
    A_s_min: float # cm2/m
    A_s_final: float # cm2/m
    rho_final: float
    
    s_max_crack: float # mm
    f_ss: float # MPa
    
    V_u: Force # kN/m
    phi_V_c: Force # kN/m
    is_shear_safe: bool

@dataclass
class WallReinforcementResult:
    stem: SectionReinforcement
    toe: SectionReinforcement
    heel: SectionReinforcement
    key: SectionReinforcement | None
