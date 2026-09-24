<script setup>
import { useWallStore } from '../stores/wallStore'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { OrbitControls } from '@tresjs/cientos'

const store = useWallStore()

const threeShapes = computed(() => store.threeShapes)
const params = computed(() => store.params)

const mainCamera = ref(null)
const axesCamera = ref(null)
let rafId = null

const syncCameras = () => {
  if (mainCamera.value && axesCamera.value) {
    axesCamera.value.quaternion.copy(mainCamera.value.quaternion)
    axesCamera.value.position.set(0, 0, 5)
    axesCamera.value.position.applyQuaternion(axesCamera.value.quaternion)
  }
  rafId = requestAnimationFrame(syncCameras)
}

onMounted(() => {
  rafId = requestAnimationFrame(syncCameras)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
})

const surchargeArrows3D = computed(() => {
  if (params.value.q_surcharge <= 0) return []
  const L = params.value.L_toe
  const St = params.value.stem_top
  const B = params.value.B
  const ext = 4 
  const startX = L + St
  const endX = B + ext
  const y = params.value.D_z + params.value.H
  
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
</script>

<template>
  <div class="w-full h-full absolute inset-0 bg-sky-50 pointer-events-auto cursor-grab active:cursor-grabbing">
    <!-- MAIN CANVAS -->
    <TresCanvas clear-color="#f0f9ff" shadows>
      <TresPerspectiveCamera ref="mainCamera" :position="[12, 10, 15]" :look-at="[0, 2, 0]" />
      <OrbitControls />
      <TresAmbientLight :intensity="0.8" color="#ffffff" />
      <TresDirectionalLight :position="[15, 20, 10]" :intensity="1.2" cast-shadow color="#fdfbf7" />
      <TresFog color="#f0f9ff" :near="15" :far="60" />
      
      <TresGroup :position="[-params.B/2, 0, -2.5]" v-if="threeShapes">
        <TresMesh cast-shadow receive-shadow>
          <TresExtrudeGeometry :args="[threeShapes.footing, { depth: 5, bevelEnabled: false }]" />
          <TresMeshStandardMaterial color="#a3a3a3" roughness="0.9" metalness="0.1" />
        </TresMesh>
        
        <TresMesh cast-shadow receive-shadow>
          <TresExtrudeGeometry :args="[threeShapes.stem, { depth: 5, bevelEnabled: false }]" />
          <TresMeshStandardMaterial color="#d4d4d4" roughness="0.85" metalness="0.1" />
        </TresMesh>

        <TresMesh receive-shadow>
          <TresExtrudeGeometry :args="[threeShapes.found, { depth: 5, bevelEnabled: false }]" />
          <TresMeshStandardMaterial color="#8c7b68" roughness="1.0" />
        </TresMesh>

        <TresMesh receive-shadow cast-shadow>
          <TresExtrudeGeometry :args="[threeShapes.backfill, { depth: 5, bevelEnabled: false }]" />
          <TresMeshStandardMaterial color="#d1bfae" roughness="1.0" />
        </TresMesh>

        <TresMesh receive-shadow cast-shadow>
          <TresExtrudeGeometry :args="[threeShapes.toeSoil, { depth: 5, bevelEnabled: false }]" />
          <TresMeshStandardMaterial color="#8c7b68" roughness="1.0" />
        </TresMesh>

        <TresGroup v-if="params.q_surcharge > 0">
          <TresMesh receive-shadow>
            <TresExtrudeGeometry :args="[threeShapes.surcharge, { depth: 5, bevelEnabled: false }]" />
            <TresMeshStandardMaterial color="#ef4444" opacity="0.3" transparent depth-write="false" />
          </TresMesh>
          <TresGroup v-for="(pos, idx) in surchargeArrows3D" :key="'arr3d'+idx" :position="[pos.x, pos.y, pos.z]">
            <TresMesh :position="[0, 0.35, 0]" cast-shadow>
              <TresCylinderGeometry :args="[0.03, 0.03, 0.3]" />
              <TresMeshStandardMaterial color="#ef4444" />
            </TresMesh>
            <TresMesh :position="[0, 0.1, 0]" :rotation="[Math.PI, 0, 0]" cast-shadow>
              <TresConeGeometry :args="[0.08, 0.2]" />
              <TresMeshStandardMaterial color="#ef4444" />
            </TresMesh>
          </TresGroup>
        </TresGroup>
      </TresGroup>

      <TresMesh :position="[0, -2.05, 0]" :rotation="[-Math.PI / 2, 0, 0]" receive-shadow>
        <TresPlaneGeometry :args="[80, 80]" />
        <TresMeshStandardMaterial color="#e2e8f0" roughness="1.0" />
      </TresMesh>
    </TresCanvas>

    <!-- AXES HELPER (BOTTOM LEFT) -->
    <div class="absolute bottom-2 left-2 w-48 h-48 pointer-events-none z-10 flex items-center justify-center">
      <TresCanvas alpha :clear-alpha="0">
        <TresPerspectiveCamera ref="axesCamera" :position="[0, 0, 5]" :look-at="[0, 0, 0]" />
        <TresAmbientLight :intensity="1.5" />
        <TresDirectionalLight :position="[5, 5, 5]" :intensity="1" />
        
        <TresGroup :scale="[1.3, 1.3, 1.3]">
          <!-- X Axis (Red) -->
          <TresGroup>
            <TresMesh :position="[0.6, 0, 0]" :rotation="[0, 0, -Math.PI / 2]">
              <TresCylinderGeometry :args="[0.05, 0.05, 1.2]" />
              <TresMeshStandardMaterial color="#ef4444" />
            </TresMesh>
            <TresMesh :position="[1.3, 0, 0]" :rotation="[0, 0, -Math.PI / 2]">
              <TresConeGeometry :args="[0.15, 0.4]" />
              <TresMeshStandardMaterial color="#ef4444" />
            </TresMesh>
          </TresGroup>

          <!-- Y Axis (Green) -->
          <TresGroup>
            <TresMesh :position="[0, 0.6, 0]">
              <TresCylinderGeometry :args="[0.05, 0.05, 1.2]" />
              <TresMeshStandardMaterial color="#22c55e" />
            </TresMesh>
            <TresMesh :position="[0, 1.3, 0]">
              <TresConeGeometry :args="[0.15, 0.4]" />
              <TresMeshStandardMaterial color="#22c55e" />
            </TresMesh>
          </TresGroup>

          <!-- Z Axis (Blue) -->
          <TresGroup>
            <TresMesh :position="[0, 0, 0.6]" :rotation="[Math.PI / 2, 0, 0]">
              <TresCylinderGeometry :args="[0.05, 0.05, 1.2]" />
              <TresMeshStandardMaterial color="#3b82f6" />
            </TresMesh>
            <TresMesh :position="[0, 0, 1.3]" :rotation="[Math.PI / 2, 0, 0]">
              <TresConeGeometry :args="[0.15, 0.4]" />
              <TresMeshStandardMaterial color="#3b82f6" />
            </TresMesh>
          </TresGroup>
          
          <!-- Center Sphere -->
          <TresMesh>
            <TresSphereGeometry :args="[0.1]" />
            <TresMeshStandardMaterial color="#333333" />
          </TresMesh>
        </TresGroup>
      </TresCanvas>
    </div>
  </div>
</template>
