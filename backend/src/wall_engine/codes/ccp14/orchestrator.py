import math
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
        all_loads = self._generate_all_loads(wall)
        
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
                
            # Seleccionar la peor permutación para VOLCAMIENTO / EXCENTRICIDAD
            # Es decir, la que genere el mayor sum_moment
            worst_perm = max(perms, key=lambda p: p.sum_moment.magnitude)
            governing_loads[ls_name] = worst_perm
            
            # 3. Estabilidad
            stab = self.stab_calc.calculate(worst_perm, wall.geometry, wall.foundation_soil)
            stability_res[ls_name] = stab
            
            # 4. Portante
            bear = self.bear_calc.calculate(stab, worst_perm, wall.geometry, wall.foundation_soil)
            bearing_res[ls_name] = bear
            
            # 5. Cortante y Momento para Estructuras
            stem_force = self.stem_calc.calculate(all_loads, worst_perm.factors_used, wall.geometry, wall.materials.concrete, wall.materials.cover)
            foot_force = self.foot_calc.calculate(all_loads, worst_perm.factors_used, wall.geometry, wall.materials.concrete, wall.materials.cover, stab)
            
            stem_forces_dict[ls_name] = stem_force
            footing_forces_dict[ls_name] = foot_force
            
        # 6. Seleccionar Envolventes Críticas para Refuerzo
        # Típicamente Strength I gobierna diseño a flexión última.
        # Service I provee los momentos para control de fisuración.
        strength_stem = stem_forces_dict.get("Strength I")
        strength_foot = footing_forces_dict.get("Strength I")
        service_stem = stem_forces_dict.get("Service I")
        service_foot = footing_forces_dict.get("Service I")
        
        if strength_stem and service_stem:
            strength_stem.M_serv = service_stem.M_u
            strength_foot.toe.M_serv = service_foot.toe.M_u
            strength_foot.heel.M_serv = service_foot.heel.M_u
            if strength_foot.key:
                strength_foot.key.M_serv = service_foot.key.M_u
                
        # 7. Diseñar Refuerzo Final
        reinf = self.reinf_calc.calculate(
            stem_forces=strength_stem,
            footing_forces=strength_foot,
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
            status="DONE" # TODO: Lógica de validación
        )
        
    def _generate_all_loads(self, wall: Wall) -> List[GenericLoad]:
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
        pa = ep_res.soil_active_force
        ang = pa.angle_horizontal.to("radians").magnitude
        loads.append(GenericLoad(
            "Empuje Activo Estático", LoadType.EH,
            force_x=pa.magnitude * math.cos(ang),
            force_y=-pa.magnitude * math.sin(ang),
            x_application=wall.geometry.toe_length + wall.geometry.stem_thickness_base,
            y_application=pa.application_height
        ))
        
        # Sismo EQ (Empuje Dinámico)
        if ep_res.seismic_active_force and ep_res.seismic_active_force.magnitude > 0:
            peq = ep_res.seismic_active_force
            loads.append(GenericLoad(
                "Incremento Sísmico Dinámico", LoadType.EQ_E,
                force_x=peq.magnitude * math.cos(ang),
                force_y=-peq.magnitude * math.sin(ang),
                x_application=wall.geometry.toe_length + wall.geometry.stem_thickness_base,
                y_application=peq.application_height
            ))
            
        # Sismo EQ (Inercial)
        eq_inerts = self.weight_calc.calculate_seismic_inertial_loads(wall)
        loads.extend(eq_inerts)
        
        # Sobrecarga LS (Traffic Surcharge)
        if wall.seismic and getattr(wall.seismic, 'q_surcharge', 0) > 0:
            pass
            
        # The correct way to call the existing method is:
        if hasattr(ep_res, 'coefficient_active'):
            k_a = ep_res.coefficient_active
        else:
            k_a = 0.3 # fallback
            
        try:
            ls_loads = self.ls_calc.calculate_ls_load(wall, k_a=k_a)
            loads.extend(ls_loads)
        except Exception as e:
            print("Error computing LS: ", e)
        
        return loads
