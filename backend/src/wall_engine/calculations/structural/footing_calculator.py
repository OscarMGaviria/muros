import math
from typing import List, Dict
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import GenericLoad, LoadType
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.units.registry import Length
from wall_engine.domain.results.stability import StabilityResult
from wall_engine.domain.results.footing_design import FootingDesignResult, FootingSectionForces
from wall_engine.calculations.structural.shear import concrete_shear_capacity
from wall_engine.calculations.stability.calculator import key_passive_resistance
from wall_engine.domain.soil.entities import Soil

class FootingCalculator:
    
    def _compute_shear_capacity(self, thickness_m: float, cover_m: float, fc_mpa: float) -> tuple[float, float]:
        return concrete_shear_capacity(fc_mpa, thickness_m, thickness_m - cover_m)
        
    def calculate(
        self,
        loads: List[GenericLoad],
        factors: Dict[LoadType, float],
        geometry: WallGeometry,
        concrete: Concrete,
        cover: Length,
        stability: StabilityResult,
        foundation_soil: Soil,
        ignore_heel_reaction: bool = False,
        uplift_at_heel: float = 0.0
    ) -> FootingDesignResult:
        """
        uplift_at_heel: subpresión sin mayorar en el extremo del talón (kPa); varía
        linealmente hasta cero en la punta y se mayora con el factor de WA. La
        presión de contacto de la estabilidad ya es neta de subpresión, así que
        la subpresión se suma como presión ascendente adicional en cada voladizo.
        """
        
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
        # Presión hacia arriba bajo la punta: contacto + subpresión
        u_heel = uplift_at_heel * factors.get(LoadType.WA, 0.0)
        def get_u_at_x(x: float) -> float:
            return u_heel * (x / b) if b > 0 else 0.0
        
        q_toe_cut = get_q_at_x(x_toe_cut)
        v_up_toe, cx_soil = _trapezoid(q_toe, q_toe_cut, toe_len)
        v_u_toe, cx_u = _trapezoid(0.0, get_u_at_x(x_toe_cut), toe_len)
        
        # Momentos respecto al corte en x_toe_cut (centroides medidos desde la punta)
        m_up_toe = v_up_toe * (toe_len - cx_soil) + v_u_toe * (toe_len - cx_u)
        v_up_toe += v_u_toe
        
        # Cargas hacia abajo en la punta (ej. peso propio, suelo)
        v_down_toe = 0.0
        m_down_toe = 0.0
        
        # Convención del motor: force_y > 0 es carga hacia abajo (pesos).
        # Un tipo de carga ausente del estado límite no participa (factor 0).
        for load in loads:
            gamma = factors.get(load.load_type, 0.0)
            x_app = load.x_application.to("m").magnitude
            if x_app < x_toe_cut:
                fy = load.force_y.to("kN/m").magnitude
                if fy > 0: # Carga hacia abajo
                    fy_factored = fy * gamma
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
            gamma = factors.get(load.load_type, 0.0)
            x_app = load.x_application.to("m").magnitude
            if x_app > x_heel_cut:
                fy = load.force_y.to("kN/m").magnitude
                if fy > 0:
                    fy_factored = fy * gamma
                    v_down_heel += fy_factored
                    arm = x_app - x_heel_cut
                    m_down_heel += fy_factored * arm
                    
        # Presión hacia arriba bajo el talón: contacto (se omite si el usuario elige
        # diseñar el talón solo con su peso y el suelo encima) + subpresión
        q_heel_cut = 0.0 if ignore_heel_reaction else get_q_at_x(x_heel_cut)
        q_heel_end = 0.0 if ignore_heel_reaction else q_heel
        v_up_heel, cx_soil_heel = _trapezoid(q_heel_cut, q_heel_end, heel_len)
        v_u_heel, cx_u_heel = _trapezoid(get_u_at_x(x_heel_cut), u_heel, heel_len)
        
        # Distancias medidas desde x_heel_cut
        m_up_heel = v_up_heel * cx_soil_heel + v_u_heel * cx_u_heel
        v_up_heel += v_u_heel
        
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
            key_width_m = geometry.key_width.to("m").magnitude
            
            if geometry.key_depth.magnitude > 0 and key_width_m > 0:
                # El dentellón se diseña para resistir el empuje pasivo nominal
                # usado en el análisis de deslizamiento (CDOT BDM Ej. 11, 2.4).
                # Sección crítica: unión con la base de la zapata.
                rep, z = key_passive_resistance(geometry, foundation_soil)
                vu_key = rep
                mu_key = rep * z
                
                vc_key_kn, phi_vc_key_kn = self._compute_shear_capacity(key_width_m, cover_m, fc_mpa)
                
                key_result = FootingSectionForces(
                    V_u=Q_(vu_key, "kN/m"),
                    M_u=Q_(mu_key, "kN*m/m"),
                    M_serv=Q_(mu_key, "kN*m/m"),  # pasivo nominal, sin mayorar
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


def _trapezoid(q_a: float, q_b: float, length: float) -> tuple[float, float]:
    """Resultante de una presión lineal de q_a a q_b en 'length' y su centroide medido desde q_a."""
    force = (q_a + q_b) / 2.0 * length
    if (q_a + q_b) > 0:
        centroid = (length / 3.0) * ((q_a + 2 * q_b) / (q_a + q_b))
    else:
        centroid = length / 2.0
    return force, centroid
