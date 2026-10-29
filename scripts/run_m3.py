"""Milestone 3: blade spacing and blade-to-blade loading differences at 2.0 N.

Run from the repo root:  python scripts/run_m3.py
Writes results/m3_spacing.csv and results/m3_tone_ladder.png.

Five cases (Empa Fig. 9 compares spectra at 2.0 N), all at Empa's microphone
(1 m, theta = 150 deg). The 4-blade cases use a hypothetical 4-blade Gemfan
5152 (ASSUMPTION, not the Donut). Also sweeps the loading mismatch over 1, 2, 5
and 10% and reports how the shaft-frequency (n = 1) tone grows.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from propnoise.bemt import operating_point, solve_hover  # noqa: E402
from propnoise.props import GEMFAN_5152, GEMFAN_5152_4BLADE  # noqa: E402
from propnoise.spacing import (MISMATCH_SWEEP, half_turn_symmetric, m3_cases,  # noqa: E402
                               shaft_spectrum)

RESULTS = ROOT / "results"
THRUST_N = 2.0
LADDER_ORDERS = 8          # shaft orders drawn in the chart
FLOOR_DBA = -10.0          # chart floor; tones below it (or cancelled) are not drawn
PROPS = {2: GEMFAN_5152, 4: GEMFAN_5152_4BLADE}


def main():
    RESULTS.mkdir(exist_ok=True)
    ops = {b: operating_point(solve_hover(p), THRUST_N) for b, p in PROPS.items()}
    for b, op in ops.items():
        print(f"{PROPS[b].name}: {op.rpm:.0f} rpm, shaft {op.shaft_Hz:.1f} Hz, "
              f"BPF {op.bpf_Hz:.1f} Hz, tip Mach {op.tip_mach:.3f}")

    rows = []

    def add(case, sweep_mismatch=""):
        s = shaft_spectrum(ops[case.blades], PROPS[case.blades], case.angles_deg, case.weights)
        for i in range(len(s.n)):
            rows.append({
                "case": case.key, "label": case.label, "mismatch": sweep_mismatch,
                "blades": case.blades,
                "angles_deg": "/".join(f"{a:g}" for a in case.angles_deg),
                "weights": "/".join(f"{w:g}" for w in case.weights),
                "thrust_N": THRUST_N, "rpm": ops[case.blades].rpm,
                "shaft_Hz": ops[case.blades].shaft_Hz, "n": int(s.n[i]),
                "freq_Hz": s.freqs_Hz[i], "array_factor": s.array_factor[i],
                "p_rms_Pa": s.p_rms_Pa[i], "spl_dB": s.spl_dB[i], "spl_dBA": s.spl_dBA[i],
                "total_dBA": s.total_dBA,
            })
        return s

    print(f"\nFive cases at {THRUST_N} N, 1 m, theta 150 deg (tone levels in dB(A))")
    print("  case                                 half-turn  total   n=1    n=2    n=4")
    spectra = {}
    for c in m3_cases():
        s = add(c)
        spectra[c.key] = (c, s)
        sym = "yes" if half_turn_symmetric(c.angles_deg, c.weights) else "no"
        print(f"  {c.label:36s} {sym:9s} {s.total_dBA:5.1f}  "
              + "  ".join(f"{v:5.1f}" for v in s.spl_dBA[[0, 1, 3]]))

    print("\nMismatch sweep: one blade pushes harder; level of the n = 1 tone")
    print("  mismatch  | (d) 4 uneven: dB  dB(A)  below loudest | (e) 2-blade: dB  dB(A)  below loudest")
    for m in MISMATCH_SWEEP:
        cells = []
        for c in m3_cases(m)[3:]:
            sweep_case = type(c)(f"{c.key}_{m * 100:g}pct", c.label, c.blades, c.angles_deg, c.weights)
            s = add(sweep_case, sweep_mismatch=m)
            gap = s.spl_dBA[0] - np.max(s.spl_dBA[1:])
            cells.append(f"{s.spl_dB[0]:5.1f} {s.spl_dBA[0]:6.1f} {gap:+8.1f}")
        print(f"  {m:6.0%}    |          {cells[0]}       |          {cells[1]}")

    out = RESULTS / "m3_spacing.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in row.items()})
    print(f"\nWrote {out.relative_to(ROOT)}")

    # Tone ladder: one row per case, shaft orders on the x axis
    fig, axes = plt.subplots(len(spectra), 1, figsize=(6.5, 8), sharex=True, sharey=True)
    for ax, (c, s) in zip(axes, spectra.values()):
        n = s.n[:LADDER_ORDERS]
        lv = s.spl_dBA[:LADDER_ORDERS]
        shown = np.isfinite(lv) & (lv > FLOOR_DBA)
        bpf = (n % c.blades == 0)
        for mask, color in ((shown & bpf, "#2a6fdb"), (shown & ~bpf & (n != 1), "#e0702b"),
                            (shown & (n == 1), "#c0392b")):
            ax.vlines(n[mask], FLOOR_DBA, lv[mask], color=color, lw=3)
            ax.plot(n[mask], lv[mask], "o", color=color, ms=4)
        ax.text(0.99, 0.9, f"{c.label}\nshaft {ops[c.blades].shaft_Hz:.0f} Hz, "
                f"total {s.total_dBA:.1f} dB(A)", transform=ax.transAxes,
                ha="right", va="top", fontsize=8)
        ax.grid(alpha=0.3)
    axes[-1].set_xticks(range(1, LADDER_ORDERS + 1))
    axes[-1].set_xlabel("Shaft order n (tone frequency = n x shaft frequency)")
    axes[len(axes) // 2].set_ylabel("Tone level at 1 m, dB(A)")
    axes[0].set_ylim(FLOOR_DBA, 65)
    axes[0].set_title(f"Milestone 3 at {THRUST_N} N, θ = 150°: blue = blade-pass tones, "
                      "orange = new tones, red = shaft tone (n = 1)", fontsize=8)
    fig.tight_layout()
    fig.savefig(RESULTS / "m3_tone_ladder.png", dpi=150)
    plt.close(fig)
    print("Wrote results/m3_tone_ladder.png")


if __name__ == "__main__":
    main()
