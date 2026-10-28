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
- `tests/`: physics sanity checks + Empa ordering checks

## Milestones
| Tag | What | Status |
|---|---|---|
| v0.1-m1 | Spin speed, hum frequency, power, figure of merit | done |
| v0.2-m2 | Tonal noise at 1 m, 60 deg (Gutin), SPL in dB(A) | next |
| v0.3-m3 | Blade-spacing study: 2 vs 4 even vs 4 uneven blades | |
| v0.4-m4 | WAV synthesis + loudness, sharpness, annoyance (MoSQITo, ISO 532-1) | |
| v0.5-m5 | Same scores on Empa's real data, if shared | |
| v0.6-m6 | Virtual rig: 3D model writing the Arduino CSV columns | |

## Known limitations (do not hide these)
- Chord distributions are estimates; measure real blades and update.
- Constant-pitch twist makes inner slices stall (angle of attack up to ~49 deg
  near the root of the 5152). Real blades twist less at the root.
- Airfoil data is generic low-Reynolds; FM does not change with RPM in this model.
- Tonal model only: broadband noise (where Empa found the toroidal differences,
  above 2-4 kHz) is not modelled. This is the biggest gap.
