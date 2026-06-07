import math
import matplotlib.pyplot as plt


# --- Reference ranges ---
TSH_LOWER = 0.4
TSH_UPPER = 4.0
T4_LOWER = 10.8
T4_UPPER = 22.0
ATPO_REF = 35


# 1. Soft deviation: ln(1 + |x - center| / center), with sign preservation
def soft_deviation(value, lower, upper):
    center = (lower + upper) / 2
    distance = abs(value - center)
    magnitude = math.log(1 + distance / center)
    sign = 1 if value >= center else -1
    return sign * magnitude


# 2. Edge sensitivity
def edge_sensitivity(value, lower, upper):
    reference_range = upper - lower
    if lower <= value <= upper:
        distance_to_nearest_border = min(value - lower, upper - value)
        edge = 1 + (1 - distance_to_nearest_border / reference_range) ** 2
    else:
        edge = 1.0
    return edge


# 3. Hard deviation
def hard_deviation(value, lower, upper):
    if value > upper:
        return (value - upper) / upper
    elif value < lower:
        return (lower - value) / lower
    else:
        return 0.0


# 4. ATPO modifier
def atpo_modifier(atpo):
    return 0.5 * (math.log10(1 + atpo / 35)) ** 1.5


# --- Patient data: (year, TSH, T4, ATPO) ---
patients = [
    (2009, 1.2,  25.2,  0.16),
    (1993, 0.4,  58.6,  68.8),
    (1999, 0.5,  18.5,  0.69),
    (2008, 0.95, 18.6,  53.7),
    (1996, 0.82, 17.3,  0.5),
    (1985, 1.1,  22.7,  254.9),
    (1992, 1.64, 17.3,  1.6),
    (2000, 1.3,  13.6,  3.4),
    (2004, 1.93, 17.0,  1.4),
    (1979, 1.22, 15.0,  1.3),
    (2011, 1.72, 15.7,  0.7),
    (2001, 3.8,  22.4,  501.6),
    (2005, 2.45, 20.0,  1.6),
    (1998, 0.9,  21.3,  0.93),
    (2016, 1.4,  18.1,  0.72),
]


# --- Calculate results for all patients ---
results = []

for year, TSH, T4, ATPO in patients:
    soft_TSH = soft_deviation(TSH, TSH_LOWER, TSH_UPPER)
    soft_T4  = soft_deviation(T4,  T4_LOWER,  T4_UPPER)

    edge_TSH = edge_sensitivity(TSH, TSH_LOWER, TSH_UPPER)
    edge_T4  = edge_sensitivity(T4,  T4_LOWER,  T4_UPPER)

    hard_TSH = hard_deviation(TSH, TSH_LOWER, TSH_UPPER)
    hard_T4  = hard_deviation(T4,  T4_LOWER,  T4_UPPER)

    Direction    = (soft_TSH * edge_TSH) - (soft_T4 * edge_T4)
    Force        = math.log(1 + hard_TSH + hard_T4)
    AT           = atpo_modifier(ATPO)
    Direction_mod = Direction * (1 + AT)
    R            = math.sqrt(Direction_mod ** 2 + Force ** 2)

    results.append({
        "year":      year,
        "Direction": Direction_mod,
        "Force":     Force,
        "AT":        AT,
        "R":         R,
    })


# --- Print results table ---
print("=== AAM Model Results ===\n")
header = f"{'Year':<6}  {'Direction':>10}  {'Force':>8}  {'AT modifier':>11}  {'R':>8}"
print(header)
print("-" * len(header))
for r in results:
    print(
        f"{r['year']:<6}  "
        f"{r['Direction']:>10.4f}  "
        f"{r['Force']:>8.4f}  "
        f"{r['AT']:>11.4f}  "
        f"{r['R']:>8.4f}"
    )


# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 8))

ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
ax.grid(True, linestyle=":", alpha=0.5)

for r in results:
    x = r["Direction"]
    y = r["Force"]
    ax.scatter(x, y, color="steelblue", s=70, zorder=5)
    ax.annotate(
        str(r["year"]),
        (x, y),
        textcoords="offset points",
        xytext=(6, 4),
        fontsize=8,
        color="darkblue",
    )

ax.set_xlabel("Direction (modified)", fontsize=12)
ax.set_ylabel("Force", fontsize=12)
ax.set_title("AAM Model — All Patients", fontsize=14)

plt.tight_layout()
plt.savefig("aam_plot.png", dpi=150)
plt.show()
print("\nPlot saved as aam_plot.png")
