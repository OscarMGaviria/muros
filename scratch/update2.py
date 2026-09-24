import os
file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

ka_modal_html = """
  <!-- Ka Modal -->
  <div v-if="showKaModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-orange-50">
        <h3 class="font-bold text-orange-900 flex items-center gap-2">
          <svg class="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>
          Proceso de Cálculo (Ka)
        </h3>
        <button @click="showKaModal = false" class="text-slate-400 hover:text-slate-600 bg-white rounded-md p-1 outline-none">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      <div class="p-5 overflow-y-auto custom-scrollbar flex-1 space-y-4">
        <div class="space-y-2">
          <p class="text-sm text-slate-600">El coeficiente de presión activa ($K_a$) se calcula utilizando la teoría de <strong>Coulomb / Mononobe-Okabe</strong>, considerando la inclinación del relleno y la fricción entre el muro y el suelo.</p>
        </div>
        <div class="bg-slate-50 p-3 rounded-lg border border-slate-200">
          <h4 class="text-xs font-bold text-slate-800 mb-2 uppercase tracking-wide">1. Valores Considerados</h4>
          <ul class="text-sm text-slate-600 space-y-1">
            <li><strong>Áng. Fricción Suelo (ϕ):</strong> {{ store.params.phi_fill }}°</li>
            <li><strong>Fricción Muro-Suelo (δ):</strong> {{ store.params.delta_fill }}°</li>
            <li><strong>Inclinación Relleno (β):</strong> {{ store.params.beta_fill }}°</li>
            <li><strong>Inclinación Respaldo (θ):</strong> 90° <span class="text-[10px] text-slate-400">(Vertical)</span></li>
          </ul>
        </div>
        <div class="bg-orange-50/50 p-3 rounded-lg border border-orange-100">
          <h4 class="text-xs font-bold text-orange-800 mb-2 uppercase tracking-wide">2. Fórmula de Coulomb</h4>
          <div class="text-center py-2 text-xs font-mono text-slate-700 bg-white border border-orange-200 rounded px-2">
            Ka = sin²(θ+ϕ) / [sin²(θ)·sin(θ-δ)·(1+√x)²]
          </div>
          <p class="text-[10px] text-slate-500 mt-2 text-center">Donde x = [sin(ϕ+δ)·sin(ϕ-β)] / [sin(θ-δ)·sin(θ+β)]</p>
        </div>
        <div class="bg-emerald-50 p-3 rounded-lg border border-emerald-100 flex items-center justify-between">
          <span class="text-sm font-bold text-emerald-900">Resultado Final (Ka)</span>
          <span class="text-lg font-black text-emerald-700 font-mono">{{ store.results?.results?.earth_pressure?.ka?.toFixed(4) || '---' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
"""

if '<!-- Ka Modal -->' not in content:
    # Find the last </template> and replace it
    parts = content.rsplit('</template>', 1)
    if len(parts) == 2:
        content = parts[0] + ka_modal_html + parts[1]

# Make sure showKaModal ref is added
if 'const showKaModal = ref(false)' not in content:
    content = content.replace('const showBearingModal = ref(false)', 'const showBearingModal = ref(false)\nconst showKaModal = ref(false)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated ParametersForm successfully')
