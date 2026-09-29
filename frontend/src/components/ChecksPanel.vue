<script setup>
// Verificaciones: veredicto global, la peor relación demanda/capacidad de cada
// verificación (con el estado límite que gobierna y el cambio respecto al cálculo
// anterior), sugerencias cuando algo no cumple y el acero de diseño por sección.
import { computed } from 'vue'
import { useWallStore, THRESHOLDS } from '../stores/wallStore'

const store = useWallStore()
const summary = computed(() => store.results?.results?.summary || null)
const prev = computed(() => {
  const m = {}
  ;(store.prevSummary?.checks || []).forEach(c => { m[c.id] = c })
  return m
})

// Nombres cortos para el panel; la memoria muestra el nombre completo
const SHORT = {
  'Strength I': 'Resistencia I', 'Strength IV': 'Resistencia IV', 'Service I': 'Servicio I',
  'Extreme Event I-a': 'Sismo I-a (100 % PAE + 50 % PIR)', 'Extreme Event I-b': 'Sismo I-b (50 % PAE + 100 % PIR)',
  envelope: 'Envolvente de diseño'
}
const stateLabel = (c) => SHORT[c.state] || c.state_label

const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v)) ? '—' : Number(v).toFixed(d)

function level (c) {
  if (c.ok === false) return 'bad'
  if ((c.ratio ?? 0) > THRESHOLDS.nearLimit) return 'warn'
  return 'ok'
}
const LEVEL = {
  ok: { text: 'Cumple', color: 'text-emerald-700', bar: 'bg-emerald-600', row: 'border-transparent' },
  warn: { text: 'Cumple, cerca del límite', color: 'text-amber-700', bar: 'bg-amber-500', row: 'border-amber-500' },
  bad: { text: 'No cumple', color: 'text-red-700', bar: 'bg-red-600', row: 'border-red-600' }
}

function delta (c) {
  const p = prev.value[c.id]
  if (!p || p.ratio == null || c.ratio == null || Math.abs(p.ratio - c.ratio) < 0.0005) return null
  return { up: c.ratio > p.ratio, before: p.ratio }
}

const groups = computed(() => {
  const out = {}
  ;(summary.value?.checks || []).forEach(c => { (out[c.group] ||= []).push(c) })
  return out
})

const SUGGEST = {
  eccentricity: 'Alargue la punta o el talón, o aumente B.',
  sliding: 'Agregue o profundice el dentellón, aumente B o alargue el talón para sumar peso de suelo.',
  bearing: 'Aumente B para reducir la presión, o revise qn con el estudio geotécnico.',
  shear_stem: 'Aumente el espesor del fuste en la base.',
  shear_toe: 'Aumente el espesor de la zapata.',
  shear_heel: 'Aumente el espesor de la zapata.',
  shear_key: 'Aumente el ancho del dentellón.'
}
const failing = computed(() => (summary.value?.checks || []).filter(c => c.ok === false))

function open (c) {
  if (c.group === 'Estabilidad') store.openMemoria(c.state, c.id)
}
</script>

<template>
  <aside class="w-[340px] shrink-0 bg-white border-l border-slate-200 flex flex-col min-h-0" aria-label="Verificaciones">
    <header class="px-4 py-3 border-b border-slate-200">
      <h2 class="text-sm font-bold text-slate-800">Verificaciones</h2>
      <p class="text-xs text-slate-500">Relación demanda / capacidad (D/C) más desfavorable entre estados límite.</p>
    </header>

    <div class="flex-1 overflow-y-auto">
      <div v-if="!summary" class="p-6 text-sm text-slate-400 text-center">
        {{ store.isLoading ? 'Calculando…' : 'Sin resultados. Revise los datos de entrada.' }}
      </div>

      <template v-else>
        <div v-for="(items, group) in groups" :key="group">
          <p class="px-4 pt-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">{{ group }}</p>
          <component :is="c.group === 'Estabilidad' ? 'button' : 'div'" v-for="c in items" :key="c.id" type="button"
                     @click="open(c)"
                     :class="[LEVEL[level(c)].row, c.group === 'Estabilidad' ? 'hover:bg-slate-50 cursor-pointer' : '']"
                     class="w-full text-left block px-4 py-2.5 border-l-[3px] focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                     :title="c.group === 'Estabilidad' ? 'Ver el cálculo en la memoria' : ''">
            <div class="flex items-baseline justify-between gap-2">
              <span class="text-sm font-semibold text-slate-800">{{ c.label }}</span>
              <span class="font-mono text-sm font-semibold tabular-nums" :class="LEVEL[level(c)].color">{{ fmt(c.ratio, 3) }}</span>
            </div>
            <div class="relative mt-1.5 h-1.5 rounded bg-slate-100" aria-hidden="true">
              <div class="absolute inset-y-0 left-0 rounded" :class="LEVEL[level(c)].bar" :style="{ width: Math.min((c.ratio || 0) / 1.25, 1) * 100 + '%' }"></div>
              <div class="absolute -top-0.5 -bottom-0.5 w-0.5 bg-slate-500" style="left: 80%" title="D/C = 1,0"></div>
            </div>
            <div class="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-slate-500">
              <span :class="LEVEL[level(c)].color" class="font-medium">{{ LEVEL[level(c)].text }}</span>
              <span>· {{ stateLabel(c) }}</span>
              <span v-if="delta(c)" class="font-mono" :class="delta(c).up ? 'text-red-600' : 'text-emerald-700'">
                {{ delta(c).up ? '▲' : '▼' }} antes {{ fmt(delta(c).before, 3) }}
              </span>
            </div>
            <div class="mt-0.5 text-[11px] font-mono text-slate-400">{{ c.demand_label }} = {{ fmt(c.demand) }} · {{ c.capacity_label }} = {{ fmt(c.capacity) }} {{ c.unit }}</div>
          </component>
        </div>

        <div v-if="failing.length" class="m-4 rounded-md bg-red-50 p-3 text-xs text-red-900 space-y-1.5">
          <p class="font-semibold">Cómo corregir</p>
          <p v-for="c in failing" :key="c.id"><span class="font-semibold">{{ c.label }}:</span> {{ SUGGEST[c.id] }}</p>
        </div>

        <div class="px-4 py-3 space-y-2">
          <h3 class="text-sm font-bold text-slate-800">Acero de diseño</h3>
          <div class="overflow-x-auto border border-slate-200 rounded-md">
            <table class="w-full text-xs">
              <thead class="bg-slate-50 text-slate-500">
                <tr><th class="text-left px-2 py-1.5 font-medium">Sección</th><th class="text-right px-2 py-1.5 font-medium">Requerido</th><th class="text-right px-2 py-1.5 font-medium">Mínimo</th><th class="text-right px-2 py-1.5 font-medium">Diseño</th></tr>
              </thead>
              <tbody class="font-mono tabular-nums">
                <tr v-for="(s, k) in summary.sections" :key="k" class="border-t border-slate-100">
                  <td class="px-2 py-1.5 font-sans">{{ s.label }}</td>
                  <td class="px-2 py-1.5 text-right">{{ fmt(s.A_s_required) }}</td>
                  <td class="px-2 py-1.5 text-right">{{ fmt(s.A_s_min) }}</td>
                  <td class="px-2 py-1.5 text-right font-semibold text-slate-900">{{ fmt(s.A_s_final) }}<span v-if="s.governed_by_minimum" class="ml-1 font-sans text-[10px] font-normal text-slate-400" title="Gobierna el refuerzo mínimo">mín</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <p class="text-[11px] leading-snug text-slate-400">cm²/m. Diseño = mayor entre el requerido por flexión y el mínimo (CCP-14 5.7.3.3.2 y 5.10.8).</p>
        </div>
      </template>
    </div>
  </aside>
</template>
