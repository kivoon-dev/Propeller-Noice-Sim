# Prompt for Claude Code: Milestone 4 (listen and score)

Given to Claude Code, opened in this repo, after Milestone 3 (v0.3-m3).

---

Read CLAUDE.md and docs/PRD.md, save this message as docs/prompts/m4_listen_and_score.md, then build Milestone 4 (tag v0.4-m4): turn the predicted sound into audio and score it.
Pre-checked: mosqito 1.2.1 installs and works with numpy 2.5 and scipy 1.18. Pin `mosqito==1.2.1` in requirements.txt. Calibration: a 1 kHz tone at 40/50/60 dB gives 1.006/2.03/4.07 sone with `loudness_zwst(signal, fs, field_type="free")`; `sharpness_din_st` of a 1 kHz 60 dB tone ≈ 1.0 acum. Hum-only at 2 N: 5152 ≈ 3.1 sone, LR5126-2 ≈ 4.8 sone.

1. `src/propnoise/audio.py`: `synthesize(tones, seconds, fs=48000, seed=0)` returns a signal in pascals (calibrated). It's a sum of sines from the M2/M3 tones (f, p_rms), with fixed random phases. Also add a function that saves a normalized 16-bit WAV for listening.
2. Broadband "whoosh" (ASSUMPTION, label it clearly):
   * Shape: seeded random noise, band 500 Hz–12 kHz, a broad hump at 3 kHz falling 6 dB per octave each side.
   * Speed scaling: level scales with tip speed⁵ (trailing-edge noise), i.e. +50·log10(U/U_ref) dB.
   * Reference: for the 5152 at 2 N, set its dB(A) to the 5152's tonal dB(A) plus an offset in {none, −10 dB, 0 dB}, named "none / low / high".
   * Check: measure dB(A) from the synthesized signal itself (A-weighted FFT) and confirm it.
3. `src/propnoise/psycho.py`:
   * Loudness N5: 95th percentile of `loudness_zwtv`. Also keep `loudness_zwst`.
   * Sharpness S: `sharpness_din_st`, DIN weighting.
   * Roughness R: mean of `roughness_dw`.
   * Fluctuation strength F: not in MoSQITo, so F = 0 (ASSUMPTION: steady hover).
   * Psychoacoustic annoyance (Zwicker & Fastl, Psychoacoustics: Facts and Models, 3rd ed.; cite it in the docstring):
      * w_S = (S − 1.75)·0.25·log10(N5 + 10) if S > 1.75, else 0
      * w_FR = (2.18 / N5^0.4)·(0.4·F + 0.6·R)
      * PA = N5·(1 + √(w_S² + w_FR²))
4. `scripts/run_m4.py`:
   * For both props, thrust 0.5–3.5 N in steps of 0.5, and each whoosh level, compute dB(A) (from the signal), N5, S, R and PA. Write `results/m4_scores.csv`.
   * At 2 N, print the ranking by dB(A) and by PA for each whoosh level.
   * Charts: `results/m4_rankings.png` (dB(A) rank vs annoyance rank) and `results/m4_scores_vs_thrust.png`.
   * Save 4-second listening WAVs at 2 N to `results/audio/` (2 props × 3 whoosh levels) and commit them; they're small.
   * Also score the M3 layouts at 2 N without whoosh, and report whether the once-per-turn note adds roughness.
5. Tests (`tests/test_psycho.py`, use 1-second signals so CI stays fast):
   * Calibration: 1 kHz 40 dB → 1 sone ± 0.05.
   * +10 dB → loudness ×2 ± 10%.
   * The synthesized signal's SPL matches the M2 prediction ± 0.2 dB.
   * Adding whoosh raises sharpness.
   * PA ≥ N5.
   * PA = N5 when S ≤ 1.75 and R = F = 0.
6. Report honestly:
   * Hum-only should give low S and R, so PA follows N.
   * Report both rankings for each whoosh level. If the ranking flips between levels, say clearly that the whoosh assumption decides the answer.
   * Update the README results section and CHANGELOG, plain words first.
   * Commit after each working step, tag v0.4-m4, push with tags.
7. Optional, only after 1–6: add a 4th "Score" tab to `viz/propeller_lab.html`. Show dB(A) vs annoyance bars from `m4_scores.csv` (embed the numbers), with play buttons for the 2 N WAVs in `results/audio/`.
