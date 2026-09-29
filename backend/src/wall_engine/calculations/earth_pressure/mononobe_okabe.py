import math
from typing import List, Optional
from wall_engine.units.registry import Q_
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.loads.entities import Surcharge
from wall_engine.domain.water.entities import Groundwater
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.domain.results.earth_pressure import EarthPressureResult, ForceComponent
from wall_engine.calculations.earth_pressure.coulomb import CoulombEarthPressure, total_retained_height
from wall_engine.units.registry import Length

class MononobeOkabeEarthPressure:
    
    def calculate(
        self,
        soil: Soil,
        geometry: WallGeometry,
        seismic: SeismicParameters,
        surcharges: List[Surcharge] = None,
        groundwater: Optional[Groundwater] = None,
        retained_height: Optional[Length] = None
    ) -> EarthPressureResult:
        
        # 1. Primero calculamos el estático usando Coulomb como base
        # (Mononobe-Okabe asume estado activo límite, que es Coulomb).
        coulomb_calc = CoulombEarthPressure()
        static_result = coulomb_calc.calculate(soil, geometry, surcharges or [], groundwater, retained_height)
        
        phi = soil.friction_angle.to('radians').magnitude
        beta = geometry.backfill_slope.to('radians').magnitude
        theta = geometry.back_face_angle.to('radians').magnitude
        delta = soil.interface_friction_angle.to('radians').magnitude if soil.interface_friction_angle else beta
        
        kh = seismic.kh
        kv = seismic.kv
        
        # Ángulo sísmico
        theta_mo = math.atan(kh / (1 - kv))
        
        # 2. Calcular Coeficiente K_AE (Mononobe-Okabe)
        # AASHTO / CCP-14
        
        # Validar estabilidad del talud
        if phi - beta - theta_mo < 0:
            # El talud fallará de manera global. En software práctico se suele asumir K_AE = 1.0 
            # o se lanza una advertencia. Lo limitaremos para evitar math domain error.
            num_gamma = 0
        else:
            num_gamma = math.sin(phi + delta) * math.sin(phi - beta - theta_mo)
            
        den_gamma = math.sin(theta - delta - theta_mo) * math.sin(theta + beta)
        
        if den_gamma <= 0 or num_gamma < 0:
            gamma = 1.0
        else:
            gamma = (1 + math.sqrt(num_gamma / den_gamma)) ** 2
            
        num_kae = math.sin(theta + phi - theta_mo) ** 2
        den_kae = math.cos(theta_mo) * (math.sin(theta) ** 2) * math.sin(theta - delta - theta_mo) * gamma
        
        if den_kae <= 0:
            kae = 1.0
        else:
            kae = num_kae / den_kae
            
        # 3. Determinar altura de retención
        h_ret = retained_height if retained_height is not None else total_retained_height(geometry)
            
        # 4. Calcular fuerza TOTAL sísmica activa (P_AE)
        # Asumiendo condición sin agua o usando peso promedio (simplificación AASHTO)
        # Si hay agua, el cálculo riguroso usa gamma efectivo y añade presiones hidrodinámicas.
        # Por simplicidad de MVP, usaremos gamma_dry.
        gamma_soil = soil.unit_weight
        
        pae_mag = 0.5 * gamma_soil * (h_ret ** 2) * kae * (1 - kv)
        pae_mag = pae_mag.to("kN/m")
        
        # La fuerza P_A (estática) ya la calculó Coulomb
        pa_static = static_result.soil_active_force.magnitude
        
        # El incremento dinámico es dP_AE = P_AE - P_A
        # Si por alguna razón K_AE < K_a, el incremento es 0 (no se reduce el estático).
        dpae_mag = pae_mag - pa_static
        if dpae_mag.magnitude < 0:
            dpae_mag = Q_(0, "kN/m")
            
        # El incremento dinámico se aplica a 0.6H medido desde la base (AASHTO).
        y_dpae = 0.6 * h_ret
        angle_pa = Q_(math.degrees(delta), "degrees")
        
        seismic_active_force = ForceComponent(
            name="Seismic Active Pressure Increment",
            magnitude=dpae_mag,
            angle_horizontal=angle_pa,
            application_height=y_dpae
        )
        
        # 5. Agregar el incremento dinámico a las resultantes
        horiz_force = static_result.horizontal_resultant + dpae_mag * math.cos(delta)
        vert_force = static_result.vertical_resultant + dpae_mag * math.sin(delta)
        
        # Devolver un nuevo resultado que contiene tanto lo estático como lo sísmico
        return EarthPressureResult(
            coefficient_active=static_result.coefficient_active,
            coefficient_passive=static_result.coefficient_passive,
            soil_active_force=static_result.soil_active_force,
            soil_passive_force=static_result.soil_passive_force,
            surcharge_force=static_result.surcharge_force,
            seismic_active_force=seismic_active_force,
            horizontal_resultant=horiz_force,
            vertical_resultant=vert_force
        )
