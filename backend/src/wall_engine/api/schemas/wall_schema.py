from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

# --- Geometry ---
class GeometrySchema(BaseModel):
    stem_height_m: float = Field(..., gt=0)
    stem_thickness_base_m: float = Field(..., gt=0)
    stem_thickness_top_m: float = Field(..., gt=0)
    footing_width_m: float = Field(..., gt=0)
    footing_thickness_m: float = Field(..., gt=0)
    toe_length_m: float = Field(..., ge=0)
    heel_length_m: float = Field(..., ge=0)
    toe_cover_soil_m: float = Field(0.0, ge=0)
    key_depth_m: Optional[float] = None
    key_width_m: Optional[float] = None
    backfill_slope_deg: float = Field(0.0, ge=0, lt=90)
    stem_batter_deg: float = Field(0.0, ge=0)
    back_face_angle_deg: float = Field(90.0, gt=0, le=180)

# --- Materials ---
class ConcreteSchema(BaseModel):
    fc_MPa: float = Field(28.0, gt=0)
    gamma_kN_m3: float = Field(24.0, gt=0)

class SteelSchema(BaseModel):
    fy_MPa: float = Field(420.0, gt=0)
    Es_MPa: float = Field(200000.0, gt=0)

class MaterialsSchema(BaseModel):
    concrete: ConcreteSchema = ConcreteSchema()
    reinforcement: SteelSchema = SteelSchema()
    cover_cm: float = Field(7.5, gt=0)

# --- Soil ---
class SoilSchema(BaseModel):
    name: str = "Suelo"
    gamma_kN_m3: float = Field(..., gt=0)
    phi_deg: float = Field(..., gt=0, lt=90)
    cohesion_kPa: float = Field(0.0, ge=0)
    interface_friction_deg: Optional[float] = None
    # Presión admisible (criterio de esfuerzos de trabajo); solo la usa el frontend.
    bearing_capacity_kPa: Optional[float] = None
    # Resistencia nominal q_n del estudio geotécnico (LRFD). Si se omite, el motor
    # la calcula con la ecuación general de capacidad portante.
    nominal_bearing_resistance_kPa: Optional[float] = Field(None, gt=0)

# --- Traffic & Seismic ---
class TrafficSchema(BaseModel):
    orientation: str = Field("PARALLEL", description="PARALLEL or PERPENDICULAR")
    distance_from_back_m: float = Field(0.0, ge=0)

class SeismicSchema(BaseModel):
    kh: float = Field(0.0, ge=0)
    kv: float = Field(0.0, ge=0)
    q_surcharge_kPa: float = Field(0.0, ge=0)

# --- Design options ---
class DesignOptionsSchema(BaseModel):
    ignore_heel_soil_reaction: bool = Field(
        False, description="Diseñar el talón sin descontar la reacción del suelo (conservador, criterio CDOT)")

# --- Main Wall ---
class WallDesignRequest(BaseModel):
    name: str = "Muro de Prueba"
    geometry: GeometrySchema
    materials: MaterialsSchema = MaterialsSchema()
    backfill: SoilSchema
    foundation_soil: SoilSchema
    traffic: Optional[TrafficSchema] = None
    seismic: Optional[SeismicSchema] = None
    design_options: DesignOptionsSchema = DesignOptionsSchema()
