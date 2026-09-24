import os

file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

script_additions = """
const ehFormulaReplaced = computed(() => {
  const p = store.params
  const ka = store.results?.results?.earth_pressure?.ka?.toFixed(3) || '0.000'
  const Fx = ehLoad.value?.Fx?.toFixed(2) || '0.00'
  const Fy = ehLoad.value?.Fy?.toFixed(2) || '0.00'
  // Calculate total EH magnitude
  const total = (0.5 * p.gamma_fill * Math.pow(p.H, 2) * (store.results?.results?.earth_pressure?.ka || 0)).toFixed(2)
  return `$$ EH = \\frac{1}{2} \\gamma_s H^2 K_a $$
$$ EH = \\frac{1}{2} (${p.gamma_fill}) (${p.H})^2 (${ka}) = ${total} \\text{ kN/m} $$
$$ EH_x = EH \\cos(\\delta) = ${total} \\cos(${p.delta_fill}^\\circ) = ${Fx} \\text{ kN/m} $$
$$ EH_y = EH \\sin(\\delta) = ${total} \\sin(${p.delta_fill}^\\circ) = ${Fy} \\text{ kN/m} $$`
})

const lsFormulaReplaced = computed(() => {
  const p = store.params
  const ka = store.results?.results?.earth_pressure?.ka?.toFixed(3) || '0.000'
  const Fx = lsLoad.value?.Fx?.toFixed(2) || '0.00'
  const Fy = lsLoad.value?.Fy?.toFixed(2) || '0.00'
  const total = (p.q_surcharge * p.H * (store.results?.results?.earth_pressure?.ka || 0)).toFixed(2)
  return `$$ LS = q_s H K_a $$
$$ LS = (${p.q_surcharge}) (${p.H}) (${ka}) = ${total} \\text{ kN/m} $$
$$ LS_x = LS \\cos(\\delta) = ${total} \\cos(${p.delta_fill}^\\circ) = ${Fx} \\text{ kN/m} $$
$$ LS_y = LS \\sin(\\delta) = ${total} \\sin(${p.delta_fill}^\\circ) = ${Fy} \\text{ kN/m} $$`
})

watch([showEhModal, showLsModal, ehFormulaReplaced, lsFormulaReplaced], async ([newEh, newLs]) => {
  if (newEh || newLs) {
    await nextTick()
    if (window.MathJax) {
      setTimeout(() => {
        window.MathJax.typesetPromise().catch((err) => console.log('MathJax error: ', err))
      }, 50)
    }
  }
})
"""

# Insert script additions right after replacedFormula definition
if "const lsFormulaReplaced = computed" not in content:
    content = content.replace("watch([showKaModal", script_additions + "\nwatch([showKaModal")

# Now replace the modals.
# For EH MODAL
eh_search = """        <div class="bg-orange-50/50 p-4 rounded-lg border border-orange-100 text-center font-mono text-orange-800 leading-relaxed shadow-inner">
          <span class="block text-[10px] text-orange-600/70 uppercase tracking-widest mb-1 font-sans">Ecuaciones Base</span>
          EH_x = 0.5 · γ · H² · Ka · cos(δ)<br/>
          EH_y = 0.5 · γ · H² · Ka · sin(δ)
        </div>"""

eh_replace = """        <div class="bg-orange-50/50 p-4 rounded-lg border border-orange-100 text-center font-mono text-orange-800 leading-relaxed shadow-inner overflow-x-auto custom-scrollbar">
          <span class="block text-[10px] text-orange-600/70 uppercase tracking-widest mb-1 font-sans">Cálculo de Empuje</span>
          <div :key="ehFormulaReplaced">{{ ehFormulaReplaced }}</div>
        </div>"""

content = content.replace(eh_search, eh_replace)

# For LS MODAL
ls_search = """        <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-center font-mono text-blue-800 leading-relaxed shadow-inner">
          <span class="block text-[10px] text-blue-600/70 uppercase tracking-widest mb-1 font-sans">Ecuaciones Base</span>
          LS_x = q_surcharge · H · Ka · cos(δ)<br/>
          LS_y = q_surcharge · H · Ka · sin(δ)
        </div>"""

ls_replace = """        <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-center font-mono text-blue-800 leading-relaxed shadow-inner overflow-x-auto custom-scrollbar">
          <span class="block text-[10px] text-blue-600/70 uppercase tracking-widest mb-1 font-sans">Cálculo de Sobrecarga</span>
          <div :key="lsFormulaReplaced">{{ lsFormulaReplaced }}</div>
        </div>"""

content = content.replace(ls_search, ls_replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated Modals with MathJax formulas.")
