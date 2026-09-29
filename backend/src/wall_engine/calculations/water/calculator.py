from wall_engine.units.registry import Q_
from wall_engine.domain.wall.entities import Wall
from wall_engine.domain.results.water import WaterPressureResult
from wall_engine.domain.results.earth_pressure import ForceComponent
from wall_engine.calculations.earth_pressure.coulomb import total_retained_height, water_height

GAMMA_W = Q_(9.80665, "kN/m**3")


class WaterPressureCalculator:
    """
    Presiones de agua (WA) con el nivel freático medido desde la base de la zapata.
    Si el relleno está drenado no hay presiones de agua. Se supone agua solo detrás
    del muro (sin agua frente a la punta).
    """
    
    def calculate(self, wall: Wall) -> WaterPressureResult:
        geom = wall.geometry
        h_ret = total_retained_height(geom)
        hw = water_height(wall.groundwater, h_ret) or Q_(0, "m")
        b = geom.footing_width

        # 1. Empuje hidrostático sobre el plano virtual (x = B): 0.5·gamma_w·hw², a hw/3
        horizontal_force = ForceComponent(
            name="Hydrostatic Pressure (Horizontal)",
            magnitude=(0.5 * GAMMA_W * hw ** 2).to("kN/m"),
            angle_horizontal=Q_(0, "degrees"),
            application_height=hw / 3
        )
        
        # 2. El agua de los poros sobre el talón no se suma aparte: ya está en el
        # peso saturado del suelo (WeightCalculator). Se conserva el campo en cero.
        vertical_force = ForceComponent(
            name="Hydrostatic Weight over Heel (incluido en el suelo saturado)",
            magnitude=Q_(0, "kN/m"),
            angle_horizontal=Q_(90, "degrees"),
            application_height=Q_(0, "m")
        )
        
        # 3. Subpresión: triangular, gamma_w·hw en el talón y cero en la punta.
        # Resultante 0.5·gamma_w·hw·B hacia arriba, a 2B/3 de la punta.
        u_heel = (GAMMA_W * hw).to("kPa")
        u_mag = (0.5 * u_heel * b).to("kN/m")
        uplift_force = ForceComponent(
            name="Uplift (Subpresión)",
            magnitude=-u_mag,  # Negativo porque va hacia arriba
            angle_horizontal=Q_(90, "degrees"),
            application_height=(2 * b) / 3  # Brazo 'x' desde la punta
        )
        
        return WaterPressureResult(
            horizontal_force=horizontal_force,
            vertical_force=vertical_force,
            uplift=uplift_force,
            resultant_horizontal=horizontal_force.magnitude,
            resultant_vertical=-u_mag,
            water_height=hw.to("m"),
            uplift_pressure_at_heel=u_heel
        )
