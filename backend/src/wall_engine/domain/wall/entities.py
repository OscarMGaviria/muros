from dataclasses import dataclass, field
from typing import Optional, List
from uuid import UUID

from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.units.registry import Length
from wall_engine.domain.loads.entities import Surcharge, TrafficSurcharge
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.domain.water.entities import Groundwater

@dataclass(frozen=True)
class WallMaterials:
    concrete: Concrete
    reinforcement: ReinforcementSteel
    cover: Length

@dataclass(frozen=True)
class DesignOptions:
    # Diseño del talón ignorando la reacción del suelo bajo él (conservador,
    # criterio del CDOT BDM Ej. 11, 2.2). Si es False se descuenta la reacción.
    ignore_heel_soil_reaction: bool = False

@dataclass
class Wall:
    id: UUID
    name: str
    geometry: WallGeometry
    materials: WallMaterials
    backfill: Soil
    foundation_soil: Soil
    groundwater: Optional[Groundwater]
    surcharges: List[Surcharge]
    seismic: Optional[SeismicParameters]
    traffic: Optional[TrafficSurcharge] = None
    options: DesignOptions = field(default_factory=DesignOptions)
