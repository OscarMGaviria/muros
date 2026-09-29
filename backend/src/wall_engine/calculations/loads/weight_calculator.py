import math
from typing import List
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.entities import Wall
from wall_engine.domain.loads.blocks import Block2D

class WeightCalculator:
    
    def calculate_concrete_blocks(self, wall: Wall) -> List[Block2D]:
        """Calcula los bloques de concreto (DC) del muro"""
        blocks = []
        gamma_c = wall.materials.concrete.density
        geom = wall.geometry
        
        # 1. Zapata (Footing), dividida en punta, bajo el fuste y talón para que
        # el diseño de cada voladizo reciba su propio peso.
        footing_parts = [
            ("Footing (Toe)", Q_(0, "m"), geom.toe_length),
            ("Footing (Under Stem)", geom.toe_length, geom.toe_length + geom.stem_thickness_base),
            ("Footing (Heel)", geom.toe_length + geom.stem_thickness_base, geom.footing_width),
        ]
        for part_name, x_start, x_end in footing_parts:
            part_width = x_end - x_start
            if part_width.magnitude <= 0:
                continue
            blocks.append(Block2D(
                name=part_name,
                load_type="DC",
                weight=(part_width * geom.footing_thickness * gamma_c).to("kN/m"),
                x_centroid=(x_start + x_end) / 2,
                y_centroid=geom.footing_thickness / 2
            ))
        
        # 2. Fuste: cara frontal vertical y cara trasera inclinada (como el Ejemplo 11
        # del CDOT y el plano de la aplicación). Rectángulo de espesor igual a la
        # corona sobre la cara frontal, y triángulo detrás de él.
        x_front = geom.toe_length
        blocks.append(Block2D(
            name="Stem (Rectangular)",
            load_type="DC",
            weight=(geom.stem_thickness_top * geom.stem_height * gamma_c).to("kN/m"),
            x_centroid=x_front + geom.stem_thickness_top / 2,
            y_centroid=geom.footing_thickness + (geom.stem_height / 2)
        ))
        
        # 3. Fuste Triangular: base abajo (Sb − St) y vértice en la corona;
        # su centroide está a 1/3 de la base medido desde el rectángulo.
        diff_thickness = geom.stem_thickness_base - geom.stem_thickness_top
        if diff_thickness.magnitude > 0:
            blocks.append(Block2D(
                name="Stem (Triangular)",
                load_type="DC",
                weight=(0.5 * diff_thickness * geom.stem_height * gamma_c).to("kN/m"),
                x_centroid=x_front + geom.stem_thickness_top + diff_thickness / 3,
                y_centroid=geom.footing_thickness + (geom.stem_height / 3)
            ))
            
        return blocks
        
    def calculate_soil_blocks(self, wall: Wall) -> List[Block2D]:
        """Calcula los bloques de suelo (EV) sobre la zapata"""
        blocks = []
        geom = wall.geometry
        gamma_s = wall.backfill.unit_weight
        
        # 1. Suelo sobre el talón (Rectangular). Bajo el nivel freático (medido desde
        # la base de la zapata, sin drenaje) se usa el peso saturado, que ya
        # incluye el agua de los poros.
        if geom.heel_length.magnitude > 0:
            x_heel_centroid = geom.toe_length + geom.stem_thickness_base + (geom.heel_length / 2)
            y_bottom = geom.footing_thickness
            y_top = geom.footing_thickness + geom.stem_height
            y_water = y_bottom
            gw = wall.groundwater
            if gw is not None and not gw.drainage_enabled:
                y_water = min(max(gw.elevation, y_bottom), y_top)
            
            if (y_water - y_bottom).magnitude > 0:
                gamma_sat = wall.backfill.saturated_unit_weight or gamma_s
                blocks.append(Block2D(
                    name="Soil over Heel (Saturated)",
                    load_type="EV",
                    weight=(geom.heel_length * (y_water - y_bottom) * gamma_sat).to("kN/m"),
                    x_centroid=x_heel_centroid,
                    y_centroid=(y_bottom + y_water) / 2
                ))
            if (y_top - y_water).magnitude > 0:
                blocks.append(Block2D(
                    name="Soil over Heel (Rectangular)",
                    load_type="EV",
                    weight=(geom.heel_length * (y_top - y_water) * gamma_s).to("kN/m"),
                    x_centroid=x_heel_centroid,
                    y_centroid=(y_water + y_top) / 2
                ))
            
            # 2. Suelo sobre el talón (Triangular por el talud)
            beta = geom.backfill_slope.to('radians').magnitude
            if beta > 0:
                slope_height = geom.heel_length * math.tan(beta)
                slope_vol = 0.5 * geom.heel_length * slope_height
                slope_weight = (slope_vol * gamma_s).to("kN/m")
                # La cuña crece desde la cara del fuste (altura 0) hasta el extremo
                # del talón: su C.G. está a 2/3 del talón medido desde el fuste.
                x_slope_centroid = geom.toe_length + geom.stem_thickness_base + (geom.heel_length * 2 / 3)
                
                blocks.append(Block2D(
                    name="Soil over Heel (Slope)",
                    load_type="EV",
                    weight=slope_weight,
                    x_centroid=x_slope_centroid,
                    y_centroid=geom.footing_thickness + geom.stem_height + (slope_height / 3)
                ))
                
        # Cuña de suelo sobre la cara trasera inclinada del fuste (EV2 del CDOT):
        # triángulo con base arriba (Sb − St) y vértice en la base del fuste.
        diff_thickness = geom.stem_thickness_base - geom.stem_thickness_top
        if diff_thickness.magnitude > 0:
            blocks.append(Block2D(
                name="Soil over Stem Batter",
                load_type="EV",
                weight=(0.5 * diff_thickness * geom.stem_height * gamma_s).to("kN/m"),
                x_centroid=geom.toe_length + geom.stem_thickness_top + 2 * diff_thickness / 3,
                y_centroid=geom.footing_thickness + 2 * geom.stem_height / 3
            ))
            
        # 3. Suelo sobre la punta
        if geom.toe_cover_soil.magnitude > 0 and geom.toe_length.magnitude > 0:
            toe_soil_vol = geom.toe_length * geom.toe_cover_soil
            toe_soil_weight = (toe_soil_vol * gamma_s).to("kN/m")
            
            blocks.append(Block2D(
                name="Soil over Toe",
                load_type="EV",
                weight=toe_soil_weight,
                x_centroid=geom.toe_length / 2,
                y_centroid=geom.footing_thickness + (geom.toe_cover_soil / 2)
            ))
            
        return blocks
        
    def calculate_seismic_inertial_loads(self, wall: Wall) -> List['GenericLoad']:
        from wall_engine.domain.loads.combinations import GenericLoad, LoadType
        
        eq_loads = []
        kh = wall.seismic.kh
        if kh <= 0:
            return eq_loads
            
        concrete_blocks = self.calculate_concrete_blocks(wall)
        soil_blocks = self.calculate_soil_blocks(wall)
        
        # PIR: Fuerzas inerciales de la estructura de retención (Concreto)
        for b in concrete_blocks:
            f_eq = b.weight * kh
            eq_loads.append(GenericLoad(
                name=f"Inertia PIR ({b.name})",
                load_type=LoadType.EQ_I,
                force_x=f_eq,  # Fuerza sísmica horizontal empujando hacia la punta (activa)
                force_y=Q_(0.0, "kN/m"),
                x_application=b.x_centroid,
                y_application=b.y_centroid
            ))
            
        # PIS: inercia del suelo inmediatamente encima del muro, incluido el talón
        # (CCP-14 11.6.5.1, W_s). El relleno sobre la punta no forma parte de W_s.
        for b in soil_blocks:
            if "Toe" in b.name:
                continue
            f_eq = b.weight * kh
            eq_loads.append(GenericLoad(
                name=f"Inertia PIS ({b.name})",
                load_type=LoadType.EQ_I,
                force_x=f_eq, # Fuerza sísmica horizontal
                force_y=Q_(0.0, "kN/m"),
                x_application=b.x_centroid,
                y_application=b.y_centroid
            ))
            
        return eq_loads
