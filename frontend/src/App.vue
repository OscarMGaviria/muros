<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { OrbitControls } from '@tresjs/cientos'
import axios from 'axios'

const viewMode = ref('2D')
const activeTab = ref('geometry')

// Reactive Inputs
const params = ref({
  // Geometry
  H: 6.00,
  B: 4.00,
  D_z: 0.60,
  L_toe: 1.20,
  stem_top: 0.30,
  stem_bot: 0.60,
  D_d: 0.50,
  W_d: 0.40,
  
  // Materials
  fc: 28.0,
  fy: 420.0,
  
  // Soil
  gamma_fill: 18.0,
  phi_fill: 32.0,
  gamma_found: 20.0,
  phi_found: 35.0,
  q_allow: 300.0,
  
  // Loads
  q_surcharge: 10.0,
  kh: 0.0
})

// Reactive Results
const results = ref(null)
const isLoading = ref(false)

const calculate = async () => {
  isLoading.value = true
  try {
    const payload = {
      name: 'Muro CCP-14',
      geometry: {
        stem_height_m: params.value.H,
        stem_thickness_base_m: params.value.stem_bot,
        stem_thickness_top_m: params.value.stem_top,
        footing_width_m: params.value.B,
        footing_thickness_m: params.value.D_z,
        toe_length_m: params.value.L_toe,
        heel_length_m: params.value.B - params.value.L_toe - params.value.stem_bot,
        toe_cover_soil_m: 0.0,
        key_depth_m: params.value.D_d,
        key_width_m: params.value.W_d,
        backfill_slope_deg: 0.0,
        stem_batter_deg: 0.0,
        back_face_angle_deg: 90.0
      },
      materials: {
        concrete: { fc_MPa: params.value.fc, gamma_kN_m3: 24.0 },
        reinforcement: { fy_MPa: params.value.fy, Es_MPa: 200000.0 },
        cover_cm: 7.5
      },
      backfill: {
        name: 'Relleno',
        gamma_kN_m3: params.value.gamma_fill,
        phi_deg: params.value.phi_fill,
        cohesion_kPa: 0.0
      },
      foundation_soil: {
        name: 'Fundación',
        gamma_kN_m3: params.value.gamma_found,
        phi_deg: params.value.phi_found,
        cohesion_kPa: 0.0,
        bearing_capacity_kPa: params.value.q_allow
      },
      seismic: {
        kh: params.value.kh,
        kv: 0.0
      }
    }
    
    const response = await axios.post('http://localhost:8000/api/v1/design/ccp14', payload)
    results.value = response.data
  } catch (error) {
    console.error("Error en el cálculo:", error)
  } finally {
    isLoading.value = false
  }
}

// ---- KONVA 2D DRAWING LOGIC ----
const containerRef = ref(null)
const stageConfig = ref({ 
  width: 800, 
  height: 600,
  draggable: true,
  scaleX: 1,
  scaleY: 1,
  x: 0,
  y: 0
})

const handleResize = () => {
  if (containerRef.value) {
    stageConfig.value.width = containerRef.value.offsetWidth
    stageConfig.value.height = containerRef.value.offsetHeight
  }
}

const handleWheel = (e) => {
  e.evt.preventDefault()
  const scaleBy = 1.1
  const stage = e.target.getStage()
  const oldScale = stage.scaleX()

  const mousePointTo = {
    x: stage.getPointerPosition().x / oldScale - stage.x() / oldScale,
    y: stage.getPointerPosition().y / oldScale - stage.y() / oldScale,
  }

  const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy
  
  stageConfig.value.scaleX = newScale
  stageConfig.value.scaleY = newScale

  stageConfig.value.x = -(mousePointTo.x - stage.getPointerPosition().x / newScale) * newScale
  stageConfig.value.y = -(mousePointTo.y - stage.getPointerPosition().y / newScale) * newScale
}

onMounted(() => {
  calculate()
  window.addEventListener('resize', handleResize)
  setTimeout(handleResize, 100) // initial measure
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

import { Shape } from 'three'

// ---- UNIFIED GEOMETRY LOGIC (Meters, Y points UP) ----
const geomPoints = computed(() => {
  const H = params.value.H
  const B = params.value.B
  const Dz = params.value.D_z
  const L = params.value.L_toe
  const St = params.value.stem_top
  const Sb = params.value.stem_bot
  const Dd = params.value.D_d
  const Wd = params.value.W_d
  
  // 1. Footing (Zapata)
  const footing = [
    0, 0,
    L, 0,
    L, -Dd,
    L + Wd, -Dd,
    L + Wd, 0,
    B, 0,
    B, Dz,
    0, Dz
  ]
  
  // 2. Stem (Fuste)
  const stem = [
    L, Dz,
    L + Sb, Dz,
    L + St, Dz + H,
    L, Dz + H
  ]
  
  // 3. Foundation Soil
  const ext = 4 // 4m
  const depth = 2 // 2m
  const found = [
    -ext, 0,
    L, 0,
    L, -Dd,
    L + Wd, -Dd,
    L + Wd, 0,
    B, 0,
    B, Dz,
    B + ext, Dz,
    B + ext, -depth,
    -ext, -depth
  ]
  
  // 4. Backfill (Relleno en Talón)
  const backfill = [
    L + Sb, Dz,
    B + ext, Dz,
    B + ext, Dz + H,
    L + St, Dz + H
  ]
  
  // 5. Toe Soil (Suelo en Punta)
  const toeSoil = [
    -ext, 0,
    0, 0,
    0, Dz,
    L, Dz,
    L, Dz + 0.5,
    -ext, Dz + 0.5
  ]
  

  // 6. Surcharge Block (for 3D)
  const surcharge = [
    L + St, Dz + H,
    B + ext, Dz + H,
    B + ext, Dz + H + 0.5,
    L + St, Dz + H + 0.5
  ]
  
  return { footing, stem, found, backfill, toeSoil, surcharge }
})


const createThreeShape = (pts) => {
  const shape = new Shape()
  shape.moveTo(pts[0], pts[1])
  for (let i = 2; i < pts.length; i += 2) {
    shape.lineTo(pts[i], pts[i+1])
  }
  return shape
}

const threeShapes = computed(() => {
return {
    footing: createThreeShape(geomPoints.value.footing),
    stem: createThreeShape(geomPoints.value.stem),
    found: createThreeShape(geomPoints.value.found),
    backfill: createThreeShape(geomPoints.value.backfill),
    toeSoil: createThreeShape(geomPoints.value.toeSoil),
    surcharge: createThreeShape(geomPoints.value.surcharge)
  }
})

const invScale = computed(() => 1 / (stageConfig.value?.scaleX || 1))

const surchargeArrows2D = computed(() => {
  const L = params.value.L_toe * scale
  const St = params.value.stem_top * scale
  const B = params.value.B * scale
  const ext = 4 * scale
  
  const startX = L + St
  const endX = B + ext
  const Y = -params.value.D_z * scale - params.value.H * scale
  
  const arrHeight = 60 * invScale.value
  const arrows = []
  const numArrows = 6
  for (let i = 0; i < numArrows; i++) {
    const x = startX + (endX - startX) * (i / (numArrows - 1))
    arrows.push([x, Y - arrHeight, x, Y])
  }
  return { 
    arrows, 
    textX: startX + (endX - startX)/2, 
    textY: Y - arrHeight - 20 * invScale.value 
  }
})

const surchargeArrows3D = computed(() => {
  if (params.value.q_surcharge <= 0) return []
  const L = params.value.L_toe
  const St = params.value.stem_top
  const B = params.value.B
  const ext = 4 // same as backfill ext
  const startX = L + St
  const endX = B + ext
  const y = params.value.D_z + params.value.H // Base of surcharge block
  
  const arrows = []
  const numX = 6
  const numZ = 3
  
  for (let i = 0; i < numX; i++) {
    const x = startX + (endX - startX) * (i / (numX - 1))
    for (let j = 0; j < numZ; j++) {
      const z = 0.5 + 4.0 * (j / (numZ - 1))
      arrows.push({ x, y, z })
    }
  }
  return arrows
})

// Escala 2D: 50 pixeles por metro. Y se invierte (Y down).
const scale = 50
const scale2D = (pts) => {
  return pts.map((val, idx) => idx % 2 === 0 ? val * scale : -val * scale)
}

const footingPoints2D = computed(() => scale2D(geomPoints.value.footing))
const stemPoints2D = computed(() => scale2D(geomPoints.value.stem))
const foundationSoilPoints2D = computed(() => scale2D(geomPoints.value.found))
const heelSoilPoints2D = computed(() => scale2D(geomPoints.value.backfill))
const toeSoilPoints2D = computed(() => scale2D(geomPoints.value.toeSoil))

const dimensions2D = computed(() => {
  const L = params.value.L_toe * scale
  const St = params.value.stem_top * scale
  const Sb = params.value.stem_bot * scale
  const B = params.value.B * scale
  const H = params.value.H * scale
  const Dz = params.value.D_z * scale
  const Dd = params.value.D_d * scale
  const Wd = params.value.W_d * scale
  
  const dims = []
  
  const addDim = (x1, y1, x2, y2, text, offset, isVertical) => {
    const offX = isVertical ? offset : 0
    const offY = isVertical ? 0 : offset
    return {
      ext1: [x1, y1, x1 + offX * 1.1, y1 + offY * 1.1],
      ext2: [x2, y2, x2 + offX * 1.1, y2 + offY * 1.1],
      line: [x1 + offX, y1 + offY, x2 + offX, y2 + offY],
      text,
      midX: (x1 + offX + x2 + offX) / 2,
      midY: (y1 + offY + y2 + offY) / 2,
      isVertical,
      isNeg: offset < 0
    }
  }

  // 1. Base (B) - Abajo
  dims.push(addDim(0, 0, B, 0, `B = ${params.value.B.toFixed(2)}m`, 60, false))
  
  // 2. Altura Total fuste (H) - Izquierda
  dims.push(addDim(L, -Dz, L, -Dz - H, `H = ${params.value.H.toFixed(2)}m`, -80, true))
  
  // 3. Zapata (Dz) - Derecha
  dims.push(addDim(B, 0, B, -Dz, `Dz = ${params.value.D_z.toFixed(2)}m`, 60, true))
  
  // 4. Punta (L_toe) - Arriba de la punta
  dims.push(addDim(0, -Dz, L, -Dz, `Punta = ${params.value.L_toe.toFixed(2)}m`, -30, false))
  
  // 5. Dentellón (Dd) - Abajo
  if (params.value.D_d > 0) {
    dims.push(addDim(L + Wd, 0, L + Wd, Dd, `Dd = ${params.value.D_d.toFixed(2)}m`, 40, true))
    dims.push(addDim(L, Dd, L + Wd, Dd, `${params.value.W_d.toFixed(2)}m`, 20, false))
  }

  // 6. Fuste Base (Sb) y Corona (St)
  dims.push(addDim(L, -Dz, L + Sb, -Dz, `Sb = ${params.value.stem_bot.toFixed(2)}m`, -60, false))
  dims.push(addDim(L, -Dz - H, L + St, -Dz - H, `St = ${params.value.stem_top.toFixed(2)}m`, -30, false))

  return dims
})

const actingLoads2D = computed(() => {
  if (!results.value || !results.value.results || !results.value.results.loads) return []
  
  let loads = results.value.results.loads
  if (viewMode.value === 'Esquema') {
    loads = loads.filter(l => !l.type.includes('DC') && !l.type.includes('EV'))
  }
  
  return loads.map(load => {
    const cx = load.x_app * scale
    const cy = -load.y_app * scale // canvas Y is inverted
    
    let isHorizontal = Math.abs(load.Fx) > Math.abs(load.Fy)
    let isVertical = !isHorizontal
    
    let startX = cx
    let startY = cy
    
    // Scale the arrow length with zoom so it doesn't become huge or tiny
    const iScale = invScale.value
    const arrowLength = 50 * iScale
    
    let color = '#ef4444' // red default
    if (load.type.includes('DC') || load.type.includes('EV')) color = '#10b981' // green for weights
    if (load.type.includes('EH')) color = '#f59e0b' // orange for active
    if (load.type.includes('EQ')) color = '#8b5cf6' // purple for seismic
    
    if (isHorizontal) {
      startX = load.Fx > 0 ? cx - arrowLength : cx + arrowLength
    } else {
      startY = load.Fy < 0 ? cy - arrowLength : cy + arrowLength
    }
    
    return {
      points: [startX, startY, cx, cy],
      color,
      text: `${isHorizontal ? load.Fx.toFixed(1) : Math.abs(load.Fy).toFixed(1)} kN`,
      textX: startX + (isHorizontal ? (load.Fx > 0 ? -60 * iScale : 10 * iScale) : 10 * iScale),
      textY: startY + (isVertical ? (load.Fy < 0 ? -25 * iScale : 10 * iScale) : -15 * iScale),
      name: load.name,
      type: load.type
    }
  })
})

const pressureDiagrams2D = computed(() => {
  if (!results.value || !results.value.results || !results.value.results.loads) return []
  
  const H_total = params.value.H + params.value.D_z
  const B = params.value.B
  const Dz = params.value.D_z
  
  // Constant schematic width
  const w = 1.2 * scale
  
  const diagrams = []
  const loads = results.value.results.loads
  
  // Helper to draw horizontal arrows pointing left
  const getHArrows = (startY, endY, minW, maxW, xBase) => {
    const arrs = []
    const n = 5
    for(let i=0; i<=n; i++) {
      const t = i/n
      const y = startY + (endY - startY) * t
      const curW = minW + (maxW - minW) * t
      if (curW > 0.1) arrs.push([xBase + curW, y, xBase, y])
    }
    return arrs
  }
  
  // Helper to draw vertical arrows pointing up
  const getVArrows = (startX, endX, minW, maxW, yBase) => {
    const arrs = []
    const n = 6
    for(let i=0; i<=n; i++) {
      const t = i/n
      const x = startX + (endX - startX) * t
      const curW = minW + (maxW - minW) * t
      if (curW > 0.1) arrs.push([x, yBase + curW, x, yBase])
    }
    return arrs
  }
  
  // EH (Empuje Estático) - Triángulo invertido geométricamente (max bottom)
  const ehLoad = loads.find(l => l.type === 'EH')
  if (ehLoad) {
    const p_max = (2 * ehLoad.Fx) / H_total
    diagrams.push({
      name: 'EH',
      points: [B * scale, -Dz * scale, B * scale, -(H_total) * scale, (B * scale) + w, -Dz * scale],
      fill: 'rgba(245, 158, 11, 0.15)',
      stroke: '#f59e0b',
      textMax: `EH = ${p_max.toFixed(1)}`,
      textX: (B * scale) + w + 10,
      textY: -Dz * scale - 15,
      arrows: getHArrows(-Dz * scale, -(H_total) * scale, w, 0, B * scale)
    })
  }
  
  // PIR / EQ_E (Sismo) - Triángulo (max top)
  const pirLoad = loads.find(l => l.type === 'EQ_E')
  if (pirLoad) {
    const p_top = (2 * pirLoad.Fx) / H_total
    diagrams.push({
      name: 'PIR',
      points: [B * scale, -Dz * scale, B * scale, -(H_total) * scale, (B * scale) + w, -(H_total) * scale],
      fill: 'rgba(139, 92, 246, 0.15)',
      stroke: '#8b5cf6',
      textMax: `PIR = ${p_top.toFixed(1)}`,
      textX: (B * scale) + w + 10,
      textY: -(H_total) * scale - 10,
      arrows: getHArrows(-Dz * scale, -(H_total) * scale, 0, w, B * scale)
    })
  }

  // LS (Sobrecarga viva) - Rectángulo
  const lsLoad = loads.find(l => l.type === 'LS')
  if (lsLoad || params.value.q_surcharge > 0) {
    const Fx = lsLoad ? lsLoad.Fx : (params.value.q_surcharge * 0.33 * H_total)
    const p = Fx / H_total
    const xBaseLS = ehLoad ? (B * scale) + w : B * scale
    diagrams.push({
      name: 'LS',
      points: [xBaseLS, -Dz * scale, xBaseLS, -(H_total) * scale, xBaseLS + w, -(H_total) * scale, xBaseLS + w, -Dz * scale],
      fill: 'rgba(239, 68, 68, 0.15)',
      stroke: '#ef4444',
      textMax: `LS = ${p.toFixed(1)}`,
      textX: xBaseLS + w + 10,
      textY: -(H_total / 2) * scale,
      arrows: getHArrows(-Dz * scale, -(H_total) * scale, w, w, xBaseLS)
    })
  }
  
  // Reacción del suelo (Bearing) - Trapecio bajo la zapata
  const bearing = results.value.results.stability?.bearing
  if (bearing && bearing.q_max > 0) {
    const q_max = bearing.q_max
    const q_min = bearing.q_min || 0
    // Keep trapezoid proportions visually
    const w_max = w
    const w_min = (q_min / q_max) * w
    
    diagrams.push({
      name: 'Reacción',
      points: [0, 0, B * scale, 0, B * scale, w_min, 0, w_max],
      fill: 'rgba(16, 185, 129, 0.15)',
      stroke: '#10b981',
      textMax: `${q_max.toFixed(0)}`,
      textMin: `${q_min.toFixed(0)}`,
      textMaxX: -25,
      textMaxY: w_max + 15,
      textMinX: B * scale - 15,
      textMinY: w_min + 15,
      arrows: getVArrows(0, B * scale, w_max, w_min, 0)
    })
  }
  
  return diagrams
})

// --------------------------------
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
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
          </span>
          Servidor Activo
        </div>
      </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
      
      <!-- LEFT TOOLBAR (Icons) -->
      <aside class="w-16 bg-white flex flex-col items-center py-5 gap-5 z-20 shrink-0 border-r border-slate-200 shadow-sm">
        <button @click="activeTab = 'geometry'" :class="activeTab === 'geometry' ? 'bg-blue-600 text-white shadow-inner' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'" class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors" title="Geometría">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>
        </button>
        <button @click="activeTab = 'materials'" :class="activeTab === 'materials' ? 'bg-blue-600 text-white shadow-inner' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'" class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors" title="Materiales Estructurales">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </button>
        <button @click="activeTab = 'soils'" :class="activeTab === 'soils' ? 'bg-blue-600 text-white shadow-inner' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'" class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors" title="Suelos (Geotecnia)">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2 10h20M5 14h14M8 18h8M11 22h2 M12 2v8"></path></svg>
        </button>
        <button @click="activeTab = 'loads'" :class="activeTab === 'loads' ? 'bg-blue-600 text-white shadow-inner' : 'text-slate-400 hover:text-blue-600 hover:bg-blue-50'" class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors" title="Cargas y Sismo">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3"></path></svg>
        </button>
      </aside>

      <!-- LEFT EXPANDED PANEL (Inputs) -->
      <aside class="w-[300px] bg-white flex flex-col z-10 shrink-0 shadow-lg border-r border-slate-200">
        <div class="px-5 py-4 bg-slate-50 border-b border-slate-200">
          <h2 class="text-sm font-extrabold text-slate-800 uppercase tracking-wider">
            {{ activeTab === 'geometry' ? 'Geometría' : activeTab === 'materials' ? 'Materiales' : activeTab === 'soils' ? 'Suelos' : 'Cargas y Sismo' }}
          </h2>
          <p class="text-[11px] text-slate-500 mt-1">Configure los parámetros</p>
        </div>
        
        <div class="p-5 space-y-4 overflow-y-auto flex-1 custom-scrollbar">
          
          <!-- TAB: GEOMETRY -->
          <template v-if="activeTab === 'geometry'">
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Altura Fuste (H)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.H" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Base Zapata (B)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.B" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Espesor Zapata (Dz)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.D_z" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Longitud Punta (L_toe)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.L_toe" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Espesor Fuste Inferior</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.stem_bot" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Espesor Fuste Superior</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.stem_top" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Profundidad Llave</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.D_d" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Ancho Llave</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.W_d" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">m</span></div></div>
          </template>

          <!-- TAB: MATERIALS -->
          <template v-if="activeTab === 'materials'">
            <div class="bg-blue-50 p-3 rounded-md mb-2 border border-blue-100">
              <h3 class="text-xs font-bold text-blue-800 mb-2">Materiales Estructurales</h3>
              <div class="space-y-3">
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Concreto f'c</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="params.fc" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">MPa</span></div></div>
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Acero fy</label><div class="flex shadow-sm"><input type="number" step="10" v-model.number="params.fy" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">MPa</span></div></div>
              </div>
            </div>
          </template>

          <!-- TAB: SOILS -->
          <template v-if="activeTab === 'soils'">
            <div class="bg-orange-50 p-3 rounded-md mb-2 border border-orange-100">
              <h3 class="text-xs font-bold text-orange-900 mb-2">Suelo de Relleno</h3>
              <div class="space-y-3">
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.gamma_fill" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Áng. Fricción (ϕ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="params.phi_fill" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
              </div>
            </div>

            <div class="bg-emerald-50 p-3 rounded-md border border-emerald-100">
              <h3 class="text-xs font-bold text-emerald-900 mb-2">Suelo de Fundación</h3>
              <div class="space-y-3">
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Peso Específico (γ)</label><div class="flex shadow-sm"><input type="number" step="0.1" v-model.number="params.gamma_found" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kN/m³</span></div></div>
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Áng. Fricción (ϕ)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="params.phi_found" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">°</span></div></div>
                <div class="space-y-1"><label class="text-[10px] font-bold text-slate-600">Capacidad Portante (q_adm)</label><div class="flex shadow-sm"><input type="number" step="10" v-model.number="params.q_allow" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1 px-2 text-xs outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-2 py-1 text-[10px] text-slate-500">kPa</span></div></div>
              </div>
            </div>
          </template>

          <!-- TAB: LOADS -->
          <template v-if="activeTab === 'loads'">
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Sobrecarga Vehicular (LS)</label><div class="flex shadow-sm"><input type="number" step="1" v-model.number="params.q_surcharge" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">kPa</span></div></div>
            <div class="space-y-1.5"><label class="text-xs font-semibold text-slate-600">Coeficiente Sísmico (kh)</label><div class="flex shadow-sm"><input type="number" step="0.01" v-model.number="params.kh" @change="calculate" class="w-full bg-white border border-slate-300 rounded-l-md py-1.5 px-3 text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" /><span class="bg-slate-50 border border-l-0 border-slate-300 rounded-r-md px-3 py-1.5 text-xs text-slate-500">g</span></div></div>
          </template>
          
        </div>
        <div class="p-4 border-t border-slate-200 bg-white">
          <button @click="calculate" :disabled="isLoading" class="w-full py-2.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 text-xs font-bold rounded-md transition-colors shadow-sm disabled:opacity-50 flex justify-center items-center gap-2">
            <svg v-if="isLoading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            {{ isLoading ? 'Recalculando...' : 'Actualizar Diseño' }}
          </button>
        </div>
      </aside>

      <!-- CENTER CANVAS (Main Viewer) -->
      <section ref="containerRef" class="flex-1 relative overflow-hidden flex flex-col shadow-inner" style="background-color: #f8fafc; background-image: radial-gradient(#cbd5e1 1px, transparent 1px); background-size: 24px 24px;">
        <!-- FLOATING PILL -->
        <div class="absolute top-6 left-1/2 -translate-x-1/2 z-20 pointer-events-auto">
          <div class="flex bg-slate-200/60 p-1 rounded-full shadow-inner border border-slate-200/50">
            <button @click="viewMode = '2D'" :class="viewMode === '2D' ? 'bg-white text-blue-600 shadow-md ring-1 ring-slate-200/50' : 'text-slate-600 hover:bg-slate-100'" class="px-5 py-2 rounded-full text-xs font-bold transition-all duration-300 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>Plano 2D</button>
            <button @click="viewMode = 'Esquema'" :class="viewMode === 'Esquema' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100'" class="px-5 py-2 rounded-full text-xs font-bold transition-all duration-300 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>Distribuciones</button>
            <button @click="viewMode = '3D'" :class="viewMode === '3D' ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-slate-100'" class="px-5 py-2 rounded-full text-xs font-bold transition-all duration-300 flex items-center gap-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>Modelo 3D</button>
          </div>
        </div>
        
        <div v-if="viewMode !== '3D'" class="w-full h-full absolute inset-0 cursor-grab active:cursor-grabbing" @wheel="handleWheel">
          <v-stage ref="stageRef" :config="stageConfig" @wheel="handleWheel">
            <v-layer>
              <!-- Grupo centralizado -->
              <v-group :config="{ x: stageConfig.width / 2 - (params.B * scale) / 2, y: stageConfig.height - 150 }">
                
                <!-- Only show soils in 2D mode, hide in Esquema -->
                <v-group v-if="viewMode === '2D'">
                  <!-- Suelo de Fundación -->
                  <v-line :config="{
                    points: foundationSoilPoints2D,
                    fill: '#8c7b68',
                    stroke: '#5c5042',
                    strokeWidth: 1 * invScale,
                    closed: true,
                    opacity: 0.7
                  }" />

                  <!-- Suelo sobre el Talón (Backfill) -->
                  <v-line :config="{
                    points: heelSoilPoints2D,
                    fill: '#d1bfae',
                    stroke: '#a8988a',
                    strokeWidth: 1 * invScale,
                    closed: true,
                    opacity: 0.8
                  }" />

                  <!-- Suelo sobre la Punta -->
                  <v-line :config="{
                    points: toeSoilPoints2D,
                    fill: '#8c7b68',
                    stroke: '#5c5042',
                    strokeWidth: 1 * invScale,
                    closed: true,
                    opacity: 0.7
                  }" />
                </v-group>

                <!-- Footing -->
                <v-line :config="{
                  points: footingPoints2D,
                  fill: '#e2e8f0',
                  stroke: '#475569',
                  strokeWidth: 2 * invScale,
                  closed: true
                }" />

                <!-- Stem -->
                <v-line :config="{
                  points: stemPoints2D,
                  fill: '#e2e8f0',
                  stroke: '#475569',
                  strokeWidth: 2 * invScale,
                  closed: true
                }" />
                
                <!-- Dimensiones -->
                <v-group v-if="viewMode === '2D'">
                  <!-- Surcharge (Sobrecarga) -->
                  <v-group v-if="params.q_surcharge > 0">
                    <v-arrow v-for="(pts, i) in surchargeArrows2D.arrows" :key="'arr'+i" :config="{
                      points: pts,
                      pointerLength: 8 * invScale,
                      pointerWidth: 8 * invScale,
                      fill: '#ef4444',
                      stroke: '#ef4444',
                      strokeWidth: 2 * invScale
                    }" />
                    <v-text :config="{ x: surchargeArrows2D.textX - 20 * invScale, y: surchargeArrows2D.textY, text: 'q = ' + params.q_surcharge + ' kPa', fontSize: 14 * invScale, fill: '#ef4444', fontStyle: 'bold' }" />
                  </v-group>
                <!-- Cotas Arquitectónicas -->
                <v-group>
                  <v-group v-for="(dim, i) in dimensions2D" :key="'dim'+i">
                    <!-- Lineas auxiliares -->
                    <v-line :config="{ points: dim.ext1, stroke: '#94a3b8', strokeWidth: 1 * invScale, dash: [4*invScale, 4*invScale] }" />
                    <v-line :config="{ points: dim.ext2, stroke: '#94a3b8', strokeWidth: 1 * invScale, dash: [4*invScale, 4*invScale] }" />
                    <!-- Linea de cota (Arrows) -->
                    <v-arrow :config="{ 
                      points: dim.line, 
                      stroke: '#334155', 
                      strokeWidth: 1.5 * invScale,
                      fill: '#334155',
                      pointerLength: 5 * invScale,
                      pointerWidth: 5 * invScale,
                      pointerAtBothEnds: true
                    }" />
                    <!-- Texto de la cota -->
                    <v-text :config="{ 
                      x: dim.midX + (dim.isVertical ? (dim.isNeg ? -75 * invScale : 10 * invScale) : -35 * invScale), 
                      y: dim.midY + (dim.isVertical ? -6 * invScale : (dim.isNeg ? -20 * invScale : 10 * invScale)), 
                      text: dim.text, 
                      fontSize: 13 * invScale, 
                      fill: '#0f172a',
                      fontFamily: 'JetBrains Mono',
                      fontStyle: 'bold'
                    }" />
                  </v-group>
                </v-group>
              </v-group>

              <!-- Only in Esquema mode: Pressure Distributions -->
              <v-group v-if="viewMode === 'Esquema'">
                <v-group v-for="(diag, idx) in pressureDiagrams2D" :key="'diag'+idx">
                  <v-line :config="{
                    points: diag.points,
                    fill: diag.fill,
                    stroke: diag.stroke,
                    strokeWidth: 2 * invScale,
                    closed: true
                  }" />
                  <v-arrow v-for="(arr, aIdx) in diag.arrows" :key="'arr'+idx+'-'+aIdx" :config="{
                    points: arr,
                    stroke: diag.stroke,
                    fill: diag.stroke,
                    strokeWidth: 1.5 * invScale,
                    pointerLength: 5 * invScale,
                    pointerWidth: 5 * invScale
                  }" />
                  <v-text :config="{
                    x: diag.textMaxX ? diag.textMaxX * invScale + (diag.points[0] * (1 - invScale)) : diag.textX,
                    y: diag.textMaxY ? diag.textMaxY * invScale + (diag.points[1] * (1 - invScale)) : diag.textY,
                    text: diag.textMax,
                    fontSize: 12 * invScale,
                    fill: diag.stroke,
                    fontStyle: 'bold',
                    fontFamily: 'JetBrains Mono'
                  }" />
                  <v-text v-if="diag.textMin" :config="{
                    x: diag.textMinX * invScale + (diag.points[0] * (1 - invScale)),
                    y: diag.textMinY * invScale + (diag.points[1] * (1 - invScale)),
                    text: diag.textMin,
                    fontSize: 12 * invScale,
                    fill: diag.stroke,
                    fontStyle: 'bold',
                    fontFamily: 'JetBrains Mono'
                  }" />
                </v-group>
              </v-group>

              <!-- Resultant Loads (show in 2D and Esquema) -->
              <v-group v-if="viewMode !== '3D'">
                <v-group v-for="(arr, idx) in actingLoads2D" :key="'actLd'+idx">
                  <v-arrow :config="{
                    points: arr.points,
                    pointerLength: 8 * invScale,
                    pointerWidth: 8 * invScale,
                    fill: arr.color,
                    stroke: arr.color,
                    strokeWidth: 2.5 * invScale
                  }" />
                  <v-text :config="{
                    x: arr.textX,
                    y: arr.textY,
                    text: arr.type + ': ' + arr.text,
                    fontSize: 12 * invScale,
                    fill: arr.color,
                    fontStyle: 'bold',
                    fontFamily: 'JetBrains Mono'
                  }" />
                </v-group>
              </v-group>
              </v-group>
            </v-layer>
          </v-stage>
        </div>

        <div v-else class="w-full h-full absolute inset-0 bg-sky-50 pointer-events-auto cursor-grab active:cursor-grabbing">
          <TresCanvas clear-color="#f0f9ff" shadows>
            <TresPerspectiveCamera :position="[12, 10, 15]" :look-at="[0, 2, 0]" />
            <OrbitControls />
            <TresAmbientLight :intensity="0.8" color="#ffffff" />
            <TresDirectionalLight :position="[15, 20, 10]" :intensity="1.2" cast-shadow color="#fdfbf7" />
            <TresFog color="#f0f9ff" :near="15" :far="60" />
            
            <!-- Grupo Principal del Muro (Extruded Shapes) -->
            <TresGroup :position="[-params.B/2, 0, -2.5]">
              <!-- Zapata y Dentellón -->
              <TresMesh cast-shadow receive-shadow>
                <TresExtrudeGeometry :args="[threeShapes.footing, { depth: 5, bevelEnabled: false }]" />
                <TresMeshStandardMaterial color="#a3a3a3" roughness="0.9" metalness="0.1" />
              </TresMesh>
              
              <!-- Fuste -->
              <TresMesh cast-shadow receive-shadow>
                <TresExtrudeGeometry :args="[threeShapes.stem, { depth: 5, bevelEnabled: false }]" />
                <TresMeshStandardMaterial color="#d4d4d4" roughness="0.85" metalness="0.1" />
              </TresMesh>

              <!-- Suelo de Cimentación -->
              <TresMesh receive-shadow>
                <TresExtrudeGeometry :args="[threeShapes.found, { depth: 5, bevelEnabled: false }]" />
                <TresMeshStandardMaterial color="#8c7b68" roughness="1.0" />
              </TresMesh>

              <!-- Suelo de Relleno en Talón -->
              <TresMesh receive-shadow cast-shadow>
                <TresExtrudeGeometry :args="[threeShapes.backfill, { depth: 5, bevelEnabled: false }]" />
                <TresMeshStandardMaterial color="#d1bfae" roughness="1.0" />
              </TresMesh>

              <!-- Suelo sobre la Punta -->
              <TresMesh receive-shadow cast-shadow>
                <TresExtrudeGeometry :args="[threeShapes.toeSoil, { depth: 5, bevelEnabled: false }]" />
                <TresMeshStandardMaterial color="#8c7b68" roughness="1.0" />
              </TresMesh>

              <!-- Sobrecarga Vehicular -->
              <TresGroup v-if="params.q_surcharge > 0">
                <TresMesh receive-shadow>
                  <TresExtrudeGeometry :args="[threeShapes.surcharge, { depth: 5, bevelEnabled: false }]" />
                  <TresMeshStandardMaterial color="#ef4444" opacity="0.3" transparent depth-write="false" />
                </TresMesh>
                <!-- Flechas de Sobrecarga en 3D -->
                <TresGroup v-for="(pos, idx) in surchargeArrows3D" :key="'arr3d'+idx" :position="[pos.x, pos.y, pos.z]">
                  <!-- Cuerpo de la flecha -->
                  <TresMesh :position="[0, 0.35, 0]" cast-shadow>
                    <TresCylinderGeometry :args="[0.03, 0.03, 0.3]" />
                    <TresMeshStandardMaterial color="#ef4444" />
                  </TresMesh>
                  <!-- Punta de la flecha (cono apuntando hacia abajo) -->
                  <TresMesh :position="[0, 0.1, 0]" :rotation="[Math.PI, 0, 0]" cast-shadow>
                    <TresConeGeometry :args="[0.08, 0.2]" />
                    <TresMeshStandardMaterial color="#ef4444" />
                  </TresMesh>
                </TresGroup>
              </TresGroup>
            </TresGroup>

            <!-- Plano de fondo lejano -->
            <TresMesh :position="[0, -2.05, 0]" :rotation="[-Math.PI / 2, 0, 0]" receive-shadow>
              <TresPlaneGeometry :args="[80, 80]" />
              <TresMeshStandardMaterial color="#e2e8f0" roughness="1.0" />
            </TresMesh>
          </TresCanvas>
        </div>
      </section>

      <!-- RIGHT PANEL (Results) -->
      <aside class="w-80 bg-white flex flex-col z-10 shrink-0 shadow-[-4px_0_15px_rgba(0,0,0,0.05)] border-l border-slate-200">
        <div class="bg-blue-50 text-blue-800 p-3.5 flex justify-between items-center border-b border-blue-100">
          <h2 class="text-xs font-bold tracking-widest text-blue-800">RESULTADOS EN VIVO</h2>
          <svg class="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        </div>
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <div v-if="!results && !isLoading" class="p-6 text-center text-slate-400"><p class="text-sm">Presiona "Actualizar Diseño" para ver los resultados</p></div>
          <div v-if="results">
            <div class="bg-slate-100/50 px-4 py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-slate-200">Estabilidad</div>
            <div class="divide-y divide-slate-100">
              <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div><div class="text-xs font-bold text-slate-800">Deslizamiento</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">Fuerzas Res / Act</div></div>
                <div class="text-right">
                  <div class="text-sm font-black text-green-600 font-mono tracking-tight" :class="{'text-red-500': results.results.stability.sliding.FS < 1.0}">FS: {{ results.results.stability.sliding.FS.toFixed(2) }}</div>
                  <div class="text-[10px] text-slate-500 font-medium">Req > 1.00</div>
                </div>
              </div>
              <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div><div class="text-xs font-bold text-slate-800">Volcamiento</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">e &lt; B/3 (CCP-14)</div></div>
                <div class="text-right">
                  <div class="text-sm font-black text-green-600 font-mono tracking-tight">e: {{ results.results.stability.eccentricity.e.toFixed(2) }} m</div>
                  <div class="text-[10px] text-slate-500 font-medium">Límite: {{ (params.B / 3).toFixed(2) }} m</div>
                </div>
              </div>
              <div class="p-4 flex items-center justify-between border-l-[3px]" :class="results.results.stability.bearing.q_max > params.q_allow ? 'bg-orange-50/50 border-orange-500' : 'hover:bg-slate-50 border-transparent'">
                <div>
                  <div class="text-xs font-bold text-slate-800" :class="{'text-orange-900': results.results.stability.bearing.q_max > params.q_allow}">Presión Contacto</div>
                  <div class="text-[10px] text-slate-400 font-medium mt-0.5" :class="{'text-orange-600/80': results.results.stability.bearing.q_max > params.q_allow}">Esfuerzo a la roca</div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-black text-slate-700 font-mono tracking-tight" :class="{'text-orange-600': results.results.stability.bearing.q_max > params.q_allow}">{{ results.results.stability.bearing.q_max.toFixed(0) }} kPa</div>
                  <div v-if="results.results.stability.bearing.q_max > params.q_allow" class="text-[10px] text-orange-600/80 font-bold px-1.5 py-0.5 bg-orange-100 rounded inline-block mt-0.5">FALLA</div>
                </div>
              </div>
            </div>
            <div class="bg-slate-100/50 px-4 py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest border-y border-slate-200 mt-2">Acero de Refuerzo</div>
            <div class="divide-y divide-slate-100">
              <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div><div class="text-xs font-bold text-slate-800">Fuste (Cara Tierra)</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">Acero principal</div></div>
                <div class="text-right"><div class="text-sm font-black text-blue-600 bg-blue-50 px-2 py-1 rounded font-mono tracking-tight">{{ results.results.structural.reinforcement.stem_flexure.A_s_required.toFixed(1) }} cm²/m</div></div>
              </div>
              <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                <div><div class="text-xs font-bold text-slate-800">Talón (Superior)</div><div class="text-[10px] text-slate-400 font-medium mt-0.5">Por peso relleno</div></div>
                <div class="text-right"><div class="text-sm font-black text-blue-600 bg-blue-50 px-2 py-1 rounded font-mono tracking-tight">{{ results.results.structural.reinforcement.heel_flexure.A_s_required.toFixed(1) }} cm²/m</div></div>
              </div>
            </div>
          <div v-if="results && results.results && results.results.loads">
            <div class="bg-slate-100/50 px-4 py-2.5 text-[10px] font-black text-slate-500 uppercase tracking-widest border-y border-slate-200 mt-2">Cargas Actuantes (Sin Mayorar)</div>
            <div class="p-3 text-xs bg-slate-50 text-slate-600 leading-relaxed text-center italic border-b border-slate-200">
              Esquema de las fuerzas aplicadas por metro lineal.
            </div>
            <div class="divide-y divide-slate-100">
              <div v-for="(load, idx) in results.results.loads" :key="'ld'+idx" class="p-3 flex items-center justify-between hover:bg-white transition-colors">
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-[10px] font-black text-white bg-slate-700 px-1.5 py-0.5 rounded shadow-sm tracking-widest">{{ load.type }}</span>
                    <div class="text-[11px] font-bold text-slate-800">{{ load.name.replace('Empuje Activo Estático', 'Empuje (EH/PEA)').replace('Incremento Sísmico Dinámico', 'Sismo (PIR)') }}</div>
                  </div>
                  <div class="text-[10px] text-slate-400 font-medium mt-1">
                    Ap: x={{ load.x_app.toFixed(2) }}m, y={{ load.y_app.toFixed(2) }}m
                  </div>
                </div>
                <div class="text-right flex flex-col gap-1">
                  <div v-if="Math.abs(load.Fx) > 0.1" class="text-xs font-black text-indigo-600 font-mono tracking-tight bg-indigo-50 px-1.5 py-0.5 rounded">Fx: {{ load.Fx.toFixed(1) }} kN</div>
                  <div v-if="Math.abs(load.Fy) > 0.1" class="text-xs font-black text-emerald-600 font-mono tracking-tight bg-emerald-50 px-1.5 py-0.5 rounded">Fy: {{ load.Fy.toFixed(1) }} kN</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        </div>
      </aside>
    </main>
  </div>
</template>
