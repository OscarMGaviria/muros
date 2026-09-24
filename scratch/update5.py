import os
file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

watcher_old = """const showKaModal = ref(false)

watch(showKaModal, async (newVal) => {
  if (newVal) {
    await nextTick()
    if (window.MathJax) {
      window.MathJax.typesetPromise()
    }
  }
})"""

watcher_new = """const showKaModal = ref(false)

const replacedFormula = computed(() => {
  const p = store.params
  const th = store.theta
  return `$$ K_a = \\\\frac{\\\\sin^2(${th}^\\circ + ${p.phi_fill}^\\circ)}{\\\\sin^2${th}^\\circ \\\\sin(${th}^\\circ - ${p.delta_fill}^\\circ) \\\\left[ 1 + \\\\sqrt{\\\\frac{\\\\sin(${p.phi_fill}^\\circ + ${p.delta_fill}^\\circ) \\\\sin(${p.phi_fill}^\\circ - ${p.beta_fill}^\\circ)}{\\\\sin(${th}^\\circ - ${p.delta_fill}^\\circ) \\\\sin(${th}^\\circ + ${p.beta_fill}^\\circ)}} \\\\right]^2 } $$`
})

watch([showKaModal, replacedFormula], async ([newModal]) => {
  if (newModal) {
    await nextTick()
    if (window.MathJax) {
      setTimeout(() => {
        // Resetting window.MathJax elements is sometimes necessary, 
        // but typesetPromise with specific elements is safer.
        window.MathJax.typesetPromise()
      }, 50)
    }
  }
})"""

if watcher_old in content:
    content = content.replace(watcher_old, watcher_new)

old_formula_block = """<div class="bg-orange-50/50 p-3 rounded-lg border border-orange-100">
          <h4 class="text-xs font-bold text-orange-800 mb-2 uppercase tracking-wide">2. Fórmula de Coulomb</h4>
          <div class="text-center py-2 text-sm text-slate-800 bg-white border border-orange-200 rounded px-2 overflow-x-auto custom-scrollbar">
            $$ K_a = \\frac{\\sin^2(\\theta + \\phi)}{\\sin^2\\theta \\sin(\\theta - \\delta) \\left[ 1 + \\sqrt{\\frac{\\sin(\\phi + \\delta) \\sin(\\phi - \\beta)}{\\sin(\\theta - \\delta) \\sin(\\theta + \\beta)}} \\right]^2 } $$
          </div>
        </div>"""

new_formula_block = """<div class="bg-orange-50/50 p-3 rounded-lg border border-orange-100">
          <h4 class="text-xs font-bold text-orange-800 mb-2 uppercase tracking-wide">2. Fórmula de Coulomb (Num. 3.11.5.3, CCP-14)</h4>
          <div class="text-center py-2 text-sm text-slate-800 bg-white border border-orange-200 rounded px-2 overflow-x-auto custom-scrollbar">
            $$ K_a = \\frac{\\sin^2(\\theta + \\phi)}{\\sin^2\\theta \\sin(\\theta - \\delta) \\left[ 1 + \\sqrt{\\frac{\\sin(\\phi + \\delta) \\sin(\\phi - \\beta)}{\\sin(\\theta - \\delta) \\sin(\\theta + \\beta)}} \\right]^2 } $$
          </div>
        </div>
        
        <div class="bg-blue-50 p-3 rounded-lg border border-blue-100">
          <h4 class="text-xs font-bold text-blue-800 mb-2 uppercase tracking-wide">3. Reemplazo de Valores</h4>
          <div :key="replacedFormula" class="text-center py-2 text-sm text-slate-800 bg-white border border-blue-200 rounded px-2 overflow-x-auto custom-scrollbar">
            {{ replacedFormula }}
          </div>
        </div>"""

if old_formula_block in content:
    content = content.replace(old_formula_block, new_formula_block)

old_res_block = """<div class="bg-emerald-50 p-3 rounded-lg border border-emerald-100 flex items-center justify-between">
          <span class="text-sm font-bold text-emerald-900">Resultado Final (Ka)</span>"""

new_res_block = """<div class="bg-emerald-50 p-3 rounded-lg border border-emerald-100 flex items-center justify-between mt-2">
          <h4 class="text-xs font-bold text-emerald-900 uppercase tracking-wide">4. Resultado Final (Ka)</h4>"""

if old_res_block in content:
    content = content.replace(old_res_block, new_res_block)


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
