# Guide for Claude Code sessions on this repo

## What this project is
A high-school student's simulation of drone propeller noise. It replicates the
conventional-propeller part of Meister, Van Renterghem & Pieren (2026),
Acta Acustica 10, 57, https://doi.org/10.1051/aacus/2026057, then asks whether
"loudest" (dB(A)) and "most annoying" (loudness, sharpness, annoyance) give the
same ranking. The full plan is in `docs/PRD.md`.

The student is learning. Explain every change in plain words first, then the
technical name. Keep code readable over clever.

## Rules
1. **Run `pytest` before every commit.** Never commit red tests.
2. **One milestone = one git tag** (`v0.1-m1`, `v0.2-m2`, ...). Small commits in
   between are fine and encouraged; each commit message says what changed and why.
3. **Never edit or delete a test just to make it pass.** If an Empa check fails,
   leave it failing, mark it `@pytest.mark.xfail(reason=...)` with an honest
   reason, and tell the student. Fitting parameters to hit the answer is not allowed.
4. **Label every assumption** in code with a comment starting `ASSUMPTION:` and
   every guessed number with `ESTIMATE`.
5. **No CFD of the toroidal propeller.** It is out of scope (see PRD).
6. Keep dependencies to numpy, scipy, matplotlib, pytest, plus `mosqito` from
   Milestone 4. Ask before adding anything else.
7. Each milestone adds: code in `src/propnoise/`, a `scripts/run_mN.py`, tests in
   `tests/`, outputs in `results/`, and an entry in `CHANGELOG.md`.
8. Update `README.md` results section when numbers change.

## Layout
- `src/propnoise/props.py`: propeller geometry (chords are ESTIMATES until measured)
- `src/propnoise/airfoil.py`: lift/drag model
- `src/propnoise/bemt.py`: Milestone 1, spin speed from thrust (hover BEMT)
- `scripts/run_m1.py`: writes `results/m1_spin_speed.csv` and charts
- `src/propnoise/gutin.py`: Milestone 2, tonal hum (Gutin) and A-weighting
- `scripts/run_m2.py`: writes `results/m2_hum.csv` and charts
- `src/propnoise/spacing.py`: Milestone 3, blade angles and loading weights
  (shaft-order tones)
- `scripts/run_m3.py`: writes `results/m3_spacing.csv` and the tone ladder
- `viz/hum_bench.html`: interactive page; copies CT/CP and constants into JS
  (`tests/test_viz.py` keeps them in sync, so update the page when geometry changes)
- `tests/`: physics sanity checks + Empa ordering checks

## Milestones
| Tag | What | Status |
|---|---|---|
| v0.1-m1 | Spin speed, hum frequency, power, figure of merit | done |
| v0.2-m2 | Tonal noise at 1 m, 60 deg below rotor, theta = 150 (Gutin), dB(A) | done |
| v0.3-m3 | Blade-spacing study: 2 vs 4 even vs 4 uneven blades, loading mismatch | done |
| v0.4-m4 | WAV synthesis + loudness, sharpness, annoyance (MoSQITo, ISO 532-1) | next |
| v0.5-m5 | Same scores on Empa's real data, if shared | |
| v0.6-m6 | Virtual rig: 3D model writing the Arduino CSV columns | |

## Known limitations (do not hide these)
- Chord distributions are estimates; measure real blades and update.
- Constant-pitch twist makes inner slices stall (angle of attack up to ~49 deg
  near the root of the 5152). Real blades twist less at the root.
- Airfoil data is generic low-Reynolds; FM does not change with RPM in this model.
- Tonal model only: broadband noise (where Empa found the toroidal differences,
  above 2-4 kHz) is not modelled. This is the biggest gap.
- Gutin lumps blade forces at 0.8 R. On the intake side (theta = 30 deg) the
  thrust and torque terms cancel; for the 5152 near 2.5 N the hum nearly
  vanishes. Empa's mic is on the slipstream side (theta = 150 deg), where they add.
- M3 4-blade cases are a hypothetical 4-blade 5152, not the Donut; the uneven
  angles (0/85/180/265) and the 5% loading mismatch are ESTIMATES. Steady-loading
  Gutin makes the slow 4-blade rotor very quiet (about 11 dB(A)); real rotors add
  unsteady-loading and broadband noise that this model leaves out.
