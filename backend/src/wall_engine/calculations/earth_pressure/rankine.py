import math
from typing import List, Optional
from wall_engine.units.registry import Q_
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.loads.entities import Surcharge
from wall_engine.domain.water.entities import Groundwater
from wall_engine.domain.results.earth_pressure import EarthPressureResult, ForceComponent
from wall_engine.calculations.earth_pressure.coulomb import total_retained_height

class RankineEarthPressure:
    
    def calculate(
        self,
        soil: Soil,
        geometry: WallGeometry,
        surcharges: List[Surcharge],
        groundwater: Optional[Groundwater] = None
    ) -> EarthPressureResult:
        
        phi = soil.friction_angle.to('radians').magnitude
        beta = geometry.backfill_slope.to('radians').magnitude
        
        if beta == 0:
            ka = math.tan(math.radians(45) - phi/2)**2
        else:
            cos_beta = math.cos(beta)
            cos_phi = math.cos(phi)
            if cos_beta < cos_phi:
                ka = 1.0 
            else:
                sqrt_term = math.sqrt(cos_beta**2 - cos_phi**2)
                ka = cos_beta * (cos_beta - sqrt_term) / (cos_beta + sqrt_term)
                
        kp = math.tan(math.radians(45) + phi/2)**2
        
        h_ret = total_retained_height(geometry)
            
        gamma_w = Q_(9.80665, "kN/m**3")
        has_water = groundwater is not None and not groundwater.drainage_enabled and groundwater.elevation.to("m").magnitude > 0
        
        if not has_water:
            pa_mag = 0.5 * soil.unit_weight * (h_ret ** 2) * ka
            y_pa = h_ret / 3
        else:
            hw = groundwater.elevation
            if hw > h_ret:
                hw = h_ret
                
            zw = h_ret - hw
            
            gamma_dry = soil.unit_weight
            gamma_sat = soil.saturated_unit_weight if soil.saturated_unit_weight else gamma_dry
            gamma_sub = gamma_sat - gamma_w
            
            f1 = 0.5 * gamma_dry * (zw**2) * ka
            y1 = hw + (zw / 3)
            
            f2 = gamma_dry * zw * hw * ka
            y2 = hw / 2
            
            f3 = 0.5 * gamma_sub * (hw**2) * ka
            y3 = hw / 3
            
            pa_mag = f1 + f2 + f3
            y_pa = (f1*y1 + f2*y2 + f3*y3) / pa_mag if pa_mag.magnitude > 0 else Q_(0, "m")

        pa_mag = pa_mag.to("kN/m")
        angle_pa = Q_(math.degrees(beta), "degrees")
        
        soil_active_force = ForceComponent(
            name="Soil Active Pressure (Rankine)",
            magnitude=pa_mag,
            angle_horizontal=angle_pa,
            application_height=y_pa
        )
        
        surcharge_comp = None
        if surcharges:
            qs = sum(s.magnitude for s in surcharges)
            ps_mag = qs * h_ret * ka
            ps_mag = ps_mag.to("kN/m")
            surcharge_comp = ForceComponent(
                name="Surcharge Active Pressure",
                magnitude=ps_mag,
                angle_horizontal=angle_pa,
                application_height=h_ret / 2
            )
            
        horiz_force = pa_mag * math.cos(beta)
        vert_force = pa_mag * math.sin(beta)
        
        if surcharge_comp:
            horiz_force += surcharge_comp.magnitude * math.cos(beta)
            vert_force += surcharge_comp.magnitude * math.sin(beta)
            
        return EarthPressureResult(
            coefficient_active=ka,
            coefficient_passive=kp,
            soil_active_force=soil_active_force,
            soil_passive_force=None,
            surcharge_force=surcharge_comp,
            seismic_active_force=None,
            horizontal_resultant=horiz_force,
            vertical_resultant=vert_force
        )
