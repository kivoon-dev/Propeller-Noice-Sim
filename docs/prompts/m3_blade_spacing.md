# Prompt for Claude Code: Milestone 3 (blade spacing)

Given to Claude Code, opened in this repo, after it proposed the array-factor
approach (each shaft order n gets one blade's Gutin tone times
|Σ e^(i·n·φ_k)|).

---

Go ahead with M3 using your array-factor approach, with these changes. First save this message as docs/prompts/m3_blade_spacing.md.

1. Symmetry problem. 0°, 85°, 180°, 265° is symmetric under a half-turn rotation, so its array factor is exactly 0 at every odd shaft order, including n = 1. I checked: |Σ e^(inφ)| for n = 1..8 is [0, 0.35, 0, 3.94, 0, 1.04, 0, 3.76]. So it cannot reproduce Empa's strongest tone at the shaft frequency. Don't let the Empa test pass on the n = 2 tone.
2. Add per-blade loading weights w_k: |Σ w_k e^(i·n·φ_k)|, with each blade carrying T·w_k/Σw and Q·w_k/Σw. Run five cases at 2.0 N (Empa Fig. 9):
   * (a) 2-blade
   * (b) 4 even
   * (c) 4 uneven 0/85/180/265 (ESTIMATE)
   * (d) case (c) with one blade +5% loading (ESTIMATE)
   * (e) 2-blade with one blade +5% loading, because real conventional props aren't perfect either
 Also sweep the mismatch over 1, 2, 5 and 10% and report how the n = 1 tone level grows.
3. 4-blade geometry. Re-run M1 BEMT with blades = 4 and the same chord. Label it as ASSUMPTION: a hypothetical 4-blade Gemfan, not the Donut.
4. Tests:
   * Even 4-blade matches the M2 Gutin result within 0.01 dB.
   * 2-blade has no odd shaft orders.
   * The symmetric uneven layout has zero n = 1 tone. This test documents the finding.
   * Any loading mismatch creates an n = 1 tone.
   * Empa check 3, stated precisely: "a shaft-frequency (n = 1) tone appears only when half-turn symmetry is broken."
5. Outputs: results/m3_spacing.csv and one tone-ladder chart with all five cases. Update the PRD's M3 pass test to the wording above. In the README, explain in plain words that the model suggests the Donut's shaft tone comes from imperfection, not from blade spacing alone, and that this is a hypothesis the real rig or Empa's data must check.
6. Housekeeping:
   * If the M1 PNGs changed only because they were redrawn (numbers the same), restore them with `git checkout -- results/m1_*.png`.
   * Keep the backup bundles until v0.3-m3 is pushed.
   * Skip GitHub Pages for now.

Commit after each working step, then tag v0.3-m3 and push with tags. Explain the results to me in plain words first, then technically.
