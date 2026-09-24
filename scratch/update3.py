import os
file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_theta_text = '<li><strong>Inclinación Respaldo (θ):</strong> 90° <span class="text-[10px] text-slate-400\">(Vertical)</span></li>'
new_theta_text = '<li><strong>Inclinación Respaldo (θ):</strong> {{ store.theta }}° <span class="text-[10px] text-slate-400\">{{ store.theta === 90 ? "(Vertical)" : "(Calculado)" }}</span></li>'

if old_theta_text in content:
    content = content.replace(old_theta_text, new_theta_text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ParametersForm successfully.")
