import { defineStore } from 'pinia'
import { calculateWallDesign, checkServerHealth } from '../services/api'
import { Shape } from 'three'

// Umbrales de seguridad (CCP-14 / AASHTO LRFD, Estado Límite de Resistencia)
export const THRESHOLDS = {
  slidingFS: 1.0,
  bearingFS: 3.0
}

export const useWallStore = defineStore('wall', {
  state: () => ({
    params: {
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
      phi_fill: 30.0,
      delta_fill: 20.0,
      beta_fill: 0.0,
      gamma_found: 20.0,
      phi_found: 35.0,
      q_allow: 300.0,
      
      // Loads
      q_surcharge: 10.0,
      kh: 0.0,

      // Sobrecarga vehicular (LS) - AASHTO Tabla 3.11.6.4
      traffic_orientation: 'PARALLEL', // 'PARALLEL' o 'PERPENDICULAR'
      traffic_distance: 0.0 // Distancia del eje de carga al respaldo del muro (m)
    },
    results: null,
    isLoading: false,
    error: null,
    serverOnline: null,
    viewMode: '2D'
  }),

  getters: {
    thresholds: () => THRESHOLDS,
    paramWarnings: (state) => {
      const p = state.params
      const warnings = []
      if (p.H <= 0) warnings.push('La altura del fuste (H) debe ser mayor a 0.')
      if (p.B <= 0) warnings.push('La base de la zapata (B) debe ser mayor a 0.')
      if (p.D_z <= 0) warnings.push('El espesor de zapata (Dz) debe ser mayor a 0.')
      if (p.L_toe <= 0) warnings.push('La longitud de punta (L_toe) debe ser mayor a 0.')
      if (p.stem_top <= 0) warnings.push('El espesor superior del fuste debe ser mayor a 0.')
      if (p.stem_bot <= 0) warnings.push('El espesor inferior del fuste debe ser mayor a 0.')
      if (p.fc <= 0) warnings.push("f'c debe ser mayor a 0.")
      if (p.fy <= 0) warnings.push('fy debe ser mayor a 0.')
      if (p.gamma_fill <= 0) warnings.push('El peso específico del relleno debe ser mayor a 0.')
      if (p.q_allow <= 0) warnings.push('La capacidad portante admisible debe ser mayor a 0.')
      const heel = p.B - p.L_toe - p.stem_bot
      if (heel <= 0) warnings.push('Geometría inválida: L_toe + espesor de fuste inferior debe ser menor que B (talón negativo).')
      return warnings
    },
        theta: (state) => {
      const dx = state.params.stem_top - state.params.stem_bot
      const dy = state.params.H
      let angle = Math.atan2(dy, dx) * 180 / Math.PI
      if (angle < 0) angle += 360
      return parseFloat(angle.toFixed(2))
    },
    geomPoints: (state) => {
      const H = state.params.H
      const B = state.params.B
      const Dz = state.params.D_z
      const L = state.params.L_toe
      const St = state.params.stem_top
      const Sb = state.params.stem_bot
      const Dd = state.params.D_d
      const Wd = state.params.W_d
      
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
    },
    threeShapes() {
      const createThreeShape = (pts) => {
        const shape = new Shape()
        shape.moveTo(pts[0], pts[1])
        for (let i = 2; i < pts.length; i += 2) {
          shape.lineTo(pts[i], pts[i+1])
        }
        return shape
      }
      
      const pts = this.geomPoints
      return {
        footing: createThreeShape(pts.footing),
        stem: createThreeShape(pts.stem),
        found: createThreeShape(pts.found),
        backfill: createThreeShape(pts.backfill),
        toeSoil: createThreeShape(pts.toeSoil),
        surcharge: createThreeShape(pts.surcharge)
      }
    }
  },

  actions: {
    async checkHealth() {
      this.serverOnline = await checkServerHealth()
    },
    async calculate() {
      if (this.isLoading) return
      this.isLoading = true
      this.error = null
      try {
        const payload = {
          name: 'Muro CCP-14',
          geometry: {
            stem_height_m: this.params.H,
            stem_thickness_base_m: this.params.stem_bot,
            stem_thickness_top_m: this.params.stem_top,
            footing_width_m: this.params.B,
            footing_thickness_m: this.params.D_z,
            toe_length_m: this.params.L_toe,
            heel_length_m: this.params.B - this.params.L_toe - this.params.stem_bot,
            toe_cover_soil_m: 0.0,
            key_depth_m: this.params.D_d,
            key_width_m: this.params.W_d,
            backfill_slope_deg: this.params.beta_fill,
            stem_batter_deg: 0.0,
            back_face_angle_deg: this.theta
          },
          materials: {
            concrete: { fc_MPa: this.params.fc, gamma_kN_m3: 24.0 },
            reinforcement: { fy_MPa: this.params.fy, Es_MPa: 200000.0 },
            cover_cm: 7.5
          },
          backfill: {
            name: 'Relleno',
            gamma_kN_m3: this.params.gamma_fill,
            phi_deg: this.params.phi_fill,
              interface_friction_deg: this.params.delta_fill,
            cohesion_kPa: 0.0
          },
          foundation_soil: {
            name: 'Fundación',
            gamma_kN_m3: this.params.gamma_found,
            phi_deg: this.params.phi_found,
            cohesion_kPa: 0.0,
            bearing_capacity_kPa: this.params.q_allow
          },
          traffic: {
            orientation: this.params.traffic_orientation,
            distance_from_back_m: this.params.traffic_distance
          },
          seismic: {
            kh: this.params.kh,
            kv: 0.0
          }
        }
        
        const data = await calculateWallDesign(payload)
        this.results = data
        this.serverOnline = true
      } catch (error) {
        console.error("Error en el cálculo:", error)
        if (error.response) {
          // El servidor respondió pero rechazó el cálculo (datos inválidos, error interno, etc.)
          this.serverOnline = true
          this.error = error.response.data?.detail || 'El servidor rechazó el cálculo. Revise los parámetros ingresados.'
        } else {
          // No hubo respuesta: backend caído o inalcanzable
          this.serverOnline = false
          this.error = 'No se pudo conectar con el servidor de cálculo. Verifique que el backend esté activo.'
        }
      } finally {
        this.isLoading = false
      }
    }
  }
})
