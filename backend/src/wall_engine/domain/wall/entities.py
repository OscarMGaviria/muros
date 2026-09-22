from dataclasses import dataclass
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
