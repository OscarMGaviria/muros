from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.units.registry import Q_

class InvalidGeometryError(Exception):
    """Excepción lanzada cuando la geometría del muro es inconsistente o inválida."""
    pass

class GeometryValidator:
    
    @staticmethod
    def validate(geometry: WallGeometry, tolerance_m: float = 0.01) -> None:
        """
        Valida que las dimensiones del muro sean físicamente posibles y consistentes.
        - Todas las dimensiones principales deben ser > 0.
        - footing_width ≈ toe + stem_thickness_base + heel
        """
        # 1. Validar dimensiones positivas
        if geometry.stem_height <= Q_(0, "m"):
            raise InvalidGeometryError("La altura del fuste debe ser mayor a 0.")
        if geometry.stem_thickness_base <= Q_(0, "m"):
            raise InvalidGeometryError("El espesor del fuste en la base debe ser mayor a 0.")
        if geometry.footing_width <= Q_(0, "m"):
            raise InvalidGeometryError("El ancho de la zapata debe ser mayor a 0.")
        if geometry.toe_length < Q_(0, "m"):
            raise InvalidGeometryError("La longitud de la punta no puede ser negativa.")
        if geometry.heel_length < Q_(0, "m"):
            raise InvalidGeometryError("La longitud del talón no puede ser negativa.")

        # 2. Validar consistencia de la zapata
        # footing_width = toe + stem_thickness_base + heel
        calculated_footing_width = geometry.toe_length + geometry.stem_thickness_base + geometry.heel_length
        difference = abs((geometry.footing_width - calculated_footing_width).to("m").magnitude)
        
        if difference > tolerance_m:
            raise InvalidGeometryError(
                f"Inconsistencia geométrica: el ancho de la zapata ({geometry.footing_width.to('m')}) "
                f"no coincide con la suma de punta, fuste y talón ({calculated_footing_width.to('m')}). "
                f"Diferencia: {difference:.4f} m (Tolerancia: {tolerance_m} m)"
            )
