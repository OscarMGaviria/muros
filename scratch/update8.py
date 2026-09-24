import os

file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add reactive variables and computed properties
vue_script_additions = """
const showDcModal = ref(false)
const showEhModal = ref(false)
const showLsModal = ref(false)

const dcLoads = computed(() => store.results?.results?.loads?.filter(ld => ld.type === 'DC') || [])
const ehLoad = computed(() => store.results?.results?.loads?.find(ld => ld.type === 'EH'))
const lsLoad = computed(() => store.results?.results?.loads?.find(ld => ld.type === 'LS'))
"""
if "const dcLoads = computed" not in content:
    content = content.replace("const showKaModal = ref(false)", "const showKaModal = ref(false)\n" + vue_script_additions)

# 2. Add buttons (chips/cards) in the Resultados tab
old_results_tab_end = """              <div class="flex justify-between border-b border-rose-100 pb-1 pt-1">
                <span class="text-slate-600">Excentricidad (e)</span>
                <span class="font-bold font-mono text-slate-800">{{ store.results.results.bearing.eccentricity.toFixed(3) }} <span class="text-[10px] text-slate-500">m</span></span>
              </div>
            </div>
          </div>
        </div>
      </template>"""

new_buttons = """              <div class="flex justify-between border-b border-rose-100 pb-1 pt-1">
                <span class="text-slate-600">Excentricidad (e)</span>
                <span class="font-bold font-mono text-slate-800">{{ store.results.results.bearing.eccentricity.toFixed(3) }} <span class="text-[10px] text-slate-500">m</span></span>
              </div>
            </div>
          </div>
          
          <div class="grid grid-cols-3 gap-2 pt-2">
            <button @click="showDcModal = true" class="bg-slate-50 hover:bg-slate-100 p-2 rounded-lg border border-slate-200 flex flex-col items-center justify-center transition-all shadow-sm hover:shadow">
              <span class="text-[10px] font-bold text-slate-500 uppercase">Pesos</span>
              <span class="text-lg font-black text-slate-700">DC</span>
            </button>
            <button @click="showEhModal = true" class="bg-orange-50 hover:bg-orange-100 p-2 rounded-lg border border-orange-200 flex flex-col items-center justify-center transition-all shadow-sm hover:shadow">
              <span class="text-[10px] font-bold text-orange-600 uppercase">Empuje</span>
              <span class="text-lg font-black text-orange-800">EH</span>
            </button>
            <button @click="showLsModal = true" class="bg-blue-50 hover:bg-blue-100 p-2 rounded-lg border border-blue-200 flex flex-col items-center justify-center transition-all shadow-sm hover:shadow">
              <span class="text-[10px] font-bold text-blue-600 uppercase">Sobrecarga</span>
              <span class="text-lg font-black text-blue-800">LS</span>
            </button>
          </div>
        </div>
      </template>"""

if "showDcModal = true" not in content:
    content = content.replace(old_results_tab_end, new_buttons)

# 3. Add the three Modals before </template>
new_modals = """
  <!-- DC MODAL -->
  <div v-if="showDcModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 class="font-bold text-slate-800">Desglose de Pesos Propios (DC)</h3>
        <button @click="showDcModal = false" class="text-slate-400 hover:text-slate-600 outline-none"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
      </div>
      <div class="p-5 overflow-y-auto custom-scrollbar">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b-2 border-slate-200 text-slate-600">
              <th class="py-2">Elemento</th>
              <th class="py-2 text-right">Área (m²)</th>
              <th class="py-2 text-right">Peso (kN/m)</th>
              <th class="py-2 text-right">Brazo X (m)</th>
              <th class="py-2 text-right">Momento (kN-m/m)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ld in dcLoads" :key="ld.name" class="border-b border-slate-100">
              <td class="py-2 font-medium text-slate-700">{{ ld.name }}</td>
              <td class="py-2 text-right font-mono text-slate-500">{{ (ld.Fy / 24).toFixed(3) }}</td>
              <td class="py-2 text-right font-mono font-bold">{{ ld.Fy.toFixed(1) }}</td>
              <td class="py-2 text-right font-mono">{{ ld.x_app.toFixed(2) }}</td>
              <td class="py-2 text-right font-mono font-bold text-slate-800">{{ (ld.Fy * ld.x_app).toFixed(1) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-slate-50 font-bold text-slate-800">
              <td class="py-2 px-2 uppercase text-[10px]">Total DC</td>
              <td class="py-2 text-right font-mono">{{ dcLoads.reduce((sum, ld) => sum + (ld.Fy/24), 0).toFixed(3) }}</td>
              <td class="py-2 text-right font-mono">{{ dcLoads.reduce((sum, ld) => sum + ld.Fy, 0).toFixed(1) }}</td>
              <td class="py-2 text-right font-mono">-</td>
              <td class="py-2 text-right font-mono">{{ dcLoads.reduce((sum, ld) => sum + (ld.Fy * ld.x_app), 0).toFixed(1) }}</td>
            </tr>
          </tfoot>
        </table>
        <p class="text-[9px] text-slate-400 mt-3 text-center">* El área se estima dividiendo el peso entre el peso específico del concreto (γc = 24 kN/m³).</p>
      </div>
    </div>
  </div>

  <!-- EH MODAL -->
  <div v-if="showEhModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-orange-100 flex justify-between items-center bg-orange-50">
        <h3 class="font-bold text-orange-900">Cálculo de Empuje Activo (EH)</h3>
        <button @click="showEhModal = false" class="text-orange-400 hover:text-orange-600 outline-none"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
      </div>
      <div class="p-5 space-y-4 text-sm">
        <div class="bg-orange-50/50 p-4 rounded-lg border border-orange-100 text-center font-mono text-orange-800 leading-relaxed shadow-inner">
          <span class="block text-[10px] text-orange-600/70 uppercase tracking-widest mb-1 font-sans">Ecuaciones Base</span>
          EH_x = 0.5 · γ · H² · Ka · cos(δ)<br/>
          EH_y = 0.5 · γ · H² · Ka · sin(δ)
        </div>
        <div class="grid grid-cols-2 gap-3 text-xs mt-4">
          <div class="border p-3 rounded-lg bg-slate-50/50 shadow-sm"><span class="block text-slate-500 mb-1">Fuerza Horizontal (Fx)</span><span class="text-lg font-black font-mono text-slate-800">{{ ehLoad?.Fx?.toFixed(2) || '0.00' }} <span class="text-xs font-sans font-normal text-slate-500">kN/m</span></span></div>
          <div class="border p-3 rounded-lg bg-slate-50/50 shadow-sm"><span class="block text-slate-500 mb-1">Fuerza Vertical (Fy)</span><span class="text-lg font-black font-mono text-slate-800">{{ ehLoad?.Fy?.toFixed(2) || '0.00' }} <span class="text-xs font-sans font-normal text-slate-500">kN/m</span></span></div>
          <div class="border p-3 rounded-lg bg-slate-50/50 shadow-sm"><span class="block text-slate-500 mb-1">Brazo Y (y_app)</span><span class="text-lg font-black font-mono text-slate-800">{{ ehLoad?.y_app?.toFixed(2) || '0.00' }} <span class="text-xs font-sans font-normal text-slate-500">m</span></span></div>
          <div class="border p-3 rounded-lg bg-orange-50 shadow-sm border-orange-200"><span class="block text-orange-700 font-bold mb-1">Momento Volteo</span><span class="text-lg font-black font-mono text-orange-900">{{ ((ehLoad?.Fx || 0) * (ehLoad?.y_app || 0)).toFixed(2) }} <span class="text-xs font-sans font-normal text-orange-700/70">kN-m/m</span></span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- LS MODAL -->
  <div v-if="showLsModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-blue-100 flex justify-between items-center bg-blue-50">
        <h3 class="font-bold text-blue-900">Cálculo de Sobrecarga (LS)</h3>
        <button @click="showLsModal = false" class="text-blue-400 hover:text-blue-600 outline-none"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
      </div>
      <div class="p-5 space-y-4 text-sm">
        <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-center font-mono text-blue-800 leading-relaxed shadow-inner">
          <span class="block text-[10px] text-blue-600/70 uppercase tracking-widest mb-1 font-sans">Ecuaciones Base</span>
          LS_x = q_surcharge · H · Ka · cos(δ)<br/>
          LS_y = q_surcharge · H · Ka · sin(δ)
        </div>
        <div class="grid grid-cols-2 gap-3 text-xs mt-4">
          <div class="border p-3 rounded-lg bg-slate-50/50 shadow-sm"><span class="block text-slate-500 mb-1">Fuerza Horizontal (Fx)</span><span class="text-lg font-black font-mono text-slate-800">{{ lsLoad?.Fx?.toFixed(2) || '0.00' }} <span class="text-xs font-sans font-normal text-slate-500">kN/m</span></span></div>
          <div class="border p-3 rounded-lg bg-slate-50/50 shadow-sm"><span class="block text-slate-500 mb-1">Fuerza Vertical (Fy)</span><span class="text-lg font-black font-mono text-slate-800">{{ lsLoad?.Fy?.toFixed(2) || '0.00' }} <span class="text-xs font-sans font-normal text-slate-500">kN/m</span></span></div>
          <div class="border p-3 rounded-lg bg-slate-50/50 shadow-sm"><span class="block text-slate-500 mb-1">Brazo Y (y_app)</span><span class="text-lg font-black font-mono text-slate-800">{{ lsLoad?.y_app?.toFixed(2) || '0.00' }} <span class="text-xs font-sans font-normal text-slate-500">m</span></span></div>
          <div class="border p-3 rounded-lg bg-blue-50 shadow-sm border-blue-200"><span class="block text-blue-700 font-bold mb-1">Momento Volteo</span><span class="text-lg font-black font-mono text-blue-900">{{ ((lsLoad?.Fx || 0) * (lsLoad?.y_app || 0)).toFixed(2) }} <span class="text-xs font-sans font-normal text-blue-700/70">kN-m/m</span></span></div>
        </div>
      </div>
    </div>
  </div>
</template>
"""

if "<!-- DC MODAL -->" not in content:
    content = content.replace("</template>\n", new_modals)
    # also handle if it's EOF without newline
    if "<!-- DC MODAL -->" not in content:
        content = content.replace("</template>", new_modals)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added cards and modals")
