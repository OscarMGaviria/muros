<script setup>
import { useWallStore } from '../stores/wallStore'

const store = useWallStore()
</script>

<template>
  <aside class="w-80 bg-white flex flex-col z-10 shrink-0 shadow-[-4px_0_15px_rgba(0,0,0,0.05)] border-l border-slate-200">
    <div class="bg-blue-50 text-blue-800 p-3.5 flex justify-between items-center border-b border-blue-100">
      <h2 class="text-xs font-bold tracking-widest text-blue-800">RESULTADOS EN VIVO</h2>
      <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
    </div>
    <div class="flex-1 overflow-y-auto custom-scrollbar">
      <div v-if="!store.results && !store.isLoading" class="p-6 text-center text-slate-400">
        <p class="text-sm">Presiona "Actualizar Diseño" para ver los resultados</p>
      </div>
      <div v-if="store.results">
        <div class="bg-slate-100/50 px-4 py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-200">Estabilidad</div>
        <div class="divide-y divide-slate-100">
          <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
            <div><div class="text-xs font-bold text-slate-800">Deslizamiento</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">Fuerzas Res / Act</div></div>
            <div class="text-right">
              <div class="text-sm font-black text-green-600 font-mono tracking-tight" :class="{'text-red-500': store.results.results.stability.sliding.FS < store.thresholds.slidingFS}">FS: {{ store.results.results.stability.sliding.FS.toFixed(2) }}</div>
              <div class="text-[10px] text-slate-500 font-medium">Req &gt; {{ store.thresholds.slidingFS.toFixed(2) }}</div>
            </div>
          </div>
          <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
            <div><div class="text-xs font-bold text-slate-800">Volcamiento</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">e &lt; B/3</div></div>
            <div class="text-right">
              <div class="text-sm font-black text-green-600 font-mono tracking-tight" :class="{'text-red-500': store.results.results.stability.eccentricity.e >= (store.params.B / 3)}">e: {{ store.results.results.stability.eccentricity.e.toFixed(2) }} m</div>
              <div class="text-[10px] text-slate-500 font-medium">Límite: {{ (store.params.B / 3).toFixed(2) }} m</div>
            </div>
          </div>
          <div class="p-4 flex items-center justify-between border-l-[3px]" :class="store.results.results.stability.bearing.q_max > store.params.q_allow ? 'bg-orange-50/50 border-orange-500' : 'hover:bg-slate-50 border-transparent'">
            <div>
              <div class="text-xs font-bold text-slate-800" :class="{'text-orange-900': store.results.results.stability.bearing.q_max > store.params.q_allow}">Presión Contacto</div>
              <div class="text-[10px] text-slate-400 font-medium mt-0.5" :class="{'text-orange-600/80': store.results.results.stability.bearing.q_max > store.params.q_allow}">Esfuerzo a la roca</div>
            </div>
            <div class="text-right">
              <div class="text-sm font-black text-slate-700 font-mono tracking-tight" :class="{'text-orange-600': store.results.results.stability.bearing.q_max > store.params.q_allow}">{{ store.results.results.stability.bearing.q_max.toFixed(0) }} kPa</div>
              <div v-if="store.results.results.stability.bearing.q_max > store.params.q_allow" class="text-[10px] text-orange-600/80 font-bold px-1.5 py-0.5 bg-orange-100 rounded inline-block mt-0.5">FALLA</div>
            </div>
          </div>
        </div>
        
        <div class="bg-slate-100/50 px-4 py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest border-y border-slate-200 mt-2">Acero de Refuerzo</div>
        <div class="divide-y divide-slate-100">
          <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
            <div><div class="text-xs font-bold text-slate-800">Fuste (Cara Tierra)</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">Acero principal</div></div>
            <div class="text-right"><div class="text-sm font-black text-blue-600 bg-blue-50 px-2 py-1 rounded font-mono tracking-tight">{{ store.results.results.structural.reinforcement.stem_flexure.A_s_required.toFixed(1) }} cm²/m</div></div>
          </div>
          <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
            <div><div class="text-xs font-bold text-slate-800">Talón (Superior)</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">Por peso relleno</div></div>
            <div class="text-right"><div class="text-sm font-black text-blue-600 bg-blue-50 px-2 py-1 rounded font-mono tracking-tight">{{ store.results.results.structural.reinforcement.heel_flexure.A_s_required.toFixed(1) }} cm²/m</div></div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
