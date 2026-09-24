import re

# 1. Update SeismicParameters
file1 = r'backend/src/wall_engine/seismic/parameters.py'
with open(file1, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('kv: float', 'kv: float\n    q_surcharge: float = 0.0')
with open(file1, 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Update design_route.py
file2 = r'backend/src/wall_engine/api/routes/design_route.py'
with open(file2, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "kv=request.seismic.kv if request.seismic else 0.0,",
    "kv=request.seismic.kv if request.seismic else 0.0,\n            q_surcharge=getattr(request.seismic, 'q_surcharge_kPa', 0.0) if request.seismic else 0.0,"
)
with open(file2, 'w', encoding='utf-8') as f:
    f.write(content)

# 3. Update orchestrator.py
file3 = r'backend/src/wall_engine/codes/ccp14/orchestrator.py'
with open(file3, 'r', encoding='utf-8') as f:
    content = f.read()

old_ls = """        # Sobrecarga LS (Traffic Surcharge)
        if wall.seismic and getattr(wall.seismic, 'q_surcharge', 0) > 0:
            pass
            
        # The correct way to call the existing method is:
        if hasattr(ep_res, 'coefficient_active'):
            k_a = ep_res.coefficient_active
        else:
            k_a = 0.3 # fallback
            
        try:
            ls_loads = self.ls_calc.calculate_ls_load(wall, k_a=k_a)
            loads.extend(ls_loads)
        except Exception as e:
            print("Error computing LS: ", e)"""

new_ls = """        # Sobrecarga LS (Traffic Surcharge)
        q_surcharge = getattr(wall.seismic, 'q_surcharge', 0.0) if wall.seismic else 0.0
        
        if hasattr(ep_res, 'coefficient_active'):
            k_a = ep_res.coefficient_active
        else:
            k_a = 0.3 # fallback
            
        try:
            ls_loads = self.ls_calc.calculate_ls_load(wall, k_a=k_a, q_surcharge_kPa=q_surcharge)
            loads.extend(ls_loads)
        except Exception as e:
            print("Error computing LS: ", e)"""

content = content.replace(old_ls, new_ls)
with open(file3, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated python files")
