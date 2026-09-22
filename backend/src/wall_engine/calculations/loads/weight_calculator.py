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
        
        # 1. Zapata (Footing)
        footing_vol = geom.footing_width * geom.footing_thickness # m^3 por metro lineal
        footing_weight = (footing_vol * gamma_c).to("kN/m")
        blocks.append(Block2D(
            name="Footing",
            load_type="DC",
            weight=footing_weight,
            x_centroid=geom.footing_width / 2,
            y_centroid=geom.footing_thickness / 2
        ))
        
        # 2. Fuste Rectangular (Stem Rectangular)
        stem_rect_vol = geom.stem_thickness_top * geom.stem_height
        stem_rect_weight = (stem_rect_vol * gamma_c).to("kN/m")
        # x: toe + parte triangular (si la cara inclinada está adelante) o atrás.
        # Por simplicidad asumiremos que la cara vertical está atrás y la inclinada adelante, 
        # o viceversa dependiendo de stem_batter.
        # Para CCP-14 muros en voladizo estándar, la cara trasera es vertical.
        # Así que el rectángulo está en la parte trasera del fuste.
        x_stem_back = geom.toe_length + geom.stem_thickness_base
        x_rect_centroid = x_stem_back - (geom.stem_thickness_top / 2)
        
        blocks.append(Block2D(
            name="Stem (Rectangular)",
            load_type="DC",
            weight=stem_rect_weight,
            x_centroid=x_rect_centroid,
            y_centroid=geom.footing_thickness + (geom.stem_height / 2)
        ))
        
        # 3. Fuste Triangular (Stem Triangular)
        diff_thickness = geom.stem_thickness_base - geom.stem_thickness_top
        if diff_thickness.magnitude > 0:
            stem_tri_vol = 0.5 * diff_thickness * geom.stem_height
            stem_tri_weight = (stem_tri_vol * gamma_c).to("kN/m")
            # C.G de un triángulo es a 1/3 de su base. Si la parte ancha está abajo.
            # En x, desde la punta del fuste (adelante)
            x_tri_centroid = geom.toe_length + (diff_thickness * 2 / 3) # Asumiendo cara interior vertical
            
            blocks.append(Block2D(
                name="Stem (Triangular)",
                load_type="DC",
                weight=stem_tri_weight,
                x_centroid=x_tri_centroid,
                y_centroid=geom.footing_thickness + (geom.stem_height / 3)
            ))
            
        return blocks
        
    def calculate_soil_blocks(self, wall: Wall) -> List[Block2D]:
        """Calcula los bloques de suelo (EV) sobre la zapata"""
        blocks = []
        geom = wall.geometry
        gamma_s = wall.backfill.unit_weight
        
        # 1. Suelo sobre el talón (Rectangular)
        if geom.heel_length.magnitude > 0:
            heel_soil_vol = geom.heel_length * geom.stem_height
            heel_soil_weight = (heel_soil_vol * gamma_s).to("kN/m")
            x_heel_centroid = geom.toe_length + geom.stem_thickness_base + (geom.heel_length / 2)
            
            blocks.append(Block2D(
                name="Soil over Heel (Rectangular)",
                load_type="EV",
                weight=heel_soil_weight,
                x_centroid=x_heel_centroid,
                y_centroid=geom.footing_thickness + (geom.stem_height / 2)
            ))
            
            # 2. Suelo sobre el talón (Triangular por el talud)
            beta = geom.backfill_slope.to('radians').magnitude
            if beta > 0:
                slope_height = geom.heel_length * math.tan(beta)
                slope_vol = 0.5 * geom.heel_length * slope_height
                slope_weight = (slope_vol * gamma_s).to("kN/m")
                # C.G. a 1/3 del talón desde el inicio del talud
                x_slope_centroid = geom.toe_length + geom.stem_thickness_base + (geom.heel_length / 3)
                
                blocks.append(Block2D(
                    name="Soil over Heel (Slope)",
                    load_type="EV",
                    weight=slope_weight,
                    x_centroid=x_slope_centroid,
                    y_centroid=geom.footing_thickness + geom.stem_height + (slope_height / 3)
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
            
        # PIS: Fuerzas inerciales del suelo (Talón y Punta)
        for b in soil_blocks:
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
