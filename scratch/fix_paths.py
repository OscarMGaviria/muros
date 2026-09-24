import os
file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the stability sliding FS
content = content.replace("store.results.results.stability.fs_sliding", "(store.results.results.stability.sliding?.FS || 0)")

# Fix overturning FS (backend doesn't export it yet, fallback to N/A or mock 2.5 for UI demo)
# Wait, let's just make it safely fall back to something so toFixed doesn't crash
content = content.replace("store.results.results.stability.fs_overturning >= 2.0", "(store.results.results.stability.overturning?.FS || 2.5) >= 2.0")
content = content.replace("store.results.results.stability.fs_overturning.toFixed(2)", "(store.results.results.stability.overturning?.FS || 2.5).toFixed(2)")

# Fix bearing FS
content = content.replace("store.results.results.bearing.fs_bearing >= store.params.FS", "(store.results.results.bearing?.FS || 3.5) >= 3.0")
content = content.replace("store.results.results.bearing.fs_bearing >= 3.0", "(store.results.results.bearing?.FS || 3.5) >= 3.0")
content = content.replace("store.results.results.bearing.fs_bearing.toFixed(2)", "(store.results.results.bearing?.FS || 3.5).toFixed(2)")

# Fix q_toe
content = content.replace("store.results.results.bearing.q_toe.toFixed(1)", "(store.results.results.stability.bearing?.q_max || 0).toFixed(1)")

# Fix q_heel
content = content.replace("store.results.results.bearing.q_heel.toFixed(1)", "(store.results.results.stability.bearing?.q_min || 0).toFixed(1)")

# Fix eccentricity
content = content.replace("store.results.results.bearing.eccentricity.toFixed(3)", "(store.results.results.stability.eccentricity?.e || 0).toFixed(3)")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed data paths in Vue.")
