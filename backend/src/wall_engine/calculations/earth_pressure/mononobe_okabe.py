import math
from typing import List, Optional
from wall_engine.units.registry import Q_
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.loads.entities import Surcharge
from wall_engine.domain.water.entities import Groundwater
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.domain.results.earth_pressure import EarthPressureResult, ForceComponent
from wall_engine.calculations.earth_pressure.coulomb import (
    CoulombEarthPressure, total_retained_height, water_height, layered_active_force
)
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
        
        kh = seismic.kh if seismic else 0.0
        kv = seismic.kv if seismic else 0.0
        height_ratio = seismic.pae_height_ratio if seismic else 1.0 / 3.0
        warnings = []
        
        # Ángulo sísmico
        theta_mo = math.atan(kh / (1 - kv))
        
        # 2. Calcular Coeficiente K_AE (Mononobe-Okabe)
        # AASHTO / CCP-14
        
        # Validar estabilidad del talud
        if phi - beta - theta_mo < 0:
            # CCP-14 11.6.5.3: M-O no es aplicable (radical negativo) y debe usarse
            # el método GLE. Se anula el radical, lo que es conservador, y se avisa.
            num_gamma = 0
            warnings.append(
                "Mononobe-Okabe no es aplicable: φ − β − θMO < 0 (CCP-14 11.6.5.3). "
                "K_AE se calculó anulando el radical, lo que es excesivamente conservador; "
                "use el método de equilibrio límite generalizado (GLE)."
            )
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
        hw = water_height(groundwater, h_ret)
        gamma_w = Q_(9.80665, "kN/m**3")
        gamma_dry = soil.unit_weight
        gamma_sat = soil.saturated_unit_weight if soil.saturated_unit_weight else gamma_dry
        
        # 4. Base de peso unitario bajo el agua para el sismo (C11.6.5.3):
        #  - relleno que no drena libremente: suelo y agua se mueven juntos -> peso total
        #  - relleno de drenaje libre: peso sumergido + presión hidrodinámica aparte
        free_draining = hw is not None and groundwater.free_draining_backfill
        gamma_below = (gamma_sat - gamma_w) if free_draining else gamma_sat
        
        # P_AE total (Ec. 11.6.5.3-2) y el empuje estático en la misma base
        pae_mag, _ = layered_active_force(kae * (1 - kv), h_ret, hw, gamma_dry, gamma_below)
        pa_basis, y_pa_basis = layered_active_force(static_result.coefficient_active, h_ret, hw, gamma_dry, gamma_below)
        
        # El incremento dinámico es dP_AE = P_AE - P_A (no se reduce el estático)
        dpae_mag = pae_mag - pa_basis
        if kh <= 0 or dpae_mag.magnitude < 0:
            dpae_mag = Q_(0, "kN/m")
        
        # 5. Ubicación: la resultante total P_AE a height_ratio·h (H/3 por defecto,
        # 0.4h a 0.5h opcional) y nunca por debajo de la resultante estática (11.6.5.3).
        y_total = max(height_ratio * h_ret, y_pa_basis)
        if dpae_mag.magnitude > 0:
            y_dpae = ((pa_basis + dpae_mag) * y_total - pa_basis * y_pa_basis) / dpae_mag
        else:
            y_dpae = y_total
        angle_pa = Q_(math.degrees(delta), "degrees")
        
        seismic_active_force = ForceComponent(
            name="Seismic Active Pressure Increment",
            magnitude=dpae_mag,
            angle_horizontal=angle_pa,
            application_height=y_dpae.to("m")
        )
        
        # 6. Presión hidrodinámica de Westergaard (relleno de drenaje libre):
        # P_wd = 7/12 · kh · gamma_w · hw², aplicada a 0.4·hw sobre la base
        hydrodynamic = None
        if free_draining and kh > 0:
            hydrodynamic = ForceComponent(
                name="Hydrodynamic Pressure (Westergaard)",
                magnitude=(7.0 / 12.0 * kh * gamma_w * hw ** 2).to("kN/m"),
                angle_horizontal=Q_(0, "degrees"),
                application_height=0.4 * hw
            )
        
        # 7. Agregar el incremento dinámico a las resultantes
        horiz_force = static_result.horizontal_resultant + dpae_mag * math.cos(delta)
        vert_force = static_result.vertical_resultant + dpae_mag * math.sin(delta)
        if hydrodynamic:
            horiz_force += hydrodynamic.magnitude
        
        return EarthPressureResult(
            coefficient_active=static_result.coefficient_active,
            coefficient_passive=static_result.coefficient_passive,
            soil_active_force=static_result.soil_active_force,
            soil_passive_force=static_result.soil_passive_force,
            surcharge_force=static_result.surcharge_force,
            seismic_active_force=seismic_active_force,
            horizontal_resultant=horiz_force,
            vertical_resultant=vert_force,
            coefficient_seismic_active=kae,
            hydrodynamic_force=hydrodynamic,
            warnings=warnings
        )
