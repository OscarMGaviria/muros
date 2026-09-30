<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useWallStore } from './stores/wallStore'
import InputPanel from './components/InputPanel.vue'
import ChecksPanel from './components/ChecksPanel.vue'
import Viewer2D from './components/Viewer2D.vue'
import Viewer3D from './components/Viewer3D.vue'
import CalcReport from './components/CalcReport.vue'

const store = useWallStore()

const VIEWS = [
  { id: '2D', label: 'Plano' },
  { id: 'Esquema', label: 'Distribuciones' },
  { id: '3D', label: 'Modelo 3D' },
  { id: 'Memoria', label: 'Memoria de cálculo' }
]

// Veredicto global del muro, del resumen del motor
const verdict = computed(() => {
  const s = store.results?.results?.summary
  if (!s) return null
  if (s.status === 'CUMPLE') return { text: 'Cumple todas las verificaciones', cls: 'bg-emerald-50 text-emerald-800 ring-emerald-200' }
  const first = s.checks.find(c => c.ok === false)
  return { text: `No cumple: ${first.label.toLowerCase()} (D/C ${first.ratio.toFixed(3)})`, cls: 'bg-red-50 text-red-800 ring-red-200', check: first }
})

function onVerdict () {
  const c = verdict.value?.check
  if (c && c.group === 'Estabilidad') store.openMemoria(c.state, c.id)
}

let healthInterval = null
onMounted(() => {
  store.checkHealth()
  store.calculate()
  healthInterval = setInterval(() => store.checkHealth(), 20000)
})
onUnmounted(() => { if (healthInterval) clearInterval(healthInterval) })
</script>

<template>
  <div class="h-screen w-screen flex flex-col bg-slate-100 font-sans text-slate-900 overflow-hidden">

    <!-- BARRA DE PROYECTO -->
    <header class="shrink-0 bg-white border-b border-slate-200 px-4 py-2 flex flex-wrap items-center gap-x-5 gap-y-2">
      <div class="font-bold tracking-wider text-slate-800">MUROS <span class="text-blue-700">CCP-14</span></div>
      <div class="flex flex-col min-w-0">
        <label for="project-name" class="sr-only">Nombre del proyecto</label>
        <input id="project-name" v-model="store.projectName"
               class="text-sm font-semibold text-slate-800 bg-transparent rounded px-1 -mx-1 hover:bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-200 min-w-0 w-64" />
        <span class="text-xs text-slate-500">CCP-14 (AASHTO LRFD) · muro en voladizo · por metro de muro · kN, m, kPa</span>
      </div>
      <div class="flex-1"></div>
      <button v-if="verdict" type="button" @click="onVerdict"
              class="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold ring-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
              :class="[verdict.cls, verdict.check ? 'cursor-pointer' : 'cursor-default']"
              :title="verdict.check ? 'Ver el cálculo en la memoria' : ''">
        <span class="h-2 w-2 rounded-full bg-current"></span>{{ verdict.text }}
      </button>
      <span v-if="store.isLoading" class="text-xs text-slate-500">Calculando…</span>
      <span class="flex items-center gap-1.5 text-xs text-slate-500">
        <span class="h-2 w-2 rounded-full" :class="store.serverOnline ? 'bg-emerald-500' : store.serverOnline === false ? 'bg-red-500' : 'bg-slate-300'"></span>
        {{ store.serverOnline ? 'Motor conectado' : store.serverOnline === false ? 'Motor desconectado' : 'Verificando…' }}
      </span>
    </header>

    <div v-if="store.error" role="alert" class="shrink-0 bg-red-50 text-red-800 border-b border-red-200 px-4 py-2 flex items-center justify-between gap-3 text-sm">
      <span>{{ store.error }}</span>
      <button @click="store.error = null" class="text-red-500 hover:text-red-700 text-xs font-semibold">Cerrar</button>
    </div>
    <div v-if="store.results?.results?.warnings?.length" class="shrink-0 bg-amber-50 text-amber-900 border-b border-amber-200 px-4 py-2 text-sm space-y-1">
      <p v-for="(w, i) in store.results.results.warnings" :key="i">⚠ {{ w }}</p>
    </div>

    <main class="flex-1 flex min-h-0">
      <InputPanel />

      <section class="flex-1 min-w-0 flex flex-col">
        <nav class="shrink-0 bg-white border-b border-slate-200 px-3 flex gap-1" role="tablist" aria-label="Vistas">
          <button v-for="v in VIEWS" :key="v.id" role="tab" :aria-selected="store.viewMode === v.id" @click="store.viewMode = v.id"
                  class="px-3 py-2.5 text-sm font-medium border-b-2 -mb-px focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                  :class="store.viewMode === v.id ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-500 hover:text-slate-800'">
            {{ v.label }}
          </button>
        </nav>
        <div class="flex-1 min-h-0 relative" style="background-color: #f8fafc; background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 24px 24px;">
          <Viewer3D v-if="store.viewMode === '3D'" />
          <CalcReport v-else-if="store.viewMode === 'Memoria'" />
          <Viewer2D v-else />
        </div>
      </section>

      <ChecksPanel />
    </main>
  </div>
</template>
