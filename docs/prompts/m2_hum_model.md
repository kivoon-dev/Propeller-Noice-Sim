# Prompt for Claude Code: Milestone 2 (hum model)

Paste everything below the line into Claude Code, opened in this repo.

---

Read `CLAUDE.md` and `docs/PRD.md` first and follow their rules.

Build Milestone 2: the tonal "hum" model. Milestone 1 (`src/propnoise/bemt.py`,
tag `v0.1-m1`) already gives RPM, thrust T and torque Q for each propeller at
0.5 to 3.5 N.

1. Create `src/propnoise/gutin.py` with a function that returns the sound
   pressure of harmonics m = 1..10 of the blade-passing frequency, using Gutin's
   formula:

   p_m = (m B Ω / (2√2 π c₀ r)) · | T cosθ − Q c₀ / (Ω R_e²) | · J_mB(m B Ω R_e sinθ / c₀)

   B = blades, Ω = rad/s, c₀ = speed of sound, r = 1 m, R_e = 0.8 R,
   J = `scipy.special.jv`. θ is measured from the shaft axis: Empa's microphone
   is 60° from the propeller plane, so θ = 30°. Before coding, check this form
   against a textbook (e.g. Goldstein, Aeroacoustics, or Hanson's propeller
   noise papers) and write the source in the docstring. If the sign convention
   or the √2 differs, use the textbook version and explain the difference.
2. Convert each tone to dB (re 20 µPa) and apply A-weighting (IEC 61672 formula,
   written out in code). Sum the tones energetically to get `spl_dBA`.
3. Write `scripts/run_m2.py`: adds `spl_dB` and `spl_dBA` columns, saves
   `results/m2_hum.csv`, a chart of dB(A) vs thrust for both props, and a tone
   spectrum chart at 2.0 N.
4. Tests in `tests/test_gutin.py`:
   - Doubling the distance lowers each tone by 6 dB.
   - Zero thrust and zero torque gives zero sound.
   - The fundamental sits at the BPF from Milestone 1.
   - Sound gets louder as thrust increases.
   - Empa check: the high-pitch 5152 is quieter in dB(A) than the low-pitch
     LR5126-2 at the same thrust (Empa measured about 5 dB). Report the gap you
     get. If the ordering comes out wrong, mark the test `xfail` with an honest
     reason. Do not tune parameters to pass it.
5. Explain to me in plain words, then technical terms: why the faster-spinning
   prop is louder, and what this model leaves out (broadband noise above
   2-4 kHz, which is where Empa found the toroidal differences).
6. Run `pytest`. When everything is green: update `README.md` results and
   `CHANGELOG.md`, commit, then `git tag v0.2-m2` and push with `--tags`.

Commit after each step that works, so we can roll back to any of them.
