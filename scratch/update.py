import os
file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add delta_fill, beta_fill, Ka to Suelo de Relleno block
suelo_relleno_new = """<div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.gamma_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Áng. Fricción Suelo (ϕ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.phi_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Fricción Muro-Suelo (δ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.delta_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Inclinación Relleno (β)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.beta_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
            <div v-if="store.results?.results?.earth_pressure?.ka" class="pt-2 border-t border-orange-200/50 mt-2 flex justify-between items-center">
              <span class="text-[10px] font-bold text-orange-800 flex items-center">
                Coef. Activo (Ka)
                <button @click="showKaModal = true" class="ml-1 text-blue-600 hover:text-blue-800 outline-none" title="Ver proceso de cálculo">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" /></svg>
                </button>
              </span>
              <div class="w-16"><input type="text" readonly disabled :value="store.results.results.earth_pressure.ka.toFixed(3)" class="w-full bg-orange-100/50 border border-orange-200 rounded py-0.5 px-2 text-xs font-mono font-black text-orange-700 text-right shadow-inner cursor-not-allowed outline-none" /></div>
            </div>"""

old_suelo_relleno = """<div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.gamma_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Áng. Fricción (ϕ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.phi_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>"""

content = content.replace(old_suelo_relleno, suelo_relleno_new)

# Clean up old delta fill if it's lingering
old_delta = """<div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Fricción Muro-Suelo (δ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.delta_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>"""
content = content.replace(old_delta + "\n" + old_delta, old_delta)

# Update Modal text
if '<li><strong>Inclinación Relleno (β):</strong> 0°</li>' in content:
    content = content.replace('<li><strong>Inclinación Relleno (β):</strong> 0°</li>', '<li><strong>Inclinación Relleno (β):</strong> {{ store.params.beta_fill }}°</li>')
if '<li><strong>Inclinación Respaldo (θ):</strong> 90°</li>' in content:
    content = content.replace('<li><strong>Inclinación Respaldo (θ):</strong> 90°</li>', '<li><strong>Inclinación Respaldo (θ):</strong> 90° <span class="text-[10px] text-slate-400">(Vertical)</span></li>')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated successfully!')
