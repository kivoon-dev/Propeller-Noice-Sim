"""Milestone 1: spin speed, hum frequency and efficiency for both propellers.

Run from the repo root:  python scripts/run_m1.py
Writes results/m1_spin_speed.csv and two charts.
"""

import csv
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from propnoise import EMPA_THRUSTS_N  # noqa: E402
from propnoise.bemt import solve_hover, sweep  # noqa: E402
from propnoise.props import PROPELLERS  # noqa: E402

RESULTS = ROOT / "results"
COLORS = {"Gemfan 5152 (high pitch)": "#2a6fdb", "Gemfan LR5126-2 (low pitch)": "#e0702b"}


def main():
    RESULTS.mkdir(exist_ok=True)
    rows = []
    for prop in PROPELLERS:
        sol = solve_hover(prop)
        print(f"\n{prop.name}: CT = {sol.ct:.5f}, CP = {sol.cp:.6f}, "
              f"angle of attack {sol.alpha_deg.min():.1f} to {sol.alpha_deg.max():.1f} deg")
        for op in sweep(prop, EMPA_THRUSTS_N):
            rows.append(asdict(op))
            print(f"  {op.thrust_N:.1f} N  {op.rpm:7.0f} rpm  tip Mach {op.tip_mach:.3f}  "
                  f"hum {op.bpf_Hz:5.0f} Hz  {op.power_W:5.1f} W  FM {op.figure_of_merit:.3f}")

    out = RESULTS / "m1_spin_speed.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in row.items()})
    print(f"\nWrote {out.relative_to(ROOT)}")

    for key, ylabel, fname in (("rpm", "Spin speed (RPM)", "m1_rpm_vs_thrust.png"),
                               ("power_W", "Shaft power (W)", "m1_power_vs_thrust.png")):
        fig, ax = plt.subplots(figsize=(6, 4))
        for prop in PROPELLERS:
            pts = [r for r in rows if r["prop_name"] == prop.name]
            ax.plot([r["thrust_N"] for r in pts], [r[key] for r in pts], "o-",
                    color=COLORS[prop.name], label=prop.name)
        ax.set_xlabel("Thrust (N)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend(frameon=False)
        ax.set_title("Milestone 1, hover BEMT (chords estimated)", fontsize=10)
        fig.tight_layout()
        fig.savefig(RESULTS / fname, dpi=150)
        plt.close(fig)
        print(f"Wrote results/{fname}")


if __name__ == "__main__":
    main()
