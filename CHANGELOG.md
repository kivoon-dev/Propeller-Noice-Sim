# Changelog

## v0.2-m2 (2026-10-28): hum model
- Gutin tonal model for BPF harmonics m = 1..10 at 1 m (`gutin.py`), checked
  against Gutin 1936 / Goldstein 1976 (from memory; scans not readable).
- A-weighting written out from IEC 61672 and checked against its table;
  tones summed by energy into `spl_dBA`.
- `scripts/run_m2.py` writes `results/m2_hum.csv` (adds `spl_dB`, `spl_dBA`),
  a dB(A)-vs-thrust chart and a 2.0 N tone spectrum.
- 19 tests pass, 2 xfail on purpose. At θ = 30° (upstream) the thrust and
  torque terms cancel for the 5152 near 2.5 N, so "louder with thrust" fails for
  the 5152 and the Empa dB(A) ordering fails at 0.5 N. Not tuned. Wake side
  (θ = 150°) gives LR5126-2 louder by +6.7 dB(A) (Empa: about 5).
- Open: confirm which side of the propeller Empa's microphone was on.

## v0.1-m1 (2026-10-28): spin-speed model
- Hover blade element momentum theory with Prandtl tip loss (`bemt.py`).
- Geometry for Gemfan 5152 and LR5126-2 (chords estimated).
- `scripts/run_m1.py` writes RPM, tip Mach, hum frequency, power, figure of merit
  for 0.5 to 3.5 N.
- 12 tests pass, including both Empa orderings: the low-pitch prop spins faster
  (higher hum) and has the higher figure of merit (0.68 vs 0.61).
- GitHub Actions runs the tests on every push.
