import os

file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add the sidebar icon
old_loads_icon = """<button @click="activeTab = 'loads'" :class="activeTab === 'loads' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Cargas"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"></path></svg></button>"""
new_results_icon = """
    <button @click="activeTab = 'results'" :class="activeTab === 'results' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Resultados"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg></button>
"""
if old_loads_icon in content:
    content = content.replace(old_loads_icon, old_loads_icon + new_results_icon)

# 2. Fix the header title
old_header = "{{ activeTab === 'geometry' ? 'Geometría' : activeTab === 'materials' ? 'Materiales' : activeTab === 'soils' ? 'Suelos' : 'Cargas y Sismo' }}"
new_header = "{{ activeTab === 'geometry' ? 'Geometría' : activeTab === 'materials' ? 'Materiales' : activeTab === 'soils' ? 'Suelos' : activeTab === 'loads' ? 'Cargas y Sismo' : 'Resultados' }}"
if old_header in content:
    content = content.replace(old_header, new_header)

# 3. Add the Results tab content
old_loads_content = """      <!-- TAB: LOADS -->
      <template v-if="activeTab === 'loads'">
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Sobrecarga (LS)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.q_surcharge" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">kPa</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Coef. Sísmico (kh)</label><div class="flex shadow-sm"><input type="number" step="0.01" v-model.number="store.params.kh" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">g</span></div></div>
      </template>"""

new_results_content = """
      <!-- TAB: RESULTS -->
      <template v-if="activeTab === 'results'">
        <div v-if="!store.results" class="flex flex-col items-center justify-center h-full text-slate-400 space-y-3 mt-10">
          <svg class="w-10 h-10 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"></path></svg>
          <p class="text-xs text-center font-medium">No hay resultados aún.<br/>Haga clic en <span class="font-bold text-slate-500">Actualizar Diseño</span>.</p>
        </div>
        <div v-else class="space-y-4">
          <div class="bg-indigo-50 p-3 rounded-md border border-indigo-100">
            <h3 class="text-xs font-bold text-indigo-900 mb-2">Factores de Seguridad</h3>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between border-b border-indigo-100 pb-1">
                <span class="text-slate-600">FS Deslizamiento</span>
                <span class="font-bold font-mono" :class="store.results.results.stability.fs_sliding >= 1.5 ? 'text-emerald-600' : 'text-red-600'">{{ store.results.results.stability.fs_sliding.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between border-b border-indigo-100 pb-1">
                <span class="text-slate-600">FS Volcamiento</span>
                <span class="font-bold font-mono" :class="store.results.results.stability.fs_overturning >= 2.0 ? 'text-emerald-600' : 'text-red-600'">{{ store.results.results.stability.fs_overturning.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between border-b border-indigo-100 pb-1">
                <span class="text-slate-600">FS Cap. Portante</span>
                <span class="font-bold font-mono" :class="store.results.results.bearing.fs_bearing >= store.params.FS ? 'text-emerald-600' : 'text-red-600'">{{ store.results.results.bearing.fs_bearing.toFixed(2) }}</span>
              </div>
            </div>
          </div>
          
          <div class="bg-rose-50 p-3 rounded-md border border-rose-100">
            <h3 class="text-xs font-bold text-rose-900 mb-2">Esfuerzos en la Base</h3>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between border-b border-rose-100 pb-1">
                <span class="text-slate-600">q_max (Punta)</span>
                <span class="font-bold font-mono text-slate-800">{{ store.results.results.bearing.q_toe.toFixed(1) }} <span class="text-[10px] text-slate-500">kPa</span></span>
              </div>
              <div class="flex justify-between border-b border-rose-100 pb-1">
                <span class="text-slate-600">q_min (Talón)</span>
                <span class="font-bold font-mono text-slate-800">{{ store.results.results.bearing.q_heel.toFixed(1) }} <span class="text-[10px] text-slate-500">kPa</span></span>
              </div>
              <div class="flex justify-between border-b border-rose-100 pb-1 pt-1">
                <span class="text-slate-600">Excentricidad (e)</span>
                <span class="font-bold font-mono text-slate-800">{{ store.results.results.bearing.eccentricity.toFixed(3) }} <span class="text-[10px] text-slate-500">m</span></span>
              </div>
            </div>
          </div>
        </div>
      </template>"""

if old_loads_content in content:
    content = content.replace(old_loads_content, old_loads_content + new_results_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated perfectly")
