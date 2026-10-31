# Changelog

## Unreleased: Score tab
- `viz/propeller_lab.html`: fourth station, Score (M4). dB(A) and annoyance
  bars from `results/m4_scores.csv` at the nearest 0.5 N, a whoosh switch, and
  play buttons for the six 2 N WAVs in `results/audio/`.
- `tests/test_viz.py` checks the embedded scores match the CSV.

## v0.4-m4 (2026-10-31): listen and score
- Plain words: the predicted hum is now a sound you can play, with an optional
  guessed "whoosh" (rushing air) at three levels, and each sound is scored the
  way listeners judge it: loudness, sharpness, roughness and annoyance.
- `audio.py`: calibrated sum of sines in pascals (seeded phases), ASSUMPTION
  whoosh (500 Hz-12 kHz, 3 kHz hump, 6 dB/octave, level ~ tip speed^5,
  reference = 5152 hum at 2 N plus none / -10 / 0 dB), A-weighted FFT level
  check, 16-bit WAV writer.
- `psycho.py`: N5 (ISO 532-1, MoSQITo `loudness_zwtv`), DIN sharpness,
  Daniel-Weber roughness, F = 0 (ASSUMPTION), Zwicker-Fastl annoyance PA.
  `mosqito==1.2.1` pinned.
- `scripts/run_m4.py`: both props, 0.5-3.5 N, three whoosh levels ->
  `results/m4_scores.csv`, `m4_rankings.png`, `m4_scores_vs_thrust.png`,
  six 4 s WAVs at 2 N in `results/audio/`, and the M3 layouts in
  `results/m4_layouts.csv`.
- Result: at 2 N the LR5126-2 is first by dB(A) and by annoyance at every
  whoosh level, so the hypothesis holds in this model. Hum-only S is 0.5-0.7
  acum and R about 0.001 asper, so PA = N5. A whoosh 10 dB(A) below the hum
  raises dB(A) by only 0.4 dB but doubles loudness. The M3 once-per-turn note
  adds no roughness, but adds 9% loudness to the 2-blade at the same dB(A).
- 15 new tests (`tests/test_psycho.py`); 68 pass.
- Also in this release, the Propeller Lab page:
  - `viz/propeller_lab.html`: one page with three stations, Spin (M1, with the
    80 blade slices and which ones stall), Hum (M2, mic below or above) and
    Notes (M3, 2 / 4 even / 4 uneven / 4 uneven with one stronger blade, a
    one-turn rhythm strip and shaft-order note bars). Same model as the Python code.
  - Published with GitHub Pages and linked at the top of the README.
  - `tests/test_viz.py` now checks both pages, plus the Lab's 4-blade
    coefficients and stalled-slice pattern.

## v0.3-m3 (2026-10-29): blade spacing and loading mismatch
- `spacing.py`: one blade's Gutin tone at every shaft order n, summed over the
  blades with |Σ w_k e^(i n φ_k)| / Σw (angles φ_k, loading weights w_k). Equal,
  evenly spaced blades reproduce M2 within 0.01 dB.
- Hypothetical 4-blade Gemfan 5152 (ASSUMPTION, same chord, not the Donut):
  8,786 rpm at 2.0 N, shaft 146 Hz.
- `scripts/run_m3.py`: five cases at 2.0 N (2-blade, 4 even, 4 uneven
  0/85/180/265, uneven + 5% on one blade, 2-blade + 5%) and a 1/2/5/10% mismatch
  sweep. Writes `results/m3_spacing.csv` and `results/m3_tone_ladder.png`.
- Finding: 0/85/180/265 is half-turn symmetric, so it cancels every odd shaft
  order, n = 1 included; its new tone is at n = 2. The n = 1 tone appears only
  when half-turn symmetry is broken, here by a loading mismatch. It grows 6 dB
  per doubling of the mismatch; at 5% it is 7 dB(A) below the loudest tone
  for the uneven 4-blade and 24 dB(A) below for the 2-blade.
- 21 new tests, including Empa check 3 in the precise wording. PRD pass test
  updated to match. 47 pass.
- Also in this release, the Hum Bench page:
  - `viz/hum_bench.html`: interactive page with a thrust slider, animated rigs
    (downwash, sound rings to the mic, slowed top view), live readouts, three
    charts (dB(A) vs thrust, tone ladder, push vs twist), a slipstream/intake
    switch, and Web Audio playback of each prop's predicted tones.
  - Same model as the Python code: M1 CT/CP plus Gutin and A-weighting in
    JavaScript; checked to match `run_m2.py` to 0.001 dB(A).
  - `tests/test_viz.py`: fails if the page's coefficients or air constants
    drift from the Python model.

## v0.2.1-m2 (2026-10-28): Empa microphone side confirmed
- Empa's mic is on the slipstream side, 60° below the rotor plane (Meister et
  al. 2026, Section 3.2, Fig. 8): θ = 150° in Gutin's convention, not 30°.
  `EMPA_THETA_DEG` changed to 150; r = 1 m kept (Empa scaled 1.4 m to 1 m).
- The two xfails are removed because both tests now pass: dB(A) rises with
  thrust for both props, and the 5152 is quieter by +6.5 to +6.7 dB(A)
  (Empa: about 5). Not tuned; θ comes from the paper.
- New test: slipstream side (150°) is louder than intake side (30°).
- `run_m2.py` uses 150° for results and shows 30° as the comparison.
- PRD scope, milestone table and Gutin section now say θ = 150° clearly.

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
