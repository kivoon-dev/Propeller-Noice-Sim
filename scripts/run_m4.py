"""Milestone 4: listen to the predictions and score them like a listener would.

Run from the repo root:  python scripts/run_m4.py   (takes a few minutes)
Writes results/m4_scores.csv, results/m4_layouts.csv, two charts, and six
4-second listening WAVs at 2 N in results/audio/.

For both props, every Empa thrust and each whoosh level ("none", "low",
"high"), the hum from Milestone 2 is turned into a signal, the ASSUMPTION
whoosh is added, and dB(A), loudness N5, sharpness S, roughness R and
psychoacoustic annoyance PA are measured from that signal.
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
import numpy as np  # noqa: E402

from propnoise import EMPA_THRUSTS_N  # noqa: E402
from propnoise.audio import (WHOOSH_LEVELS, save_wav, synthesize, tones_from_spectrum,  # noqa: E402
                             whoosh, whoosh_dBA)
from propnoise.bemt import operating_point, solve_hover  # noqa: E402
from propnoise.gutin import tone_spectrum  # noqa: E402
from propnoise.props import GEMFAN_5152, GEMFAN_5152_4BLADE, PROPELLERS  # noqa: E402
from propnoise.psycho import score  # noqa: E402
from propnoise.spacing import m3_cases, shaft_spectrum  # noqa: E402

RESULTS = ROOT / "results"
AUDIO = RESULTS / "audio"
SCORE_SECONDS = 2.0        # long enough for N5 and roughness, short enough to run quickly
WAV_SECONDS = 4.0
RANK_THRUST_N = 2.0
COLORS = {"Gemfan 5152 (high pitch)": "#2a6fdb", "Gemfan LR5126-2 (low pitch)": "#e0702b"}
STYLES = {"none": ":", "low": "--", "high": "-"}
SHORT = {GEMFAN_5152.name: "5152", PROPELLERS[1].name: "LR5126-2"}


def render(spec, op, level, ref, seconds):
    """Signal (Pa) for one prop and thrust; the whoosh is scaled from the reference."""
    signal = synthesize(tones_from_spectrum(spec), seconds)
    offset = WHOOSH_LEVELS[level]
    if offset is None:
        return signal, -np.inf
    w_dba = whoosh_dBA(op.tip_speed_ms, ref["dBA"] + offset, ref["tip_speed"])
    return signal + whoosh(seconds, w_dba), w_dba


def main():
    RESULTS.mkdir(exist_ok=True)
    AUDIO.mkdir(exist_ok=True)
    sols = {p.name: solve_hover(p) for p in PROPELLERS}
    ref_op = operating_point(sols[GEMFAN_5152.name], RANK_THRUST_N)
    ref = {"dBA": tone_spectrum(ref_op, GEMFAN_5152).total_dBA, "tip_speed": ref_op.tip_speed_ms}
    print(f"Whoosh reference: 5152 at {RANK_THRUST_N} N, tonal {ref['dBA']:.1f} dB(A), "
          f"tip speed {ref['tip_speed']:.1f} m/s (ASSUMPTION)")

    rows = []
    for prop in PROPELLERS:
        for thrust in EMPA_THRUSTS_N:
            op = operating_point(sols[prop.name], thrust)
            spec = tone_spectrum(op, prop)
            for level in WHOOSH_LEVELS:
                signal, w_dba = render(spec, op, level, ref, SCORE_SECONDS)
                s = score(signal)
                rows.append({"prop_name": prop.name, "thrust_N": thrust, "rpm": op.rpm,
                             "tip_mach": op.tip_mach, "bpf_Hz": op.bpf_Hz, "power_W": op.power_W,
                             "whoosh": level, "tonal_dBA_predicted": spec.total_dBA,
                             "whoosh_dBA": w_dba, **asdict(s)})
                print(f"  {SHORT[prop.name]:8s} {thrust:.1f} N  whoosh {level:4s}  "
                      f"{s.spl_dBA:5.1f} dB(A)  N5 {s.N5:6.2f} sone  S {s.S:4.2f}  "
                      f"R {s.R:.3f}  PA {s.PA:6.2f}")

    out = RESULTS / "m4_scores.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in row.items()})
    print(f"\nWrote {out.relative_to(ROOT)}")

    # Rankings at 2 N
    print(f"\nRankings at {RANK_THRUST_N} N (1 = loudest / most annoying)")
    ranks = {}
    for level in WHOOSH_LEVELS:
        at = [r for r in rows if r["thrust_N"] == RANK_THRUST_N and r["whoosh"] == level]
        by_dba = [r["prop_name"] for r in sorted(at, key=lambda r: -r["spl_dBA"])]
        by_pa = [r["prop_name"] for r in sorted(at, key=lambda r: -r["PA"])]
        ranks[level] = (at, by_dba, by_pa)
        same = "same" if by_dba == by_pa else "DIFFERENT"
        print(f"  whoosh {level:4s}: dB(A) {' > '.join(SHORT[n] for n in by_dba)}   "
              f"annoyance {' > '.join(SHORT[n] for n in by_pa)}   ({same})")
    first = {lvl: (d[0], p[0]) for lvl, (_, d, p) in ranks.items()}
    if len(set(first.values())) > 1:
        print("  NOTE: the ranking changes with the whoosh level, so the whoosh ASSUMPTION decides the answer.")
    else:
        print("  The ranking is the same at every whoosh level.")

    # Listening WAVs at 2 N, all on one full scale so loudness differences stay audible
    wavs = {}
    for prop in PROPELLERS:
        op = operating_point(sols[prop.name], RANK_THRUST_N)
        spec = tone_spectrum(op, prop)
        for level in WHOOSH_LEVELS:
            wavs[(SHORT[prop.name], level)] = render(spec, op, level, ref, WAV_SECONDS)[0]
    full_scale = max(np.max(np.abs(x)) for x in wavs.values()) / 0.9
    for (name, level), x in wavs.items():
        save_wav(AUDIO / f"m4_{name}_2N_whoosh-{level}.wav", x, full_scale_Pa=full_scale)
    print(f"Wrote {len(wavs)} WAVs to {AUDIO.relative_to(ROOT)} (shared full scale "
          f"{full_scale:.3f} Pa, so the louder files really are louder)")

    # M3 layouts at 2 N, hum only: does the once-per-turn note add roughness?
    print(f"\nM3 layouts at {RANK_THRUST_N} N, no whoosh")
    props = {2: GEMFAN_5152, 4: GEMFAN_5152_4BLADE}
    ops = {b: operating_point(solve_hover(p), RANK_THRUST_N) for b, p in props.items()}
    layout_rows = []
    for c in m3_cases():
        spec = shaft_spectrum(ops[c.blades], props[c.blades], c.angles_deg, c.weights)
        s = score(synthesize(tones_from_spectrum(spec), SCORE_SECONDS))
        has_n1 = spec.p_rms_Pa[0] > 0
        layout_rows.append({"case": c.key, "label": c.label, "has_shaft_tone": has_n1,
                            "shaft_tone_dBA": spec.spl_dBA[0], **asdict(s)})
        print(f"  {c.label:36s} shaft tone {'yes' if has_n1 else 'no ':3s}  {s.spl_dBA:5.1f} dB(A)  "
              f"N5 {s.N5:5.2f}  S {s.S:4.2f}  R {s.R:.4f} asper  PA {s.PA:5.2f}")
    for base, plus in (("c", "d"), ("a", "e")):
        r0 = next(r for r in layout_rows if r["case"] == base)["R"]
        r1 = next(r for r in layout_rows if r["case"] == plus)["R"]
        print(f"  roughness ({plus}) minus ({base}): {r1 - r0:+.4f} asper")
    out = RESULTS / "m4_layouts.csv"
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(layout_rows[0].keys()))
        writer.writeheader()
        for row in layout_rows:
            writer.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in row.items()})
    print(f"Wrote {out.relative_to(ROOT)}")

    # Chart 1: rank by dB(A) vs rank by annoyance at 2 N, one panel per whoosh level
    fig, axes = plt.subplots(1, len(ranks), figsize=(8, 3.4), sharey=True)
    for ax, (level, (at, by_dba, by_pa)) in zip(axes, ranks.items()):
        for r in at:
            name = r["prop_name"]
            y = [by_dba.index(name) + 1, by_pa.index(name) + 1]
            ax.plot([0, 1], y, "o-", color=COLORS[name], lw=2)
            ax.text(-0.06, y[0], f"{r['spl_dBA']:.1f} dB(A)", ha="right", va="center", fontsize=7)
            ax.text(1.06, y[1], f"PA {r['PA']:.1f}", ha="left", va="center", fontsize=7)
        ax.set_xlim(-0.7, 1.7)
        ax.set_xticks([0, 1], ["by dB(A)", "by annoyance"])
        ax.set_title(f"whoosh: {level}", fontsize=9)
        ax.grid(alpha=0.3, axis="y")
    axes[0].set_ylim(2.5, 0.5)
    axes[0].set_yticks([1, 2], ["1st\n(worst)", "2nd"])
    handles = [plt.Line2D([], [], color=c, marker="o", lw=2) for c in COLORS.values()]
    fig.legend(handles, [SHORT[n] for n in COLORS], loc="lower center", ncol=2, frameon=False, fontsize=8)
    fig.suptitle(f"Milestone 4 at {RANK_THRUST_N} N: is the loudest also the most annoying?", fontsize=10)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(RESULTS / "m4_rankings.png", dpi=150)
    plt.close(fig)
    print("Wrote results/m4_rankings.png")

    # Chart 2: scores vs thrust
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), sharex=True)
    for ax, (key, label) in zip(axes.flat, (("spl_dBA", "dB(A), from the signal"),
                                            ("N5", "Loudness N5 (sone)"),
                                            ("S", "Sharpness S (acum)"),
                                            ("PA", "Annoyance PA"))):
        for prop in PROPELLERS:
            for level in WHOOSH_LEVELS:
                pts = [r for r in rows if r["prop_name"] == prop.name and r["whoosh"] == level]
                ax.plot([r["thrust_N"] for r in pts], [r[key] for r in pts], STYLES[level],
                        color=COLORS[prop.name], marker="o", ms=3,
                        label=f"{SHORT[prop.name]}, whoosh {level}")
        if key == "S":
            ax.axhline(1.75, color="0.5", lw=0.8)
            ax.text(0.5, 1.78, "1.75: sharpness starts to add annoyance", fontsize=7, color="0.4")
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("Thrust (N)")
    axes[0, 0].legend(frameon=False, fontsize=7)
    fig.suptitle("Milestone 4: hum (Gutin) + ASSUMPTION whoosh, 1 m, θ = 150°", fontsize=10)
    fig.tight_layout()
    fig.savefig(RESULTS / "m4_scores_vs_thrust.png", dpi=150)
    plt.close(fig)
    print("Wrote results/m4_scores_vs_thrust.png")


if __name__ == "__main__":
    main()
