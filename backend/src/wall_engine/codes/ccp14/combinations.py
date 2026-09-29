from typing import Dict
from wall_engine.domain.loads.combinations import LimitState, LoadType, LoadFactor

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
            }
        )

    @staticmethod
    def extreme_event_I() -> LimitState:
        """Evento Extremo I: Combinación para Sismo"""
        return LimitState(
            name="Extreme Event I",
            factors={
                LoadType.DC: LoadFactor(gamma_max=1.25, gamma_min=0.90), # AASHTO permite usar el extremo desfavorable
                LoadType.EV: LoadFactor(gamma_max=1.35, gamma_min=1.00),
                LoadType.EH: LoadFactor(gamma_max=1.50, gamma_min=0.90), # Algunos estados usan 1.0 para sismo, pero CCP14 puede variar. Asumiremos Max.
                LoadType.EQ_E: LoadFactor(gamma_max=1.00, gamma_min=1.00),
            LoadType.EQ_I: LoadFactor(gamma_max=1.00, gamma_min=1.00), # Sismo siempre va completo
            }
        )
        
    @staticmethod
    def get_all() -> Dict[str, LimitState]:
        return {
            "Strength I": CCP14Combinations.strength_I(),
            "Strength IV": CCP14Combinations.strength_IV(),
            "Service I": CCP14Combinations.service_I(),
            "Extreme Event I": CCP14Combinations.extreme_event_I()
        }
