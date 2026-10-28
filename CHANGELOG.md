# Changelog

## v0.1-m1 (2026-10-28): spin-speed model
- Hover blade element momentum theory with Prandtl tip loss (`bemt.py`).
- Geometry for Gemfan 5152 and LR5126-2 (chords estimated).
- `scripts/run_m1.py` writes RPM, tip Mach, hum frequency, power, figure of merit
  for 0.5 to 3.5 N.
- 12 tests pass, including both Empa orderings: the low-pitch prop spins faster
  (higher hum) and has the higher figure of merit (0.68 vs 0.61).
- GitHub Actions runs the tests on every push.
