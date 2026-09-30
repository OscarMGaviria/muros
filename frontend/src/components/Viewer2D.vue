<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWallStore } from '../stores/wallStore'

const store = useWallStore()

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
    fitToScreen()
  }
}

const fitToScreen = () => {
  if (!containerRef.value) return

  // Geometry boundaries based on unified logic (ext = 4)
  const ext = 4
  const scale = 50
  const B = store.params.B
  const H = store.params.H
  const Dz = store.params.D_z
  const depth = 2
  
  // Base dimensions in Konva units (scale = 50)
  // X ranges from -ext to B + ext
  const minX = -ext * scale
  const maxX = (B + ext) * scale
  const drawWidth = maxX - minX
  
  // Y ranges from -depth to Dz + H (but Y is inverted visually because canvas Y goes down, 
  // and we mapped y -> -y * scale for stem etc., except footing uses positive scale? 
  // Wait, in scale2D: idx % 2 === 0 ? val * scale : -val * scale.
  // So Y coordinates: depth is at -depth -> Y = depth * scale (bottom)
  // top of stem is at Dz + H -> Y = -(Dz + H) * scale (top)
  const minY = -(Dz + H) * scale - 100 // Add some padding for dimensions at the top
  const maxY = depth * scale + 50 // Padding for dimensions at bottom
  const drawHeight = maxY - minY
  
  const stageW = stageConfig.value.width
  const stageH = stageConfig.value.height
  
  // Calculate scale to fit with 10% padding
  const padding = 0.1
  const availableW = stageW * (1 - padding * 2)
  const availableH = stageH * (1 - padding * 2)
  
  const scaleFitX = availableW / drawWidth
  const scaleFitY = availableH / drawHeight
  const newScale = Math.min(scaleFitX, scaleFitY)
  
  stageConfig.value.scaleX = newScale
  stageConfig.value.scaleY = newScale
  
  // Center it
  const centerX = minX + drawWidth / 2
  const centerY = minY + drawHeight / 2
  
  stageConfig.value.x = stageW / 2 - centerX * newScale
  stageConfig.value.y = stageH / 2 - centerY * newScale
}

watch(() => store.params, () => {
  fitToScreen()
}, { deep: true })

const handleWheel = (e) => {
  if (!e.evt) return; // Ignore native DOM events bubbling from div
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
  store.calculate()
  window.addEventListener('resize', handleResize)
  setTimeout(handleResize, 100) // initial measure
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

import { Shape } from 'three'

// ---- UNIFIED GEOMETRY LOGIC (Meters, Y points UP) ----
const geomPoints = computed(() => {
  const H = store.params.H
  const B = store.params.B
  const Dz = store.params.D_z
  const L = store.params.L_toe
  const St = store.params.stem_top
  const Sb = store.params.stem_bot
  const Dd = store.params.D_d
  const Wd = store.params.W_d
  
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
    footing: createThreeShape(store.geomPoints.footing),
    stem: createThreeShape(store.geomPoints.stem),
    found: createThreeShape(store.geomPoints.found),
    backfill: createThreeShape(store.geomPoints.backfill),
    toeSoil: createThreeShape(store.geomPoints.toeSoil),
    surcharge: createThreeShape(store.geomPoints.surcharge)
  }
})

const invScale = computed(() => 1 / (stageConfig.value?.scaleX || 1))

const surchargeArrows2D = computed(() => {
  const L = store.params.L_toe * scale
  const St = store.params.stem_top * scale
  const B = store.params.B * scale
  const ext = 4 * scale
  
  const startX = L + St
  const endX = B + ext
  const Y = -store.params.D_z * scale - store.params.H * scale
  
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

const scale = 50
const scale2D = (pts) => {
  return pts.map((val, idx) => idx % 2 === 0 ? val * scale : -val * scale)
}

const footingPoints2D = computed(() => scale2D(store.geomPoints.footing))
const stemPoints2D = computed(() => scale2D(store.geomPoints.stem))
const foundationSoilPoints2D = computed(() => scale2D(store.geomPoints.found))
const heelSoilPoints2D = computed(() => scale2D(store.geomPoints.backfill))
const toeSoilPoints2D = computed(() => scale2D(store.geomPoints.toeSoil))

const dimensions2D = computed(() => {
  const L = store.params.L_toe * scale
  const St = store.params.stem_top * scale
  const Sb = store.params.stem_bot * scale
  const B = store.params.B * scale
  const H = store.params.H * scale
  const Dz = store.params.D_z * scale
  const Dd = store.params.D_d * scale
  const Wd = store.params.W_d * scale
  
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
  dims.push(addDim(0, 0, B, 0, `B = ${store.params.B.toFixed(2)}m`, 60, false))
  
  // 2. Altura Total fuste (H) - Izquierda
  dims.push(addDim(L, -Dz, L, -Dz - H, `H = ${store.params.H.toFixed(2)}m`, -80, true))
  
  // 3. Zapata (Dz) - Derecha
  dims.push(addDim(B, 0, B, -Dz, `Dz = ${store.params.D_z.toFixed(2)}m`, 60, true))
  
  // 4. Punta (L_toe) - Arriba de la punta
  dims.push(addDim(0, -Dz, L, -Dz, `Punta = ${store.params.L_toe.toFixed(2)}m`, -30, false))
  
  // 5. Dentellón (Dd) - Abajo
  if (store.params.D_d > 0) {
    dims.push(addDim(L + Wd, 0, L + Wd, Dd, `Dd = ${store.params.D_d.toFixed(2)}m`, 40, true))
    dims.push(addDim(L, Dd, L + Wd, Dd, `${store.params.W_d.toFixed(2)}m`, 20, false))
  }

  // 6. Fuste Base (Sb) y Corona (St)
  dims.push(addDim(L, -Dz, L + Sb, -Dz, `Sb = ${store.params.stem_bot.toFixed(2)}m`, -60, false))
  dims.push(addDim(L, -Dz - H, L + St, -Dz - H, `St = ${store.params.stem_top.toFixed(2)}m`, -30, false))

  return dims
})

const actingLoads2D = computed(() => {
  if (!store.results || !store.results.results || !store.results.results.loads) return []
  
  let loads = store.results.results.loads.filter(l => !l.type.includes('DC') && !l.type.includes('EV'))
  if (store.viewMode === 'Esquema') {
    return [] // Hide resultant arrows in Esquema mode
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
      // Convención del motor: Fy > 0 hacia abajo (pesos), Fy < 0 hacia arriba (subpresión)
      startY = load.Fy < 0 ? cy + arrowLength : cy - arrowLength
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
  if (!store.results || !store.results.results || !store.results.results.loads) return []
  
  const H_total = store.params.H + store.params.D_z
  const B = store.params.B
  const Dz = store.params.D_z
  
  // Constant schematic width
  const w = 1.2 * scale
  
  const diagrams = []
  const loads = store.results.results.loads
  
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
      textMax: `EH = ${p_max.toFixed(1)} kPa`,
      textX: (B * scale) + w/2 - 25,
      textY: -Dz * scale + 15,
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
      textMax: `PIR = ${p_top.toFixed(1)} kPa`,
      textX: (B * scale) + w/2 - 25,
      textY: -Dz * scale + 15,
      arrows: getHArrows(-Dz * scale, -(H_total) * scale, 0, w, B * scale)
    })
  }

  // LS (Sobrecarga viva) - Rectángulo
  const lsLoad = loads.find(l => l.type === 'LS')
  if (lsLoad || store.params.q_surcharge > 0) {
    const Fx = lsLoad ? lsLoad.Fx : (store.params.q_surcharge * 0.33 * H_total)
    const p = Fx / H_total
    const xBaseLS = ehLoad ? (B * scale) + w : B * scale
    diagrams.push({
      name: 'LS',
      points: [xBaseLS, -Dz * scale, xBaseLS, -(H_total) * scale, xBaseLS + w, -(H_total) * scale, xBaseLS + w, -Dz * scale],
      fill: 'rgba(239, 68, 68, 0.15)',
      stroke: '#ef4444',
      textMax: `LS = ${p.toFixed(1)} kPa`,
      textX: xBaseLS + w + 10,
      textY: -(store.params.D_z + store.params.H / 2) * scale,
      arrows: getHArrows(-Dz * scale, -(H_total) * scale, w, w, xBaseLS)
    })
  }
  
  // Reacción del suelo (Bearing) - Trapecio bajo la zapata
  const bearing = store.results.results.stability?.bearing
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
      textMax: `${q_max.toFixed(0)} kPa`,
      textMin: `${q_min.toFixed(0)} kPa`,
      textMaxX: -30,
      textMaxY: w_max + 10,
      textMinX: B * scale + 10,
      textMinY: w_min + 10,
      arrows: getVArrows(0, B * scale, w_max, w_min, 0)
    })
  }
  
  return diagrams
})

// --------------------------------

</script>

<template>
<div ref="containerRef" class="w-full h-full absolute inset-0 cursor-grab active:cursor-grabbing" @wheel="handleWheel">
          <v-stage ref="stageRef" :config="stageConfig" @wheel="handleWheel">
            <v-layer>
              <!-- Grupo centralizado por el stage -->
              <v-group>
                
                <!-- Only show soils in 2D mode, hide in Esquema -->
                <v-group v-if="store.viewMode === '2D'">
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
                <v-group v-if="store.viewMode === '2D'">
                  <!-- Surcharge (Sobrecarga) -->
                  <v-group v-if="store.params.q_surcharge > 0">
                    <v-arrow v-for="(pts, i) in surchargeArrows2D.arrows" :key="'arr'+i" :config="{
                      points: pts,
                      pointerLength: 8 * invScale,
                      pointerWidth: 8 * invScale,
                      fill: '#ef4444',
                      stroke: '#ef4444',
                      strokeWidth: 2 * invScale
                    }" />
                    <v-text :config="{ x: surchargeArrows2D.textX - 20 * invScale, y: surchargeArrows2D.textY, text: 'q = ' + store.params.q_surcharge + ' kPa', fontSize: 14 * invScale, fill: '#ef4444', fontStyle: 'bold' }" />
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
              <v-group v-if="store.viewMode === 'Esquema'">
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
                    x: diag.textMaxX !== undefined ? diag.textMaxX : diag.textX,
                    y: diag.textMaxY !== undefined ? diag.textMaxY : diag.textY,
                    text: diag.textMax,
                    fontSize: 12 * invScale,
                    fill: diag.stroke,
                    fontStyle: 'bold',
                    fontFamily: 'JetBrains Mono'
                  }" />
                  <v-text v-if="diag.textMin" :config="{
                    x: diag.textMinX !== undefined ? diag.textMinX : diag.textX,
                    y: diag.textMinY !== undefined ? diag.textMinY : diag.textY,
                    text: diag.textMin,
                    fontSize: 12 * invScale,
                    fill: diag.stroke,
                    fontStyle: 'bold',
                    fontFamily: 'JetBrains Mono'
                  }" />
                </v-group>
              </v-group>

              <!-- Resultant Loads (show in 2D and Esquema) -->
              <v-group v-if="store.viewMode !== '3D'">
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

</template>
