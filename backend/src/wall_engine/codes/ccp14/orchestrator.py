import math
from dataclasses import replace
from typing import Dict, List
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.entities import Wall
from wall_engine.domain.loads.combinations import GenericLoad, LoadType, LimitState, FactoredResult
from wall_engine.domain.results.report import WallDesignReport
from wall_engine.calculations.earth_pressure.mononobe_okabe import MononobeOkabeEarthPressure
from wall_engine.calculations.loads.weight_calculator import WeightCalculator
from wall_engine.calculations.loads.surcharge_calculator import LSSurchargeCalculator
from wall_engine.calculations.loads.combinator import CombinationEngine
from wall_engine.calculations.stability.calculator import StabilityCalculator
from wall_engine.calculations.foundation.bearing_capacity import BearingCapacityCalculator
from wall_engine.calculations.structural.stem_calculator import StemCalculator
from wall_engine.calculations.structural.footing_calculator import FootingCalculator
from wall_engine.calculations.structural.reinforcement_calculator import ReinforcementCalculator
from wall_engine.codes.ccp14.combinations import CCP14Combinations
from wall_engine.domain.results.stem_design import StemForcesResult
from wall_engine.domain.results.footing_design import FootingDesignResult, FootingSectionForces

class CCP14Orchestrator:
    def __init__(self):
        self.ep_calc = MononobeOkabeEarthPressure()
        self.weight_calc = WeightCalculator()
        self.ls_calc = LSSurchargeCalculator()
        self.combinator = CombinationEngine()
        self.stab_calc = StabilityCalculator()
        self.bear_calc = BearingCapacityCalculator()
        self.stem_calc = StemCalculator()
        self.foot_calc = FootingCalculator()
        self.reinf_calc = ReinforcementCalculator()

    def design_wall(self, wall: Wall) -> WallDesignReport:
        # 1. Generar todas las cargas genéricas
        all_loads, ep_res, traffic_heq_m, traffic_qs_kPa = self._generate_all_loads(wall)
        # Cargas que actúan sobre el fuste (presiones evaluadas con la altura del fuste)
        stem_loads = self._generate_stem_loads(wall, all_loads, ep_res.coefficient_active, traffic_qs_kPa)
        
        # 2. Generar combinaciones y permutaciones
        limit_states = CCP14Combinations.get_all()
        governing_loads = {}
        stability_res = {}
        bearing_res = {}
        
        stem_forces_dict = {}
        footing_forces_dict = {}
        
        for ls_name, ls in limit_states.items():
            perms = self.combinator.generate_permutations(all_loads, ls)
            if not perms:
                continue
                
            # 3. Estabilidad de cada permutación. Cada verificación la gobierna
            # una permutación distinta (AASHTO C11.5.6):
            #  - Excentricidad: la mayor |e| (verticales mínimas, horizontales máximas)
            #  - Deslizamiento: la mayor relación demanda/capacidad
            #  - Presión de contacto: la mayor presión (verticales máximas)
            evaluated = [
                (perm, self.stab_calc.calculate(perm, wall.geometry, wall.foundation_soil))
                for perm in perms
            ]
            ecc_perm, ecc_stab = max(evaluated, key=lambda ps: abs(ps[1].eccentricity.to("m").magnitude))
            _, slide_stab = max(evaluated, key=lambda ps: ps[1].sliding_ratio)
            _, bear_stab = max(evaluated, key=lambda ps: max(ps[1].q_toe, ps[1].q_heel))
            
            governing_loads[ls_name] = ecc_perm
            stability_res[ls_name] = replace(
                ecc_stab,
                sliding_demand=slide_stab.sliding_demand,
                sliding_capacity=slide_stab.sliding_capacity,
                sliding_ratio=slide_stab.sliding_ratio,
                q_toe=bear_stab.q_toe,
                q_heel=bear_stab.q_heel
            )
            
            # 4. Portante: estados de resistencia y evento extremo (en servicio se
            # revisan asentamientos, no resistencia). Gobierna la mayor relación
            # demanda / resistencia entre las permutaciones.
            if ls_name != "Service I":
                embedment = (wall.geometry.toe_cover_soil + wall.geometry.footing_thickness).to("m").magnitude
                bearing_res[ls_name] = max(
                    (self.bear_calc.calculate(stab, perm, wall.geometry, wall.foundation_soil, embedment)
                     for perm, stab in evaluated),
                    key=lambda br: br.bearing_ratio
                )
            
            # 5. Cortante y Momento para Estructuras: envolvente de todas las permutaciones
            stem_candidates = []
            footing_candidates = []
            for perm, stab in evaluated:
                stem_candidates.append(self.stem_calc.calculate(
                    stem_loads, perm.factors_used, wall.geometry, wall.materials.concrete, wall.materials.cover))
                footing_candidates.append(self.foot_calc.calculate(
                    all_loads, perm.factors_used, wall.geometry, wall.materials.concrete, wall.materials.cover, stab,
                    wall.foundation_soil, wall.options.ignore_heel_soil_reaction))
            
            stem_forces_dict[ls_name] = _envelope_stem(stem_candidates)
            footing_forces_dict[ls_name] = _envelope_footing(footing_candidates)
            
        # 6. Envolvente de diseño: estados de resistencia y evento extremo.
        # Service I provee los momentos para control de fisuración.
        design_states = [n for n in ("Strength I", "Strength IV", "Extreme Event I") if n in stem_forces_dict]
        design_stem = _envelope_stem([stem_forces_dict[n] for n in design_states])
        design_foot = _envelope_footing([footing_forces_dict[n] for n in design_states])
        service_stem = stem_forces_dict.get("Service I")
        service_foot = footing_forces_dict.get("Service I")
        
        if service_stem and service_foot:
            design_stem.M_serv = service_stem.M_u
            design_foot.toe.M_serv = service_foot.toe.M_u
            design_foot.heel.M_serv = service_foot.heel.M_u
            if design_foot.key and service_foot.key:
                design_foot.key.M_serv = service_foot.key.M_u
                
        # 7. Diseñar Refuerzo Final
        reinf = self.reinf_calc.calculate(
            stem_forces=design_stem,
            footing_forces=design_foot,
            geometry=wall.geometry,
            concrete=wall.materials.concrete,
            steel=wall.materials.reinforcement,
            cover=wall.materials.cover
        )
        
        # 8. Generar Reporte
        return WallDesignReport(
            wall_id=wall.id,
            wall_name=wall.name,
            unfactored_loads=all_loads,
            governing_loads=governing_loads,
            stability_results=stability_res,
            bearing_results=bearing_res,
            structural_design=reinf,
            status="DONE", # TODO: Lógica de validación
            earth_pressure=ep_res,
            traffic_heq_m=traffic_heq_m,
            traffic_qs_kPa=traffic_qs_kPa
        )
        
    def _generate_all_loads(self, wall: Wall):
        loads = []
        # Pesos
        c_blocks = self.weight_calc.calculate_concrete_blocks(wall)
        s_blocks = self.weight_calc.calculate_soil_blocks(wall)
        for b in c_blocks:
            loads.append(GenericLoad(b.name, LoadType.DC, Q_(0, "kN/m"), b.weight, b.x_centroid, b.y_centroid))
        for b in s_blocks:
            loads.append(GenericLoad(b.name, LoadType.EV, Q_(0, "kN/m"), b.weight, b.x_centroid, b.y_centroid))
            
        # Empujes EH
        ep_res = self.ep_calc.calculate(wall.backfill, wall.geometry, wall.seismic)
        # El empuje actúa sobre el plano virtual vertical en el extremo del talón
        # (x = B), con altura total medida desde la base de la zapata. Su componente
        # vertical va hacia abajo (force_y > 0) y es estabilizante.
        pa = ep_res.soil_active_force
        ang = pa.angle_horizontal.to("radians").magnitude
        x_virtual_back = wall.geometry.footing_width
        loads.append(GenericLoad(
            "Empuje Activo Estático", LoadType.EH,
            force_x=pa.magnitude * math.cos(ang),
            force_y=pa.magnitude * math.sin(ang),
            x_application=x_virtual_back,
            y_application=pa.application_height
        ))
        
        # Sismo EQ (Empuje Dinámico)
        if ep_res.seismic_active_force and ep_res.seismic_active_force.magnitude > 0:
            peq = ep_res.seismic_active_force
            loads.append(GenericLoad(
                "Incremento Sísmico Dinámico", LoadType.EQ_E,
                force_x=peq.magnitude * math.cos(ang),
                force_y=peq.magnitude * math.sin(ang),
                x_application=x_virtual_back,
                y_application=peq.application_height
            ))
            
        # Sismo EQ (Inercial)
        eq_inerts = self.weight_calc.calculate_seismic_inertial_loads(wall)
        loads.extend(eq_inerts)
        
        # Sobrecarga LS (Traffic Surcharge) - AASHTO Tabla 3.11.6.4
        if hasattr(ep_res, 'coefficient_active'):
            k_a = ep_res.coefficient_active
        else:
            k_a = 0.3 # fallback

        traffic_heq_m = 0.0
        traffic_qs_kPa = 0.0
        try:
            ls_loads, traffic_heq_m, traffic_qs_kPa = self.ls_calc.calculate_ls_load(wall, k_a=k_a)
            loads.extend(ls_loads)
        except Exception as e:
            print("Error computing LS: ", e)

        return loads, ep_res, traffic_heq_m, traffic_qs_kPa

    def _generate_stem_loads(self, wall: Wall, all_loads: List[GenericLoad], k_a: float, traffic_qs_kPa: float) -> List[GenericLoad]:
        """
        Cargas horizontales que actúan sobre el fuste, para su diseño estructural.
        Los empujes se evalúan con la altura del fuste (sin zapata) sobre su cara
        trasera; las alturas de aplicación se expresan desde la base de la zapata.
        """
        geom = wall.geometry
        t_f = geom.footing_thickness
        h_stem = geom.stem_height
        x_back = geom.toe_length + geom.stem_thickness_base
        
        groundwater = wall.groundwater
        if groundwater is not None:
            groundwater = replace(groundwater, elevation=groundwater.elevation - t_f)
        
        ep_stem = self.ep_calc.calculate(wall.backfill, geom, wall.seismic,
                                         groundwater=groundwater, retained_height=h_stem)
        loads = []
        
        pa = ep_stem.soil_active_force
        ang = pa.angle_horizontal.to("radians").magnitude
        loads.append(GenericLoad(
            "Empuje Activo sobre Fuste", LoadType.EH,
            force_x=pa.magnitude * math.cos(ang),
            force_y=Q_(0, "kN/m"),
            x_application=x_back,
            y_application=t_f + pa.application_height
        ))
        
        peq = ep_stem.seismic_active_force
        if peq and peq.magnitude.magnitude > 0:
            loads.append(GenericLoad(
                "Incremento Sísmico sobre Fuste", LoadType.EQ_E,
                force_x=peq.magnitude * math.cos(ang),
                force_y=Q_(0, "kN/m"),
                x_application=x_back,
                y_application=t_f + peq.application_height
            ))
        
        if traffic_qs_kPa > 0:
            h_stem_m = h_stem.to("m").magnitude
            loads.append(GenericLoad(
                "Sobrecarga Vehicular sobre Fuste (LS)", LoadType.LS,
                force_x=Q_(traffic_qs_kPa * k_a * h_stem_m, "kN/m"),
                force_y=Q_(0, "kN/m"),
                x_application=x_back,
                y_application=t_f + h_stem / 2
            ))
        
        # Inercia del propio fuste (no la del suelo sobre el talón o la punta)
        loads.extend(ld for ld in all_loads if ld.load_type == LoadType.EQ_I and "Stem" in ld.name)
        return loads


def _envelope_stem(results: List[StemForcesResult]) -> StemForcesResult:
    """Envolvente: máximos V_u y M_u entre varios resultados del fuste."""
    vu = max(r.V_u.to("kN/m").magnitude for r in results)
    mu = max(r.M_u.to("kN*m/m").magnitude for r in results)
    ms = max(r.M_serv.to("kN*m/m").magnitude for r in results)
    ref = results[0]
    return StemForcesResult(
        V_u=Q_(vu, "kN/m"),
        M_u=Q_(mu, "kN*m/m"),
        M_serv=Q_(ms, "kN*m/m"),
        V_c=ref.V_c,
        phi_V_c=ref.phi_V_c,
        is_shear_safe=vu <= ref.phi_V_c.to("kN/m").magnitude
    )


def _envelope_section(sections: List[FootingSectionForces]) -> FootingSectionForces:
    vu = max(s.V_u.to("kN/m").magnitude for s in sections)
    mu = max(s.M_u.to("kN*m/m").magnitude for s in sections)
    ms = max(s.M_serv.to("kN*m/m").magnitude for s in sections)
    ref = sections[0]
    return FootingSectionForces(
        V_u=Q_(vu, "kN/m"),
        M_u=Q_(mu, "kN*m/m"),
        M_serv=Q_(ms, "kN*m/m"),
        V_c=ref.V_c,
        phi_V_c=ref.phi_V_c,
        is_shear_safe=vu <= ref.phi_V_c.to("kN/m").magnitude
    )


def _envelope_footing(results: List[FootingDesignResult]) -> FootingDesignResult:
    """Envolvente: máximos V_u y M_u por sección (punta, talón, dentellón)."""
    keys = [r.key for r in results if r.key is not None]
    return FootingDesignResult(
        toe=_envelope_section([r.toe for r in results]),
        heel=_envelope_section([r.heel for r in results]),
        key=_envelope_section(keys) if keys else None
    )
