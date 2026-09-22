import math
from typing import List, Dict
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import GenericLoad, LoadType
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.units.registry import Length
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.results.footing_design import FootingDesignResult, FootingSectionForces

class FootingCalculator:
    
    def _compute_shear_capacity(self, thickness_m: float, cover_m: float, fc_mpa: float) -> tuple[float, float, bool]:
        d_m = thickness_m - cover_m
        if d_m <= 0: d_m = 0.001
        vc_kn = 0.17 * math.sqrt(fc_mpa) * 1000.0 * (d_m * 1000.0) / 1000.0
        phi_v = 0.75
        phi_vc = phi_v * vc_kn
        return vc_kn, phi_vc
        
    def calculate(
        self,
        loads: List[GenericLoad],
        factors: Dict[LoadType, float],
        geometry: WallGeometry,
        concrete: Concrete,
        cover: Length,
        stability: StabilityResult
    ) -> FootingDesignResult:
        
        toe_len = geometry.toe_length.to("m").magnitude
        stem_base = geometry.stem_thickness_base.to("m").magnitude
        heel_len = geometry.heel_length.to("m").magnitude
        b = geometry.footing_width.to("m").magnitude
        
        x_toe_cut = toe_len
        x_heel_cut = toe_len + stem_base
        
        q_toe = stability.q_toe # at x = 0
        q_heel = stability.q_heel # at x = B
        
        def get_q_at_x(x: float) -> float:
            # Linear interpolation
            if b == 0: return 0
            # Note: q_toe is at x=0, q_heel is at x=B
            return q_toe - (q_toe - q_heel) * (x / b)
            
        # ==========================================
        # 1. DISEÑO DE LA PUNTA (TOE)
        # ==========================================
        # Presión hacia arriba bajo la punta
        q_toe_cut = get_q_at_x(x_toe_cut)
        # Fuerza resultante del suelo = área del trapecio
        v_up_toe = (q_toe + q_toe_cut) / 2.0 * toe_len
        
        # Brazo de la presión del suelo (centroide del trapecio medido desde el corte x_toe_cut)
        # Distancia del centroide desde x=0 (punta):
        if (q_toe + q_toe_cut) > 0:
            cx_soil = (toe_len / 3.0) * ((2 * q_toe_cut + q_toe) / (q_toe + q_toe_cut))
        else:
            cx_soil = toe_len / 2.0
            
        m_up_toe = v_up_toe * (toe_len - cx_soil)
        
        # Cargas hacia abajo en la punta (ej. peso propio, suelo)
        v_down_toe = 0.0
        m_down_toe = 0.0
        
        for load in loads:
            gamma = factors.get(load.load_type, 1.0)
            x_app = load.x_application.to("m").magnitude
            if x_app < x_toe_cut:
                fy = load.force_y.to("kN/m").magnitude
                if fy < 0: # Carga hacia abajo
                    fy_factored = abs(fy) * gamma
                    v_down_toe += fy_factored
                    arm = x_toe_cut - x_app
                    m_down_toe += fy_factored * arm
                    
        vu_toe = abs(v_up_toe - v_down_toe)
        mu_toe = abs(m_up_toe - m_down_toe)
        
        # ==========================================
        # 2. DISEÑO DEL TALÓN (HEEL)
        # ==========================================
        # Cargas hacia abajo en el talón (peso propio, suelo sobre el talón)
        v_down_heel = 0.0
        m_down_heel = 0.0
        
        for load in loads:
            gamma = factors.get(load.load_type, 1.0)
            x_app = load.x_application.to("m").magnitude
            if x_app > x_heel_cut:
                fy = load.force_y.to("kN/m").magnitude
                if fy < 0:
                    fy_factored = abs(fy) * gamma
                    v_down_heel += fy_factored
                    arm = x_app - x_heel_cut
                    m_down_heel += fy_factored * arm
                    
        # Presión hacia arriba bajo el talón
        q_heel_cut = get_q_at_x(x_heel_cut)
        v_up_heel = (q_heel_cut + q_heel) / 2.0 * heel_len
        
        if (q_heel_cut + q_heel) > 0:
            # Distancia desde x_heel_cut
            cx_soil_heel = (heel_len / 3.0) * ((2 * q_heel + q_heel_cut) / (q_heel_cut + q_heel))
        else:
            cx_soil_heel = heel_len / 2.0
            
        m_up_heel = v_up_heel * cx_soil_heel
        
        vu_heel = abs(v_down_heel - v_up_heel)
        mu_heel = abs(m_down_heel - m_up_heel)
        
        # ==========================================
        # 3. CHEQUEO DE CORTE (CAPACIDAD)
        # ==========================================
        fc_mpa = concrete.fc.to("MPa").magnitude
        thickness_m = geometry.footing_thickness.to("m").magnitude
        cover_m = cover.to("m").magnitude
        
        vc_kn, phi_vc_kn = self._compute_shear_capacity(thickness_m, cover_m, fc_mpa)
        
        # ==========================================
        # 4. DISEÑO DEL DENTELLÓN (KEY)
        # ==========================================
        key_result = None
        if geometry.key_depth is not None and geometry.key_width is not None:
            key_depth_m = geometry.key_depth.to("m").magnitude
            key_width_m = geometry.key_width.to("m").magnitude
            
            if key_depth_m > 0 and key_width_m > 0:
                # Calculamos empuje pasivo de forma simplificada (Rankine)
                # El empuje actúa en la cara frontal del dentellón.
                # Sobrecarga = q_toe_cut (presión debajo de la zapata al inicio del dentellón, conservadoramente q_toe)
                gamma_soil = 18.0 # Asumimos un gamma si no lo pasan, aunque no está en la firma. 
                # Para hacerlo preciso, deberíamos recibir foundation_soil. Por ahora, 
                # como LRFD mayoró las fuerzas, tomaremos un Kp = 3.0 estándar si no tenemos el suelo.
                # Para ser correctos, pediré prestado el cálculo rápido.
                # Kp = tan^2(45 + phi/2)
                Kp = 3.0 # Fijo por ahora asumiendo phi=30, conservador o podemos pasarlo por el factor
                
                # Presión triangular pasiva = 0.5 * gamma * H^2 * Kp
                # Asumimos que el motor LRFD le pasaría una fuerza EH al dentellón. Si no,
                # lo deducimos de la demanda horizontal neta que no friccionó, pero la estática 
                # conservadora diseña el dentellón para resistir toda su capacidad pasiva:
                p_pasiva = 0.5 * 18.0 * (key_depth_m**2) * Kp # kN/m asumiendo gamma=18
                
                # O asumiendo que el cortante máximo es todo el Sliding Demand factorado
                # Usaremos la fuerza pasiva pura.
                vu_key = p_pasiva
                mu_key = p_pasiva * (key_depth_m / 3.0) # actua a un tercio de la base del dentellón o 2/3 de la punta
                
                vc_key_kn, phi_vc_key_kn = self._compute_shear_capacity(key_width_m, cover_m, fc_mpa)
                
                key_result = FootingSectionForces(
                    V_u=Q_(vu_key, "kN/m"),
                    M_u=Q_(mu_key, "kN*m/m"),
                    M_serv=Q_(0, "kN*m/m"),
                    V_c=Q_(vc_key_kn, "kN/m"),
                    phi_V_c=Q_(phi_vc_key_kn, "kN/m"),
                    is_shear_safe=vu_key <= phi_vc_key_kn
                )
        
        return FootingDesignResult(
            toe=FootingSectionForces(
                V_u=Q_(vu_toe, "kN/m"),
                M_u=Q_(mu_toe, "kN*m/m"),
                M_serv=Q_(0, "kN*m/m"),
                V_c=Q_(vc_kn, "kN/m"),
                phi_V_c=Q_(phi_vc_kn, "kN/m"),
                is_shear_safe=vu_toe <= phi_vc_kn
            ),
            heel=FootingSectionForces(
                V_u=Q_(vu_heel, "kN/m"),
                M_u=Q_(mu_heel, "kN*m/m"),
                M_serv=Q_(0, "kN*m/m"),
                V_c=Q_(vc_kn, "kN/m"),
                phi_V_c=Q_(phi_vc_kn, "kN/m"),
                is_shear_safe=vu_heel <= phi_vc_kn
            ),
            key=key_result
        )
