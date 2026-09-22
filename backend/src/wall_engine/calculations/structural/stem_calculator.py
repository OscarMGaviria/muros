import math
from typing import List, Dict
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import GenericLoad, LoadType
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.units.registry import Length
from wall_engine.domain.results.stem_design import StemForcesResult

class StemCalculator:
    
    def calculate(
        self,
        loads: List[GenericLoad],
        factors: Dict[LoadType, float],
        geometry: WallGeometry,
        concrete: Concrete,
        cover: Length
    ) -> StemForcesResult:
        
        # Elevación de la base del fuste (donde ocurre el corte crítico)
        stem_base_y = geometry.footing_thickness
        
        vu_mag = 0.0
        mu_mag = 0.0
        mu_serv = 0.0
        
        for load in loads:
            # Factor de carga aplicado en el estado límite crítico
            gamma = factors.get(load.load_type, 1.0)
            gamma_serv = 1.0 # Para Service I
            
            # Solo nos importan las fuerzas horizontales que actúan SOBRE el fuste.
            # Fuerzas verticales (como el peso del fuste) generan carga axial, no cortante ni momento transversal.
            # Además, la fuerza debe aplicarse por encima de la base del fuste.
            if load.y_application > stem_base_y:
                fx = load.force_x.to("kN/m").magnitude
                if abs(fx) > 0:
                    # Cortante
                    factored_fx = fx * gamma
                    serv_fx = fx * gamma_serv
                    vu_mag += abs(factored_fx)
                    
                    # Brazo de palanca desde la base del fuste
                    lever_arm = (load.y_application - stem_base_y).to("m").magnitude
                    
                    # Momento Flector
                    mu_mag += abs(factored_fx * lever_arm)
                    mu_serv += abs(serv_fx * lever_arm)
                    
        # Capacidad al Corte del Concreto (Vc) - Fórmula ACI / AASHTO
        # Vc = 0.17 * sqrt(f'c) * b * d  (en MPa)
        # b = 1000 mm (1 m)
        fc_mpa = concrete.fc.to("MPa").magnitude
        
        # Peralte efectivo (d)
        thickness_m = geometry.stem_thickness_base.to("m").magnitude
        cover_m = cover.to("m").magnitude
        d_m = thickness_m - cover_m
        
        if d_m <= 0:
            d_m = 0.001
            
        b_mm = 1000.0
        d_mm = d_m * 1000.0
        
        vc_newtons = 0.17 * math.sqrt(fc_mpa) * b_mm * d_mm
        vc_kn = vc_newtons / 1000.0 # Convertir a kN
        
        # Factor de reducción de resistencia a corte
        phi_v = 0.75
        phi_vc_kn = phi_v * vc_kn
        
        is_safe = vu_mag <= phi_vc_kn
        
        return StemForcesResult(
            V_u=Q_(vu_mag, "kN/m"),
            M_u=Q_(mu_mag, "kN*m/m"),
            M_serv=Q_(mu_serv, "kN*m/m"),
            V_c=Q_(vc_kn, "kN/m"),
            phi_V_c=Q_(phi_vc_kn, "kN/m"),
            is_shear_safe=is_safe
        )
