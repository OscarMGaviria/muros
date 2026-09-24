<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import { useWallStore } from '../stores/wallStore'

const store = useWallStore()
const activeTab = ref('geometry')

const showBearingModal = ref(false)

const showKaModal = ref(false)

const showDcModal = ref(false)
const showEvModal = ref(false)
const showEhModal = ref(false)
const showLsModal = ref(false)

const dcLoads = computed(() => store.results?.results?.loads?.filter(ld => ld.type === 'DC') || [])
const evLoads = computed(() => store.results?.results?.loads?.filter(ld => ld.type === 'EV') || [])
const ehLoad = computed(() => store.results?.results?.loads?.find(ld => ld.type === 'EH'))
const lsLoad = computed(() => store.results?.results?.loads?.find(ld => ld.type === 'LS'))


const replacedFormula = computed(() => {
  const p = store.params
  const th = store.theta
  return `$$ K_a = \\frac{\\sin^2(${th}^\\circ + ${p.phi_fill}^\\circ)}{\\sin^2${th}^\\circ \\sin(${th}^\\circ - ${p.delta_fill}^\\circ) \\left[ 1 + \\sqrt{\\frac{\\sin(${p.phi_fill}^\\circ + ${p.delta_fill}^\\circ) \\sin(${p.phi_fill}^\\circ - ${p.beta_fill}^\\circ)}{\\sin(${th}^\\circ - ${p.delta_fill}^\\circ) \\sin(${th}^\\circ + ${p.beta_fill}^\\circ)}} \\right]^2 } $$`
})


const ehFormulaReplaced = computed(() => {
  const p = store.params
  const ka = store.results?.results?.earth_pressure?.ka?.toFixed(3) || '0.000'
  const Fx = ehLoad.value?.Fx?.toFixed(2) || '0.00'
  const Fy = ehLoad.value?.Fy?.toFixed(2) || '0.00'
  const h_total = p.H + p.D_z
  // Calculate total EH magnitude
  const total = (0.5 * p.gamma_fill * Math.pow(h_total, 2) * (store.results?.results?.earth_pressure?.ka || 0)).toFixed(2)
  return `$$ EH = \\frac{1}{2} \\gamma_s H_{total}^2 K_a $$
$$ EH = \\frac{1}{2} (${p.gamma_fill}) (${h_total.toFixed(2)})^2 (${ka}) = ${total} \\text{ kN/m} $$
$$ EH_x = EH \\cos(\\delta) = ${total} \\cos(${p.delta_fill}^\\circ) = ${Fx} \\text{ kN/m} $$
$$ EH_y = EH \\sin(\\delta) = ${total} \\sin(${p.delta_fill}^\\circ) = ${Fy} \\text{ kN/m} $$`
})


const lsFormulaReplaced = computed(() => {
  const p = store.params
  const ka = store.results?.results?.earth_pressure?.ka?.toFixed(3) || '0.000'
  const Fx = lsLoad.value?.Fx?.toFixed(2) || '0.00'
  const heq = store.results?.results?.traffic_surcharge?.heq_m?.toFixed(2) || '0.00'
  const qs = store.results?.results?.traffic_surcharge?.qs_kPa?.toFixed(2) || '0.00'
  const h_total = p.H + p.D_z
  return `$$ q_s = h_{eq} \\cdot \\gamma_{relleno} $$
$$ q_s = (${heq}) (${p.gamma_fill}) = ${qs} \\text{ kPa} $$
$$ LS_x = q_s H_{total} K_a $$
$$ LS_x = (${qs}) (${h_total.toFixed(2)}) (${ka}) = ${Fx} \\text{ kN/m} $$
$$ LS_y = 0 \\text{ kN/m (empuje puramente horizontal)} $$`
})


watch([showEhModal, showLsModal, ehFormulaReplaced, lsFormulaReplaced], async ([newEh, newLs]) => {
  if (newEh || newLs) {
    await nextTick()
    if (window.MathJax) {
      setTimeout(() => {
        window.MathJax.typesetPromise().catch((err) => console.log('MathJax error: ', err))
      }, 50)
    }
  }
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
})


const calcParams = ref({
  c: 0,
  gamma: store.params.gamma_found,
  phi: store.params.phi_found,
  B: store.params.B,
  Df: 1.0,
  FS: 3.0
})

watch(showBearingModal, (newVal) => {
  if (newVal) {
    calcParams.value.gamma = store.params.gamma_found
    calcParams.value.phi = store.params.phi_found
    calcParams.value.B = store.params.B
  }
})

const calcResults = computed(() => {
  const phi_rad = calcParams.value.phi * Math.PI / 180
  const c = calcParams.value.c
  const gamma = calcParams.value.gamma
  const B = calcParams.value.B
  const Df = calcParams.value.Df
  
  let Nq = 1.0
  let Nc = 5.14
  let Ngamma = 0.0

  if (calcParams.value.phi > 0) {
    Nq = Math.exp(Math.PI * Math.tan(phi_rad)) * Math.pow(Math.tan(Math.PI/4 + phi_rad/2), 2)
    Nc = (Nq - 1) / Math.tan(phi_rad)
    Ngamma = 2 * (Nq + 1) * Math.tan(phi_rad)
  }

  const q_ult = c * Nc + gamma * Df * Nq + 0.5 * gamma * B * Ngamma
  const q_adm = q_ult / calcParams.value.FS

  return { Nq, Nc, Ngamma, q_ult, q_adm }
})

const applyBearingCapacity = () => {
  store.params.q_allow = parseFloat(calcResults.value.q_adm.toFixed(2))
  showBearingModal.value = false
  store.calculate()
}
</script>

<template>
  <aside class="w-16 bg-white flex flex-col items-center py-5 gap-5 z-20 shrink-0 border-r border-slate-200 shadow-sm ">
    <button @click="activeTab = 'geometry'" :class="activeTab === 'geometry' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Geometría"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg></button>
    <button @click="activeTab = 'materials'" :class="activeTab === 'materials' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Materiales"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg></button>
    <button @click="activeTab = 'soils'" :class="activeTab === 'soils' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Suelos"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2 10h20M5 14h14M8 18h8M11 22h2 M12 2v8"></path></svg></button>
    <button @click="activeTab = 'loads'" :class="activeTab === 'loads' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Cargas"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"></path></svg></button>
    <button @click="activeTab = 'results'" :class="activeTab === 'results' ? 'bg-blue-600 text-white' : 'text-slate-400'" class="w-10 h-10 rounded-xl flex items-center justify-center" title="Resultados"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg></button>

  </aside>
  <aside class="w-[300px] bg-white flex flex-col z-10 shrink-0 shadow-lg border-r border-slate-200">
    <div class="px-5 py-4 bg-slate-50 border-b border-slate-200">
      <h2 class="text-sm font-extrabold text-slate-800 uppercase tracking-wider">
        {{ activeTab === 'geometry' ? 'Geometría' : activeTab === 'materials' ? 'Materiales' : activeTab === 'soils' ? 'Suelos' : activeTab === 'loads' ? 'Cargas y Sismo' : 'Resultados' }}
      </h2>
      <p class="text-[11px] text-slate-500 mt-1">Configure los parámetros</p>
    </div>
    
    <div class="p-5 space-y-4 overflow-y-auto flex-1 custom-scrollbar">
      <!-- TAB: GEOMETRY -->
      <template v-if="activeTab === 'geometry'">
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Altura Fuste (H)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.H" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Base Zapata (B)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.B" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Espesor Zapata (Dz)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.D_z" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Longitud Punta (L_toe)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.L_toe" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Espesor Fuste Inferior</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.stem_bot" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Espesor Fuste Superior</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.stem_top" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Profundidad Llave</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.D_d" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Ancho Llave</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.W_d" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
      </template>

      <!-- TAB: MATERIALS -->
      <template v-if="activeTab === 'materials'">
        <div class="bg-blue-50 p-3 rounded-md mb-2 border border-blue-100">
          <h3 class="text-xs font-bold text-blue-800 mb-2">Materiales Estructurales</h3>
          <div class="space-y-3">
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Concreto f'c</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.fc" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">MPa</span></div></div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Acero fy</label><div class="flex shadow-sm"><input type="number" step="10" v-model.number="store.params.fy" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">MPa</span></div></div>
          </div>
        </div>
      </template>

      <!-- TAB: SOILS -->
      <template v-if="activeTab === 'soils'">
        <div class="bg-orange-50 p-3 rounded-md mb-2 border border-orange-100">
          <h3 class="text-xs font-bold text-orange-900 mb-2">Suelo de Relleno</h3>
          <div class="space-y-3">
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.gamma_fill" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
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
            </div>
          </div>
        </div>

        <div class="bg-emerald-50 p-3 rounded-md border border-emerald-100">
          <h3 class="text-xs font-bold text-emerald-900 mb-2">Suelo de Fundación</h3>
          <div class="space-y-3">
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="store.params.gamma_found" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Áng. Fricción (ϕ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.phi_found" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
            <div class="space-y-1">
              <label class="text-[10px] font-bold text-slate-600 flex items-center">
                Cap. Portante (q_adm)
                <button @click="showBearingModal = true" class="ml-1 text-blue-600 hover:text-blue-800 outline-none" title="Calcular Capacidad Portante">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-3.5 h-3.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25v-.008Zm0 2.25h.008v.008H8.25v-.008Zm2.25-4.5h.008v.008H10.5v-.008Zm0 2.25h.008v.008H10.5v-.008Zm0 2.25h.008v.008H10.5v-.008Zm2.25-4.5h.008v.008H12.75v-.008Zm0 2.25h.008v.008H12.75v-.008Zm0 2.25h.008v.008H12.75v-.008Z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h3m-1.5-1.5v3" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3h10.5a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 17.25 21H6.75A2.25 2.25 0 0 1 4.5 18.75V5.25A2.25 2.25 0 0 1 6.75 3Z" />
                  </svg>
                </button>
              </label>
              <div class="flex shadow-sm"><input type="number" step="10" v-model.number="store.params.q_allow" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kPa</span></div>
            </div>
          </div>
        </div>
      </template>

      <!-- TAB: LOADS -->
      <template v-if="activeTab === 'loads'">
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Sobrecarga Visual (diagrama)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="store.params.q_surcharge" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">kPa</span></div><p class="text-[10px] text-slate-400 leading-tight">Solo controla el bloque de sobrecarga en el dibujo. El empuje LS de diseño se calcula automáticamente (ver abajo).</p></div>
        <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Coef. Sísmico (kh)</label><div class="flex shadow-sm"><input type="number" step="0.01" v-model.number="store.params.kh" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">g</span></div></div>

        <div class="bg-blue-50 p-3 rounded-md border border-blue-100 mt-2">
          <h3 class="text-xs font-bold text-blue-900 mb-2">Sobrecarga Vehicular (LS) — AASHTO Tabla 3.11.6.4</h3>
          <div class="space-y-3">
            <div class="space-y-1">
              <label class="text-[10px] font-bold text-slate-600">Orientación respecto al tráfico</label>
              <select v-model="store.params.traffic_orientation" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-md py-1 px-2 text-xs outline-none shadow-sm">
                <option value="PARALLEL">Paralelo al tráfico</option>
                <option value="PERPENDICULAR">Perpendicular al tráfico</option>
              </select>
            </div>
            <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Distancia al respaldo del muro</label><div class="flex shadow-sm"><input type="number" step="0.1" min="0" v-model.number="store.params.traffic_distance" @change="store.calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">m</span></div></div>
            <div v-if="store.results?.results?.traffic_surcharge" class="pt-2 border-t border-blue-200/50 mt-2 space-y-1.5">
              <div class="flex justify-between items-center">
                <span class="text-[10px] font-bold text-blue-800">Altura Equiv. (heq)</span>
                <span class="text-xs font-mono font-black text-blue-700">{{ store.results.results.traffic_surcharge.heq_m.toFixed(2) }} m</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-[10px] font-bold text-blue-800">qs = heq · γ_relleno</span>
                <span class="text-xs font-mono font-black text-blue-700">{{ store.results.results.traffic_surcharge.qs_kPa.toFixed(2) }} kPa</span>
              </div>
            </div>
          </div>
        </div>
      </template>
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
                <span class="font-bold font-mono" :class="(store.results.results.stability.sliding?.FS || 0) >= store.thresholds.slidingFS ? 'text-emerald-600' : 'text-red-600'">{{ (store.results.results.stability.sliding?.FS || 0).toFixed(2) }}</span>
              </div>
              <div class="flex justify-between border-b border-indigo-100 pb-1">
                <span class="text-slate-600">Excentricidad (e &lt; B/3)</span>
                <span class="font-bold font-mono" :class="(store.results.results.stability.eccentricity?.e || 0) <= (store.params.B / 3) ? 'text-emerald-600' : 'text-red-600'">{{ (store.results.results.stability.eccentricity?.e || 0).toFixed(3) }} m</span>
              </div>
              <div class="flex justify-between border-b border-indigo-100 pb-1">
                <span class="text-slate-600">FS Cap. Portante</span>
                <span class="font-bold font-mono" :class="(store.params.q_allow / (store.results.results.stability.bearing?.q_max || 1)) >= store.thresholds.bearingFS ? 'text-emerald-600' : 'text-red-600'">{{ (store.params.q_allow / (store.results.results.stability.bearing?.q_max || 1)).toFixed(2) }}</span>
              </div>
            </div>
          </div>
          
          <div class="bg-rose-50 p-3 rounded-md border border-rose-100">
            <h3 class="text-xs font-bold text-rose-900 mb-2">Esfuerzos en la Base</h3>
            <div class="space-y-2 text-xs">
              <div class="flex justify-between border-b border-rose-100 pb-1">
                <span class="text-slate-600">q_max (Punta)</span>
                <span class="font-bold font-mono text-slate-800">{{ (store.results.results.stability.bearing?.q_max || 0).toFixed(1) }} <span class="text-[10px] text-slate-500">kPa</span></span>
              </div>
              <div class="flex justify-between border-b border-rose-100 pb-1">
                <span class="text-slate-600">q_min (Talón)</span>
                <span class="font-bold font-mono text-slate-800">{{ (store.results.results.stability.bearing?.q_min || 0).toFixed(1) }} <span class="text-[10px] text-slate-500">kPa</span></span>
              </div>
              <div class="flex justify-between border-b border-rose-100 pb-1 pt-1">
                <span class="text-slate-600">Excentricidad (e)</span>
                <span class="font-bold font-mono text-slate-800">{{ (store.results.results.stability.eccentricity?.e || 0).toFixed(3) }} <span class="text-[10px] text-slate-500">m</span></span>
              </div>
            </div>
          </div>
          
          <div class="grid grid-cols-2 gap-2 pt-2">
            <button @click="showDcModal = true" class="bg-slate-50 hover:bg-slate-100 p-2 rounded-lg border border-slate-200 flex flex-col items-center justify-center transition-all shadow-sm hover:shadow">
              <span class="text-[10px] font-bold text-slate-500 uppercase">Muro</span>
              <span class="text-lg font-black text-slate-700">DC</span>
            </button>
            <button @click="showEvModal = true" class="bg-emerald-50 hover:bg-emerald-100 p-2 rounded-lg border border-emerald-200 flex flex-col items-center justify-center transition-all shadow-sm hover:shadow">
              <span class="text-[10px] font-bold text-emerald-600 uppercase">Suelo</span>
              <span class="text-lg font-black text-emerald-800">EV</span>
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
      </template>
    </div>
    
    <div class="p-4 border-t border-slate-200 bg-white">
      <div v-if="store.paramWarnings.length" class="mb-3 p-2.5 bg-amber-50 border border-amber-200 rounded-md space-y-1">
        <div v-for="(w, i) in store.paramWarnings" :key="i" class="text-[10px] text-amber-800 flex items-start gap-1.5">
          <svg class="w-3 h-3 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"></path></svg>
          <span>{{ w }}</span>
        </div>
      </div>
      <button @click="store.calculate" :disabled="store.isLoading" class="w-full py-2.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-bold rounded-md transition-colors shadow-sm flex justify-center items-center gap-2">
        <svg v-if="store.isLoading" class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        {{ store.isLoading ? 'Recalculando...' : 'Actualizar Diseño' }}
      </button>
    </div>
  </aside>

  <!-- BEARING CAPACITY MODAL -->
  <div v-if="showBearingModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 class="font-bold text-slate-800">Calculadora de Cap. Portante</h3>
        <button @click="showBearingModal = false" class="text-slate-400 hover:text-slate-600 outline-none">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>
      <div class="p-5 space-y-3 overflow-y-auto custom-scrollbar flex-1">
        <div class="text-[10px] text-slate-500 mb-2 leading-tight">Cálculo simplificado basado en ecuación general de Terzaghi/Vesic.</div>
        
        <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Cohesión (c)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="calcParams.c" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kPa</span></div></div>
        
        <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Áng. Fricción (ϕ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="calcParams.phi" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
        
        <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="calcParams.gamma" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
        
        <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Base Zapata (B)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="calcParams.B" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">m</span></div></div>

        <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Prof. Desplante (Df)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="calcParams.Df" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">m</span></div></div>
        
        <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Factor de Seguridad (FS)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="calcParams.FS" class="w-full bg-white border border-slate-300 rounded-md py-1 px-2 text-xs outline-none" /></div></div>
        
        <div class="mt-4 p-3 bg-blue-50/50 rounded border border-blue-100">
          <h4 class="text-[10px] font-bold text-blue-800 mb-2 border-b border-blue-100 pb-1">Resultados del Cálculo</h4>
          <div class="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[10px]">
            <div class="flex justify-between"><span class="text-slate-500">Nq:</span><span class="font-mono font-bold text-slate-700">{{ calcResults.Nq.toFixed(2) }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Nc:</span><span class="font-mono font-bold text-slate-700">{{ calcResults.Nc.toFixed(2) }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Nγ:</span><span class="font-mono font-bold text-slate-700">{{ calcResults.Ngamma.toFixed(2) }}</span></div>
            <div class="col-span-2 mt-1 pt-1 border-t border-blue-100 flex justify-between">
              <span class="text-slate-500">q_ult:</span><span class="font-mono font-bold text-slate-700">{{ calcResults.q_ult.toFixed(1) }} kPa</span>
            </div>
            <div class="col-span-2 flex justify-between">
              <span class="font-bold text-blue-700">q_adm:</span><span class="font-mono font-black text-blue-700">{{ calcResults.q_adm.toFixed(1) }} kPa</span>
            </div>
          </div>
        </div>
      </div>
      <div class="p-3 border-t border-slate-100 bg-slate-50 flex gap-2 justify-end">
        <button @click="showBearingModal = false" class="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-800 transition-colors">Cancelar</button>
        <button @click="applyBearingCapacity" class="px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded shadow-sm transition-colors">Aplicar</button>
      </div>
    </div>
  </div>

  <!-- Ka Modal -->
  <div v-if="showKaModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 class="font-bold text-slate-800 flex items-center gap-2">
          Proceso de Cálculo (Ka)
        </h3>
        <button @click="showKaModal = false" class="text-slate-400 hover:text-slate-600 outline-none">
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
            <li><strong>Inclinación Respaldo (θ):</strong> {{ store.theta }}° <span class="text-[10px] text-slate-400">{{ store.theta === 90 ? "(Vertical)" : "(Calculado)" }}</span></li>
          </ul>
        </div>
        <div class="bg-orange-50/50 p-3 rounded-lg border border-orange-100">
          <h4 class="text-xs font-bold text-orange-800 mb-2 uppercase tracking-wide">2. Fórmula de Coulomb (Num. 3.11.5.3, CCP-14)</h4>
          <div class="text-center py-2 text-sm text-slate-800 bg-white border border-orange-200 rounded px-2 overflow-x-auto custom-scrollbar">
            $$ K_a = \frac{\sin^2(\theta + \phi)}{\sin^2\theta \sin(\theta - \delta) \left[ 1 + \sqrt{\frac{\sin(\phi + \delta) \sin(\phi - \beta)}{\sin(\theta - \delta) \sin(\theta + \beta)}} \right]^2 } $$
          </div>
        </div>
        
        <div class="bg-blue-50 p-3 rounded-lg border border-blue-100">
          <h4 class="text-xs font-bold text-blue-800 mb-2 uppercase tracking-wide">3. Reemplazo de Valores</h4>
          <div :key="replacedFormula" class="text-center py-2 text-sm text-slate-800 bg-white border border-blue-200 rounded px-2 overflow-x-auto custom-scrollbar">
            {{ replacedFormula }}
          </div>
        </div>
        <div class="bg-emerald-50 p-3 rounded-lg border border-emerald-100 flex items-center justify-between mt-2">
          <h4 class="text-xs font-bold text-emerald-900 uppercase tracking-wide">4. Resultado Final (Ka)</h4>
          <span class="text-lg font-black text-emerald-700 font-mono">{{ store.results?.results?.earth_pressure?.ka?.toFixed(4) || '---' }}</span>
        </div>
      </div>
    </div>
  </div>
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
  <!-- EV MODAL -->
  <div v-if="showEvModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 class="font-bold text-slate-800">Desglose de Peso de Suelo (EV)</h3>
        <button @click="showEvModal = false" class="text-slate-400 hover:text-slate-600 outline-none"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
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
            <tr v-for="ld in evLoads" :key="ld.name" class="border-b border-slate-100">
              <td class="py-2 font-medium text-slate-700">{{ ld.name }}</td>
              <td class="py-2 text-right font-mono text-slate-500">{{ (ld.Fy / store.params.gamma_fill).toFixed(3) }}</td>
              <td class="py-2 text-right font-mono font-bold">{{ ld.Fy.toFixed(1) }}</td>
              <td class="py-2 text-right font-mono">{{ ld.x_app.toFixed(2) }}</td>
              <td class="py-2 text-right font-mono font-bold text-slate-800">{{ (ld.Fy * ld.x_app).toFixed(1) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="bg-slate-50 font-bold text-slate-800">
              <td class="py-2 px-2 uppercase text-[10px]">Total EV</td>
              <td class="py-2 text-right font-mono">{{ evLoads.reduce((sum, ld) => sum + (ld.Fy / store.params.gamma_fill), 0).toFixed(3) }}</td>
              <td class="py-2 text-right font-mono">{{ evLoads.reduce((sum, ld) => sum + ld.Fy, 0).toFixed(1) }}</td>
              <td class="py-2 text-right font-mono">-</td>
              <td class="py-2 text-right font-mono">{{ evLoads.reduce((sum, ld) => sum + (ld.Fy * ld.x_app), 0).toFixed(1) }}</td>
            </tr>
          </tfoot>
        </table>
        <p class="text-[9px] text-slate-400 mt-3 text-center">* El área se estima dividiendo el peso entre el peso específico del relleno (γs = {{ store.params.gamma_fill }} kN/m³).</p>
      </div>
    </div>
  </div>

  <!-- EH MODAL -->
  <div v-if="showEhModal" class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 class="font-bold text-slate-800">Cálculo de Empuje Activo (EH)</h3>
        <button @click="showEhModal = false" class="text-slate-400 hover:text-slate-600 outline-none"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
      </div>
      <div class="p-5 space-y-4 text-sm">
        <div class="bg-orange-50/50 p-4 rounded-lg border border-orange-100 text-center font-mono text-orange-800 leading-relaxed shadow-inner overflow-x-auto custom-scrollbar">
          <span class="block text-[10px] text-orange-600/70 uppercase tracking-widest mb-1 font-sans">Cálculo de Empuje</span>
          <div :key="ehFormulaReplaced">{{ ehFormulaReplaced }}</div>
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
    <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
      <div class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 class="font-bold text-slate-800">Cálculo de Sobrecarga (LS)</h3>
        <button @click="showLsModal = false" class="text-slate-400 hover:text-slate-600 outline-none"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
      </div>
      <div class="p-5 space-y-4 text-sm">
        <div class="bg-blue-50/50 p-4 rounded-lg border border-blue-100 text-center font-mono text-blue-800 leading-relaxed shadow-inner overflow-x-auto custom-scrollbar">
          <span class="block text-[10px] text-blue-600/70 uppercase tracking-widest mb-1 font-sans">Cálculo de Sobrecarga</span>
          <div :key="lsFormulaReplaced">{{ lsFormulaReplaced }}</div>
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

