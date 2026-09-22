from wall_engine.units.registry import Q_
from wall_engine.domain.wall.entities import Wall
from wall_engine.domain.results.water import WaterPressureResult
from wall_engine.domain.results.earth_pressure import ForceComponent
import math

class WaterPressureCalculator:
    
    def calculate(self, wall: Wall) -> WaterPressureResult:
        gamma_w = Q_(9.80665, "kN/m**3")
        
        # 1. Por defecto no hay empujes de agua si no hay nivel freático 
        # o si el sistema de drenaje está habilitado (lo que alivia las presiones hidrostáticas).
        hw = Q_(0, "m")
        if wall.groundwater and not wall.groundwater.drainage_enabled:
            hw = wall.groundwater.elevation
            
        # Altura retenida (H_ret) para limitar la columna de agua
        beta = wall.geometry.backfill_slope.to('radians').magnitude
        h_ret = wall.geometry.stem_height
        if wall.geometry.heel_length.magnitude > 0 and beta > 0:
            h_ret += wall.geometry.heel_length * math.tan(beta)
            
        if hw > h_ret:
            hw = h_ret

        # 2. Fuerza Horizontal (Empuje Hidrostático en la cara posterior)
        # F_wh = 0.5 * gamma_w * hw^2
        f_wh_mag = (0.5 * gamma_w * (hw**2)).to("kN/m")
        y_wh = hw / 3
        
        horizontal_force = ForceComponent(
            name="Hydrostatic Pressure (Horizontal)",
            magnitude=f_wh_mag,
            angle_horizontal=Q_(0, "degrees"),
            application_height=y_wh
        )
        
        # 3. Fuerza Vertical del Agua (Peso del agua sobre el talón sumergido)
        # Si hay agua sobre el talón, su peso actúa hacia abajo ayudando a la estabilidad.
        heel_len = wall.geometry.heel_length
        f_wv_mag = Q_(0, "kN/m")
        x_wv = Q_(0, "m")
        
        if hw > Q_(0, "m") and heel_len > Q_(0, "m"):
            # Columna de agua rectangular sobre el talón
            f_wv_mag = (gamma_w * hw * heel_len).to("kN/m")
            # El brazo de palanca se mide típicamente desde el extremo de la punta para volcamiento.
            # Asumiremos la distancia "x" desde la esquina inferior izquierda (punta) para consistencia.
            # x = toe + stem_base + heel/2
            x_wv = wall.geometry.toe_length + wall.geometry.stem_thickness_base + (heel_len / 2)
            
        vertical_force = ForceComponent(
            name="Hydrostatic Weight over Heel",
            magnitude=f_wv_mag,
            angle_horizontal=Q_(90, "degrees"),
            application_height=x_wv # Usamos application_height temporalmente como brazo 'x' 
        )
        
        # 4. Subpresión (Uplift) bajo la zapata
        # Si no hay drenaje, el agua ejerce una presión ascendente en la base.
        # Asumiremos un perfil triangular estándar (máxima en el talón, cero en la punta) si hay agua atrás y no adelante.
        # Si hay agua adelante, sería un trapecio. Para CCP-14 usaremos triangular básico (todo el ancho B).
        b = wall.geometry.footing_width
        u_mag = Q_(0, "kN/m")
        x_u = Q_(0, "m")
        
        if hw > Q_(0, "m") and b > Q_(0, "m"):
            # U = 0.5 * (gamma_w * hw) * B
            u_mag = (0.5 * gamma_w * hw * b).to("kN/m")
            # Se aplica en el centroide del triángulo (medido desde la punta: 2/3 B, porque la mayor presión está en el talón)
            x_u = (2 * b) / 3
            
        uplift_force = ForceComponent(
            name="Uplift (Subpresión)",
            magnitude=-u_mag, # Negativo porque va hacia arriba
            angle_horizontal=Q_(90, "degrees"),
            application_height=x_u # Brazo 'x' desde la punta
        )
        
        # Resultantes netas del agua
        res_horiz = f_wh_mag
        res_vert = f_wv_mag - u_mag
        
        return WaterPressureResult(
            horizontal_force=horizontal_force,
            vertical_force=vertical_force,
            uplift=uplift_force,
            resultant_horizontal=res_horiz,
            resultant_vertical=res_vert
        )
