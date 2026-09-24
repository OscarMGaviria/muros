import os
import re

file_path = r'backend/src/wall_engine/calculations/loads/surcharge_calculator.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_method = '''    def calculate_ls_load(self, wall: Wall, k_a: float, q_surcharge_kPa: float) -> List[GenericLoad]:
        if q_surcharge_kPa <= 0:
            return []
            
        h_m = wall.geometry.stem_height.to('m').magnitude + wall.geometry.footing_thickness.to('m').magnitude
        
        # LS = q_s * H * K_a
        p_ls = q_surcharge_kPa * h_m * k_a
        y_app = h_m / 2.0
        
        delta_rad = wall.backfill.interface_friction.to('radians').magnitude if wall.backfill.interface_friction else 0.0
        import math
        force_x = p_ls * math.cos(delta_rad)
        force_y = -p_ls * math.sin(delta_rad) # Pushing down
        
        load = GenericLoad(
            name="Traffic Surcharge (LS)",
            type=LoadType.LS,
            force_x=Q_(force_x, "kN/m"),
            force_y=Q_(force_y, "kN/m"),
            application_y=Q_(y_app, "m"),
            application_x=wall.geometry.toe_length + wall.geometry.stem_thickness_base
        )
        return [load]'''

content = re.sub(r'    def calculate_ls_load.*', new_method, content, flags=re.DOTALL)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated surcharge_calculator.py')
