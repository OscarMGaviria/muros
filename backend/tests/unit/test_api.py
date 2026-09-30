import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient
from wall_engine.api.main import app

client = TestClient(app)

BASE = {
    "geometry": {"stem_height_m": 6, "stem_thickness_base_m": 0.6, "stem_thickness_top_m": 0.3,
                 "footing_width_m": 4, "footing_thickness_m": 0.6, "toe_length_m": 1,
                 "heel_length_m": 2.4, "toe_cover_soil_m": 0.5},
    "backfill": {"gamma_kN_m3": 19, "gamma_sat_kN_m3": 21, "phi_deg": 32, "interface_friction_deg": 21},
    "foundation_soil": {"gamma_kN_m3": 20, "phi_deg": 32},
}


def post(**extra):
    return client.post("/api/v1/design/ccp14", json={**BASE, **extra})


def test_kh_from_pga_and_groundwater():
    r = post(seismic={"kh_mode": "PGA", "pga": 0.25, "site_class": "D", "allow_displacement": True,
                      "gamma_eq": 0.5, "pae_height_ratio": 0.4},
             groundwater={"elevation_m": 2.0, "free_draining_backfill": True})
    assert r.status_code == 200
    res = r.json()["results"]
    assert res["seismic"]["kh0"] == pytest.approx(0.325)
    assert res["seismic"]["kh"] == pytest.approx(0.1625)
    assert res["seismic"]["extreme_event_states"] == ["Extreme Event I-a", "Extreme Event I-b"]
    assert res["water"]["hw_m"] == pytest.approx(2.0)
    types = {ld["type"] for ld in res["loads"]}
    assert {"WA", "EQ_E", "EQ_I"} <= types


def test_direct_kh_payload_is_backwards_compatible():
    r = post(seismic={"kh": 0.15, "kv": 0})
    assert r.status_code == 200
    assert r.json()["results"]["seismic"]["kh"] == pytest.approx(0.15)


@pytest.mark.parametrize("seismic", [{"kh_mode": "PGA"}, {"kh_mode": "PGA", "pga": 0.25, "site_class": "F"}])
def test_invalid_seismic_input_returns_422(seismic):
    assert post(seismic=seismic).status_code == 422
