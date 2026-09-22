from dataclasses import dataclass
from wall_engine.units.registry import Force, Length, Q_

@dataclass
class Block2D:
    name: str
    load_type: str  # Ej: "DC" (Concreto), "EV" (Suelo Vertical)
    weight: Force
    x_centroid: Length  # Distancia horizontal desde la punta (0,0) de la zapata
    y_centroid: Length  # Distancia vertical desde la base (0,0) de la zapata
    
    @property
    def moment_about_toe(self):
        """Momento estático respecto a la punta (resistencia al volcamiento)"""
        return self.weight * self.x_centroid
