import os

file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_eh = r"""const ehFormulaReplaced = computed(() => {
  const p = store.params
  const ka = store.results?.results?.earth_pressure?.ka?.toFixed(3) || '0.000'
  const Fx = ehLoad.value?.Fx?.toFixed(2) || '0.00'
  const Fy = ehLoad.value?.Fy?.toFixed(2) || '0.00'
  const h_total = p.H + p.D_z
  // Calculate total EH magnitude
  const total = (0.5 * p.gamma_fill * Math.pow(h_total, 2) * (store.results?.results?.earth_pressure?.ka || 0)).toFixed(2)
  return `$$ EH = \\frac{1}{2} \\gamma_s H_{total}^2 K_a $$
$$ EH = \\frac{1}{2} (${p.gamma_fill}) (${h_total.toFixed(2)})^2 (${ka}) = ${total} \\text{ kN/m} $$
$$ EH_x = EH \\cos(\\delta) = ${total} \\cos(${p.delta_fill}^\\circ) = ${Fx} \\text{ kN/m} $$
$$ EH_y = EH \\sin(\\delta) = ${total} \\sin(${p.delta_fill}^\\circ) = ${Fy} \\text{ kN/m} $$`
})
"""

new_ls = r"""const lsFormulaReplaced = computed(() => {
  const p = store.params
  const ka = store.results?.results?.earth_pressure?.ka?.toFixed(3) || '0.000'
  const Fx = lsLoad.value?.Fx?.toFixed(2) || '0.00'
  const Fy = lsLoad.value?.Fy?.toFixed(2) || '0.00'
  const h_total = p.H + p.D_z
  const total = (p.q_surcharge * h_total * (store.results?.results?.earth_pressure?.ka || 0)).toFixed(2)
  return `$$ LS = q_s H_{total} K_a $$
$$ LS = (${p.q_surcharge}) (${h_total.toFixed(2)}) (${ka}) = ${total} \\text{ kN/m} $$
$$ LS_x = LS \\cos(\\delta) = ${total} \\cos(${p.delta_fill}^\\circ) = ${Fx} \\text{ kN/m} $$
$$ LS_y = LS \\sin(\\delta) = ${total} \\sin(${p.delta_fill}^\\circ) = ${Fy} \\text{ kN/m} $$`
})
"""

start_eh = -1
end_eh = -1
for i, l in enumerate(lines):
    if l.startswith("const ehFormulaReplaced = computed"):
        start_eh = i
    if start_eh != -1 and l.startswith("})"):
        end_eh = i
        break

if start_eh != -1 and end_eh != -1:
    lines = lines[:start_eh] + [new_eh] + lines[end_eh+1:]

start_ls = -1
end_ls = -1
for i, l in enumerate(lines):
    if l.startswith("const lsFormulaReplaced = computed"):
        start_ls = i
    if start_ls != -1 and l.startswith("})"):
        end_ls = i
        break

if start_ls != -1 and end_ls != -1:
    lines = lines[:start_ls] + [new_ls] + lines[end_ls+1:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done using slice replacement with H_total.")
