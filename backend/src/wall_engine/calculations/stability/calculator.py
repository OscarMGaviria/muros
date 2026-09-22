import math
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import FactoredResult
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry

class StabilityCalculator:
    
    def calculate(
        self,
        factored_load: FactoredResult,
        geometry: WallGeometry,
        foundation_soil: Soil,
        is_rock: bool = False
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
        
        # Límite de excentricidad típico: B/3 para suelo, B/4 para roca (AASHTO/CCP-14)
        # En LRFD extremo puede ser B/3 o B/2 dependiendo del estado límite, pero
        # tomaremos B/3 como estándar conservador general (se puede ajustar luego por estado límite).
        is_extreme = 'Extreme' in factored_load.limit_state_name
        e_limit = (0.4 * b) if is_extreme else ((b / 4) if is_rock else (b / 3))
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
        
        # Pasivo del dentellón y la punta (AASHTO permite usar el pasivo si se garantiza que el suelo no será removido)
        # H_pasivo = recubrimiento + espesor_zapata + profundidad_dentellon
        h_pasivo = geometry.toe_cover_soil.to("m").magnitude + geometry.footing_thickness.to("m").magnitude
        if geometry.key_depth and geometry.key_depth.magnitude > 0:
            h_pasivo += geometry.key_depth.to("m").magnitude
            # Si hay dentellón, la falla por deslizamiento ocurre a través del suelo mismo, no concreto-suelo.
            # Por lo tanto, podríamos usar math.tan(phi) puro, pero mantendremos delta_base (que por defecto es phi).
            
        passive_cap = 0.0
        if h_pasivo > 0:
            phi_f = foundation_soil.friction_angle.to("radians").magnitude
            # K_p simplificado (Rankine o Coulomb asumiendo beta=0, delta=0 para pasivo seguro)
            k_p = (1 + math.sin(phi_f)) / (1 - math.sin(phi_f))
            gamma_f = foundation_soil.unit_weight.to("kN/m**3").magnitude
            # Fuerza pasiva = 0.5 * gamma * H^2 * Kp
            passive_cap = 0.5 * gamma_f * (h_pasivo ** 2) * k_p
            
            # En LRFD, el factor de resistencia (phi_tau) para el empuje pasivo suele ser 0.50 (muy castigado)
            # Para deslizamiento por fricción suele ser 0.80.
            # El CCP14Orchestrator se encargará de reportarlo. Aquí enviamos la capacidad nominal o ya factorizada.
            # Asumiremos la suma de ambas capacidades (Fricción + Pasivo).
            
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
