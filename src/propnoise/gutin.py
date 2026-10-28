"""Milestone 2: how loud is the hum at the microphone?

Plain words
-----------
Each blade pushes air down (thrust) and drags air around with it (torque). As
the blades sweep past, these two forces press on the air at a steady beat: the
blade-passing frequency (BPF), the "hum" from Milestone 1. The hum is not a pure
note; it also has overtones at 2x, 3x, ... the BPF. This module works out how
strong each of the first 10 tones is at the microphone, then turns them into
one A-weighted number, dB(A), which counts tones the way human ears do.

Technical
---------
Gutin's (1936) far-field model of steady-loading ("rotational") noise from a
propeller with no forward speed. The blade forces are lumped at one effective
radius R_e and the sound field is expanded in harmonics of the BPF. The RMS
pressure of harmonic m is

    p_m = (m B Ω / (2√2 π c₀ r)) · | T cosθ − Q c₀ / (Ω R_e²) | · J_mB(m B Ω R_e sinθ / c₀)

Source: L. Gutin, "On the sound field of a rotating propeller", Phys. Z.
Sowjetunion 9 (1936); English translation NACA TM 1195 (1948). Same result in
M. E. Goldstein, Aeroacoustics (McGraw-Hill, 1976), section on propeller noise,
where the bracket is written | −T cosθ + Q c₀/(Ω R_e²) |. That is identical to
the form above because of the absolute value. The 2√2 converts peak amplitude to
RMS (the older imperial form with the 169.3 prefactor is the same equation).
NOTE: this check was made from memory of those texts; the scanned PDFs could
not be read in the session that wrote this file. Re-check against a printed copy.

Angle convention (important): θ is measured from the propeller axis on the side
the thrust points to (upstream, the side air is sucked in from). On that side
the thrust and torque terms have opposite signs and partly cancel. On the
downstream side (θ > 90°) cosθ < 0 and the two terms add. Gutin's hum is
therefore loudest a little behind the propeller plane. Empa's microphone is on
the downstream side (θ = 150°, see EMPA_THETA_DEG).
"""

from dataclasses import dataclass

import numpy as np
from scipy.special import jv

from .constants import SPEED_OF_SOUND

P_REF = 20e-6               # Pa, reference pressure for dB in air

# ASSUMPTION: all blade forces act at 80% of the tip radius (Gutin's usual
# choice; the real loading is spread along the blade).
RE_FRACTION = 0.8

# Empa's microphone (Meister et al. 2026, Section 3.2, Fig. 8) is on the
# downwash/slipstream side, 60 deg below the rotor plane, i.e. 30 deg from the
# downstream axis. In Gutin's convention (theta from the thrust direction) that
# is theta = 150 deg: cos(theta) < 0, so the thrust and torque terms add.
# sin(theta) = 0.5 as at 30 deg, so the Bessel argument is the same.
# Empa measured at 1.4 m and scaled to 1 m, so r = 1 m matches their numbers.
EMPA_DISTANCE_M = 1.0
EMPA_THETA_DEG = 150.0

# The intake side at the same angle from the plane, kept for comparison.
INTAKE_THETA_DEG = 30.0

N_HARMONICS = 10


def a_weighting_dB(f_Hz):
    """A-weighting correction in dB (IEC 61672-1:2013, Annex E).

    Plain words: ears hear low and very high notes as quieter than mid notes
    (1-5 kHz). A-weighting subtracts dB from each frequency to match that.
    It is 0 dB at 1 kHz by definition.
    """
    f2 = np.asarray(f_Hz, dtype=float) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / (
        (f2 + 20.6 ** 2)
        * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2))
        * (f2 + 12194.0 ** 2)
    )
    return 20.0 * np.log10(ra) + 2.00


def to_dB(p_rms_Pa):
    """Sound pressure level in dB re 20 µPa. Zero pressure gives -inf."""
    p = np.asarray(p_rms_Pa, dtype=float)
    with np.errstate(divide="ignore"):
        return 20.0 * np.log10(p / P_REF)


def energetic_sum_dB(levels_dB):
    """Add tones by energy (not by adding dB): 10 log10( sum 10^(L/10) )."""
    total = np.sum(10.0 ** (np.asarray(levels_dB, dtype=float) / 10.0))
    with np.errstate(divide="ignore"):
        return float(10.0 * np.log10(total))


def harmonic_pressures(thrust_N, torque_Nm, omega_rad_s, blades, radius_m,
                       r_m=EMPA_DISTANCE_M, theta_deg=EMPA_THETA_DEG,
                       c0=SPEED_OF_SOUND, n_harmonics=N_HARMONICS,
                       re_fraction=RE_FRACTION):
    """RMS pressure (Pa) of harmonics m = 1..n_harmonics, and their frequencies (Hz).

    Returns (freqs_Hz, p_rms_Pa), both arrays of length n_harmonics.
    """
    m = np.arange(1, n_harmonics + 1)
    theta = np.radians(theta_deg)
    re = re_fraction * radius_m
    loading = abs(thrust_N * np.cos(theta) - torque_Nm * c0 / (omega_rad_s * re ** 2))
    bessel = jv(m * blades, m * blades * omega_rad_s * re * np.sin(theta) / c0)
    p_rms = (m * blades * omega_rad_s / (2.0 * np.sqrt(2.0) * np.pi * c0 * r_m)) * loading * np.abs(bessel)
    freqs = m * blades * omega_rad_s / (2.0 * np.pi)
    return freqs, p_rms


@dataclass
class ToneSpectrum:
    freqs_Hz: np.ndarray      # m x BPF, m = 1..10
    p_rms_Pa: np.ndarray
    spl_dB: np.ndarray        # each tone, unweighted
    spl_dBA: np.ndarray       # each tone, A-weighted
    total_dB: float           # all tones added by energy
    total_dBA: float


def tone_spectrum(op, prop, r_m=EMPA_DISTANCE_M, theta_deg=EMPA_THETA_DEG,
                  n_harmonics=N_HARMONICS) -> ToneSpectrum:
    """Hum spectrum at the microphone for one Milestone 1 operating point."""
    omega = op.rpm * 2.0 * np.pi / 60.0
    freqs, p = harmonic_pressures(op.thrust_N, op.torque_Nm, omega, prop.blades,
                                  prop.radius_m, r_m=r_m, theta_deg=theta_deg,
                                  n_harmonics=n_harmonics)
    spl = to_dB(p)
    spl_a = spl + a_weighting_dB(freqs)
    return ToneSpectrum(freqs, p, spl, spl_a, energetic_sum_dB(spl), energetic_sum_dB(spl_a))
