<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useWallStore } from './stores/wallStore'
import ParametersForm from './components/ParametersForm.vue'
import Viewer2D from './components/Viewer2D.vue'
import Viewer3D from './components/Viewer3D.vue'
import ResultsPanel from './components/ResultsPanel.vue'

const store = useWallStore()
const isMenuExpanded = ref(false)

let healthInterval = null

onMounted(() => {
  store.checkHealth()
  store.calculate()
  healthInterval = setInterval(() => store.checkHealth(), 20000)
})

onUnmounted(() => {
  if (healthInterval) clearInterval(healthInterval)
})
</script>

<template>
  <div class="h-screen w-screen flex flex-col bg-slate-50 font-sans text-slate-900 overflow-hidden">
    
    <!-- HEADER -->
    <header class="h-14 bg-blue-600 text-white flex items-center justify-between px-5 shrink-0 z-30 shadow-md border-b border-blue-700">
      <div class="flex items-center gap-6">
        <div class="font-bold text-lg tracking-widest flex items-center gap-2">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
          <span class="text-white">MUROS</span><span class="text-white font-light">CCP14</span>
        </div>
      </div>
      <div class="flex items-center gap-5">
        <div class="text-xs text-blue-100 flex items-center gap-2 font-medium">
          <span class="relative flex h-2.5 w-2.5">
            <span v-if="store.serverOnline" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5" :class="store.serverOnline ? 'bg-green-500' : store.serverOnline === false ? 'bg-red-500' : 'bg-slate-300'"></span>
          </span>
          {{ store.serverOnline ? 'Servidor Activo' : store.serverOnline === false ? 'Servidor Desconectado' : 'Verificando...' }}
        </div>
      </div>
    </header>

    <div v-if="store.error" class="shrink-0 bg-red-50 text-red-800 border-b border-red-200 px-5 py-2 flex items-center justify-between gap-3 text-xs font-medium">
      <span class="flex items-center gap-2">
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"></path></svg>
        {{ store.error }}
      </span>
      <button @click="store.error = null" class="text-red-400 hover:text-red-600 shrink-0" title="Cerrar">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </button>
    </div>

    <div v-if="store.results?.results?.warnings?.length" class="shrink-0 bg-amber-50 text-amber-900 border-b border-amber-200 px-5 py-2 text-xs font-medium space-y-1">
      <div v-for="(w, i) in store.results.results.warnings" :key="i" class="flex items-start gap-2">
        <svg class="w-4 h-4 shrink-0 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"></path></svg>
        <span>{{ w }}</span>
      </div>
    </div>

    <main class="flex-1 flex overflow-hidden relative">
      <ParametersForm />
      
      <section class="flex-1 relative overflow-hidden flex flex-col shadow-inner" style="background-color: #f8fafc; background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 24px 24px;">
        <div class="absolute top-6 right-6 z-20 pointer-events-auto">
          <div class="flex flex-col bg-slate-200/60 p-1 rounded-2xl shadow-inner border border-slate-200/50 transition-all duration-300 backdrop-blur-sm">
            
            <!-- Botón colapsado -->
            <button 
              v-if="!isMenuExpanded" 
              @click="isMenuExpanded = true" 
              class="p-2.5 rounded-xl bg-white text-blue-600 shadow-md ring-1 ring-slate-200/50 hover:bg-slate-50 transition-all duration-300 flex items-center justify-center"
              title="Mostrar Vistas"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 16.5l6 4.5 6-4.5m-12-3l6 4.5 6-4.5m-12-3L12 3l6 4.5-6 4.5L6 10.5z" />
              </svg>
            </button>

            <!-- Menú expandido (solo iconos) -->
            <div v-else class="flex flex-col gap-1">
              <!-- Cerrar -->
              <button @click="isMenuExpanded = false" class="p-2 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-all flex items-center justify-center mb-0.5 border-b border-slate-300/30" title="Ocultar">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 mb-1">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
                </svg>
              </button>

              <button @click="store.viewMode = '2D'; isMenuExpanded = false" :class="store.viewMode === '2D' ? 'bg-white text-blue-600 shadow-sm ring-1 ring-slate-200/50' : 'text-slate-600 hover:bg-slate-100'" class="p-2.5 rounded-xl transition-all duration-300 flex items-center justify-center" title="Plano 2D">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" /></svg>
              </button>
              
              <button @click="store.viewMode = 'Esquema'; isMenuExpanded = false" :class="store.viewMode === 'Esquema' ? 'bg-indigo-600 text-white shadow-sm ring-1 ring-indigo-200/50' : 'text-slate-600 hover:bg-slate-100'" class="p-2.5 rounded-xl transition-all duration-300 flex items-center justify-center" title="Distribuciones">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" /><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" /></svg>
              </button>
              
              <button @click="store.viewMode = '3D'; isMenuExpanded = false" :class="store.viewMode === '3D' ? 'bg-blue-600 text-white shadow-sm ring-1 ring-blue-200/50' : 'text-slate-600 hover:bg-slate-100'" class="p-2.5 rounded-xl transition-all duration-300 flex items-center justify-center" title="Modelo 3D">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" /></svg>
              </button>
            </div>
          </div>
        </div>
        
        <Viewer3D v-if="store.viewMode === '3D'" />
        <Viewer2D v-else />
      </section>

      <ResultsPanel />
    </main>
  </div>
</template>
