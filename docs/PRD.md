# Propeller Noise Simulator PRD (repo copy)

Living version (source of truth): https://claude.ai/artifact/AWLGCYxQTaAqX4Mmkfa16v
This file is a condensed copy so coding sessions have the plan next to the code.
If the two disagree, the living doc wins; update this file to match.

## Overview
A Python program that predicts how loud two 5-inch drone propellers are at the
same thrust, and how annoying each sounds, before money is spent on the real test
rig. It replicates the conventional-propeller part of Empa's 2026 study
([Meister, Van Renterghem & Pieren, Acta Acustica](https://doi.org/10.1051/aacus/2026057)).
The physical rig comes later, to check the predictions.

## Question and hypothesis
At the same thrust, which propeller is loudest, and is the loudest also the most
annoying? Hypothesis: yes. Merino-Martínez (TU Delft) noted that A-weighting
already counts 3-4 kHz heavily, so the dB(A) ranking and the annoyance ranking
may agree.

## Scope
In: Gemfan 5152 (high pitch) and LR5126-2 (low pitch), 2-blade, 5.1 in; thrust
0.5 to 3.5 N in hover; microphone at 1 m, 60° below the propeller plane on the
slipstream side (Empa measured at 1.4 m and scaled to 1 m); a
blade-spacing study (2 vs 4 even vs 4 uneven); loudness and annoyance scores;
Empa's measured data if shared.

Out: CFD of the toroidal propeller; forward flight; motor/electronics noise;
room echoes; exact dB values (the goal is the ranking).

## Milestones
| # | Plain words | Technical | Tag |
|---|---|---|---|
| 1 | How fast must each prop spin for each thrust | Hover BEMT, Prandtl tip loss; RPM, tip Mach, BPF, power, FM | v0.1-m1 |
| 2 | Predict the hum at the microphone | Gutin tonal model, harmonics m = 1..10, r = 1 m, θ = 150° from the thrust direction (mic 60° below the rotor plane, slipstream side); dB and dB(A) | v0.2-m2 |
| 3 | Why an uneven 4-blade (like the Donut) sounds different | Sum one blade's Gutin tone over the blades at every shaft order, with blade angles and loading weights; 2, 4 even, 4 uneven, and +5% loading on one blade, at 2.0 N | v0.3-m3 |
| 4 | Turn each prediction into audio and score it | WAV synthesis + labelled broadband floor; dB(A), Zwicker loudness (ISO 532-1), sharpness, annoyance via MoSQITo | v0.4-m4 |
| 5 | Score Empa's real recordings (stretch) | Same metrics on Empa spectra/audio if shared | v0.5-m5 |
| 6 | Virtual rig (later) | 3D model + animated throttle sweep writing the Arduino CSV columns | v0.6-m6 |

Gutin (milestone 2):

p_m = (m B Ω / (2√2 π c₀ r)) · | T cosθ − Q c₀ / (Ω R_e²) | · J_mB(m B Ω R_e sinθ / c₀)

B = blades, Ω = rad/s, c₀ = speed of sound, R_e ≈ 0.8 R, J = Bessel function.
Check the exact form against a textbook source before coding.

Angle: θ is measured from the forward thrust direction (Gutin's convention).
Empa's microphone (Meister et al. 2026, Section 3.2, Fig. 8) is on the
downwash/slipstream side, 60° below the rotor plane, i.e. 30° from the
downstream axis, so **θ = 150°**. There cos θ < 0 and the thrust and torque
terms add. sin θ = 0.5, the same as at 30°, so the Bessel argument does not
change. θ = 30° would be the intake side, where the two terms partly cancel.

## Output CSV columns
prop, thrust_N, rpm, tip_mach, bpf_Hz, power_W (M1); spl_dBA (M2);
loudness_sone, sharpness_acum, annoyance (M4). Plus one WAV per prop per thrust.
thrust_N and power_W match the rig's Arduino log.

## Success criteria
| M | Pass test | Compared against |
|---|---|---|
| 1 | Low-pitch prop needs the highest RPM at every thrust | Empa: low-pitch BPF sits higher |
| 2 | High-pitch prop quieter in dB(A) | Empa: about 5 dB quieter |
| 3 | A shaft-frequency (n = 1) tone appears only when half-turn symmetry is broken | Empa: Donut has strongest shaft-frequency tone |
| 4 | dB(A) and annoyance rankings both reported; hypothesis answered | Merino-Martínez: rankings may agree |

## Biggest risk
Tones only. Empa found most of the toroidal difference in broadband noise above
2-4 kHz. Mitigation: a labelled broadband estimate and Empa's real data (M5).

## Timeline
M1 Oct 29-Nov 4 · M2 Nov 5-11 · M3 Nov 12-15 · M4 Nov 12-22 · M5 Nov 19-25 ·
article + video Nov 23-30 · Project due Nov 30 · physical rig Dec, if funded.
