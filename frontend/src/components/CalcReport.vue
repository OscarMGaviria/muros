<script setup>
import { computed, ref, watch } from 'vue'
import { useWallStore } from '../stores/wallStore'
import MathBlock from './MathBlock.vue'

const store = useWallStore()
const trace = computed(() => store.results?.results?.trace || null)

const activeState = ref('Strength I')
const openTables = ref({})

const states = computed(() => trace.value?.stability || [])
const currentState = computed(() => states.value.find(s => s.name === activeState.value) || states.value[0])

watch(states, (list) => {
  if (list.length && !list.some(s => s.name === activeState.value)) activeState.value = list[0].name
}, { immediate: true })

const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v)) ? '—' : Number(v).toFixed(d)

// Matriz de factores: filas = tipos de carga, columnas = estados límite
const factorMatrix = computed(() => {
  const ls = trace.value?.limit_states || []
  const types = []
  ls.forEach(s => s.factors.forEach(f => { if (!types.some(t => t.type === f.type)) types.push({ type: f.type, label: f.label }) }))
  return types.map(t => ({
    ...t,
    cells: ls.map(s => {
      const f = s.factors.find(x => x.type === t.type)
      if (!f) return '—'
      return f.max === f.min ? fmt(f.max) : `${fmt(f.max)} / ${fmt(f.min)}`
    })
  }))
})

function stepLatex (s) {
  const unit = s.unit ? `\\ \\text{${s.unit}}` : ''
  const parts = [s.symbol]
  if (s.formula) parts.push(s.formula)
  if (s.substitution) parts.push(s.substitution)
  parts.push(`${fmt(s.value, 3)}${unit}`)
  return parts.join(' = ')
}

function statusOf (check) {
  const r = check.result
  if (r.ok === null || r.ok === undefined) return { text: 'Informativo', cls: 'bg-slate-100 text-slate-600' }
  return r.ok
    ? { text: 'Cumple', cls: 'bg-emerald-100 text-emerald-700' }
    : { text: 'No cumple', cls: 'bg-red-100 text-red-700' }
}

function toggleTable (key) {
  openTables.value = { ...openTables.value, [key]: !openTables.value[key] }
}

// Exporta las cargas sin mayorar a CSV (separador ; para Excel en español)
function exportLoadsCsv () {
  const t = trace.value
  if (!t) return
  const header = ['N°', 'Carga', 'Tipo', 'Fx (kN/m)', 'Fy (kN/m)', 'x (m)', 'y (m)', 'M_V = Fx·y (kN·m/m)', 'M_R = Fy·x (kN·m/m)']
  const lines = [header]
  t.loads.groups.forEach(g => g.rows.forEach(r => lines.push([r.id, r.name, g.label, r.Fx, r.Fy, r.x, r.y, r.M_V, r.M_R])))
  const tot = t.loads.total
  lines.push(['', 'TOTAL', '', tot.Fx, tot.Fy, '', '', tot.M_V, tot.M_R])
  const csv = lines.map(l => l.map(v => typeof v === 'number' ? v.toFixed(4).replace('.', ',') : `"${String(v).replace(/"/g, '""')}"`).join(';')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'cargas_muro.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

</script>

<template>
  <div class="h-full overflow-y-auto bg-slate-50">
    <div v-if="!trace" class="h-full flex items-center justify-center text-sm text-slate-400">
      Calcule el muro para ver la memoria de cálculo.
    </div>

    <!-- pr-20: deja libre la franja del botón flotante de vistas -->
    <div v-else class="max-w-5xl mx-auto pl-6 pr-20 py-8 space-y-10 text-slate-800">
      <header class="space-y-2">
        <p class="text-[11px] font-bold uppercase tracking-widest text-blue-600">Memoria de cálculo · CCP-14 / AASHTO LRFD</p>
        <h1 class="text-2xl font-extrabold">Cargas y estabilidad externa</h1>
        <p class="text-xs text-slate-500 max-w-3xl leading-relaxed">{{ trace.loads.convention }}</p>
      </header>

      <!-- 1. CARGAS SIN MAYORAR -->
      <section class="space-y-3">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold">1. Cargas sin mayorar</h2>
            <p class="text-xs text-slate-500">Por metro de muro. Momentos respecto a la punta (x = 0, y = 0).</p>
          </div>
          <button @click="exportLoadsCsv" class="text-xs font-semibold px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500">
            Exportar a Excel (CSV)
          </button>
        </div>
        <div class="overflow-x-auto bg-white border border-slate-200 rounded-lg">
          <table class="w-full text-xs">
            <thead class="bg-slate-100 text-slate-500 text-[10px]">
              <tr>
                <th class="text-left px-3 py-2">N°</th>
                <th class="text-left px-3 py-2">Carga</th>
                <th class="text-right px-3 py-2">Fx (kN/m)</th>
                <th class="text-right px-3 py-2">Fy (kN/m)</th>
                <th class="text-right px-3 py-2">x (m)</th>
                <th class="text-right px-3 py-2">y (m)</th>
                <th class="text-right px-3 py-2">M<sub>V</sub> = Fx·y</th>
                <th class="text-right px-3 py-2">M<sub>R</sub> = Fy·x</th>
              </tr>
            </thead>
            <tbody class="font-mono tabular-nums">
              <template v-for="g in trace.loads.groups" :key="g.type">
                <tr class="bg-slate-50"><td colspan="8" class="px-3 py-1.5 font-sans font-bold text-slate-600">{{ g.label }}</td></tr>
                <tr v-for="r in g.rows" :key="r.id" class="border-t border-slate-100">
                  <td class="px-3 py-1.5 text-slate-400">{{ r.id }}</td>
                  <td class="px-3 py-1.5 font-sans">{{ r.name }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(r.Fx) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(r.Fy) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(r.x, 3) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(r.y, 3) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(r.M_V) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(r.M_R) }}</td>
                </tr>
                <tr class="border-t border-slate-200 text-slate-500">
                  <td></td><td class="px-3 py-1.5 font-sans italic">Subtotal</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(g.subtotal.Fx) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(g.subtotal.Fy) }}</td>
                  <td></td><td></td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(g.subtotal.M_V) }}</td>
                  <td class="px-3 py-1.5 text-right">{{ fmt(g.subtotal.M_R) }}</td>
                </tr>
              </template>
              <tr class="border-t-2 border-slate-400 font-bold bg-slate-50">
                <td></td><td class="px-3 py-2 font-sans">Total sin mayorar</td>
                <td class="px-3 py-2 text-right">{{ fmt(trace.loads.total.Fx) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(trace.loads.total.Fy) }}</td>
                <td></td><td></td>
                <td class="px-3 py-2 text-right">{{ fmt(trace.loads.total.M_V) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(trace.loads.total.M_R) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 2. COMBINACIONES -->
      <section class="space-y-3">
        <div>
          <h2 class="text-lg font-bold">2. Factores de carga por estado límite</h2>
          <p class="text-xs text-slate-500">CCP-14 Tabla 3.4.1-1. Cuando hay dos valores (máx / mín) el motor evalúa todas las permutaciones y cada verificación toma la más desfavorable.</p>
        </div>
        <div class="overflow-x-auto bg-white border border-slate-200 rounded-lg">
          <table class="w-full text-xs">
            <thead class="bg-slate-100 text-slate-500 text-[10px]">
              <tr>
                <th class="text-left px-3 py-2">Carga</th>
                <th v-for="s in trace.limit_states" :key="s.name" class="text-center px-3 py-2">{{ s.label }}</th>
              </tr>
            </thead>
            <tbody class="font-mono tabular-nums">
              <tr v-for="row in factorMatrix" :key="row.type" class="border-t border-slate-100">
                <td class="px-3 py-1.5 font-sans">{{ row.label }}</td>
                <td v-for="(c, i) in row.cells" :key="i" class="px-3 py-1.5 text-center">{{ c }}</td>
              </tr>
              <tr class="border-t border-slate-200 text-slate-500">
                <td class="px-3 py-1.5 font-sans italic">Permutaciones evaluadas</td>
                <td v-for="s in trace.limit_states" :key="s.name" class="px-3 py-1.5 text-center">{{ s.permutations }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 3. ESTABILIDAD -->
      <section class="space-y-4">
        <div>
          <h2 class="text-lg font-bold">3. Estabilidad externa</h2>
          <p class="text-xs text-slate-500">Para cada verificación se muestra la combinación que gobierna, sus cargas mayoradas y el cálculo paso a paso.</p>
        </div>

        <div class="flex flex-wrap gap-2" role="tablist">
          <button v-for="s in states" :key="s.name" role="tab" :aria-selected="s.name === currentState?.name"
                  @click="activeState = s.name"
                  :class="s.name === currentState?.name ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-100'"
                  class="text-xs font-semibold px-3 py-1.5 rounded-full border focus:outline-none focus:ring-2 focus:ring-blue-500">
            {{ s.label }}
            <span v-if="s.checks.some(c => c.result.ok === false)" class="ml-1 inline-block w-2 h-2 rounded-full bg-red-500 align-middle" title="Tiene verificaciones que no cumplen"></span>
          </button>
        </div>

        <p v-if="currentState?.note" class="text-xs text-slate-500 italic">{{ currentState.note }}</p>

        <article v-for="check in currentState?.checks || []" :key="currentState.name + check.kind"
                 class="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <header class="px-4 py-3 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 class="text-sm font-bold">{{ check.label }}</h3>
              <p class="text-[11px] text-slate-500">{{ check.criterion }}</p>
            </div>
            <div class="flex items-center gap-3">
              <span v-if="check.result.ratio !== null" class="text-xs font-mono tabular-nums text-slate-600">
                {{ check.result.demand_label }} / {{ check.result.capacity_label }} = {{ fmt(check.result.ratio, 3) }}
              </span>
              <span :class="statusOf(check).cls" class="text-[11px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full">{{ statusOf(check).text }}</span>
            </div>
          </header>

          <div class="px-4 py-3 space-y-3">
            <div class="flex flex-wrap items-center gap-1.5 text-[11px]">
              <span class="text-slate-500">Combinación gobernante:</span>
              <span v-for="f in check.combination.factors" :key="f.type" class="font-mono bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded">
                γ<sub>{{ f.type }}</sub> = {{ fmt(f.gamma) }}
              </span>
              <button @click="toggleTable(currentState.name + check.kind)" class="ml-auto text-blue-600 font-semibold hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
                {{ openTables[currentState.name + check.kind] ? 'Ocultar' : 'Ver' }} cargas mayoradas
              </button>
            </div>

            <div v-if="openTables[currentState.name + check.kind]" class="space-y-2">
              <div class="overflow-x-auto border border-slate-200 rounded-md">
                <table class="w-full text-[11px]">
                  <thead class="bg-slate-50 text-slate-500 text-[10px]">
                    <tr>
                      <th class="text-left px-2 py-1.5">N°</th><th class="text-left px-2 py-1.5">Carga</th>
                      <th class="text-right px-2 py-1.5">γ</th>
                      <th class="text-right px-2 py-1.5">γ·Fx</th><th class="text-right px-2 py-1.5">γ·Fy</th>
                      <th class="text-right px-2 py-1.5">γ·M<sub>V</sub></th><th class="text-right px-2 py-1.5">γ·M<sub>R</sub></th>
                    </tr>
                  </thead>
                  <tbody class="font-mono tabular-nums">
                    <tr v-for="r in check.combination.rows" :key="r.id" class="border-t border-slate-100">
                      <td class="px-2 py-1 text-slate-400">{{ r.id }}</td>
                      <td class="px-2 py-1 font-sans">{{ r.name }}</td>
                      <td class="px-2 py-1 text-right">{{ fmt(r.gamma) }}</td>
                      <td class="px-2 py-1 text-right">{{ fmt(r.Fx) }}</td>
                      <td class="px-2 py-1 text-right">{{ fmt(r.Fy) }}</td>
                      <td class="px-2 py-1 text-right">{{ fmt(r.M_V) }}</td>
                      <td class="px-2 py-1 text-right">{{ fmt(r.M_R) }}</td>
                    </tr>
                    <tr class="border-t-2 border-slate-300 font-bold bg-slate-50">
                      <td></td><td class="px-2 py-1.5 font-sans">Σ</td><td></td>
                      <td class="px-2 py-1.5 text-right">{{ fmt(check.combination.sums.Fx) }}</td>
                      <td class="px-2 py-1.5 text-right">{{ fmt(check.combination.sums.Fy) }}</td>
                      <td class="px-2 py-1.5 text-right">{{ fmt(check.combination.sums.M_V) }}</td>
                      <td class="px-2 py-1.5 text-right">{{ fmt(check.combination.sums.M_R) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p class="text-[11px]" :class="check.combination.cross_check.ok ? 'text-emerald-700' : 'text-red-700'">
                {{ check.combination.cross_check.ok ? '✓' : '✗' }}
                Chequeo cruzado: ΣH = {{ fmt(check.combination.cross_check.table.sum_H) }}, ΣV = {{ fmt(check.combination.cross_check.table.sum_V) }}
                y ΣM = ΣM<sub>V</sub> − ΣM<sub>R</sub> = {{ fmt(check.combination.cross_check.table.sum_M) }}
                {{ check.combination.cross_check.ok ? 'coinciden con el motor de cálculo.' : 'NO coinciden con el motor de cálculo.' }}
              </p>
            </div>

            <ol class="space-y-2">
              <li v-for="(s, i) in check.steps" :key="i" class="border-l-2 border-blue-200 pl-3">
                <p class="text-[11px] font-semibold text-slate-600">{{ s.label }}</p>
                <MathBlock :tex="stepLatex(s)" :text="s.text" />
                <p v-if="s.clause" class="text-[10px] text-slate-400">{{ s.clause }}</p>
              </li>
            </ol>

            <p v-if="check.kind === 'contact'" class="text-[11px] text-slate-500">
              q<sub>punta</sub> = {{ fmt(check.result.q_toe) }} kPa · q<sub>talón</sub> = {{ fmt(check.result.q_heel) }} kPa. {{ check.note }}
            </p>
            <p v-else-if="check.result.ratio !== null" class="text-xs font-semibold" :class="check.result.ok ? 'text-emerald-700' : 'text-red-700'">
              {{ check.result.demand_label }} = {{ fmt(check.result.demand) }} {{ check.result.unit }}
              {{ check.result.ok ? '≤' : '>' }}
              {{ check.result.capacity_label }} = {{ fmt(check.result.capacity) }} {{ check.result.unit }}
              → {{ check.result.ok ? 'Cumple' : 'No cumple' }}
            </p>
          </div>
        </article>
      </section>
    </div>
  </div>
</template>
