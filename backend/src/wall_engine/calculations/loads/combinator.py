import itertools
from typing import List, Dict
from wall_engine.units.registry import Q_
from wall_engine.domain.loads.combinations import LimitState, GenericLoad, FactoredResult, LoadType

class CombinationEngine:
    
    def generate_permutations(
        self,
        loads: List[GenericLoad],
        limit_state: LimitState
    ) -> List[FactoredResult]:
        
        # Encontrar los LoadTypes únicos presentes en las cargas proporcionadas
        present_types = {load.load_type for load in loads}
        
        # Filtrar solo los tipos que tienen factores definidos en este LimitState
        valid_types = [t for t in present_types if t in limit_state.factors]
        
        if not valid_types:
            return []
            
        # Preparar las opciones de factores (max, min) para cada tipo de carga
        # Utilizamos set() para no duplicar si gamma_max == gamma_min
        factor_options_by_type = {}
        for t in valid_types:
            lf = limit_state.factors[t]
            factor_options_by_type[t] = list({lf.gamma_max, lf.gamma_min})
            
        # Generar producto cartesiano de todas las combinaciones de factores
        # factor_options_by_type.values() nos da una lista de listas de opciones
        # ej: [[1.25, 0.9], [1.35, 1.0], [1.5, 0.9]]
        keys = list(factor_options_by_type.keys())
        options_lists = [factor_options_by_type[k] for k in keys]
        
        permutations = list(itertools.product(*options_lists))
        
        results = []
        for i, perm in enumerate(permutations):
            # perm es una tupla de factores correspondientes a 'keys'
            # ej: (1.25, 1.35, 1.5)
            current_factors = dict(zip(keys, perm))
            
            # Inicializar acumuladores
            # Los inicializamos con las unidades base a cero
            sum_fx = Q_(0.0, "kN/m")
            sum_fy = Q_(0.0, "kN/m")
            sum_m = Q_(0.0, "kN*m/m") # Unidades típicas para momento por ancho unitario
            
            # Aplicar factores a cada carga
            for load in loads:
                if load.load_type in current_factors:
                    gamma = current_factors[load.load_type]
                    
                    sum_fx += load.force_x * gamma
                    sum_fy += load.force_y * gamma
                    sum_m += load.overturning_moment * gamma
                    
            results.append(FactoredResult(
                limit_state_name=limit_state.name,
                permutation_id=i+1,
                sum_force_x=sum_fx,
                sum_force_y=sum_fy,
                sum_moment=sum_m,
                factors_used=current_factors
            ))
            
        return results
