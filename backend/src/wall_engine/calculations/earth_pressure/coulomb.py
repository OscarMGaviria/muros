import math
from typing import List, Optional
from wall_engine.units.registry import Q_
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.loads.entities import Surcharge
from wall_engine.domain.water.entities import Groundwater
from wall_engine.domain.results.earth_pressure import EarthPressureResult, ForceComponent
from wall_engine.units.registry import Length


def total_retained_height(geometry: WallGeometry) -> Length:
    """Altura del plano virtual en el extremo del talón: fuste + zapata + talud sobre el talón."""
    beta = geometry.backfill_slope.to('radians').magnitude
    h = geometry.stem_height + geometry.footing_thickness
    if geometry.heel_length.magnitude > 0 and beta > 0:
        h += geometry.heel_length * math.tan(beta)
    return h

class CoulombEarthPressure:
    
    def calculate(
        self,
        soil: Soil,
        geometry: WallGeometry,
        surcharges: List[Surcharge],
        groundwater: Optional[Groundwater] = None,
        retained_height: Optional[Length] = None
    ) -> EarthPressureResult:
        """
        Por defecto el empuje se evalúa sobre el plano virtual vertical que pasa
        por el extremo del talón, con altura total desde la base de la zapata
        (AASHTO/CCP-14 Fig. 3.11.5.3-1, 11.6.3.2). Las alturas de aplicación se
        miden desde la base de esa altura.
        retained_height permite evaluar otra altura (p. ej. solo el fuste).
        """
        
        phi = soil.friction_angle.to('radians').magnitude
        beta = geometry.backfill_slope.to('radians').magnitude
        
        # Utilizamos el ángulo theta (cara trasera del muro con respecto a la horizontal) 
        # tal como lo especifica la ecuación 3.11.5.3-1 y la figura 3.11.5.3-1 del CCP-14.
        theta = geometry.back_face_angle.to('radians').magnitude
        
        delta = soil.interface_friction_angle.to('radians').magnitude if soil.interface_friction_angle else beta
        
        # 1. Calcular Coeficiente de Presión Activa (Ka)
        num_gamma = math.sin(phi + delta) * math.sin(phi - beta)
        den_gamma = math.sin(theta - delta) * math.sin(theta + beta)
        
        if den_gamma == 0 or num_gamma / den_gamma < 0:
            gamma = 1.0
        else:
            gamma = (1 + math.sqrt(num_gamma / den_gamma)) ** 2
            
        num_ka = math.sin(theta + phi) ** 2
        den_ka = gamma * (math.sin(theta) ** 2) * math.sin(theta - delta)
        ka = num_ka / den_ka
        kp = math.tan(math.radians(45) + phi/2)**2
        
        # 2. Determinar altura de retención (H_ret)
        h_ret = retained_height if retained_height is not None else total_retained_height(geometry)
            
        # 3. Determinar efecto del nivel freático
        # Asumimos que la elevación de la base es 0 para la medición de hw
        gamma_w = Q_(9.80665, "kN/m**3")
        
        has_water = groundwater is not None and not groundwater.drainage_enabled and groundwater.elevation.to("m").magnitude > 0
        
        if not has_water:
            # Caso seco / totalmente drenado
            pa_mag = 0.5 * soil.unit_weight * (h_ret ** 2) * ka
            y_pa = h_ret / 3
        else:
            hw = groundwater.elevation
            if hw > h_ret:
                hw = h_ret # El agua no puede estar por encima del suelo retenido para empujes
                
            zw = h_ret - hw # Profundidad desde la superficie hasta el nivel de agua
            
            gamma_dry = soil.unit_weight
            gamma_sat = soil.saturated_unit_weight if soil.saturated_unit_weight else gamma_dry
            gamma_sub = gamma_sat - gamma_w
            
            # Fuerza 1: Triángulo superior (seco)
            f1 = 0.5 * gamma_dry * (zw**2) * ka
            y1 = hw + (zw / 3)
            
            # Fuerza 2: Rectángulo inferior (presión constante del estrato superior)
            f2 = gamma_dry * zw * hw * ka
            y2 = hw / 2
            
            # Fuerza 3: Triángulo inferior (suelo sumergido)
            f3 = 0.5 * gamma_sub * (hw**2) * ka
            y3 = hw / 3
            
            pa_mag = f1 + f2 + f3
            y_pa = (f1*y1 + f2*y2 + f3*y3) / pa_mag if pa_mag.magnitude > 0 else Q_(0, "m")

        pa_mag = pa_mag.to("kN/m")
        angle_pa = Q_(math.degrees(delta), "degrees")
        
        soil_active_force = ForceComponent(
            name="Soil Active Pressure",
            magnitude=pa_mag,
            angle_horizontal=angle_pa,
            application_height=y_pa
        )
        
        # 4. Sobrecargas
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
            
        # 5. Resultantes
        horiz_force = pa_mag * math.cos(delta)
        vert_force = pa_mag * math.sin(delta)
        
        if surcharge_comp:
            horiz_force += surcharge_comp.magnitude * math.cos(delta)
            vert_force += surcharge_comp.magnitude * math.sin(delta)
            
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
