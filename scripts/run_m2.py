"""Milestone 2: how loud is each propeller's hum at Empa's microphone?

Run from the repo root:  python scripts/run_m2.py
Writes results/m2_hum.csv and two charts.

Main results use Empa's microphone position: 1 m, 60 deg below the rotor plane
on the slipstream side, theta = 150 deg in Gutin's convention (Meister et al.
2026, Section 3.2, Fig. 8). The intake side (theta = 30 deg) is printed and
drawn as a dashed line for comparison.
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
from propnoise.bemt import sweep  # noqa: E402
from propnoise.gutin import EMPA_THETA_DEG, INTAKE_THETA_DEG, tone_spectrum  # noqa: E402
from propnoise.props import GEMFAN_5152, GEMFAN_LR5126, PROPELLERS  # noqa: E402

RESULTS = ROOT / "results"
COLORS = {"Gemfan 5152 (high pitch)": "#2a6fdb", "Gemfan LR5126-2 (low pitch)": "#e0702b"}
SPECTRUM_THRUST_N = 2.0


def main():
    RESULTS.mkdir(exist_ok=True)
    rows = []
    intake = {}
    for prop in PROPELLERS:
        print(f"\n{prop.name}")
        print(f"  thrust   dB    dB(A)   | intake side (theta {INTAKE_THETA_DEG:.0f}): dB(A)")
        intake[prop.name] = []
        for op in sweep(prop, EMPA_THRUSTS_N):
            s = tone_spectrum(op, prop)
            up = tone_spectrum(op, prop, theta_deg=INTAKE_THETA_DEG)
            intake[prop.name].append(up.total_dBA)
            rows.append({**asdict(op), "spl_dB": s.total_dB, "spl_dBA": s.total_dBA})
            print(f"  {op.thrust_N:.1f} N  {s.total_dB:5.1f}  {s.total_dBA:5.1f}   | {up.total_dBA:5.1f}")

    print("\nEmpa check: LR5126-2 minus 5152 in dB(A) at the same thrust (Empa: about +5)")
    hi = [r for r in rows if r["prop_name"] == GEMFAN_5152.name]
    lo = [r for r in rows if r["prop_name"] == GEMFAN_LR5126.name]
    for i, (h, l) in enumerate(zip(hi, lo)):
        intake_gap = intake[GEMFAN_LR5126.name][i] - intake[GEMFAN_5152.name][i]
        print(f"  {h['thrust_N']:.1f} N  theta {EMPA_THETA_DEG:.0f}: {l['spl_dBA'] - h['spl_dBA']:+5.1f}   "
              f"(intake side, theta {INTAKE_THETA_DEG:.0f}: {intake_gap:+6.1f})")

    out = RESULTS / "m2_hum.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in row.items()})
    print(f"\nWrote {out.relative_to(ROOT)}")

    # Chart 1: dB(A) vs thrust
    fig, ax = plt.subplots(figsize=(6, 4))
    for prop in PROPELLERS:
        pts = [r for r in rows if r["prop_name"] == prop.name]
        thrusts = [r["thrust_N"] for r in pts]
        ax.plot(thrusts, [r["spl_dBA"] for r in pts], "o-", color=COLORS[prop.name],
                label=f"{prop.name}, Empa mic (θ = {EMPA_THETA_DEG:.0f}°)")
        ax.plot(thrusts, intake[prop.name], "--", color=COLORS[prop.name], alpha=0.6,
                label=f"same prop, intake side (θ = {INTAKE_THETA_DEG:.0f}°)")
    ax.set_xlabel("Thrust (N)")
    ax.set_ylabel("Hum level at 1 m, dB(A)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Milestone 2, Gutin tones only (no broadband noise)", fontsize=10)
    fig.tight_layout()
    fig.savefig(RESULTS / "m2_dBA_vs_thrust.png", dpi=150)
    plt.close(fig)
    print("Wrote results/m2_dBA_vs_thrust.png")

    # Chart 2: tone spectrum at 2.0 N
    fig, ax = plt.subplots(figsize=(6, 4))
    for prop, offset in zip(PROPELLERS, (-0.012, 0.012)):
        op = sweep(prop, [SPECTRUM_THRUST_N])[0]
        s = tone_spectrum(op, prop)
        ax.vlines(s.freqs_Hz * (1 + offset), -40, s.spl_dBA, color=COLORS[prop.name], lw=2)
        ax.plot(s.freqs_Hz * (1 + offset), s.spl_dBA, "o", color=COLORS[prop.name],
                label=f"{prop.name}, BPF {op.bpf_Hz:.0f} Hz")
    ax.set_xscale("log")
    ax.set_ylim(-40, None)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Tone level, dB(A)")
    ax.grid(alpha=0.3, which="both")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"Hum tones m = 1..10 at {SPECTRUM_THRUST_N} N, 1 m, θ = {EMPA_THETA_DEG:.0f}°",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(RESULTS / "m2_spectrum_2N.png", dpi=150)
    plt.close(fig)
    print("Wrote results/m2_spectrum_2N.png")


if __name__ == "__main__":
    main()
