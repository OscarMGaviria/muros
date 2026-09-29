"""Memoria de cálculo trazable: cargas sin mayorar, combinaciones y estabilidad."""
import json
import math
import pytest
from test_cdot_example11 import make_cdot_wall, kip_ft, ft
from wall_engine.codes.ccp14.orchestrator import CCP14Orchestrator
from wall_engine.reporting.calculation_trace import build_trace


@pytest.fixture(scope="module")
def trace():
    wall = make_cdot_wall(kh=0.2)
    return build_trace(wall, CCP14Orchestrator().design_wall(wall))


def all_checks(trace):
    return [c for s in trace["stability"] for c in s["checks"]]


def test_trace_is_json_serializable(trace):
    json.dumps(trace)


def test_unfactored_loads_moments(trace):
    """Cada fila cumple M_V = Fx·y y M_R = Fy·x; los subtotales suman el total."""
    groups = trace["loads"]["groups"]
    rows = [r for g in groups for r in g["rows"]]
    for r in rows:
        assert r["M_V"] == pytest.approx(r["Fx"] * r["y"])
        assert r["M_R"] == pytest.approx(r["Fy"] * r["x"])
    for key in ("Fx", "Fy", "M_V", "M_R"):
        assert sum(g["subtotal"][key] for g in groups) == pytest.approx(trace["loads"]["total"][key])
    # Empuje del ejemplo CDOT: EHH = 4.03 kip/ft a 5.42 ft; EHV = 1.68 kip/ft en x = B = 10 ft
    eh = next(g for g in groups if g["type"] == "EH")["rows"][0]
    assert eh["Fx"] == pytest.approx(kip_ft(4.03), rel=0.01)
    assert eh["M_R"] == pytest.approx(kip_ft(1.68) * ft(10.0), rel=0.01)


def test_factored_tables_match_engine(trace):
    """Chequeo cruzado: las sumas de cada tabla mayorada coinciden con las del motor."""
    for check in all_checks(trace):
        combo = check["combination"]
        assert combo["cross_check"]["ok"], check["label"]
        for row in combo["rows"]:
            factor = next(f["gamma"] for f in combo["factors"] if f["type"] == row["type"])
            assert row["gamma"] == factor


def test_limit_state_factors(trace):
    states = {s["name"]: s for s in trace["limit_states"]}
    assert set(states) == {"Strength I", "Strength IV", "Service I", "Extreme Event I-a", "Extreme Event I-b"}
    dc = next(f for f in states["Strength I"]["factors"] if f["type"] == "DC")
    assert (dc["max"], dc["min"]) == (1.25, 0.90)
    assert states["Strength I"]["permutations"] == 16  # DC, EV, EH y LS con dos factores cada uno


def test_eccentricity_steps_reproduce_result(trace):
    """x0 = (ΣM_R − ΣM_V)/ΣV y e = B/2 − x0, con las sumas de la tabla mostrada."""
    b = trace["geometry"]["B"]
    for section in trace["stability"]:
        check = next(c for c in section["checks"] if c["kind"] == "eccentricity")
        sums = check["combination"]["sums"]
        x0 = (sums["M_R"] - sums["M_V"]) / sums["Fy"]
        assert check["steps"][0]["value"] == pytest.approx(x0)
        assert check["steps"][1]["value"] == pytest.approx(b / 2 - x0)
        assert check["result"]["ok"] == (abs(b / 2 - x0) <= check["result"]["capacity"])


def test_sliding_steps_reproduce_result(trace):
    """Strength Ia del ejemplo: ΣH = 7.92 kip/ft y R_R = ΣV·tan20° (sin dentellón no cumple)."""
    sliding = next(c for c in trace["stability"][0]["checks"] if c["kind"] == "sliding")
    sums = sliding["combination"]["sums"]
    assert sliding["result"]["demand"] == pytest.approx(abs(sums["Fx"]))
    assert sliding["result"]["capacity"] == pytest.approx(sums["Fy"] * math.tan(math.radians(20)))
    assert sliding["result"]["demand"] == pytest.approx(kip_ft(7.92), rel=0.02)
    assert sliding["result"]["ok"] is False


def test_bearing_steps(trace):
    for section in trace["stability"]:
        bearing = [c for c in section["checks"] if c["kind"] == "bearing"]
        if section["name"] == "Service I":
            assert bearing == [] and section["note"]
            continue
        steps = {s["symbol"]: s["value"] for s in bearing[0]["steps"]}
        assert steps[r"\sigma_V"] == pytest.approx(bearing[0]["combination"]["sums"]["Fy"] / steps["B'"])
        assert bearing[0]["result"]["capacity"] == pytest.approx(steps["q_R"])


def test_bearing_nominal_resistance_recomposes_from_shown_factors(trace):
    """q_n = c·Nc·ic + q·Nq·iq + ½·γ·B'·Nγ·iγ con los valores que muestra la memoria."""
    bearing = next(c for c in trace["stability"][0]["checks"] if c["kind"] == "bearing")
    v = {s["symbol"]: s["value"] for s in bearing["steps"]}
    phi = math.radians(20)
    assert v["N_q"] == pytest.approx(math.exp(math.pi * math.tan(phi)) * math.tan(math.radians(45) + phi / 2) ** 2)
    gamma = 0.130 * 157.087  # kcf -> kN/m³
    q_n = 0.0 + v["q"] * v["N_q"] * v["i_q"] + 0.5 * gamma * v["B'"] * v[r"N_\gamma"] * v[r"i_\gamma"]
    assert v["q_n"] == pytest.approx(q_n, rel=1e-3)


def test_every_step_has_readable_text(trace):
    for check in all_checks(trace):
        for step in check["steps"]:
            assert "\\" not in step["text"], step["text"]
            assert f"{step['value']:.3f}" in step["text"]
