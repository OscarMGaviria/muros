"""
Memoria de cálculo trazable: cargas sin mayorar, combinaciones y estabilidad.

Convierte el reporte del motor en datos que el usuario puede revisar a mano:
cada carga con sus brazos y momentos, los factores de cada estado límite, la
combinación que gobierna cada verificación con su tabla de cargas mayoradas y
los pasos de cálculo (fórmula, sustitución numérica, resultado y artículo).

Convención (la del motor): x se mide desde la punta, y desde la base de la
zapata; Fx > 0 empuja el muro hacia la punta y Fy > 0 va hacia abajo.
Momentos respecto a la punta: M_V = Fx·y (volcante), M_R = Fy·x (resistente).
"""
import math
from typing import Dict, List, Optional

from wall_engine.domain.loads.combinations import FactoredResult, GenericLoad, LoadType
from wall_engine.domain.results.report import WallDesignReport
from wall_engine.domain.wall.entities import Wall

TOLERANCE = 1e-6

LOAD_TYPE_LABELS = {
    LoadType.DC: "Peso propio (DC)",
    LoadType.EV: "Peso del suelo (EV)",
    LoadType.EH: "Empuje de tierras (EH)",
    LoadType.LS: "Sobrecarga viva (LS)",
    LoadType.WA: "Agua (WA)",
    LoadType.EQ_E: "Sismo: empuje (EQ)",
    LoadType.EQ_I: "Sismo: inercia (EQ)",
}
LOAD_TYPE_ORDER = [LoadType.DC, LoadType.EV, LoadType.EH, LoadType.LS, LoadType.WA, LoadType.EQ_E, LoadType.EQ_I]

LIMIT_STATE_LABELS = {
    "Strength I": "Resistencia I",
    "Strength IV": "Resistencia IV",
    "Service I": "Servicio I",
    "Extreme Event I-a": "Evento Extremo I-a (100 % P_AE + 50 % P_IR)",
    "Extreme Event I-b": "Evento Extremo I-b (50 % P_AE ≥ P_A + 100 % P_IR)",
}

_BLOCK_LABELS = {
    "Footing (Toe)": "Zapata: punta",
    "Footing (Under Stem)": "Zapata: bajo el fuste",
    "Footing (Heel)": "Zapata: talón",
    "Stem (Rectangular)": "Fuste: rectángulo",
    "Stem (Triangular)": "Fuste: triángulo",
    "Soil over Heel (Rectangular)": "Suelo sobre el talón",
    "Soil over Heel (Saturated)": "Suelo saturado sobre el talón",
    "Soil over Heel (Slope)": "Cuña del talud sobre el talón",
    "Soil over Toe": "Relleno sobre la punta",
}

CHECK_LABELS = {
    "eccentricity": "Excentricidad (volcamiento)",
    "sliding": "Deslizamiento",
    "contact": "Presión de contacto",
    "bearing": "Capacidad portante",
}
CHECK_CRITERIA = {
    "eccentricity": "Gobierna la combinación con mayor |e| (verticales mínimas, horizontales máximas).",
    "sliding": "Gobierna la combinación con mayor relación demanda / capacidad.",
    "contact": "Gobierna la combinación con mayor presión en la base (verticales máximas).",
    "bearing": "Gobierna la combinación con mayor relación σV / φb·qn.",
}


def load_label(name: str) -> str:
    """Nombre en español de una carga del motor."""
    if name in _BLOCK_LABELS:
        return _BLOCK_LABELS[name]
    for prefix, text in (("Inertia PIR (", "Inercia de "), ("Inertia PIS (", "Inercia de ")):
        if name.startswith(prefix) and name.endswith(")"):
            inner = name[len(prefix):-1]
            return text + _BLOCK_LABELS.get(inner, inner).lower()
    return name


def _n(value: float, digits: int = 2) -> str:
    """Número para LaTeX, con paréntesis si es negativo."""
    text = f"{value:.{digits}f}"
    return f"({text})" if value < 0 else text


_LATEX_SYMBOLS = [
    (r"\Rightarrow", "⇒"), (r"\Sigma", "Σ"), (r"\sigma", "σ"), (r"\gamma", "γ"), (r"\phi", "φ"),
    (r"\tau", "τ"), (r"\delta", "δ"), (r"\pi", "π"), (r"\cdot", "·"), (r"\ldots", "…"),
    (r"\tan", "tan"), (r"\cos", "cos"), (r"\cot", "cot"), (r"\left", ""), (r"\right", ""),
    (r"^\circ", "°"), (r"\,", " "), (r"\ ", " "), (r"\tfrac", r"\frac"),
]


def latex_to_text(tex: str) -> str:
    """Versión legible en texto de las expresiones LaTeX usadas en la memoria."""
    import re
    text = tex
    for a, b in _LATEX_SYMBOLS:
        text = text.replace(a, b)
    text = re.sub(r"\\text\{([^{}]*)\}", r"\1", text)
    frac = re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}")
    while frac.search(text):
        text = frac.sub(lambda m: f"({m.group(1)})/({m.group(2)})", text)
    text = re.sub(r"\(([^()+\-·/ ]+)\)/\(([^()+\-·/ ]+)\)", r"\1/\2", text)  # (a)/(b) simple -> a/b
    text = re.sub(r"_\{([^{}]*)\}", r"_\1", text)
    text = re.sub(r"\^\{([^{}]*)\}", r"^\1", text)
    return re.sub(r"\s+", " ", text.replace("{", "").replace("}", "")).strip()


def _step(label, symbol, formula, substitution, value, unit, clause=""):
    parts = [symbol] + [p for p in (formula, substitution) if p]
    text = " = ".join(latex_to_text(p) for p in parts) + f" = {value:.3f}" + (f" {unit}" if unit else "")
    return {
        "text": text,
        "label": label,
        "symbol": symbol,
        "formula": formula,
        "substitution": substitution,
        "value": value,
        "unit": unit,
        "clause": clause,
    }


def _load_row(index: int, load: GenericLoad) -> dict:
    fx = load.force_x.to("kN/m").magnitude
    fy = load.force_y.to("kN/m").magnitude
    x = load.x_application.to("m").magnitude
    y = load.y_application.to("m").magnitude
    return {
        "id": index,
        "name": load_label(load.name),
        "type": load.load_type.value,
        "type_label": LOAD_TYPE_LABELS.get(load.load_type, load.load_type.value),
        "Fx": fx,
        "Fy": fy,
        "x": x,
        "y": y,
        "M_V": fx * y,
        "M_R": fy * x,
    }


def _sum_rows(rows: List[dict], keys=("Fx", "Fy", "M_V", "M_R")) -> dict:
    return {k: sum(r[k] for r in rows) for k in keys}


def unfactored_loads_section(loads: List[GenericLoad]) -> dict:
    rows = [_load_row(i + 1, ld) for i, ld in enumerate(loads)]
    groups = []
    for lt in LOAD_TYPE_ORDER:
        group_rows = [r for r in rows if r["type"] == lt.value]
        if group_rows:
            groups.append({
                "type": lt.value,
                "label": LOAD_TYPE_LABELS[lt],
                "rows": group_rows,
                "subtotal": _sum_rows(group_rows),
            })
    return {
        "convention": (
            "x desde la punta y y desde la base de la zapata. Fx > 0 empuja hacia la punta; "
            "Fy > 0 va hacia abajo. Momentos respecto a la punta: M_V = Fx·y (volcante) y "
            "M_R = Fy·x (resistente). Una Fy negativa (subpresión) resta momento resistente."
        ),
        "units": {"force": "kN/m", "length": "m", "moment": "kN·m/m"},
        "groups": groups,
        "total": _sum_rows(rows),
    }


def limit_states_section(report: WallDesignReport) -> List[dict]:
    states = []
    for name, ls in report.limit_states.items():
        if name not in report.permutation_counts:
            continue
        factors = []
        for lt in LOAD_TYPE_ORDER:
            if lt in ls.factors:
                f = ls.factors[lt]
                factors.append({"type": lt.value, "label": LOAD_TYPE_LABELS[lt],
                                "max": f.gamma_max, "min": f.gamma_min})
        states.append({
            "name": name,
            "label": LIMIT_STATE_LABELS.get(name, name),
            "factors": factors,
            "permutations": report.permutation_counts[name],
        })
    return states


def factored_table(loads: List[GenericLoad], perm: FactoredResult) -> dict:
    """Cargas de la combinación con su factor y el chequeo cruzado contra el motor."""
    rows = []
    for i, ld in enumerate(loads):
        gamma = perm.factors_used.get(ld.load_type)
        if gamma is None:
            continue  # el tipo de carga no participa en este estado límite
        base = _load_row(i + 1, ld)
        rows.append({
            "id": base["id"], "name": base["name"], "type": base["type"],
            "gamma": gamma,
            "Fx": gamma * base["Fx"], "Fy": gamma * base["Fy"],
            "M_V": gamma * base["M_V"], "M_R": gamma * base["M_R"],
        })
    sums = _sum_rows(rows)
    engine = {
        "sum_H": perm.sum_force_x.to("kN/m").magnitude,
        "sum_V": perm.sum_force_y.to("kN/m").magnitude,
        "sum_M": perm.sum_moment.to("kN*m/m").magnitude,
    }
    cross_check = {
        "table": {"sum_H": sums["Fx"], "sum_V": sums["Fy"], "sum_M": sums["M_V"] - sums["M_R"]},
        "engine": engine,
    }
    cross_check["ok"] = all(
        math.isclose(cross_check["table"][k], engine[k], rel_tol=TOLERANCE, abs_tol=TOLERANCE) for k in engine
    )
    return {
        "permutation": perm.permutation_id,
        "factors": [
            {"type": lt.value, "label": LOAD_TYPE_LABELS[lt], "gamma": perm.factors_used[lt]}
            for lt in LOAD_TYPE_ORDER if lt in perm.factors_used
        ],
        "rows": rows,
        "sums": sums,
        "cross_check": cross_check,
    }


def _eccentricity_steps(stab, table) -> List[dict]:
    b, v = stab.footing_width, stab.sum_V
    e = stab.eccentricity.to("m").magnitude
    sums = table["sums"]
    return [
        _step("Ubicación de la resultante desde la punta", "x_0",
              r"\frac{\Sigma M_R - \Sigma M_V}{\Sigma V}",
              rf"\frac{{{_n(sums['M_R'])} - {_n(sums['M_V'])}}}{{{_n(v)}}}", stab.x_resultant, "m"),
        _step("Excentricidad respecto al centro de la base", "e", r"\frac{B}{2} - x_0",
              rf"\frac{{{_n(b)}}}{{2}} - {_n(stab.x_resultant, 3)}", e, "m"),
        _step("Excentricidad máxima admisible", r"e_{max}", "", "", stab.e_limit, "m", stab.e_limit_rule),
    ]


def _sliding_steps(stab) -> List[dict]:
    tan_phi = math.tan(math.radians(stab.friction_angle_deg))
    steps = [_step("Demanda: fuerza horizontal mayorada", r"\Sigma H", "", "", abs(stab.sum_H), "kN/m")]
    if stab.key_split:
        ks = stab.key_split
        cos_d = math.cos(math.radians(ks["delta_sub_deg"]))
        steps.append(_step(
            "Fricción con dentellón (tramo R1 sobre el bloque inerte y R2 sobre la base)", r"R_\tau",
            r"R_1 \tan\phi_f \cos\delta_{sub} + R_2 \tan\phi_f",
            rf"{_n(ks['R1'])} \cdot {tan_phi:.3f} \cdot {cos_d:.3f} + {_n(ks['R2'])} \cdot {tan_phi:.3f}",
            stab.friction_nominal, "kN/m", "CCP-14 10.6.3.4; método del bloque inerte (CDOT BDM)"))
    else:
        steps.append(_step("Resistencia nominal por fricción", r"R_\tau", r"\Sigma V \tan\phi_f",
                            rf"{_n(stab.sum_V)} \cdot \tan({stab.friction_angle_deg:.1f}^\circ)",
                            stab.friction_nominal, "kN/m", "CCP-14 Ec. 10.6.3.4-2"))
    steps.append(_step(
        "Resistencia pasiva del dentellón (se desprecia el suelo frente a la punta)", r"R_{ep}", "", "",
        stab.passive_nominal, "kN/m", "CCP-14 11.6.3.5"))
    steps.append(_step(
        "Resistencia factorada", r"R_R", r"\phi_\tau R_\tau + \phi_{ep} R_{ep}",
        rf"{stab.phi_tau:.2f} \cdot {_n(stab.friction_nominal)} + {stab.phi_ep:.2f} \cdot {_n(stab.passive_nominal)}",
        stab.sliding_capacity.to("kN/m").magnitude, "kN/m", "CCP-14 Tabla 11.5.7-1 y 11.5.8"))
    return steps


def _contact_steps(stab) -> List[dict]:
    b, v = stab.footing_width, stab.sum_V
    e = stab.eccentricity.to("m").magnitude
    if stab.pressure_distribution == "trapezoidal":
        return [
            _step("Presión en la punta (resultante en el tercio medio)", r"q_{punta}",
                  r"\frac{\Sigma V}{B}\left(1 + \frac{6e}{B}\right)",
                  rf"\frac{{{_n(v)}}}{{{_n(b)}}}\left(1 + \frac{{6 \cdot {_n(e, 3)}}}{{{_n(b)}}}\right)",
                  stab.q_toe, "kPa"),
            _step("Presión en el talón", r"q_{talon}",
                  r"\frac{\Sigma V}{B}\left(1 - \frac{6e}{B}\right)",
                  rf"\frac{{{_n(v)}}}{{{_n(b)}}}\left(1 - \frac{{6 \cdot {_n(e, 3)}}}{{{_n(b)}}}\right)",
                  stab.q_heel, "kPa"),
        ]
    if stab.pressure_distribution == "triangular":
        q_max = max(stab.q_toe, stab.q_heel)
        return [_step("Presión máxima (resultante fuera del tercio medio, distribución triangular)",
                      r"q_{max}", r"\frac{2\,\Sigma V}{3\left(\frac{B}{2} - |e|\right)}",
                      rf"\frac{{2 \cdot {_n(v)}}}{{3\left(\frac{{{_n(b)}}}{{2}} - {abs(e):.3f}\right)}}",
                      q_max, "kPa")]
    return []


def _bearing_steps(br) -> List[dict]:
    b, e, v = br.footing_width, br.eccentricity, br.sum_V
    steps = [
        _step("Ancho efectivo", "B'", r"B - 2|e|", rf"{_n(b)} - 2 \cdot {abs(e):.3f}", br.effective_width, "m"),
        _step("Presión vertical uniforme sobre B'", r"\sigma_V", r"\frac{\Sigma V}{B'}",
              rf"\frac{{{_n(v)}}}{{{br.effective_width:.3f}}}", br.q_demand, "kPa", "CCP-14 Ec. 11.6.3.2-1"),
    ]
    if br.uses_geotechnical_q_n:
        steps.append(_step("Resistencia nominal del estudio geotécnico", "q_n", "", "",
                           br.q_nominal.to("kPa").magnitude, "kPa"))
    else:
        phi = br.friction_angle_deg
        v_, h_, c_ = br.sum_V, br.sum_H, br.cohesion
        if phi > 0:
            den = rf"{_n(v_)} + {c_:.1f} \cdot {br.effective_width:.3f} \cdot \cot({phi:.1f}^\circ)"
            steps += [
                _step("Factor de capacidad portante", "N_q",
                      r"e^{\pi\tan\phi}\tan^2\left(45^\circ + \frac{\phi}{2}\right)",
                      rf"e^{{\pi\tan({phi:.1f}^\circ)}}\tan^2\left(45^\circ + {phi / 2:.2f}^\circ\right)",
                      br.N_q, "", "CCP-14 10.6.3.1.2a"),
                _step("Factor de capacidad portante", "N_c", r"(N_q - 1)\cot\phi",
                      rf"({br.N_q:.3f} - 1)\cot({phi:.1f}^\circ)", br.N_c, ""),
                _step("Factor de capacidad portante", r"N_\gamma", r"2(N_q + 1)\tan\phi",
                      rf"2({br.N_q:.3f} + 1)\tan({phi:.1f}^\circ)", br.N_gamma, ""),
                _step("Factor de inclinación de la carga (zapata corrida, n = 2)", "i_q",
                      r"\left[1 - \frac{H}{V + c B' \cot\phi}\right]^2",
                      rf"\left[1 - \frac{{{_n(h_)}}}{{{den}}}\right]^2", br.i_q, "", "CCP-14 10.6.3.1.2a"),
                _step("Factor de inclinación de la carga", r"i_\gamma",
                      r"\left[1 - \frac{H}{V + c B' \cot\phi}\right]^3",
                      rf"\left[1 - \frac{{{_n(h_)}}}{{{den}}}\right]^3", br.i_gamma, ""),
                _step("Factor de inclinación de la carga", "i_c", r"i_q - \frac{1 - i_q}{N_q - 1}",
                      rf"{br.i_q:.3f} - \frac{{1 - {br.i_q:.3f}}}{{{br.N_q:.3f} - 1}}", br.i_c, ""),
            ]
        else:
            steps += [
                _step("Factores de capacidad portante para φ = 0", "N_c", "", "", br.N_c, "", "N_q = 1, N_γ = 0"),
                _step("Factor de inclinación de la carga (φ = 0)", "i_c",
                      r"1 - \frac{n H}{5.14\, c\, B'}",
                      rf"1 - \frac{{2 \cdot {_n(h_)}}}{{5.14 \cdot {c_:.1f} \cdot {br.effective_width:.3f}}}",
                      br.i_c, ""),
            ]
        steps += [
            _step("Sobrecarga al nivel de fundación", "q", r"\gamma D_f",
                  rf"{br.unit_weight:.1f} \cdot {br.embedment_depth:.2f}", br.q_overburden, "kPa"),
            _step("Resistencia nominal", "q_n",
                  r"c N_c i_c + q N_q i_q + \tfrac{1}{2}\gamma B' N_\gamma i_\gamma",
                  rf"{br.cohesion:.1f} \cdot {br.N_c:.2f} \cdot {br.i_c:.3f} + {br.q_overburden:.2f} \cdot {br.N_q:.2f} \cdot {br.i_q:.3f}"
                  rf" + 0.5 \cdot {br.unit_weight:.1f} \cdot {br.effective_width:.3f} \cdot {br.N_gamma:.2f} \cdot {br.i_gamma:.3f}",
                  br.q_nominal.to("kPa").magnitude, "kPa"),
        ]
    steps.append(_step("Resistencia factorada", "q_R", r"\phi_b\, q_n",
                       rf"{br.phi_b:.2f} \cdot {br.q_nominal.to('kPa').magnitude:.2f}", br.q_resistance, "kPa",
                       "CCP-14 Tabla 11.5.7-1 (0.55); 1.0 en evento extremo"))
    return steps


def _check(kind, table, steps, demand, capacity, demand_label, capacity_label, unit, note=""):
    ratio = demand / capacity if capacity > 0 else float("inf")
    return {
        "kind": kind,
        "label": CHECK_LABELS[kind],
        "criterion": CHECK_CRITERIA[kind],
        "combination": table,
        "steps": steps,
        "result": {
            "demand": demand, "capacity": capacity,
            "demand_label": demand_label, "capacity_label": capacity_label,
            "unit": unit, "ratio": ratio if math.isfinite(ratio) else None,
            "ok": ratio <= 1.0,
        },
        "note": note,
    }


def stability_section(report: WallDesignReport) -> List[dict]:
    loads = report.unfactored_loads
    sections = []
    for name, checks in report.stability_checks.items():
        items = []
        perm, stab = checks["eccentricity"]
        e = stab.eccentricity.to("m").magnitude
        table = factored_table(loads, perm)
        items.append(_check("eccentricity", table, _eccentricity_steps(stab, table),
                            abs(e), stab.e_limit, "|e|", "e_max", "m"))

        perm, stab = checks["sliding"]
        items.append(_check("sliding", factored_table(loads, perm), _sliding_steps(stab),
                            stab.sliding_demand.to("kN/m").magnitude, stab.sliding_capacity.to("kN/m").magnitude,
                            "ΣH", "R_R", "kN/m"))

        perm, stab = checks["contact"]
        q_max = max(stab.q_toe, stab.q_heel)
        contact = _check("contact", factored_table(loads, perm), _contact_steps(stab), q_max, q_max, "q_max", "q_max", "kPa",
                         "Distribución lineal de presiones usada para el diseño de la punta y el talón. "
                         "La verificación contra la resistencia del suelo es la de capacidad portante.")
        contact["result"].update({"ratio": None, "ok": None, "capacity": None,
                                  "q_toe": stab.q_toe, "q_heel": stab.q_heel})
        items.append(contact)

        if "bearing" in checks:
            perm, br = checks["bearing"]
            items.append(_check("bearing", factored_table(loads, perm), _bearing_steps(br),
                                br.q_demand, br.q_resistance, "σV", "φb·qn", "kPa"))
        sections.append({
            "name": name,
            "label": LIMIT_STATE_LABELS.get(name, name),
            "checks": items,
            "note": "" if "bearing" in checks else
                    "En Servicio I no se revisa la resistencia del suelo; se usa para asentamientos y fisuración.",
        })
    return sections


def build_trace(wall: Wall, report: WallDesignReport) -> dict:
    geom = wall.geometry
    return {
        "geometry": {
            "B": geom.footing_width.to("m").magnitude,
            "H_total": (geom.stem_height + geom.footing_thickness).to("m").magnitude,
        },
        "loads": unfactored_loads_section(report.unfactored_loads),
        "limit_states": limit_states_section(report),
        "stability": stability_section(report),
    }
