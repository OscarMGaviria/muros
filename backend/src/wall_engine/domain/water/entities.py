from dataclasses import dataclass
from typing import Optional
from wall_engine.units.registry import Length

@dataclass(frozen=True)
class Groundwater:
    elevation: Length
    drainage_enabled: bool
    drainage_type: Optional[str]
    # Relleno muy permeable (p. ej. triturado): en sismo el agua no se mueve con
    # el suelo; se usa el peso sumergido y se añade la presión hidrodinámica.
    free_draining_backfill: bool = False
