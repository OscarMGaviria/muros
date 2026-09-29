<script setup>
// Datos de entrada organizados por secciones con nombre, en el orden en que se diseña un muro.
import { computed, ref } from 'vue'
import { useWallStore } from '../stores/wallStore'
import NumField from './ui/NumField.vue'

const store = useWallStore()
const p = store.params
const res = computed(() => store.results?.results)

const FIELDS = {
  geometry: ['H', 'B', 'D_z', 'L_toe', 'stem_bot', 'stem_top', 'toe_cover', 'D_d', 'W_d'],
  materials: ['fc', 'fy', 'gamma_c', 'cover_cm'],
  soils: ['gamma_fill', 'gamma_sat_fill', 'phi_fill', 'delta_fill', 'beta_fill', 'gamma_found', 'phi_found', 'c_found', 'qn_nominal'],
  loads: [],
  seismic: ['kh', 'pga', 'fpga'],
  water: ['gw_elevation'],
  criteria: []
}

const sections = [
  { id: 'geometry', title: 'Geometría' },
  { id: 'materials', title: 'Materiales' },
  { id: 'soils', title: 'Suelos' },
  { id: 'loads', title: 'Sobrecarga vehicular' },
  { id: 'seismic', title: 'Sismo' },
  { id: 'water', title: 'Nivel freático' },
  { id: 'criteria', title: 'Criterios de diseño' }
]

const open = ref({ geometry: true })
const toggle = (id) => { open.value = { ...open.value, [id]: !open.value[id] } }

const errorCount = (id) => FIELDS[id].filter(k => store.fieldErrors[k]).length
function badge (id) {
  const n = errorCount(id)
  if (n) return { text: n === 1 ? '1 error' : `${n} errores`, cls: 'bg-red-50 text-red-700' }
  if (id === 'seismic' && p.kh_mode === 'DIRECT' && !(p.kh > 0)) return { text: 'Sin sismo', cls: 'bg-slate-100 text-slate-500' }
  if (id === 'water' && !p.gw_enabled) return { text: 'Drenado', cls: 'bg-slate-100 text-slate-500' }
  return null
}

const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v)) ? '—' : Number(v).toFixed(d)
const recalc = () => store.calculate()
</script>

<template>
  <aside class="w-[300px] shrink-0 bg-white border-r border-slate-200 flex flex-col min-h-0" aria-label="Datos de entrada">
    <header class="px-4 py-3 border-b border-slate-200">
      <h2 class="text-sm font-bold text-slate-800">Datos de entrada</h2>
      <p class="text-xs text-slate-500">Por metro de muro. Cada cambio recalcula el diseño.</p>
    </header>

    <div class="flex-1 overflow-y-auto">
      <section v-for="s in sections" :key="s.id" class="border-b border-slate-200">
        <button type="button" @click="toggle(s.id)" :aria-expanded="!!open[s.id]"
                class="w-full flex items-center gap-2 px-4 py-2.5 text-left text-sm font-semibold text-slate-800 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
          <svg class="w-3.5 h-3.5 text-slate-400 transition-transform" :class="open[s.id] ? 'rotate-90' : ''" viewBox="0 0 20 20" fill="currentColor"><path d="M7 5l6 5-6 5V5z"/></svg>
          {{ s.title }}
          <span v-if="badge(s.id)" class="ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full" :class="badge(s.id).cls">{{ badge(s.id).text }}</span>
        </button>

        <div v-if="open[s.id]" class="px-4 pb-4 pt-1 space-y-3">
          <!-- GEOMETRÍA -->
          <template v-if="s.id === 'geometry'">
            <NumField field="H" label="Altura del fuste (H)" unit="m" step="0.1" />
            <NumField field="B" label="Ancho de la zapata (B)" unit="m" step="0.1" />
            <NumField field="D_z" label="Espesor de la zapata" unit="m" step="0.05" />
            <NumField field="L_toe" label="Longitud de la punta" unit="m" step="0.05" />
            <NumField field="stem_bot" label="Espesor del fuste en la base" unit="m" step="0.05" />
            <NumField field="stem_top" label="Espesor del fuste en la corona" unit="m" step="0.05" hint="Cara frontal vertical; la cara trasera se inclina." />
            <div class="flex items-center justify-between rounded-md px-3 py-2 text-xs"
                 :class="store.heelLength > 0 ? 'bg-slate-50 text-slate-600' : 'bg-red-50 text-red-700'">
              <span>Talón (B − punta − fuste)</span>
              <span class="font-mono font-semibold tabular-nums">{{ fmt(store.heelLength) }} m</span>
            </div>
            <NumField field="toe_cover" label="Relleno sobre la punta" unit="m" step="0.1" hint="Se usa en el empotramiento para la capacidad portante." />
            <NumField field="D_d" label="Profundidad del dentellón" unit="m" step="0.05" hint="0 si no lleva dentellón. Se ubica bajo el fuste." />
            <NumField v-if="p.D_d > 0" field="W_d" label="Ancho del dentellón" unit="m" step="0.05" />
          </template>

          <!-- MATERIALES -->
          <template v-else-if="s.id === 'materials'">
            <NumField field="fc" label="Resistencia del concreto f'c" unit="MPa" step="1" />
            <NumField field="fy" label="Fluencia del acero fy" unit="MPa" step="10" />
            <NumField field="gamma_c" label="Peso unitario del concreto" unit="kN/m³" step="0.5" />
            <NumField field="cover_cm" label="Recubrimiento del refuerzo" unit="cm" step="0.5" norm="CCP-14 5.12.3" />
          </template>

          <!-- SUELOS -->
          <template v-else-if="s.id === 'soils'">
            <p class="text-xs font-semibold text-slate-700">Relleno</p>
            <NumField field="gamma_fill" label="Peso unitario (γ)" unit="kN/m³" step="0.1" />
            <NumField field="gamma_sat_fill" label="Peso saturado (γsat)" unit="kN/m³" step="0.1" hint="Solo se usa bajo el nivel freático." />
            <NumField field="phi_fill" label="Ángulo de fricción (φ)" unit="°" step="1" />
            <NumField field="delta_fill" label="Fricción muro-suelo (δ)" unit="°" step="1" norm="típico 2/3 φ" />
            <NumField field="beta_fill" label="Inclinación del relleno (β)" unit="°" step="1" />
            <div v-if="res?.earth_pressure" class="grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-md bg-slate-50 px-3 py-2"><span class="text-slate-500">Ka (Coulomb)</span><div class="font-mono font-semibold">{{ fmt(res.earth_pressure.ka, 3) }}</div></div>
              <div v-if="res.earth_pressure.kae" class="rounded-md bg-slate-50 px-3 py-2"><span class="text-slate-500">KAE (M-O)</span><div class="font-mono font-semibold">{{ fmt(res.earth_pressure.kae, 3) }}</div></div>
            </div>
            <p class="text-xs font-semibold text-slate-700 pt-2">Suelo de fundación</p>
            <NumField field="gamma_found" label="Peso unitario (γ)" unit="kN/m³" step="0.1" />
            <NumField field="phi_found" label="Ángulo de fricción (φ)" unit="°" step="1" />
            <NumField field="c_found" label="Cohesión (c)" unit="kPa" step="1" />
            <NumField field="qn_nominal" label="Resistencia nominal qn" unit="kPa" step="10" optional placeholder="Calcular"
                      norm="estudio geotécnico" hint="Vacío: el motor la calcula con la ecuación general de capacidad portante." />
          </template>

          <!-- SOBRECARGA -->
          <template v-else-if="s.id === 'loads'">
            <div class="space-y-1">
              <label for="f-traffic" class="text-xs font-medium text-slate-600">Orientación respecto al tráfico</label>
              <select id="f-traffic" v-model="p.traffic_orientation" @change="recalc" class="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm">
                <option value="PARALLEL">Muro paralelo al tráfico</option>
                <option value="PERPENDICULAR">Estribo perpendicular al tráfico</option>
              </select>
            </div>
            <NumField field="traffic_distance" label="Distancia del tráfico al respaldo" unit="m" step="0.1" norm="Tabla 3.11.6.4-2" />
            <div v-if="res?.traffic_surcharge" class="grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-md bg-slate-50 px-3 py-2"><span class="text-slate-500">heq</span><div class="font-mono font-semibold">{{ fmt(res.traffic_surcharge.heq_m) }} m</div></div>
              <div class="rounded-md bg-slate-50 px-3 py-2"><span class="text-slate-500">qs = heq·γ</span><div class="font-mono font-semibold">{{ fmt(res.traffic_surcharge.qs_kPa, 1) }} kPa</div></div>
            </div>
          </template>

          <!-- SISMO -->
          <template v-else-if="s.id === 'seismic'">
            <div class="space-y-1">
              <label for="f-khmode" class="text-xs font-medium text-slate-600">Coeficiente sísmico kh</label>
              <select id="f-khmode" v-model="p.kh_mode" @change="recalc" class="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm">
                <option value="DIRECT">Dato directo</option>
                <option value="PGA">Calcular desde PGA (kh0 = Fpga·PGA)</option>
              </select>
            </div>
            <NumField v-if="p.kh_mode === 'DIRECT'" field="kh" label="kh" unit="g" step="0.01" min="0" hint="0 = sin sismo." />
            <template v-else>
              <NumField field="pga" label="Aceleración pico del terreno (PGA)" unit="g" step="0.01" min="0" />
              <div class="space-y-1">
                <label for="f-site" class="text-xs font-medium text-slate-600">Tipo de perfil de suelo</label>
                <select id="f-site" v-model="p.site_class" @change="recalc" class="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm">
                  <option v-for="c in ['A', 'B', 'C', 'D', 'E', 'F']" :key="c" :value="c">Perfil {{ c }}</option>
                </select>
              </div>
              <NumField field="fpga" label="Fpga" step="0.05" optional placeholder="Tabla 3.10.3.2-1" hint="Vacío: se toma de la tabla según PGA y perfil." />
              <label class="flex items-start gap-2 text-xs text-slate-600 cursor-pointer">
                <input type="checkbox" v-model="p.allow_displacement" @change="recalc" class="mt-0.5 accent-blue-600" />
                <span>El muro puede desplazarse 25–50 mm (kh = 0,5·kh0, CCP-14 11.6.5.2.2)</span>
              </label>
              <div v-if="res?.seismic?.kh0 != null" class="grid grid-cols-3 gap-2 text-xs">
                <div class="rounded-md bg-slate-50 px-2 py-2"><span class="text-slate-500">Fpga</span><div class="font-mono font-semibold">{{ fmt(res.seismic.fpga) }}</div></div>
                <div class="rounded-md bg-slate-50 px-2 py-2"><span class="text-slate-500">kh0</span><div class="font-mono font-semibold">{{ fmt(res.seismic.kh0, 3) }}</div></div>
                <div class="rounded-md bg-slate-50 px-2 py-2"><span class="text-slate-500">kh</span><div class="font-mono font-semibold">{{ fmt(res.seismic.kh, 3) }}</div></div>
              </div>
            </template>
            <div class="space-y-1">
              <label for="f-pae" class="text-xs font-medium text-slate-600">Altura de la resultante de P_AE</label>
              <select id="f-pae" v-model.number="p.pae_height_ratio" @change="recalc" class="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm">
                <option :value="1 / 3">H/3 (CCP-14 11.6.5.3)</option>
                <option :value="0.4">0,4H</option>
                <option :value="0.5">0,5H</option>
              </select>
            </div>
            <div class="space-y-1">
              <label for="f-geq" class="text-xs font-medium text-slate-600">Sobrecarga vehicular durante el sismo (γEQ)</label>
              <select id="f-geq" v-model.number="p.gamma_eq" @change="recalc" class="w-full rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm">
                <option :value="0">0,0 (sin tráfico)</option>
                <option :value="0.5">0,5</option>
                <option :value="1">1,0</option>
              </select>
            </div>
          </template>

          <!-- AGUA -->
          <template v-else-if="s.id === 'water'">
            <label class="flex items-start gap-2 text-xs text-slate-700 cursor-pointer">
              <input type="checkbox" v-model="p.gw_enabled" @change="recalc" class="mt-0.5 accent-blue-600" />
              <span class="font-medium">Considerar nivel freático detrás del muro</span>
            </label>
            <template v-if="p.gw_enabled">
              <NumField field="gw_elevation" label="Altura desde la base de la zapata" unit="m" step="0.1" min="0" />
              <label class="flex items-start gap-2 text-xs text-slate-600 cursor-pointer">
                <input type="checkbox" v-model="p.gw_drained" @change="recalc" class="mt-0.5 accent-blue-600" />
                <span>Relleno con drenaje (sin presión de agua)</span>
              </label>
              <label class="flex items-start gap-2 text-xs text-slate-600 cursor-pointer">
                <input type="checkbox" v-model="p.gw_free_draining" @change="recalc" class="mt-0.5 accent-blue-600" />
                <span>Relleno de drenaje libre (triturado): en sismo usa peso sumergido y presión hidrodinámica</span>
              </label>
              <div v-if="res?.water?.hw_m > 0" class="grid grid-cols-2 gap-2 text-xs">
                <div class="rounded-md bg-slate-50 px-3 py-2"><span class="text-slate-500">Empuje hidrostático</span><div class="font-mono font-semibold">{{ fmt(res.water.hydrostatic_kN_m, 1) }} kN/m</div></div>
                <div class="rounded-md bg-slate-50 px-3 py-2"><span class="text-slate-500">Subpresión en el talón</span><div class="font-mono font-semibold">{{ fmt(res.water.uplift_at_heel_kPa, 1) }} kPa</div></div>
              </div>
            </template>
          </template>

          <!-- CRITERIOS -->
          <template v-else-if="s.id === 'criteria'">
            <label class="flex items-start gap-2 text-xs text-slate-600 cursor-pointer">
              <input type="checkbox" v-model="p.ignore_heel_reaction" @change="recalc" class="mt-0.5 accent-blue-600" />
              <span><span class="font-medium text-slate-700">Diseñar el talón sin la reacción del suelo</span><br>Conservador, criterio del CDOT. Desmarcado se descuenta la presión de contacto.</span>
            </label>
          </template>
        </div>
      </section>
    </div>
  </aside>
</template>
