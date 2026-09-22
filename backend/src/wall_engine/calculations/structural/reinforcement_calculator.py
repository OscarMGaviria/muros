import math
from wall_engine.units.registry import Q_
from wall_engine.domain.results.stem_design import StemForcesResult
from wall_engine.domain.results.footing_design import FootingDesignResult
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.units.registry import Length
from wall_engine.domain.results.reinforcement import SectionReinforcement, WallReinforcementResult

class ReinforcementCalculator:
    
    def _calculate_section(
        self,
        name: str,
        mu_kNm_m: float,
        vu_kN_m: float,
        thickness_m: float,
        cover_m: float,
        fc_mpa: float,
        fy_mpa: float
    ) -> SectionReinforcement:
        
        d_m = thickness_m - cover_m
        if d_m <= 0:
            d_m = 0.001
            
        # b = 1000 mm (1 metro de ancho)
        b_mm = 1000.0
        d_mm = d_m * 1000.0
        
        phi = 0.90 # Factor de reducción de resistencia a flexión
        
        # M_u en N-mm
        mu_N_mm = mu_kNm_m * 1e6
        
        # Cuantía requerida (rho_req)
        # R_n = M_u / (phi * b * d^2)
        if mu_N_mm > 0:
            R_n = mu_N_mm / (phi * b_mm * (d_mm ** 2))
            
            # rho = (0.85 * fc / fy) * [1 - sqrt(1 - 2*Rn / (0.85*fc))]
            discriminant = 1 - (2 * R_n) / (0.85 * fc_mpa)
            if discriminant < 0:
                # La sección es demasiado pequeña, falla por compresión antes de fluir el acero (falla frágil)
                # Requiere acero a compresión o aumentar la sección. Por ahora devolvemos un rho muy alto.
                rho_req = 0.05
            else:
                rho_req = (0.85 * fc_mpa / fy_mpa) * (1 - math.sqrt(discriminant))
        else:
            rho_req = 0.0
            
        As_req_mm2 = rho_req * b_mm * d_mm
        As_req_cm2 = As_req_mm2 / 100.0
        
        # ========================================================
        # REFUERZO MÍNIMO A FLEXIÓN (CCP-14 5.7.3.3.2 / AASHTO)
        # ========================================================
        # Módulo de rotura del concreto (5.4.2.6 para peso normal)
        fr_mpa = 0.63 * math.sqrt(fc_mpa)
        
        # Factores de variación (Ec. 5.7.3.3.2-1)
        gamma_1 = 1.6 # Estructuras monolíticas in-situ
        gamma_3 = 0.67 # Asumiendo acero A615 Grado 60 (420 MPa)
        if fy_mpa > 420: gamma_3 = 0.75 # A706 o mayor
        
        thickness_mm = thickness_m * 1000.0
        Sc_mm3 = (b_mm * (thickness_mm ** 2)) / 6.0
        
        # Mcr de la norma (con factores ya integrados)
        Mcr_N_mm = gamma_3 * (gamma_1 * fr_mpa) * Sc_mm3
        Mcr_kNm_m = Mcr_N_mm / 1e6
        
        # El límite es el menor entre 1.33 Mu y Mcr
        Mu_133_kNm_m = 1.33 * mu_kNm_m
        M_design_min_kNm_m = min(Mu_133_kNm_m, Mcr_kNm_m)
        M_design_min_N_mm = M_design_min_kNm_m * 1e6
        
        # Cuantía requerida para el M_design_min
        if M_design_min_N_mm > 0:
            R_n_min = M_design_min_N_mm / (phi * b_mm * (d_mm ** 2))
            disc_min = 1 - (2 * R_n_min) / (0.85 * fc_mpa)
            if disc_min < 0:
                rho_min_flex = 0.05
            else:
                rho_min_flex = (0.85 * fc_mpa / fy_mpa) * (1 - math.sqrt(disc_min))
        else:
            rho_min_flex = 0.0
            
        As_min_flex_mm2 = rho_min_flex * b_mm * d_mm
        As_min_flex_cm2 = As_min_flex_mm2 / 100.0
        
        # Cuantía mínima por retracción y temperatura (CCP-14 5.10.8)
        # Se usa típicamente 0.0018 Ag para Grado 60
        rho_min_temp = 0.0018
        if fy_mpa != 420.0:
            rho_min_temp = 0.0018 * 420.0 / fy_mpa
            
        As_min_temp_mm2 = rho_min_temp * b_mm * thickness_mm
        As_min_temp_cm2 = As_min_temp_mm2 / 100.0
        
        # El As_min que reportamos será el que controla entre temperatura y flexión normativa
        As_min_cm2 = max(As_min_flex_cm2, As_min_temp_cm2)
        
        # El área final requerida es el máximo entre el requerido por análisis y el mínimo normativo
        As_final_cm2 = max(As_req_cm2, As_min_cm2)
        rho_final = (As_final_cm2 * 100.0) / (b_mm * d_mm)
        
        # ========================================================
        # CONTROL DE FISURACIÓN (AASHTO 5.7.3.4)
        # ========================================================
        # Aproximamos M_serv si no se pasa de forma explícita
        # En un motor completo, M_serv vendría de la combinación Service I.
        M_serv_N_mm = (mu_kNm_m / 1.5) * 1e6 
        
        # 1. Relación Modular n = Es / Ec
        # Ec = 4800 sqrt(f'c)
        Ec_mpa = 4800.0 * math.sqrt(fc_mpa)
        Es_mpa = 200000.0
        n_mod = Es_mpa / Ec_mpa
        
        # 2. Análisis elástico agrietado
        rho_elastic = As_final_cm2 * 100.0 / (b_mm * d_mm)
        n_rho = n_mod * rho_elastic
        k_elastic = math.sqrt(2 * n_rho + (n_rho ** 2)) - n_rho
        j_elastic = 1.0 - (k_elastic / 3.0)
        
        # 3. Esfuerzo en el acero bajo carga de servicio
        if As_final_cm2 > 0 and j_elastic > 0:
            f_ss_mpa = M_serv_N_mm / ((As_final_cm2 * 100.0) * j_elastic * d_mm)
        else:
            f_ss_mpa = 0.01
            
        # 4. Espaciamiento máximo (s_max)
        # beta_s = 1 + dc / (0.7(h - dc))
        dc_mm = cover_m * 1000.0 + 10.0 # Asumimos radio de la varilla de 10mm
        if thickness_mm - dc_mm > 0:
            beta_s = 1.0 + dc_mm / (0.7 * (thickness_mm - dc_mm))
        else:
            beta_s = 1.0
            
        gamma_e = 0.75 if "Stem" in name or "Toe" in name else 1.00 # Clase 2 para expuestos
        
        s_max_mm = (123000.0 * gamma_e) / (beta_s * f_ss_mpa) - 2.0 * dc_mm
        if s_max_mm < 0: s_max_mm = 0.0
        
        # ========================================================
        # CORTANTE LRFD (AASHTO 5.8.3.3)
        # ========================================================
        # dv = max(d - a/2, 0.9d, 0.72h)
        # a = As_final * fy / (0.85 * fc * b)
        a_mm = (As_final_cm2 * 100.0 * fy_mpa) / (0.85 * fc_mpa * b_mm)
        dv_mm = max(d_mm - a_mm/2.0, 0.9 * d_mm, 0.72 * thickness_mm)
        
        beta_shear = 2.0
        # Vc = 0.083 * beta * sqrt(fc) * b * dv (en N)
        vc_newtons = 0.083 * beta_shear * math.sqrt(fc_mpa) * b_mm * dv_mm
        vc_kn = vc_newtons / 1000.0
        phi_v = 0.90
        phi_vc_kn = phi_v * vc_kn
        
        return SectionReinforcement(
            section_name=name,
            M_u=Q_(mu_kNm_m, "kN*m/m"),
            M_serv=Q_(M_serv_N_mm / 1e6, "kN*m/m"),
            thickness=Q_(thickness_m, "m"),
            d=Q_(d_m, "m"),
            A_s_required=As_req_cm2,
            A_s_min=As_min_cm2,
            A_s_final=As_final_cm2,
            rho_final=rho_final,
            s_max_crack=s_max_mm,
            f_ss=f_ss_mpa,
            V_u=Q_(vu_kN_m, "kN/m"),
            phi_V_c=Q_(phi_vc_kn, "kN/m"),
            is_shear_safe=vu_kN_m <= phi_vc_kn
        )
        
    def calculate(
        self,
        stem_forces: StemForcesResult,
        footing_forces: FootingDesignResult,
        geometry: WallGeometry,
        concrete: Concrete,
        steel: ReinforcementSteel,
        cover: Length
    ) -> WallReinforcementResult:
        
        fc = concrete.fc.to("MPa").magnitude
        fy = steel.fy.to("MPa").magnitude
        cover_m = cover.to("m").magnitude
        
        # 1. Fuste (Stem)
        stem = self._calculate_section(
            name="Stem Base",
            mu_kNm_m=stem_forces.M_u.to("kN*m/m").magnitude,
            vu_kN_m=stem_forces.V_u.to("kN/m").magnitude,
            thickness_m=geometry.stem_thickness_base.to("m").magnitude,
            cover_m=cover_m,
            fc_mpa=fc,
            fy_mpa=fy
        )
        
        # 2. Punta (Toe)
        toe = self._calculate_section(
            name="Toe",
            mu_kNm_m=footing_forces.toe.M_u.to("kN*m/m").magnitude,
            vu_kN_m=footing_forces.toe.V_u.to("kN/m").magnitude,
            thickness_m=geometry.footing_thickness.to("m").magnitude,
            cover_m=cover_m,
            fc_mpa=fc,
            fy_mpa=fy
        )
        
        # 3. Talón (Heel)
        # Nota: típicamente el recubrimiento superior del talón es de 5cm y el inferior de 7.5cm,
        # pero usaremos el cover global por simplificación.
        heel = self._calculate_section(
            name="Heel",
            mu_kNm_m=footing_forces.heel.M_u.to("kN*m/m").magnitude,
            vu_kN_m=footing_forces.heel.V_u.to("kN/m").magnitude,
            thickness_m=geometry.footing_thickness.to("m").magnitude,
            cover_m=cover_m,
            fc_mpa=fc,
            fy_mpa=fy
        )
        
        # 4. Dentellón (Key) - Opcional
        key_res = None
        if footing_forces.key is not None and geometry.key_width is not None:
            key_res = self._calculate_section(
                name="Shear Key",
                mu_kNm_m=footing_forces.key.M_u.to("kN*m/m").magnitude,
                vu_kN_m=footing_forces.key.V_u.to("kN/m").magnitude,
                thickness_m=geometry.key_width.to("m").magnitude, # El "espesor" de diseño a flexión del dentellón es su ancho
                cover_m=cover_m,
                fc_mpa=fc,
                fy_mpa=fy
            )
            
        return WallReinforcementResult(
            stem=stem,
            toe=toe,
            heel=heel,
            key=key_res
        )
