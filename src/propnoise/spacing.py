"""Milestone 3: what changes when the blades are not all alike or not evenly spaced?

Plain words
-----------
Each blade on its own makes a hum at the shaft frequency (once per turn) and all
its multiples. With identical, evenly spaced blades, most of these tones cancel
between blades: only every B-th one survives, which is the blade-passing hum from
Milestone 2. Move a blade, or let one blade push a little harder than the others,
and the cancelling is no longer perfect, so new tones appear at shaft orders that
used to be silent.

Technical
---------
Gutin's model for one blade gives shaft-order harmonics n = 1, 2, ... with Bessel
order n. Blade k sits at angle phi_k and carries a share s_k = w_k / sum(w) of the
total thrust T and torque Q. Its tone at order n has the same size as a single
blade carrying all the load, times s_k, and a phase n * phi_k. Adding the blades:

    p_n = (n Ω / (2√2 π c₀ r)) · |T cosθ − Q c₀/(Ω R_e²)| · J_n(n Ω R_e sinθ / c₀)
          · |Σ_k w_k e^(i n φ_k)| / Σ_k w_k

For B equal, evenly spaced blades |Σ e^(i n φ_k)| is B when n is a multiple of B
and 0 otherwise, which gives back the Milestone 2 formula with m = n / B.

ASSUMPTION: every blade sees the same inflow (Milestone 1 BEMT for the whole
rotor), so moving a blade changes only its phase, not its aerodynamics. A loading
weight w_k is a stand-in for any small blade-to-blade difference (pitch, chord,
manufacturing) that makes one blade push harder.
"""

from dataclasses import dataclass

import numpy as np
from scipy.special import jv

from .constants import SPEED_OF_SOUND
from .gutin import (EMPA_DISTANCE_M, EMPA_THETA_DEG, RE_FRACTION, a_weighting_dB,
                    energetic_sum_dB, to_dB)

# Shaft orders kept: 40 covers the first 10 blade-pass tones of a 4-blade rotor,
# the same tones Milestone 2 used.
N_SHAFT_ORDERS = 40

# Below this the blade sum is floating-point rounding of an exact zero.
_ZERO_TOL = 1e-9


def even_angles_deg(blades):
    """Evenly spaced blade angles, starting at 0 deg."""
    return tuple(360.0 * k / blades for k in range(blades))


def array_factor(n, angles_deg, weights=None):
    """|Σ w_k e^(i n φ_k)| for shaft order(s) n. Equal weights of 1 if not given."""
    phi = np.radians(np.asarray(angles_deg, dtype=float))
    w = np.ones_like(phi) if weights is None else np.asarray(weights, dtype=float)
    n = np.atleast_1d(np.asarray(n, dtype=float))
    af = np.abs(np.exp(1j * np.outer(n, phi)) @ w)
    af[af < _ZERO_TOL * w.sum()] = 0.0
    return af


def shaft_order_pressures(thrust_N, torque_Nm, omega_rad_s, radius_m, angles_deg,
                          weights=None, r_m=EMPA_DISTANCE_M, theta_deg=EMPA_THETA_DEG,
                          c0=SPEED_OF_SOUND, n_orders=N_SHAFT_ORDERS,
                          re_fraction=RE_FRACTION):
    """RMS pressure (Pa) of shaft orders n = 1..n_orders, and their frequencies (Hz).

    thrust_N and torque_Nm are rotor totals; each blade gets the share w_k / Σw.
    Returns (n, freqs_Hz, array_factor, p_rms_Pa).
    """
    w = np.ones(len(angles_deg)) if weights is None else np.asarray(weights, dtype=float)
    n = np.arange(1, n_orders + 1)
    theta = np.radians(theta_deg)
    re = re_fraction * radius_m
    loading = abs(thrust_N * np.cos(theta) - torque_Nm * c0 / (omega_rad_s * re ** 2))
    bessel = jv(n, n * omega_rad_s * re * np.sin(theta) / c0)
    one_blade = (n * omega_rad_s / (2.0 * np.sqrt(2.0) * np.pi * c0 * r_m)) * loading * np.abs(bessel)
    af = array_factor(n, angles_deg, w)
    freqs = n * omega_rad_s / (2.0 * np.pi)
    return n, freqs, af, one_blade * af / w.sum()


# ESTIMATE: an uneven 4-blade layout. The Donut's real blade angles are not
# known. Note it is symmetric under a half-turn (phi and phi + 180 deg), so on
# its own it cancels every odd shaft order, n = 1 included.
UNEVEN_4_DEG = (0.0, 85.0, 180.0, 265.0)

# ESTIMATE: one blade carries 5% more load than the others.
MISMATCH = 0.05
MISMATCH_SWEEP = (0.01, 0.02, 0.05, 0.10)


@dataclass(frozen=True)
class SpacingCase:
    key: str
    label: str
    blades: int
    angles_deg: tuple
    weights: tuple


def mismatched(weights, mismatch):
    """Same weights with blade 0 pushing harder by the given fraction."""
    return (weights[0] * (1.0 + mismatch),) + tuple(weights[1:])


def m3_cases(mismatch=MISMATCH):
    """The five Milestone 3 cases (Empa Fig. 9 compares spectra at 2.0 N)."""
    pct = f"+{mismatch:.0%}"
    return (
        SpacingCase("a", "(a) 2-blade", 2, even_angles_deg(2), (1.0, 1.0)),
        SpacingCase("b", "(b) 4-blade even", 4, even_angles_deg(4), (1.0,) * 4),
        SpacingCase("c", "(c) 4-blade uneven 0/85/180/265", 4, UNEVEN_4_DEG, (1.0,) * 4),
        SpacingCase("d", f"(d) case c, one blade {pct}", 4, UNEVEN_4_DEG,
                    mismatched((1.0,) * 4, mismatch)),
        SpacingCase("e", f"(e) 2-blade, one blade {pct}", 2, even_angles_deg(2),
                    mismatched((1.0, 1.0), mismatch)),
    )


def half_turn_symmetric(angles_deg, weights=None, tol_deg=1e-6):
    """True if turning the rotor by 180 deg maps every blade onto an equal blade."""
    w = np.ones(len(angles_deg)) if weights is None else np.asarray(weights, dtype=float)
    a = np.mod(np.asarray(angles_deg, dtype=float), 360.0)
    for ak, wk in zip(a, w):
        d = np.abs(np.mod(a - (ak + 180.0) + 180.0, 360.0) - 180.0)
        if not np.any((d < tol_deg) & np.isclose(w, wk)):
            return False
    return True


@dataclass
class ShaftSpectrum:
    n: np.ndarray             # shaft orders 1..40
    freqs_Hz: np.ndarray      # n x shaft frequency
    array_factor: np.ndarray  # |Σ w_k e^(i n φ_k)|
    p_rms_Pa: np.ndarray
    spl_dB: np.ndarray        # -inf where a tone cancels exactly
    spl_dBA: np.ndarray
    total_dB: float
    total_dBA: float


def shaft_spectrum(op, prop, angles_deg=None, weights=None, r_m=EMPA_DISTANCE_M,
                   theta_deg=EMPA_THETA_DEG, n_orders=N_SHAFT_ORDERS) -> ShaftSpectrum:
    """Tones at every shaft order for one Milestone 1 operating point.

    angles_deg defaults to even spacing for prop.blades; weights default to equal.
    """
    if angles_deg is None:
        angles_deg = even_angles_deg(prop.blades)
    if len(angles_deg) != prop.blades:
        raise ValueError(f"{len(angles_deg)} blade angles for a {prop.blades}-blade prop")
    omega = op.rpm * 2.0 * np.pi / 60.0
    n, freqs, af, p = shaft_order_pressures(op.thrust_N, op.torque_Nm, omega, prop.radius_m,
                                            angles_deg, weights, r_m=r_m,
                                            theta_deg=theta_deg, n_orders=n_orders)
    spl = to_dB(p)
    spl_a = spl + a_weighting_dB(freqs)
    return ShaftSpectrum(n, freqs, af, p, spl, spl_a,
                         energetic_sum_dB(spl), energetic_sum_dB(spl_a))
