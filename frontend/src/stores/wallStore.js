import { defineStore } from 'pinia'
import { calculateWallDesign, checkServerHealth } from '../services/api'
import { Shape } from 'three'

// Umbrales de seguridad (CCP-14 / AASHTO LRFD, Estado Límite de Resistencia)
export const THRESHOLDS = {
  nearLimit: 0.9  // relación D/C a partir de la cual se marca "cerca del límite"
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
      gamma_sat_fill: 20.0, // Peso saturado del relleno (bajo el nivel freático)
      gamma_found: 20.0,
      phi_found: 35.0,
      c_found: 0.0,            // Cohesión del suelo de fundación (kPa)
      qn_nominal: null,        // qn del estudio geotécnico (kPa); vacío = ecuación general
      toe_cover: 0.5,          // Relleno sobre la punta (m)
      cover_cm: 7.5,           // Recubrimiento del refuerzo (cm)
      gamma_c: 24.0,           // Peso unitario del concreto (kN/m³)
      
      // Loads
      q_surcharge: 10.0,

      // Sismo (CCP-14 11.6.5)
      kh_mode: 'DIRECT', // 'DIRECT' (kh dado) o 'PGA' (kh = Fpga·PGA, 11.6.5.2)
      kh: 0.0,
      pga: 0.25,
      site_class: 'D',
      fpga: null, // Opcional; si se deja vacío se toma de la Tabla 3.10.3.2-1
      allow_displacement: false, // Desplazamiento de 25-50 mm aceptable: kh = 0.5·kh0
      gamma_eq: 0.0, // Factor de LS en Evento Extremo I
      pae_height_ratio: 1 / 3, // Altura de la resultante de P_AE: H/3, 0.4H o 0.5H

      // Nivel freático
      gw_enabled: false,
      gw_elevation: 2.0, // Medido desde la base de la zapata (m)
      gw_drained: false, // Relleno con drenaje: sin presiones de agua
      gw_free_draining: false, // Relleno muy permeable: presión hidrodinámica en sismo

      // Sobrecarga vehicular (LS) - AASHTO Tabla 3.11.6.4
      traffic_orientation: 'PARALLEL', // 'PARALLEL' o 'PERPENDICULAR'
      traffic_distance: 0.0, // Distancia del eje de carga al respaldo del muro (m)

      // Criterios de diseño
      ignore_heel_reaction: false // Diseñar el talón sin la reacción del suelo (criterio CDOT)
    },
    projectName: 'Muro en voladizo 1',
    results: null,
    prevSummary: null,          // resumen del cálculo anterior, para mostrar qué cambió
    memoriaFocus: null,         // { state, kind } a mostrar en la memoria
    pendingCalc: false,
    isLoading: false,
    error: null,
    serverOnline: null,
    viewMode: '2D'  // '2D' | 'Esquema' | '3D' | 'Memoria'
  }),

  getters: {
    thresholds: () => THRESHOLDS,
    // Errores de validación por campo, para mostrarlos junto a cada entrada
    fieldErrors: (state) => {
      const p = state.params
      const e = {}
      const pos = (k, msg) => { if (!(p[k] > 0)) e[k] = msg }
      pos('H', 'Debe ser mayor que 0.')
      pos('B', 'Debe ser mayor que 0.')
      pos('D_z', 'Debe ser mayor que 0.')
      pos('L_toe', 'Debe ser mayor que 0.')
      pos('stem_top', 'Debe ser mayor que 0.')
      pos('stem_bot', 'Debe ser mayor que 0.')
      pos('fc', 'Debe ser mayor que 0.')
      pos('fy', 'Debe ser mayor que 0.')
      pos('gamma_fill', 'Debe ser mayor que 0.')
      pos('gamma_found', 'Debe ser mayor que 0.')
      pos('cover_cm', 'Debe ser mayor que 0.')
      pos('gamma_c', 'Debe ser mayor que 0.')
      if (p.stem_top > p.stem_bot) e.stem_top = 'La corona no puede ser más gruesa que la base del fuste.'
      if (p.B - p.L_toe - p.stem_bot <= 0) e.B = `El talón resulta negativo: B debe ser mayor que punta + fuste (${(p.L_toe + p.stem_bot).toFixed(2)} m).`
      if (p.D_d < 0) e.D_d = 'No puede ser negativa.'
      if (p.D_d > 0 && !(p.W_d > 0)) e.W_d = 'Indique el ancho del dentellón.'
      if (p.toe_cover < 0) e.toe_cover = 'No puede ser negativo.'
      if (!(p.phi_fill > 0 && p.phi_fill < 50)) e.phi_fill = 'Valor fuera de rango (0° a 50°).'
      if (!(p.phi_found > 0 && p.phi_found < 50)) e.phi_found = 'Valor fuera de rango (0° a 50°).'
      if (p.delta_fill > p.phi_fill) e.delta_fill = 'δ no debería superar a φ del relleno.'
      if (p.beta_fill >= p.phi_fill) e.beta_fill = 'β debe ser menor que φ del relleno.'
      if (p.gamma_sat_fill < p.gamma_fill) e.gamma_sat_fill = 'Debería ser mayor o igual al peso seco.'
      if (p.qn_nominal !== null && p.qn_nominal !== '' && !(p.qn_nominal > 0)) e.qn_nominal = 'Debe ser mayor que 0 o quedar vacío.'
      if (p.kh_mode === 'PGA' && !(p.pga > 0)) e.pga = 'Ingrese el PGA.'
      if (p.kh_mode === 'PGA' && p.site_class === 'F' && !(p.fpga > 0)) e.fpga = 'Perfil F: ingrese Fpga del estudio de respuesta de sitio.'
      if (p.kh_mode === 'DIRECT' && p.kh < 0) e.kh = 'No puede ser negativo.'
      if (p.kh > 0.6) e.kh = 'Valor inusualmente alto; revise.'
      if (p.gw_enabled && p.gw_elevation < 0) e.gw_elevation = 'No puede ser negativo.'
      return e
    },
    paramWarnings () {
      return Object.values(this.fieldErrors)
    },
    heelLength: (state) => state.params.B - state.params.L_toe - state.params.stem_bot,
    // El empuje se evalúa sobre el plano vertical que pasa por el talón: θ = 90°
    theta: () => 90,
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
    openMemoria(state, kind) {
      this.memoriaFocus = { state, kind, t: Date.now() }
      this.viewMode = 'Memoria'
    },
    async checkHealth() {
      this.serverOnline = await checkServerHealth()
    },
    async calculate() {
      // Si llega un cambio mientras se calcula, se recalcula al terminar (no se pierde)
      if (this.isLoading) { this.pendingCalc = true; return }
      const blocking = ['H', 'B', 'D_z', 'L_toe', 'stem_top', 'stem_bot', 'fc', 'fy', 'gamma_fill', 'gamma_found', 'cover_cm', 'gamma_c', 'W_d', 'pga', 'fpga']
        .filter(k => this.fieldErrors[k])
      if (blocking.length) {
        this.error = 'Corrija los campos marcados en rojo para calcular.'
        return
      }
      this.isLoading = true
      this.error = null
      try {
        const payload = {
          name: this.projectName,
          geometry: {
            stem_height_m: this.params.H,
            stem_thickness_base_m: this.params.stem_bot,
            stem_thickness_top_m: this.params.stem_top,
            footing_width_m: this.params.B,
            footing_thickness_m: this.params.D_z,
            toe_length_m: this.params.L_toe,
            heel_length_m: this.params.B - this.params.L_toe - this.params.stem_bot,
            toe_cover_soil_m: this.params.toe_cover,
            key_depth_m: this.params.D_d,
            key_width_m: this.params.W_d,
            backfill_slope_deg: this.params.beta_fill,
            stem_batter_deg: 0.0,
            back_face_angle_deg: this.theta
          },
          materials: {
            concrete: { fc_MPa: this.params.fc, gamma_kN_m3: this.params.gamma_c },
            reinforcement: { fy_MPa: this.params.fy, Es_MPa: 200000.0 },
            cover_cm: this.params.cover_cm
          },
          backfill: {
            name: 'Relleno',
            gamma_kN_m3: this.params.gamma_fill,
            phi_deg: this.params.phi_fill,
              interface_friction_deg: this.params.delta_fill,
            cohesion_kPa: 0.0,
            gamma_sat_kN_m3: this.params.gamma_sat_fill
          },
          foundation_soil: {
            name: 'Fundación',
            gamma_kN_m3: this.params.gamma_found,
            phi_deg: this.params.phi_found,
            cohesion_kPa: this.params.c_found,
            nominal_bearing_resistance_kPa: this.params.qn_nominal > 0 ? this.params.qn_nominal : null
          },
          traffic: {
            orientation: this.params.traffic_orientation,
            distance_from_back_m: this.params.traffic_distance
          },
          seismic: {
            kh_mode: this.params.kh_mode,
            kh: this.params.kh,
            kv: 0.0,
            pga: this.params.pga,
            site_class: this.params.site_class,
            fpga: this.params.fpga > 0 ? this.params.fpga : null,
            allow_displacement: this.params.allow_displacement,
            gamma_eq: this.params.gamma_eq,
            pae_height_ratio: this.params.pae_height_ratio
          },
          groundwater: this.params.gw_enabled ? {
            elevation_m: this.params.gw_elevation,
            drainage_enabled: this.params.gw_drained,
            free_draining_backfill: this.params.gw_free_draining
          } : null,
          design_options: {
            ignore_heel_soil_reaction: this.params.ignore_heel_reaction
          }
        }
        
        const data = await calculateWallDesign(payload)
        this.prevSummary = this.results?.results?.summary || null
        this.results = data
        // El bloque de sobrecarga del plano muestra el qs real de la sobrecarga vehicular
        this.params.q_surcharge = Math.round((data.results.traffic_surcharge?.qs_kPa || 0) * 10) / 10
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
        if (this.pendingCalc) { this.pendingCalc = false; this.calculate() }
      }
    }
  }
})
