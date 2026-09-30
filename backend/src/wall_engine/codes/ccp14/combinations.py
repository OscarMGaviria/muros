from typing import Dict
from wall_engine.domain.loads.combinations import LimitState, LoadType, LoadFactor

# Presión de agua (Tabla 3.4.1-1): 1.00 en Resistencia, Servicio y Evento Extremo I
_WA = LoadFactor(gamma_max=1.00, gamma_min=1.00)


class CCP14Combinations:
    @staticmethod
    def strength_I() -> LimitState:
        """Resistencia I: Combinación básica de carga gravitacional"""
        return LimitState(
            name="Strength I",
            factors={
                LoadType.DC: LoadFactor(gamma_max=1.25, gamma_min=0.90),
                LoadType.EV: LoadFactor(gamma_max=1.35, gamma_min=1.00),
                LoadType.EH: LoadFactor(gamma_max=1.50, gamma_min=0.90),
                LoadType.LS: LoadFactor(gamma_max=1.75, gamma_min=0.00),
                LoadType.WA: _WA,
            }
        )
        
    @staticmethod
    def strength_IV() -> LimitState:
        """Resistencia IV: relación muy alta entre cargas permanentes y vivas (DC máx = 1.50, sin LS)"""
        return LimitState(
            name="Strength IV",
            factors={
                LoadType.DC: LoadFactor(gamma_max=1.50, gamma_min=0.90),
                LoadType.EV: LoadFactor(gamma_max=1.35, gamma_min=1.00),
                LoadType.EH: LoadFactor(gamma_max=1.50, gamma_min=0.90),
                LoadType.WA: _WA,
            }
        )

    @staticmethod
    def service_I() -> LimitState:
        """Servicio I: Combinación para asentamientos, excentricidad (AASHTO 11.6.3) y fisuración"""
        return LimitState(
            name="Service I",
            factors={
                LoadType.DC: LoadFactor(gamma_max=1.00, gamma_min=1.00),
                LoadType.EV: LoadFactor(gamma_max=1.00, gamma_min=1.00),
                LoadType.EH: LoadFactor(gamma_max=1.00, gamma_min=1.00),
                LoadType.LS: LoadFactor(gamma_max=1.00, gamma_min=0.00),
                LoadType.WA: _WA,
            }
        )

    @staticmethod
    def extreme_event_I(name: str, eq_e_factor: float, eq_i_factor: float, gamma_eq: float = 0.0) -> LimitState:
        """
        Evento Extremo I (sismo). P_AE ya contiene el empuje estático (C11.6.5.1),
        por lo que EH y el incremento sísmico EQ_E entran con factor 1.0 y no se
        mayora la parte estática. eq_e_factor y eq_i_factor aplican la regla de
        no concurrencia de P_AE y P_IR (11.6.5.1). LS entra con γEQ.
        """
        factors = {
            LoadType.DC: LoadFactor(gamma_max=1.25, gamma_min=0.90),
            LoadType.EV: LoadFactor(gamma_max=1.35, gamma_min=1.00),
            LoadType.EH: LoadFactor(gamma_max=1.00, gamma_min=1.00),
            LoadType.EQ_E: LoadFactor(gamma_max=eq_e_factor, gamma_min=eq_e_factor),
            LoadType.EQ_I: LoadFactor(gamma_max=eq_i_factor, gamma_min=eq_i_factor),
            LoadType.WA: _WA,
        }
        if gamma_eq > 0:
            factors[LoadType.LS] = LoadFactor(gamma_max=gamma_eq, gamma_min=0.00)
        return LimitState(name=name, factors=factors)

    @staticmethod
    def extreme_event_I_cases(pa_static: float, dpae: float, gamma_eq: float = 0.0) -> Dict[str, LimitState]:
        """
        Los dos casos de CCP-14 11.6.5.1, con P_AE = P_A + ΔP_AE:
         a) 100 % de P_AE con 50 % de P_IR
         b) 50 % de P_AE, pero no menos que P_A, con 100 % de P_IR
        En b) el factor del incremento resulta de P_A + f·ΔP_AE = max(0.5·P_AE, P_A).
        """
        if dpae > 0:
            f_b = max(0.5 * (pa_static + dpae) - pa_static, 0.0) / dpae
        else:
            f_b = 0.0
        return {
            "Extreme Event I-a": CCP14Combinations.extreme_event_I("Extreme Event I-a", 1.0, 0.5, gamma_eq),
            "Extreme Event I-b": CCP14Combinations.extreme_event_I("Extreme Event I-b", f_b, 1.0, gamma_eq),
        }
        
    @staticmethod
    def get_all(seismic: bool = False, pa_static: float = 0.0, dpae: float = 0.0, gamma_eq: float = 0.0) -> Dict[str, LimitState]:
        states = {
            "Strength I": CCP14Combinations.strength_I(),
            "Strength IV": CCP14Combinations.strength_IV(),
            "Service I": CCP14Combinations.service_I(),
        }
        if seismic:
            states.update(CCP14Combinations.extreme_event_I_cases(pa_static, dpae, gamma_eq))
        return states
