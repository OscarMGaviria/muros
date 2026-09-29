from fastapi import APIRouter, HTTPException
import uuid
from wall_engine.api.schemas.wall_schema import WallDesignRequest, TrafficSchema
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.domain.wall.entities import WallMaterials, Wall, DesignOptions
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.loads.entities import TrafficSurcharge
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.codes.ccp14.orchestrator import CCP14Orchestrator

router = APIRouter()

@router.post("/ccp14")
def design_wall_ccp14(request: WallDesignRequest):
    try:
        # 1. Map Schema to Domain
        geom = WallGeometry(
            stem_height=Q_(request.geometry.stem_height_m, "m"),
            stem_thickness_base=Q_(request.geometry.stem_thickness_base_m, "m"),
            stem_thickness_top=Q_(request.geometry.stem_thickness_top_m, "m"),
            footing_width=Q_(request.geometry.footing_width_m, "m"),
            footing_thickness=Q_(request.geometry.footing_thickness_m, "m"),
            toe_length=Q_(request.geometry.toe_length_m, "m"),
            heel_length=Q_(request.geometry.heel_length_m, "m"),
            toe_cover_soil=Q_(request.geometry.toe_cover_soil_m, "m"),
            key_depth=Q_(request.geometry.key_depth_m, "m") if request.geometry.key_depth_m else None,
            key_width=Q_(request.geometry.key_width_m, "m") if request.geometry.key_width_m else None,
            backfill_slope=Q_(request.geometry.backfill_slope_deg, "degrees"),
            stem_batter=Q_(request.geometry.stem_batter_deg, "degrees"),
            back_face_angle=Q_(request.geometry.back_face_angle_deg, "degrees")
        )
        
        mats = WallMaterials(
            concrete=Concrete(fc=Q_(request.materials.concrete.fc_MPa, "MPa"), density=Q_(request.materials.concrete.gamma_kN_m3, "kN/m**3"), elastic_modulus=None),
            reinforcement=ReinforcementSteel(fy=Q_(request.materials.reinforcement.fy_MPa, "MPa"), fu=None, elastic_modulus=Q_(request.materials.reinforcement.Es_MPa, "MPa")),
            cover=Q_(request.materials.cover_cm, "cm")
        )
        
        back_soil = Soil(
            name=request.backfill.name,
            unit_weight=Q_(request.backfill.gamma_kN_m3, "kN/m**3"),
            saturated_unit_weight=None,
            friction_angle=Q_(request.backfill.phi_deg, "degrees"),
            cohesion=Q_(request.backfill.cohesion_kPa, "kPa"),
            interface_friction_angle=Q_(request.backfill.interface_friction_deg, "degrees") if request.backfill.interface_friction_deg is not None else Q_(request.backfill.phi_deg * 0.66, "degrees"),
            bearing_capacity=None
        )
        
        found_soil = Soil(
            name=request.foundation_soil.name,
            unit_weight=Q_(request.foundation_soil.gamma_kN_m3, "kN/m**3"),
            saturated_unit_weight=None,
            friction_angle=Q_(request.foundation_soil.phi_deg, "degrees"),
            cohesion=Q_(request.foundation_soil.cohesion_kPa, "kPa"),
            interface_friction_angle=Q_(request.foundation_soil.interface_friction_deg, "degrees") if request.foundation_soil.interface_friction_deg is not None else Q_(request.foundation_soil.phi_deg, "degrees"),
            # El motor LRFD usa la resistencia nominal q_n; la presión admisible
            # (bearing_capacity_kPa) no es equivalente y no se le pasa.
            bearing_capacity=Q_(request.foundation_soil.nominal_bearing_resistance_kPa, "kPa") if request.foundation_soil.nominal_bearing_resistance_kPa else None
        )
        
        seis = SeismicParameters(
            ag=request.seismic.kh if request.seismic else 0.0,
            kh=request.seismic.kh if request.seismic else 0.0,
            kv=request.seismic.kv if request.seismic else 0.0,
            soil_factor=None, seismic_zone=None
        )

        traffic_req = request.traffic or TrafficSchema()
        traffic = TrafficSurcharge(
            orientation=traffic_req.orientation,
            distance_from_back=Q_(traffic_req.distance_from_back_m, "m")
        )

        wall = Wall(
            id=uuid.uuid4(),
            name=request.name,
            geometry=geom,
            materials=mats,
            backfill=back_soil,
            foundation_soil=found_soil,
            groundwater=None,
            surcharges=[],
            seismic=seis,
            traffic=traffic,
            options=DesignOptions(
                ignore_heel_soil_reaction=request.design_options.ignore_heel_soil_reaction
            )
        )
        
        # 2. Run Engine
        orch = CCP14Orchestrator()
        report = orch.design_wall(wall)
        
        # 3. Return a clean dict (Pydantic models will be implemented later, for now we return raw dict)
        # To avoid Pint Quantity serialization errors, we extract magnitudes manually for the critical results.
        # Extract loads
        loads_list = []
        for ld in report.unfactored_loads:
            loads_list.append({
                "name": ld.name,
                "type": ld.load_type.name,
                "Fx": float(ld.force_x.magnitude),
                "Fy": float(ld.force_y.magnitude),
                "x_app": float(ld.x_application.magnitude) if hasattr(ld.x_application, 'magnitude') else float(ld.x_application),
                "y_app": float(ld.y_application.magnitude) if hasattr(ld.y_application, 'magnitude') else float(ld.y_application),
            })
            
        res = {
            "results": {
                "stability": {
                    "sliding": {
                        "FS": float(1.0 / report.stability_results["Strength I"].sliding_ratio) if "Strength I" in report.stability_results and report.stability_results["Strength I"].sliding_ratio > 0 else 1.0
                    },
                    "eccentricity": {
                        "e": float(report.stability_results["Strength I"].eccentricity.to("m").magnitude) if "Strength I" in report.stability_results else 0.0
                    },
                    "bearing": {
                        "q_max": float(report.stability_results["Strength I"].q_toe) if "Strength I" in report.stability_results else 0.0,
                        "q_min": float(report.stability_results["Strength I"].q_heel) if "Strength I" in report.stability_results else 0.0,
                        # Verificación LRFD: sigma_V = V/B' frente a phi_b * q_n, por estado límite
                        "checks": {
                            name: {
                                "q_demand_kPa": float(br.q_demand),
                                "q_nominal_kPa": float(br.q_nominal.to("kPa").magnitude),
                                "phi_b": br.phi_b,
                                "q_resistance_kPa": float(br.q_resistance),
                                "ratio": float(br.bearing_ratio),
                                "is_safe": bool(br.is_safe)
                            }
                            for name, br in report.bearing_results.items()
                        }
                    }
                },
                "earth_pressure": {
                    "ka": report.earth_pressure.coefficient_active,
                    "kp": report.earth_pressure.coefficient_passive
                },
                "traffic_surcharge": {
                    "heq_m": report.traffic_heq_m,
                    "qs_kPa": report.traffic_qs_kPa
                },
                "structural": {
                    "reinforcement": {
                        "stem_flexure": {
                            "A_s_required": report.structural_design.stem.A_s_required
                        },
                        "heel_flexure": {
                            "A_s_required": report.structural_design.heel.A_s_required
                        }
                    }
                },
                "loads": loads_list
            }
        }
            
        return res
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
