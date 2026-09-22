import os

front_dir = r"c:\Users\luis\Documents\Proyes personales\Muros CCP14\frontend"

tailwind_config = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          800: '#1E293B',
          900: '#0F172A',
        },
        primary: '#1D4ED8',
        accent: '#F97316'
      }
    },
  },
  plugins: [],
}
"""
with open(os.path.join(front_dir, "tailwind.config.js"), "w", encoding="utf-8") as f:
    f.write(tailwind_config)

postcss_config = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
with open(os.path.join(front_dir, "postcss.config.js"), "w", encoding="utf-8") as f:
    f.write(postcss_config)

css_content = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
    background-color: #F8FAFC;
    color: #334155;
    margin: 0;
    padding: 0;
}
"""
with open(os.path.join(front_dir, "src", "style.css"), "w", encoding="utf-8") as f:
    f.write(css_content)

app_vue = """<script setup>
import { ref } from 'vue'

const activeTab = ref('geometry')
</script>

<template>
  <div class="h-screen w-screen flex overflow-hidden bg-slate-50 font-sans">
    
    <!-- LEFT COLUMN: Input Panel (25%) -->
    <div class="w-1/4 h-full bg-white shadow-xl z-10 flex flex-col border-r border-slate-200">
      <div class="p-5 bg-slate-900 text-white flex items-center gap-3">
        <div class="w-8 h-8 rounded bg-primary flex items-center justify-center font-bold">C</div>
        <h1 class="text-xl font-semibold tracking-tight">Muros CCP-14</h1>
      </div>
      
      <div class="flex-1 overflow-y-auto p-5">
        <h2 class="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Parametros de Diseño</h2>
        
        <!-- Accordion style sections -->
        <div class="space-y-4">
          <div class="border border-slate-200 rounded-lg overflow-hidden">
            <div class="bg-slate-100 p-3 font-medium text-slate-700 cursor-pointer flex justify-between">
              Geometría
            </div>
            <div class="p-4 space-y-3 bg-white">
              <div>
                <label class="block text-xs font-medium text-slate-500 mb-1">Altura del Fuste (m)</label>
                <input type="number" value="6.0" class="w-full border border-slate-300 rounded p-2 text-sm focus:ring-primary focus:border-primary outline-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-500 mb-1">Base de la Zapata (m)</label>
                <input type="number" value="4.0" class="w-full border border-slate-300 rounded p-2 text-sm focus:ring-primary focus:border-primary outline-none" />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-500 mb-1">Dentellon (m)</label>
                <input type="number" value="0.5" class="w-full border border-slate-300 rounded p-2 text-sm focus:ring-primary focus:border-primary outline-none" />
              </div>
            </div>
          </div>
          
          <div class="border border-slate-200 rounded-lg overflow-hidden">
            <div class="bg-slate-100 p-3 font-medium text-slate-700 cursor-pointer flex justify-between">
              Suelos & Materiales
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CENTER COLUMN: Canvas 2D/3D (50%) -->
    <div class="w-2/4 h-full flex flex-col bg-slate-100 relative">
      <!-- Toggle 2D/3D -->
      <div class="absolute top-4 left-1/2 -translate-x-1/2 bg-white rounded-full shadow-md flex p-1 border border-slate-200 z-10">
        <button class="px-4 py-1.5 rounded-full text-sm font-medium bg-primary text-white shadow-sm">Plano 2D</button>
        <button class="px-4 py-1.5 rounded-full text-sm font-medium text-slate-500 hover:text-slate-700">Modelo 3D</button>
      </div>
      
      <!-- Canvas Area -->
      <div class="flex-1 w-full h-full flex items-center justify-center" style="background-color: #1E1E1E; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px;">
        <p class="text-slate-400 font-mono text-sm border border-slate-600 px-4 py-2 rounded border-dashed">El canvas de Konva ira aqui...</p>
      </div>
    </div>

    <!-- RIGHT COLUMN: Results (25%) -->
    <div class="w-1/4 h-full bg-slate-900 text-slate-300 flex flex-col border-l border-slate-800 shadow-2xl z-10">
      <div class="p-5 border-b border-slate-800">
        <h2 class="text-lg font-medium text-white">Resultados LRFD</h2>
        <p class="text-xs text-slate-400 mt-1">Análisis en tiempo real</p>
      </div>
      
      <div class="flex-1 overflow-y-auto p-5 space-y-6">
        
        <!-- Stability Checks -->
        <div>
          <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Estabilidad</h3>
          <div class="space-y-3">
            <div class="flex items-center justify-between bg-slate-800 p-3 rounded border border-slate-700">
              <span class="text-sm">Deslizamiento</span>
              <span class="text-xs font-bold px-2 py-1 bg-green-900/50 text-green-400 rounded">OK (FS: 1.8)</span>
            </div>
            <div class="flex items-center justify-between bg-slate-800 p-3 rounded border border-slate-700">
              <span class="text-sm">Volcamiento</span>
              <span class="text-xs font-bold px-2 py-1 bg-green-900/50 text-green-400 rounded">OK (e = B/4)</span>
            </div>
            <div class="flex items-center justify-between bg-slate-800 p-3 rounded border border-slate-700 border-l-2 border-l-accent">
              <span class="text-sm">Presion Contacto</span>
              <span class="text-xs font-bold px-2 py-1 bg-orange-900/50 text-orange-400 rounded">ALERTA (q > qa)</span>
            </div>
          </div>
        </div>
        
        <!-- Structural Results -->
        <div>
          <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Diseño Estructural</h3>
          <div class="bg-primary/10 border border-primary/30 p-4 rounded-lg">
            <div class="text-xs text-primary mb-1 font-medium">Acero Requerido Fuste Base</div>
            <div class="text-2xl font-bold text-white flex items-end gap-1">
              18.4 <span class="text-sm font-normal text-slate-400 mb-1">cm2/m</span>
            </div>
          </div>
        </div>
        
      </div>
      
      <!-- Export Action -->
      <div class="p-5 border-t border-slate-800 bg-slate-900/50">
        <button class="w-full bg-primary hover:bg-blue-600 text-white font-medium py-3 rounded shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2">
          Generar Memoria PDF
        </button>
      </div>
    </div>
    
  </div>
</template>
"""
with open(os.path.join(front_dir, "src", "App.vue"), "w", encoding="utf-8") as f:
    f.write(app_vue)

with open(os.path.join(front_dir, "src", "main.js"), "w", encoding="utf-8") as f:
    f.write("import { createApp } from 'vue'\nimport './style.css'\nimport App from './App.vue'\n\ncreateApp(App).mount('#app')\n")
