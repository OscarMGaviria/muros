import math
from wall_engine.units.registry import Q_
from wall_engine.domain.results.bearing import BearingCapacityResult
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.loads.combinations import FactoredResult
from wall_engine.domain.results.stability import StabilityResult

class BearingCapacityCalculator:
    
    def calculate(
        self,
        stability: StabilityResult,
        factored_load: FactoredResult,
        geometry: WallGeometry,
        foundation_soil: Soil,
        embedment_depth: float = 0.0 # D_f en m: profundidad de la base bajo la superficie frente a la punta
    ) -> BearingCapacityResult:
        
        phi = foundation_soil.friction_angle.to("radians").magnitude
        c = foundation_soil.cohesion.to("kPa").magnitude if foundation_soil.cohesion else 0.0
        gamma = foundation_soil.unit_weight.to("kN/m**3").magnitude
        
        b = geometry.footing_width.to("m").magnitude
        e = stability.eccentricity.to("m").magnitude
        
        # 1. Ancho efectivo de Meyerhof
        b_prime = b - 2 * abs(e)
        if b_prime <= 0:
            # Caso teóricamente imposible / muro volcado
            b_prime = 0.001
            
        # 2. Factores de Capacidad Portante (Vesic / AASHTO)
        if phi > 0:
            N_q = math.exp(math.pi * math.tan(phi)) * (math.tan(math.radians(45) + phi / 2) ** 2)
            N_c = (N_q - 1) / math.tan(phi)
            N_gamma = 2 * (N_q + 1) * math.tan(phi)
        else:
            N_q = 1.0
            N_c = 5.14
            N_gamma = 0.0
            
        # 3. Factores de inclinación
        # Para zapata continua (L -> inf), m = 2
        # Según AASHTO:
        # i_q = [1 - H / (V + c * B' * L' * cot(phi))]^m
        v = factored_load.sum_force_y.to("kN/m").magnitude
        h = abs(factored_load.sum_force_x.to("kN/m").magnitude)
        
        if v > 0:
            # L' = 1m para análisis por metro lineal
            if phi > 0:
                den = v + c * b_prime * 1.0 * (1 / math.tan(phi))
            else:
                den = v
                
            ratio = h / den if den > 0 else 1.0
            
            # Limitar a 1.0 para evitar raíces negativas (lo cual indica falla por corte deslizante inminente)
            if ratio > 1.0:
                ratio = 1.0
                
            i_q = (1 - ratio) ** 2
            
            if phi > 0:
                i_gamma = (1 - ratio) ** 3  # m+1 = 3
                i_c = i_q - (1 - i_q) / (N_q - 1)
            else:
                i_gamma = 1.0
                # Para phi = 0, m=2 (zapata corrida)
                m = 2.0
                if c > 0:
                    i_c = 1 - (m * h) / (5.14 * c * b_prime)
                    if i_c < 0: i_c = 0.0
                else:
                    i_c = 1.0
        else:
            i_q, i_c, i_gamma = 1.0, 1.0, 1.0
            
        # 4. Ecuación general de capacidad portante
        # q_n = c Nc ic + q Nq iq + 0.5 gamma B' N_gamma i_gamma
        # q_s es el esfuerzo vertical efectivo al nivel de fundación: q_s = gamma * D_f
        q_s = embedment_depth * gamma
        
        term_c = c * N_c * i_c
        term_q = q_s * N_q * i_q
        term_gamma = 0.5 * gamma * b_prime * N_gamma * i_gamma
        
        q_n = term_c + term_q + term_gamma
        
        # 5. Verificación LRFD
        # Si el estudio geotécnico entrega la resistencia nominal, esa gobierna.
        uses_geotech = foundation_soil.bearing_capacity is not None
        if uses_geotech:
            q_n = foundation_soil.bearing_capacity.to("kPa").magnitude
        
        # Presión vertical uniforme sobre el ancho efectivo (AASHTO Ec. 11.6.3.2-1)
        q_demand = v / b_prime if v > 0 else 0.0
        
        # phi_b = 0.55 (Tabla 11.5.7-1); 1.0 en Evento Extremo (11.5.8)
        phi_b = 1.0 if 'Extreme' in factored_load.limit_state_name else 0.55
        q_resistance = phi_b * q_n
        ratio = q_demand / q_resistance if q_resistance > 0 else float('inf')
        
        return BearingCapacityResult(
            q_nominal=Q_(q_n, "kPa"),
            effective_width=b_prime,
            N_c=N_c,
            N_q=N_q,
            N_gamma=N_gamma,
            i_c=i_c,
            i_q=i_q,
            i_gamma=i_gamma,
            q_demand=q_demand,
            phi_b=phi_b,
            q_resistance=q_resistance,
            bearing_ratio=ratio,
            is_safe=ratio <= 1.0,
            uses_geotechnical_q_n=uses_geotech
        )
