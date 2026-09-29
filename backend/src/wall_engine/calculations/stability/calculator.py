import math
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import FactoredResult
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry


def key_passive_resistance(geometry: WallGeometry, foundation_soil: Soil) -> tuple[float, float]:
    """
    Empuje pasivo nominal frente al dentellón (AASHTO 11.6.3.5): se desprecia el
    suelo sobre la punta y la zapata, y solo se cuenta la franja entre la base de
    la zapata (y1) y el fondo del dentellón (y2), con profundidades medidas desde
    la superficie sobre la punta. Kp de Rankine (beta = 0, delta = 0).
    Retorna (Rep en kN/m, brazo z en m medido hacia abajo desde la base de la zapata).
    """
    d_key = geometry.key_depth.to("m").magnitude if geometry.key_depth else 0.0
    if d_key <= 0:
        return 0.0, 0.0
    phi_f = foundation_soil.friction_angle.to("radians").magnitude
    k_p = (1 + math.sin(phi_f)) / (1 - math.sin(phi_f))
    gamma_f = foundation_soil.unit_weight.to("kN/m**3").magnitude
    y1 = geometry.toe_cover_soil.to("m").magnitude + geometry.footing_thickness.to("m").magnitude
    p1 = gamma_f * k_p * y1           # presión en la base de la zapata
    dp = gamma_f * k_p * d_key        # incremento hasta el fondo del dentellón
    rep = p1 * d_key + 0.5 * dp * d_key
    z = (p1 * d_key * d_key / 2 + 0.5 * dp * d_key * (2 * d_key / 3)) / rep
    return rep, z


class StabilityCalculator:
    
    def calculate(
        self,
        factored_load: FactoredResult,
        geometry: WallGeometry,
        foundation_soil: Soil,
        is_rock: bool = False,
        gamma_eq: float = 1.0
    ) -> StabilityResult:
        
        b = geometry.footing_width.to("m").magnitude
        
        fx = factored_load.sum_force_x.to("kN/m").magnitude
        fy = factored_load.sum_force_y.to("kN/m").magnitude
        m_toe = factored_load.sum_moment.to("kN*m/m").magnitude
        
        # 1. Volcamiento (Excentricidad)
        if fy <= 0:
            x_0 = 0
            e_mag = b / 2
        else:
            # x_0 = - (Suma Momentos) / Suma Fy (por convención M_o = Fx*Y - Fy*X)
            x_0 = -m_toe / fy
            # Excentricidad respecto al centro de la zapata (B/2)
            e_mag = (b / 2) - x_0
            
        e = Q_(e_mag, "m")
        
        # Límite de excentricidad: B/3 para suelo, B/4 para roca (AASHTO/CCP-14).
        # En sismo (11.6.5.1) la resultante debe quedar en los 2/3 centrales de la
        # base con γEQ = 0 (e ≤ B/3) y en los 8/10 centrales con γEQ = 1 (e ≤ 0.4B),
        # interpolando linealmente para valores intermedios.
        is_extreme = 'Extreme' in factored_load.limit_state_name
        if is_extreme:
            e_limit = b * (1 / 3 + gamma_eq * (0.4 - 1 / 3))
        else:
            e_limit = (b / 4) if is_rock else (b / 3)
        # Absoluto porque la resultante puede caer hacia el talón o la punta
        is_safe_ecc = abs(e_mag) <= e_limit
        
        # 2. Deslizamiento
        phi_base = foundation_soil.friction_angle.to("radians").magnitude
        
        # Implementación CDOT (Bloque Inclinado) para dentellón
        # Si hay dentellón, la zapata se divide en R2 (plano) y R1 (plano inclinado delta_sub)
        d_key = geometry.key_depth.to("m").magnitude if geometry.key_depth else 0.0
        if d_key > 0:
            # Asumimos que el dentellón está ubicado bajo el fuste.
            # X_key = longitud del talón + parte del fuste
            x_key = geometry.heel_length.to("m").magnitude + geometry.stem_thickness_base.to("m").magnitude
            # delta_sub es el ángulo del bloque inerte
            delta_sub = math.atan(d_key / x_key) if x_key > 0 else 0.0
            
            # Repartir Fy (peso) proporcionalmente al área de la base para R1 (atrás) y R2 (adelante)
            # R1 actúa sobre X_key, R2 actúa sobre (B - X_key)
            # Por simplicidad asumimos presión vertical uniforme sigma_v = Fy / B para la fricción.
            r1 = fy * (x_key / b)
            r2 = fy * ((b - x_key) / b)
            
            # CDOT: R1 resbala sobre suelo-suelo (phi) afectado por cos(delta_sub)
            # R2 resbala sobre concreto-suelo (típicamente 0.8 phi o phi puro)
            # Asumiremos phi puro por cast-in-place AASHTO.
            friction_cap = (r1 * math.tan(phi_base) * math.cos(delta_sub)) + (r2 * math.tan(phi_base))
        else:
            friction_cap = fy * math.tan(phi_base)
        
        # Factores de resistencia (AASHTO/CCP-14 Tabla 11.5.7-1 y 11.5.8):
        # fricción φτ = 1.0; empuje pasivo φep = 0.50; en Evento Extremo ambos 1.0.
        phi_tau = 1.0
        phi_ep = 1.0 if is_extreme else 0.50

        # Empuje pasivo: solo el movilizado por el dentellón (AASHTO 11.6.3.5)
        passive_cap, _ = key_passive_resistance(geometry, foundation_soil)

        # Capacidad factorada: φτ·R_τ + φep·R_ep
        friction_cap = phi_tau * friction_cap
        passive_cap = phi_ep * passive_cap
            
        sliding_cap = friction_cap + passive_cap
        
        if foundation_soil.cohesion:
            pass 
            
        sliding_demand = abs(fx)
        sliding_ratio = sliding_demand / sliding_cap if sliding_cap > 0 else float('inf')
        
        # 3. Presiones de Contacto (Bearing)
        q_toe = 0.0
        q_heel = 0.0
        
        if fy > 0:
            # Resultante dentro del tercio medio (toda la zapata en compresión)
            if abs(e_mag) <= b / 6:
                q_toe = (fy / b) * (1 + (6 * e_mag / b))
                q_heel = (fy / b) * (1 - (6 * e_mag / b))
            else:
                # Resultante fuera del tercio medio (levantamiento del talón)
                # Distribución triangular de Meyerhof
                if e_mag > 0: # Cae hacia la punta
                    q_toe = (2 * fy) / (3 * (b/2 - e_mag))
                    q_heel = 0.0
                else: # Cae hacia el talón
                    q_toe = 0.0
                    q_heel = (2 * fy) / (3 * (b/2 - abs(e_mag)))
                    
        return StabilityResult(
            limit_state=factored_load.limit_state_name,
            permutation_id=factored_load.permutation_id,
            eccentricity=e,
            is_eccentricity_safe=is_safe_ecc,
            sliding_demand=Q_(sliding_demand, "kN/m"),
            sliding_capacity=Q_(sliding_cap, "kN/m"),
            sliding_ratio=sliding_ratio,
            q_toe=q_toe,
            q_heel=q_heel
        )
