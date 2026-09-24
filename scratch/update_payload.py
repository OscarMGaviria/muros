import os
import re

# 1. Update frontend/src/stores/wallStore.js
store_file = r'frontend/src/stores/wallStore.js'
with open(store_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("kh: this.params.kh,", "kh: this.params.kh,\n            q_surcharge_kPa: this.params.q_surcharge,")
with open(store_file, 'w', encoding='utf-8') as f:
    f.write(content)

# 2. Update backend/src/wall_engine/api/schemas/wall_schema.py
schema_file = r'backend/src/wall_engine/api/schemas/wall_schema.py'
with open(schema_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("kv: float = Field(0.0, ge=0)", "kv: float = Field(0.0, ge=0)\n    q_surcharge_kPa: float = Field(0.0, ge=0)")
with open(schema_file, 'w', encoding='utf-8') as f:
    f.write(content)

# 3. Update backend/src/wall_engine/domain/wall/entities.py
# If Seismic object doesn't have q_surcharge, we can just use the raw request or add it.
# Let's check entities.py and orchestrator.py
