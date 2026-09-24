const fs = require('fs');
const file = 'd:/OMARQUEZG/Desktop/Aplicaciones GOB/Muros/frontend/src/components/ParametersForm.vue';
let content = fs.readFileSync(file, 'utf8');

const newScript = `<script setup>
import { ref, watch, computed } from 'vue'
import { useWallStore } from '../stores/wallStore'

const store = useWallStore()
const activeTab = ref('geometry')

const showBearingModal = ref(false)

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
`;
content = newScript + content;
fs.writeFileSync(file, content);
console.log('patched');
