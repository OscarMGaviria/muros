import pytest
import uuid
from wall_engine.units.registry import Q_
from wall_engine.domain.wall.geometry import WallGeometry
from wall_engine.domain.soil.entities import Soil
from wall_engine.domain.materials.concrete import Concrete
from wall_engine.domain.materials.steel import ReinforcementSteel
from wall_engine.domain.wall.entities import Wall, WallMaterials
from wall_engine.seismic.parameters import SeismicParameters
from wall_engine.codes.ccp14.orchestrator import CCP14Orchestrator

def test_ccp14_orchestrator_full_pipeline():
    geom = WallGeometry(
        stem_height=Q_(6.0, "m"),
        stem_thickness_base=Q_(0.6, "m"),
        stem_thickness_top=Q_(0.3, "m"),
        footing_width=Q_(4.0, "m"),
        footing_thickness=Q_(0.6, "m"),
        toe_length=Q_(1.0, "m"),
        heel_length=Q_(2.4, "m"),
        toe_cover_soil=Q_(0.5, "m"),
        key_depth=None,
        key_width=None,
        backfill_slope=Q_(0, "degrees"),
        stem_batter=Q_(0, "degrees"),
        back_face_angle=Q_(90, "degrees")
    )
    
    wall = Wall(
        id=uuid.uuid4(),
        name="Muro CCP14",
        geometry=geom,
        materials=WallMaterials(
            concrete=Concrete(Q_(28, "MPa"), Q_(24, "kN/m**3"), None),
            reinforcement=ReinforcementSteel(Q_(420, "MPa"), None, Q_(200000, "MPa")),
            cover=Q_(7.5, "cm")
        ),
        backfill=Soil("Relleno", Q_(19, "kN/m**3"), None, Q_(32, "degrees"), Q_(0, "kPa"), Q_(16, "degrees"), None),
        foundation_soil=Soil("Subrasante", Q_(20, "kN/m**3"), None, Q_(35, "degrees"), Q_(20, "kPa"), Q_(35, "degrees"), None),
        groundwater=None,
        surcharges=[],
        seismic=SeismicParameters(ag=0.15, kh=0.15, kv=0.0, soil_factor=None, seismic_zone=None)
    )
    
    orchestrator = CCP14Orchestrator()
    report = orchestrator.design_wall(wall)
    
    # Assertions
    assert report is not None
    assert report.wall_name == "Muro CCP14"
    assert "Strength I" in report.governing_loads
    assert "Service I" in report.governing_loads
    assert "Extreme Event I" in report.governing_loads
    
    # Volcamiento (Excentricidad) para Strength
    stab = report.stability_results["Strength I"]
    assert stab.eccentricity > 0
    assert stab.q_toe > 0
    
    # Acero
    reinf = report.structural_design
    assert reinf.stem.A_s_final > 0
    assert reinf.toe.A_s_final > 0
    assert reinf.heel.A_s_final > 0
