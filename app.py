import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AAM Model Calculator", layout="wide")

# ── Reference ranges ───────────────────────────────────────────────────────────
TSH_LOWER = 0.4
TSH_UPPER = 4.0
T4_LOWER  = 10.8
T4_UPPER  = 22.0
ATPO_REF  = 35


# ── AAM Formulas (unchanged) ───────────────────────────────────────────────────
def soft_deviation(value, lower, upper):
    center    = (lower + upper) / 2
    distance  = abs(value - center)
    magnitude = math.log(1 + distance / center)
    sign      = 1 if value >= center else -1
    return sign * magnitude


def edge_sensitivity(value, lower, upper):
    reference_range = upper - lower
    if lower <= value <= upper:
        d    = min(value - lower, upper - value)
        edge = 1 + (1 - d / reference_range) ** 2
    else:
        edge = 1.0
    return edge


def hard_deviation(value, lower, upper):
    if value > upper:
        return (value - upper) / upper
    elif value < lower:
        return (lower - value) / lower
    return 0.0


def atpo_modifier(atpo):
    return 0.5 * (math.log10(1 + atpo / 35)) ** 1.5


def calculate(TSH, T4, ATPO):
    soft_TSH  = soft_deviation(TSH, TSH_LOWER, TSH_UPPER)
    soft_T4   = soft_deviation(T4,  T4_LOWER,  T4_UPPER)
    edge_TSH  = edge_sensitivity(TSH, TSH_LOWER, TSH_UPPER)
    edge_T4   = edge_sensitivity(T4,  T4_LOWER,  T4_UPPER)
    hard_TSH  = hard_deviation(TSH, TSH_LOWER, TSH_UPPER)
    hard_T4   = hard_deviation(T4,  T4_LOWER,  T4_UPPER)
    Direction     = ((soft_TSH * edge_TSH) - (soft_T4 * edge_T4)) * 0.7
    Force         = math.log(1 + hard_TSH + hard_T4)
    AT            = atpo_modifier(ATPO)
    Direction_mod = Direction * (1 + AT)
    R             = math.sqrt(Direction_mod ** 2 + Force ** 2)
    return Direction_mod, Force, AT, R


# ── R-Zone classification (recalibrated) ───────────────────────────────────────
ZONE_ORDER = [
    "Stable Homeostasis",
    "Compensated Tension",
    "Instability Zone",
    "Significant Dysfunction",
    "Extreme Decompensation",
]
ZONE_COLORS  = ["#27ae60", "#f39c12", "#e67e22", "#e74c3c", "#8e44ad"]
ZONE_RANGES  = "0–0.45 | 0.45–0.8 | 0.8–1.3 | 1.3–2.0 | >2.0"

ZONE_VL_SCALE = {"domain": ZONE_ORDER, "range": ZONE_COLORS}


def get_zone(R: float) -> str:
    if R < 0.45:
        return "Stable Homeostasis"
    elif R < 0.8:
        return "Compensated Tension"
    elif R < 1.3:
        return "Instability Zone"
    elif R < 2.0:
        return "Significant Dysfunction"
    return "Extreme Decompensation"


# ── Hidden Instability Flags ───────────────────────────────────────────────────
FLAG_A = "Hidden Autoimmune Activity"
FLAG_B = "Subclinical Autoimmune State"
FLAG_C = "Latent Destabilization"


def get_flags(tsh: float, t4: float, atpo: float, r: float, force: float) -> list[str]:
    flags = []
    tsh_in_range = TSH_LOWER <= tsh <= TSH_UPPER
    t4_in_range  = T4_LOWER  <= t4  <= T4_UPPER

    # A: High ATPO but low overall R — autoimmune load masked by geometry
    if atpo > 35 and r < 0.45:
        flags.append(FLAG_A)

    # B: Very high ATPO + no hard hormone imbalance (Force ≈ 0)
    if atpo > 100 and force < 0.001:
        flags.append(FLAG_B)

    # C: Hormones within reference range but ATPO strongly elevated
    if tsh_in_range and t4_in_range and atpo > 100:
        flags.append(FLAG_C)

    return flags


# ── Patient data — all 51 records: (year, TSH, T4, ATPO) ─────────────────────
PATIENTS = [
    (2009, 1.20,  25.20,  0.16),
    (1993, 0.40,  58.60,  68.80),
    (1999, 0.50,  18.50,  0.69),
    (2008, 0.95,  18.60,  53.70),
    (1996, 0.82,  17.30,  0.50),
    (1985, 1.10,  22.70,  254.90),
    (1992, 1.64,  17.30,  1.60),
    (2000, 1.30,  13.60,  3.40),
    (2004, 1.93,  17.00,  1.40),
    (1979, 1.22,  15.00,  1.30),
    (2011, 1.72,  15.70,  0.70),
    (2001, 3.80,  22.40,  501.60),
    (2005, 2.45,  20.00,  1.60),
    (1998, 0.90,  21.30,  0.93),
    (2016, 1.40,  18.10,  0.72),
    (2010, 2.30,  12.40,  0.80),
    (2005, 0.94,  14.80,  0.30),
    (1964, 2.54,  10.10,  0.95),
    (1986, 2.54,  15.30,  0.70),
    (1991, 1.23,  17.10,  1.40),
    (1981, 2.00,  14.50,  0.70),
    (1988, 1.93,  12.70,  447.50),
    (1997, 3.10,  14.30,  1.60),
    (1984, 0.80,  10.40,  0.80),
    (1995, 2.60,  12.40,  1.80),
    (2007, 1.30,  17.50,  0.60),
    (1990, 2.91,  12.80,  1.60),
    (2008, 1.82,  14.20,  0.80),
    (2009, 1.80,  20.40,  0.30),
    (2010, 1.45,  16.60,  0.60),
    (2004, 0.87,  22.50,  1.30),
    (2002, 1.90,  14.70,  0.07),
    (2003, 3.10,  15.60,  0.50),
    (1962, 1.93,  20.50,  155.30),
    (1985, 3.94,  15.40,  37.70),
    (1972, 1.63,  18.10,  0.80),
    (1968, 2.00,  16.60,  1.20),
    (2006, 2.60,  18.30,  1.10),
    (1971, 2.95,  17.80,  0.90),
    (2003, 2.90,  16.60,  1.60),
    (1976, 4.60,  18.40,  121.60),
    (1994, 1.50,  19.60,  0.60),
    (1989, 1.60,  15.10,  0.94),
    (2013, 2.40,  13.30,  117.40),
    (2004, 1.50,  16.20,  2.70),
    (2002, 2.90,  14.45,  0.80),
    (2010, 3.20,  17.40,  3.00),
    (1988, 1.30,  18.40,  13.50),
    (1992, 0.63,  14.50,  9.40),
    (1995, 4.80,  12.60,  0.93),
    (1991, 3.50,  11.50,  2.20),
]


# ── Pre-compute full history ───────────────────────────────────────────────────
history: list[dict] = []
for _i, (_year, _tsh, _t4, _atpo) in enumerate(PATIENTS, start=1):
    _d, _f, _at, _r = calculate(_tsh, _t4, _atpo)
    _zone  = get_zone(_r)
    _flags = get_flags(_tsh, _t4, _atpo, _r, _f)
    history.append({
        "#":           _i,
        "Year":        _year,
        "TSH":         _tsh,
        "T4":          _t4,
        "ATPO":        _atpo,
        "Direction":   round(_d,  4),
        "Force":       round(_f,  4),
        "AT Modifier": round(_at, 4),
        "R":           round(_r,  4),
        "Zone":        _zone,
        "Flags":       _flags,           # list[str], used internally
        "FlagStr":     "; ".join(_flags),
        "Flagged":     len(_flags) > 0,
        "Label":       f"#{_i}",
    })


# ── Shared Vega-Lite config ────────────────────────────────────────────────────
VL_CONFIG = {
    "axis": {
        "grid":          True,
        "gridColor":     "#cccccc",
        "gridOpacity":   1.0,
        "domainColor":   "#888888",
        "domainWidth":   1,
        "tickColor":     "#888888",
        "labelFontSize": 11,
        "titleFontSize": 12,
    },
    "view": {"stroke": "#888888", "strokeWidth": 1},
}


# ── Chart builders ─────────────────────────────────────────────────────────────
def _axis_enc(x_min, x_max, y_min, y_max):
    """Shared x/y encoding spec (no title, with domain) used by axis line layers."""
    return {
        "x": {
            "field": "Direction (modified)", "type": "quantitative",
            "scale": {"domain": [x_min, x_max]}, "axis": None,
        },
        "y": {
            "field": "Force", "type": "quantitative",
            "scale": {"domain": [y_min, y_max]}, "axis": None,
        },
    }


def make_single_chart(direction: float, force: float, label: str, zone: str) -> dict:
    pad   = 0.5
    x_min = min(direction - pad, -pad)
    x_max = max(direction + pad,  pad)
    y_min = min(force - pad,     -pad)
    y_max = max(force + pad,      pad)
    color = ZONE_COLORS[ZONE_ORDER.index(zone)]
    pt    = [{"Direction (modified)": direction, "Force": force, "label": label}]

    # Axis lines: two-point mark_line using the same field names → guaranteed scale sharing
    h_line = [
        {"Direction (modified)": x_min, "Force": 0.0},
        {"Direction (modified)": x_max, "Force": 0.0},
    ]
    v_line = [
        {"Direction (modified)": 0.0, "Force": y_min},
        {"Direction (modified)": 0.0, "Force": y_max},
    ]
    axis_style = {"type": "line", "color": "#333333", "strokeWidth": 2.5}
    ax_enc     = _axis_enc(x_min, x_max, y_min, y_max)

    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "title":   {"text": "AAM Model — Patient Position", "fontSize": 14},
        "width":   "container",
        "height":  460,
        "config":  VL_CONFIG,
        "layer": [
            # ── Horizontal axis at y = 0 ─────────────────────────────────
            {"mark": axis_style, "data": {"values": h_line}, "encoding": ax_enc},
            # ── Vertical axis at x = 0 ───────────────────────────────────
            {"mark": axis_style, "data": {"values": v_line}, "encoding": ax_enc},
            # ── Patient point ────────────────────────────────────────────
            {
                "mark": {"type": "point", "filled": True, "color": color, "size": 130},
                "data": {"values": pt},
                "encoding": {
                    "x": {
                        "field": "Direction (modified)", "type": "quantitative",
                        "title": "Direction (modified)",
                        "scale": {"domain": [x_min, x_max]},
                    },
                    "y": {
                        "field": "Force", "type": "quantitative",
                        "title": "Force",
                        "scale": {"domain": [y_min, y_max]},
                    },
                    "tooltip": [
                        {"field": "Direction (modified)", "type": "quantitative", "format": ".4f"},
                        {"field": "Force",                "type": "quantitative", "format": ".4f"},
                    ],
                },
            },
            # ── Label ────────────────────────────────────────────────────
            {
                "mark": {
                    "type": "text", "color": color,
                    "fontSize": 11, "dx": 10, "dy": -8, "align": "left",
                },
                "data": {"values": pt},
                "encoding": {
                    "x":    {"field": "Direction (modified)", "type": "quantitative"},
                    "y":    {"field": "Force",                "type": "quantitative"},
                    "text": {"field": "label",                "type": "nominal"},
                },
            },
        ],
    }


def make_history_chart(records: list[dict]) -> dict:
    if not records:
        return {}

    x_vals = [r["Direction"] for r in records]
    y_vals = [r["Force"]     for r in records]
    pad    = 0.4
    x_min  = min(min(x_vals) - pad, -pad)
    x_max  = max(max(x_vals) + pad,  pad)
    y_min  = min(min(y_vals) - pad, -pad)
    y_max  = max(max(y_vals) + pad,  pad)

    values = [
        {
            "Direction (modified)": r["Direction"],
            "Force":                r["Force"],
            "Zone":                 r["Zone"],
            "Label":                r["Label"],
            "Year":                 str(r["Year"]),
            "R":                    r["R"],
            "TSH":                  r["TSH"],
            "T4":                   r["T4"],
            "ATPO":                 r["ATPO"],
            "Flagged":              r["Flagged"],
            "FlagStr":              r["FlagStr"] if r["FlagStr"] else "—",
        }
        for r in records
    ]

    # Axis lines: two-point mark_line with same field names → guaranteed scale sharing
    h_line = [
        {"Direction (modified)": x_min, "Force": 0.0},
        {"Direction (modified)": x_max, "Force": 0.0},
    ]
    v_line = [
        {"Direction (modified)": 0.0, "Force": y_min},
        {"Direction (modified)": 0.0, "Force": y_max},
    ]
    axis_style = {"type": "line", "color": "#333333", "strokeWidth": 2.5}
    ax_enc     = _axis_enc(x_min, x_max, y_min, y_max)

    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "title":   {"text": f"AAM Model — {len(records)} Patients", "fontSize": 14},
        "width":   "container",
        "height":  580,
        "config":  VL_CONFIG,
        "layer": [
            # ── Horizontal axis at y = 0 ─────────────────────────────────
            {"mark": axis_style, "data": {"values": h_line}, "encoding": ax_enc},
            # ── Vertical axis at x = 0 ───────────────────────────────────
            {"mark": axis_style, "data": {"values": v_line}, "encoding": ax_enc},
            # ── Patient points colored by R zone ─────────────────────────
            {
                "mark": {"type": "point", "filled": True, "size": 75},
                "data": {"values": values},
                "encoding": {
                    "x": {
                        "field": "Direction (modified)", "type": "quantitative",
                        "title": "Direction (modified)",
                        "scale": {"domain": [x_min, x_max]},
                    },
                    "y": {
                        "field": "Force", "type": "quantitative",
                        "title": "Force",
                        "scale": {"domain": [y_min, y_max]},
                    },
                    "color": {
                        "field": "Zone", "type": "nominal",
                        "scale": ZONE_VL_SCALE,
                        "legend": {
                            "title":         "R Zone",
                            "orient":        "bottom",
                            "columns":       3,
                            "labelFontSize": 10,
                        },
                    },
                    "tooltip": [
                        {"field": "Label",                "type": "nominal",      "title": "Patient"},
                        {"field": "Year",                 "type": "nominal",      "title": "Year"},
                        {"field": "TSH",                  "type": "quantitative", "title": "TSH"},
                        {"field": "T4",                   "type": "quantitative", "title": "T4"},
                        {"field": "ATPO",                 "type": "quantitative", "title": "ATPO"},
                        {"field": "Direction (modified)", "type": "quantitative", "title": "Direction", "format": ".4f"},
                        {"field": "Force",                "type": "quantitative", "title": "Force",     "format": ".4f"},
                        {"field": "R",                    "type": "quantitative", "title": "R",         "format": ".4f"},
                        {"field": "Zone",                 "type": "nominal",      "title": "Zone"},
                        {"field": "FlagStr",              "type": "nominal",      "title": "⚠ Flags"},
                    ],
                },
            },
            # ── Patient labels — red if flagged ──────────────────────────
            {
                "mark": {
                    "type": "text",
                    "fontSize": 8, "dx": 5, "dy": -6, "align": "left",
                },
                "data": {"values": values},
                "encoding": {
                    "x":    {"field": "Direction (modified)", "type": "quantitative"},
                    "y":    {"field": "Force",                "type": "quantitative"},
                    "text": {"field": "Label",                "type": "nominal"},
                    "color": {
                        "condition": {"test": "datum.Flagged", "value": "#cc0000"},
                        "value": "#444444",
                    },
                },
            },
        ],
    }


# ── Table builder with Styler ──────────────────────────────────────────────────
def make_table_df(records: list[dict]) -> "pd.io.formats.style.Styler":
    rows = []
    for r in records:
        flag_display = ("⚠️  " + r["FlagStr"]) if r["FlagStr"] else ""
        rows.append({
            "#":           r["#"],
            "Year":        r["Year"],
            "TSH":         r["TSH"],
            "T4":          r["T4"],
            "ATPO":        r["ATPO"],
            "Direction":   r["Direction"],
            "Force":       r["Force"],
            "AT Modifier": r["AT Modifier"],
            "R":           r["R"],
            "Zone":        r["Zone"],
            "Instability Flags": flag_display,
            "_flagged":    r["Flagged"],
        })
    df = pd.DataFrame(rows)

    def highlight_row(row):
        if df.loc[row.name, "_flagged"]:
            return ["background-color: #ffe4e4; color: #990000"] * len(row)
        return [""] * len(row)

    _fmt_g = lambda v: f"{v:.4g}"  # compact: no trailing zeros, max 4 sig digits
    styled = (
        df.drop(columns=["_flagged"])
          .style
          .apply(highlight_row, axis=1)
          .format({
              "TSH":         _fmt_g,
              "T4":          _fmt_g,
              "ATPO":        _fmt_g,
              "Direction":   _fmt_g,
              "Force":       _fmt_g,
              "AT Modifier": _fmt_g,
              "R":           _fmt_g,
          })
    )
    return styled


# ── Dynamic Timeline helpers ───────────────────────────────────────────────────
import calendar as _cal

MONTH_ABBR = {i: _cal.month_abbr[i] for i in range(1, 13)}

EXAMPLE_TIMELINE_INPUT = pd.DataFrame({
    "Month": [1,    3,    5,    7   ],
    "Year":  [2024, 2024, 2024, 2024],
    "TSH":   [1.8,  2.3,  3.1,  4.4 ],
    "T4":    [17.8, 16.9, 15.2, 13.4],
    "ATPO":  [90.0, 140.0, 210.0, 320.0],
})


def compute_timeline(df: pd.DataFrame) -> list[dict]:
    rows   = df.to_dict("records")
    result = []
    for i, row in enumerate(rows):
        d, f, at, r = calculate(float(row["TSH"]), float(row["T4"]), float(row["ATPO"]))
        zone       = get_zone(r)
        date_label = f"{MONTH_ABBR[int(row['Month'])]} {int(row['Year'])}"

        if i == 0:
            vel = 0.0
        else:
            prev       = rows[i - 1]
            months_gap = (int(row["Year"]) - int(prev["Year"])) * 12 + \
                         (int(row["Month"]) - int(prev["Month"]))
            vel = (r - result[i - 1]["R"]) / months_gap if months_gap > 0 else 0.0

        acc = 0.0 if i < 2 else (vel - result[i - 1]["Velocity"])

        result.append({
            "Index":        i,
            "Date":         date_label,
            "Month":        int(row["Month"]),
            "Year":         int(row["Year"]),
            "TSH":          float(row["TSH"]),
            "T4":           float(row["T4"]),
            "ATPO":         float(row["ATPO"]),
            "Direction":    round(d,   4),
            "Force":        round(f,   4),
            "AT Modifier":  round(at,  4),
            "R":            round(r,   4),
            "Zone":         zone,
            "Velocity":     round(vel, 5),
            "Acceleration": round(acc, 5),
        })
    return result


def make_trajectory_chart(timeline: list[dict]) -> dict:
    if not timeline:
        return {}
    xs   = [t["Direction"] for t in timeline]
    ys   = [t["Force"]     for t in timeline]
    pad  = 0.4
    xmin = min(min(xs) - pad, -pad)
    xmax = max(max(xs) + pad,  pad)
    ymin = min(min(ys) - pad, -pad)
    ymax = max(max(ys) + pad,  pad)

    vals   = [{"Direction": t["Direction"], "Force": t["Force"],
               "Date": t["Date"], "Index": t["Index"],
               "R": t["R"], "Zone": t["Zone"]} for t in timeline]
    h_line = [{"Direction": xmin, "Force": 0.0}, {"Direction": xmax, "Force": 0.0}]
    v_line = [{"Direction": 0.0,  "Force": ymin}, {"Direction": 0.0,  "Force": ymax}]
    ax_enc = {
        "x": {"field": "Direction", "type": "quantitative",
              "scale": {"domain": [xmin, xmax]}, "axis": None},
        "y": {"field": "Force",     "type": "quantitative",
              "scale": {"domain": [ymin, ymax]}, "axis": None},
    }
    ax_style = {"type": "line", "color": "#333333", "strokeWidth": 2.5}
    pt_enc   = {
        "x": {"field": "Direction", "type": "quantitative",
              "title": "Direction (modified)", "scale": {"domain": [xmin, xmax]}},
        "y": {"field": "Force",     "type": "quantitative",
              "title": "Force",               "scale": {"domain": [ymin, ymax]}},
    }

    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "title":   {"text": "Trajectory — Direction vs Force over Time", "fontSize": 14},
        "width":   "container",
        "height":  460,
        "config":  VL_CONFIG,
        "layer": [
            # Axis crosshairs
            {"mark": ax_style, "data": {"values": h_line}, "encoding": ax_enc},
            {"mark": ax_style, "data": {"values": v_line}, "encoding": ax_enc},
            # Dashed connecting path (ordered by Index)
            {
                "mark": {"type": "line", "strokeWidth": 1.8, "strokeDash": [5, 3], "color": "#5588bb"},
                "data": {"values": vals},
                "encoding": {**pt_enc, "order": {"field": "Index", "type": "quantitative"}},
            },
            # Points colored by R zone
            {
                "mark": {"type": "point", "filled": True, "size": 110},
                "data": {"values": vals},
                "encoding": {
                    **pt_enc,
                    "color": {
                        "field": "Zone", "type": "nominal",
                        "scale": ZONE_VL_SCALE,
                        "legend": {"title": "R Zone", "orient": "bottom"},
                    },
                    "tooltip": [
                        {"field": "Date",      "type": "nominal",      "title": "Date"},
                        {"field": "Direction", "type": "quantitative", "title": "Direction", "format": ".4f"},
                        {"field": "Force",     "type": "quantitative", "title": "Force",     "format": ".4f"},
                        {"field": "R",         "type": "quantitative", "title": "R",         "format": ".4f"},
                        {"field": "Zone",      "type": "nominal",      "title": "Zone"},
                    ],
                },
            },
            # Date labels above each point
            {
                "mark": {"type": "text", "fontSize": 10, "dy": -11, "align": "center", "color": "#333333"},
                "data": {"values": vals},
                "encoding": {
                    "x":    {"field": "Direction", "type": "quantitative"},
                    "y":    {"field": "Force",     "type": "quantitative"},
                    "text": {"field": "Date",      "type": "nominal"},
                },
            },
        ],
    }


def make_r_timeline_chart(timeline: list[dict]) -> dict:
    if len(timeline) < 2:
        return {}

    r_vals    = [{"Date": t["Date"], "R": t["R"], "Zone": t["Zone"]} for t in timeline]
    r_max_dom = max(max(t["R"] for t in timeline) * 1.2, 2.1)

    # Melt velocity + acceleration into one series table
    va_vals = []
    for t in timeline:
        va_vals.append({"Date": t["Date"], "Series": "Velocity",     "Value": t["Velocity"]})
        va_vals.append({"Date": t["Date"], "Series": "Acceleration", "Value": t["Acceleration"]})

    # Zone threshold dashed lines (using datum — x is nominal so rule spans full width)
    zone_rules = [
        {"threshold": thr, "color": ZONE_COLORS[i]}
        for i, thr in enumerate([0.45, 0.80, 1.30, 2.00])
    ]

    r_chart = {
        "title":  {"text": "R Progression Over Time", "fontSize": 13},
        "width":  "container",
        "height": 240,
        "config": VL_CONFIG,
        "layer": [
            # Zone boundary reference lines
            *[
                {
                    "mark": {
                        "type": "rule", "color": zr["color"],
                        "strokeWidth": 0.9, "strokeDash": [4, 3], "opacity": 0.7,
                    },
                    "encoding": {"y": {"datum": zr["threshold"], "type": "quantitative"}},
                }
                for zr in zone_rules
            ],
            # R line with zone-colored points
            {
                "mark": {"type": "line", "strokeWidth": 2.2, "point": True},
                "data": {"values": r_vals},
                "encoding": {
                    "x": {"field": "Date", "type": "nominal", "sort": None,
                          "title": "", "axis": {"labelAngle": 0}},
                    "y": {"field": "R", "type": "quantitative", "title": "R (radius)",
                          "scale": {"domain": [0, r_max_dom]}},
                    "color": {
                        "field": "Zone", "type": "nominal",
                        "scale": ZONE_VL_SCALE,
                        "legend": {"title": "R Zone", "orient": "right"},
                    },
                    "tooltip": [
                        {"field": "Date", "type": "nominal"},
                        {"field": "R",    "type": "quantitative", "format": ".4f"},
                        {"field": "Zone", "type": "nominal"},
                    ],
                },
            },
        ],
    }

    va_chart = {
        "title":  {"text": "Velocity & Acceleration of R", "fontSize": 13},
        "width":  "container",
        "height": 180,
        "config": VL_CONFIG,
        "layer": [
            # Zero reference line
            {
                "mark": {"type": "rule", "color": "#aaaaaa", "strokeWidth": 1},
                "encoding": {"y": {"datum": 0, "type": "quantitative"}},
            },
            {
                "mark": {"type": "line", "point": True, "strokeWidth": 2},
                "data": {"values": va_vals},
                "encoding": {
                    "x": {"field": "Date",   "type": "nominal", "sort": None,
                          "title": "", "axis": {"labelAngle": 0}},
                    "y": {"field": "Value",  "type": "quantitative", "title": "Value / month"},
                    "color": {
                        "field": "Series", "type": "nominal",
                        "scale": {"domain": ["Velocity", "Acceleration"],
                                  "range":  ["#e67e22", "#8e44ad"]},
                        "legend": {"title": "", "orient": "right"},
                    },
                    "tooltip": [
                        {"field": "Date",   "type": "nominal"},
                        {"field": "Series", "type": "nominal"},
                        {"field": "Value",  "type": "quantitative", "format": ".5f"},
                    ],
                },
            },
        ],
    }

    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "vconcat":  [r_chart, va_chart],
        "spacing":  16,
        "resolve":  {"scale": {"color": "independent"}},
    }


def generate_interpretation(timeline: list[dict]) -> list[str]:
    if len(timeline) < 2:
        return ["Add at least 2 timepoints to generate an interpretation."]

    r_vals  = [t["R"]           for t in timeline]
    dirs    = [t["Direction"]   for t in timeline]
    forces  = [t["Force"]       for t in timeline]
    atpos   = [t["ATPO"]        for t in timeline]
    vels    = [t["Velocity"]    for t in timeline]
    accs    = [t["Acceleration"] for t in timeline]
    zones   = [t["Zone"]        for t in timeline]

    notes     = []
    delta_r   = r_vals[-1] - r_vals[0]
    mono_up   = all(r_vals[i] <= r_vals[i + 1] for i in range(len(r_vals) - 1))
    mono_down = all(r_vals[i] >= r_vals[i + 1] for i in range(len(r_vals) - 1))

    if mono_up:
        notes.append(f"Progressive increase in R across all timepoints (total Δ = +{delta_r:.4f}).")
    elif mono_down:
        notes.append(f"Progressive decrease in R across all timepoints (total Δ = {delta_r:.4f}).")
    else:
        notes.append(f"Non-monotonic R trajectory — R fluctuated (total Δ = {delta_r:+.4f}).")

    dir_delta = dirs[-1] - dirs[0]
    if abs(dir_delta) > 0.03:
        drift = "rightward (TSH-dominant)" if dir_delta > 0 else "leftward (T4-dominant)"
        notes.append(f"Consistent {drift} drift in Direction axis (Δ = {dir_delta:+.4f}).")

    force_delta = forces[-1] - forces[0]
    if abs(force_delta) > 0.01:
        fw = "increasing" if force_delta > 0 else "decreasing"
        detail = "growing hard deviation from reference range" if force_delta > 0 else "hormones approaching reference range"
        notes.append(f"Force is {fw} (Δ = {force_delta:+.4f}) — {detail}.")

    nz_vels = [v for v in vels if v != 0.0]
    if nz_vels:
        avg_vel = sum(nz_vels) / len(nz_vels)
        notes.append(f"Average R progression velocity: {avg_vel:+.5f} R/month.")

    nz_accs = [a for a in accs if a != 0.0]
    if nz_accs:
        last_acc = nz_accs[-1]
        if last_acc > 0.001:
            notes.append(
                "Acceleration of destabilization detected — the rate of R increase is growing, "
                "suggesting the system is losing regulatory capacity."
            )
        elif last_acc < -0.001:
            notes.append("Deceleration detected — the rate of R progression is slowing.")
        else:
            notes.append("R velocity is approximately constant (near-zero acceleration).")

    unique_zones = list(dict.fromkeys(zones))
    if len(unique_zones) > 1:
        notes.append(f"Zone progression observed: {' → '.join(unique_zones)}.")
    else:
        notes.append(f"Patient remained in zone '{zones[-1]}' throughout the observation period.")

    atpo_delta = atpos[-1] - atpos[0]
    if atpo_delta > 30:
        notes.append(
            f"ATPO increased significantly (+{atpo_delta:.0f}), "
            "suggesting an active and progressing autoimmune process."
        )
    elif atpo_delta < -30:
        notes.append(f"ATPO decreased by {abs(atpo_delta):.0f} — possible treatment response.")

    return notes


# ── Sidebar — global summary ───────────────────────────────────────────────────
_zone_color_map = dict(zip(ZONE_ORDER, ZONE_COLORS))

with st.sidebar:
    st.header("Patient Statistics")
    st.caption("All 51 patients")

    st.subheader("R-Zone Distribution")
    zone_counts = {z: 0 for z in ZONE_ORDER}
    for row in history:
        zone_counts[row["Zone"]] += 1
    for zone in ZONE_ORDER:
        cnt = zone_counts[zone]
        st.markdown(
            f'<span style="color:{_zone_color_map[zone]};font-weight:bold">■</span> '
            f'**{zone}:** {cnt}',
            unsafe_allow_html=True,
        )

    st.divider()
    _flagged_all = [r for r in history if r["Flagged"]]
    st.subheader(f"⚠️ Hidden Instability: {len(_flagged_all)}")
    for _flag in [FLAG_A, FLAG_B, FLAG_C]:
        _cnt = sum(1 for r in history if _flag in r["Flags"])
        if _cnt:
            st.write(f"• {_flag}: **{_cnt}**")

    st.divider()
    st.subheader("R Statistics")
    avg_r   = sum(r["R"] for r in history) / len(history)
    highest = max(history, key=lambda x: x["R"])
    lowest  = min(history, key=lambda x: x["R"])

    st.metric("Average R", f"{avg_r:.4f}")
    st.write(f"**Highest R:** {highest['Label']} / {highest['Year']}")
    st.write(f"R = {highest['R']:.4f} — {highest['Zone']}")
    st.write(f"**Lowest R:** {lowest['Label']} / {lowest['Year']}")
    st.write(f"R = {lowest['R']:.4f} — {lowest['Zone']}")

    st.divider()
    st.caption(
        "⚠️ R-zones are exploratory research clusters.\n"
        "NOT medical diagnoses."
    )


# ── App layout ─────────────────────────────────────────────────────────────────
st.title("AAM Model Calculator")
tab1, tab2, tab3 = st.tabs(["Calculator", "Patient History", "Dynamic Timeline"])


# ── Tab 1: Single patient calculator ──────────────────────────────────────────
with tab1:
    st.write("Enter patient lab values below and press **Calculate** to see the results.")
    st.subheader("Patient Input")

    col1, col2, col3 = st.columns(3)
    with col1:
        TSH = st.number_input(
            "TSH", min_value=0.0, value=1.2, step=0.01, format="%.2f",
            help="Reference: 0.4 – 4.0",
        )
    with col2:
        T4 = st.number_input(
            "T4", min_value=0.0, value=25.2, step=0.1, format="%.1f",
            help="Reference: 10.8 – 22.0",
        )
    with col3:
        ATPO = st.number_input(
            "ATPO", min_value=0.0, value=0.16, step=0.01, format="%.2f",
            help="Reference: up to 35",
        )

    if st.button("Calculate", type="primary"):
        Direction_mod, Force, AT, R = calculate(TSH, T4, ATPO)
        zone  = get_zone(R)
        flags = get_flags(TSH, T4, ATPO, R, Force)

        st.subheader("Results")
        r1, r2, r3, r4, r5 = st.columns(5)
        r1.metric("Direction",   f"{Direction_mod:.4f}")
        r2.metric("Force",       f"{Force:.4f}")
        r3.metric("AT Modifier", f"{AT:.4f}")
        r4.metric("R (radius)",  f"{R:.4f}")
        r5.metric("R Zone",      zone)

        if flags:
            st.warning("⚠️ Hidden Instability Detected:  " + " | ".join(flags))

        st.subheader("Graph")
        label = f"({Direction_mod:.2f}, {Force:.2f})"
        st.vega_lite_chart(
            make_single_chart(Direction_mod, Force, label, zone),
            use_container_width=True,
        )


# ── Tab 2: Patient history + filters + chart ───────────────────────────────────
with tab2:
    st.subheader("Patient History — 51 Patients")

    # Filters
    st.write("**Filter patients:**")
    fcol1, fcol2 = st.columns([2, 2])
    with fcol1:
        filter_option = st.radio(
            "Show:",
            [
                "All patients",
                "By R zone",
                "ATPO > 35",
                "TSH > 3",
                "T4 outside reference",
                "Flagged (hidden instability)",
            ],
            horizontal=False,
            label_visibility="collapsed",
        )
    with fcol2:
        selected_zone = None
        if filter_option == "By R zone":
            selected_zone = st.selectbox("Select R zone:", ZONE_ORDER)

    # Apply filter
    if filter_option == "By R zone" and selected_zone:
        filtered = [r for r in history if r["Zone"] == selected_zone]
    elif filter_option == "ATPO > 35":
        filtered = [r for r in history if r["ATPO"] > 35]
    elif filter_option == "TSH > 3":
        filtered = [r for r in history if r["TSH"] > 3]
    elif filter_option == "T4 outside reference":
        filtered = [r for r in history if r["T4"] < T4_LOWER or r["T4"] > T4_UPPER]
    elif filter_option == "Flagged (hidden instability)":
        filtered = [r for r in history if r["Flagged"]]
    else:
        filtered = history

    st.write(f"Showing **{len(filtered)}** of 51 patients")

    # Table with row highlighting
    if filtered:
        st.dataframe(
            make_table_df(filtered),
            use_container_width=True,
            hide_index=True,
        )

        # Chart
        st.subheader("Graph")
        st.vega_lite_chart(make_history_chart(filtered), use_container_width=True)
        st.caption(
            "Red labels = hidden instability flag active. "
            "⚠️ Zones are exploratory research clusters, NOT diagnoses. "
            "Zones: " + ZONE_RANGES
        )
    else:
        st.info("No patients match the selected filter.")


# ── Tab 3: Dynamic Timeline Mode ───────────────────────────────────────────────
with tab3:
    st.subheader("Dynamic Timeline Mode")
    st.write(
        "Track one patient's endocrine trajectory over multiple measurements. "
        "Edit the table below or use the built-in example patient."
    )

    # ── Data entry ────────────────────────────────────────────────────────────
    if st.button("↺  Load Hashimoto Progression Example", key="load_example"):
        st.session_state["timeline_df"] = EXAMPLE_TIMELINE_INPUT.copy()

    if "timeline_df" not in st.session_state:
        st.session_state["timeline_df"] = EXAMPLE_TIMELINE_INPUT.copy()

    edited_df = st.data_editor(
        st.session_state["timeline_df"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Month": st.column_config.NumberColumn(
                "Month (1–12)", min_value=1, max_value=12, step=1, format="%d",
            ),
            "Year": st.column_config.NumberColumn(
                "Year", min_value=1900, max_value=2100, step=1, format="%d",
            ),
            "TSH":  st.column_config.NumberColumn("TSH",  format="%.2f"),
            "T4":   st.column_config.NumberColumn("T4",   format="%.1f"),
            "ATPO": st.column_config.NumberColumn("ATPO", format="%.1f"),
        },
        key="timeline_editor",
    )
    st.session_state["timeline_df"] = edited_df

    # ── Compute ───────────────────────────────────────────────────────────────
    try:
        tl_df = edited_df.dropna().copy()
        tl_df = tl_df[
            tl_df["Month"].between(1, 12) &
            (tl_df["TSH"]  > 0) &
            (tl_df["T4"]   > 0) &
            (tl_df["ATPO"] >= 0)
        ]
        tl_df = tl_df.sort_values(["Year", "Month"]).reset_index(drop=True)

        if len(tl_df) < 1:
            st.info("Add at least one valid measurement to begin.")
        else:
            timeline = compute_timeline(tl_df)

            # ── Results table ─────────────────────────────────────────────────
            st.subheader("Computed Timeline")
            _fmt  = lambda v: f"{v:.4g}"
            _fmtv = lambda v: f"{v:+.5f}"
            tl_display = pd.DataFrame(timeline)[[
                "Date", "TSH", "T4", "ATPO",
                "Direction", "Force", "AT Modifier", "R",
                "Zone", "Velocity", "Acceleration",
            ]]
            styled_tl = (
                tl_display.style
                .format({
                    "TSH":          _fmt,
                    "T4":           _fmt,
                    "ATPO":         _fmt,
                    "Direction":    _fmt,
                    "Force":        _fmt,
                    "AT Modifier":  _fmt,
                    "R":            _fmt,
                    "Velocity":     _fmtv,
                    "Acceleration": _fmtv,
                })
                .map(
                    lambda v: (
                        f"color: {ZONE_COLORS[ZONE_ORDER.index(v)]}; font-weight:bold"
                        if v in ZONE_ORDER else ""
                    ),
                    subset=["Zone"],
                )
            )
            st.dataframe(styled_tl, use_container_width=True, hide_index=True)

            if len(timeline) >= 2:
                # ── Trajectory graph ──────────────────────────────────────────
                st.subheader("Trajectory Graph")
                st.caption(
                    "Each point is one timepoint; the dashed line shows the path through time. "
                    "X = Direction, Y = Force."
                )
                st.vega_lite_chart(
                    make_trajectory_chart(timeline), use_container_width=True,
                )

                # ── R over time ───────────────────────────────────────────────
                st.subheader("R Progression Over Time")
                st.caption(
                    "Top: R (radius) over time with zone boundary reference lines. "
                    "Bottom: velocity and acceleration of R change."
                )
                st.vega_lite_chart(
                    make_r_timeline_chart(timeline), use_container_width=True,
                )

                # ── Interpretation ────────────────────────────────────────────
                st.subheader("Model Interpretation")
                for note in generate_interpretation(timeline):
                    st.write(f"• {note}")
                st.caption(
                    "⚠️ Interpretation is algorithmic and exploratory. "
                    "NOT a medical assessment or diagnosis."
                )
            else:
                st.info("Add at least 2 timepoints to see trajectory charts and interpretation.")

    except Exception as e:
        st.error(f"Calculation error: {e}")
