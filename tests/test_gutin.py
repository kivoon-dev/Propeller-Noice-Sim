"""Milestone 2 checks.

Same two kinds of test as Milestone 1: physics sanity, and Empa orderings.
If an Empa check fails, it is marked xfail with the honest reason. Do NOT
change theta, R_e or the geometry to make it pass; that would be fitting the
answer.
"""

import numpy as np
import pytest

from propnoise import EMPA_THRUSTS_N
from propnoise.bemt import operating_point, solve_hover, sweep
from propnoise.gutin import a_weighting_dB, harmonic_pressures, tone_spectrum
from propnoise.props import GEMFAN_5152, GEMFAN_LR5126, PROPELLERS

UPSTREAM_CANCELLATION = (
    "At theta = 30 deg (upstream side) Gutin's thrust term T cos(theta) and torque "
    "term Q c0/(Omega Re^2) have opposite signs. For the 5152 they cancel almost "
    "exactly near 2.5 N (2 dB(A)), because the model puts all blade force at one "
    "radius. Not tuned away. On the wake side (theta = 150 deg) this test passes."
)


@pytest.fixture(scope="module", params=PROPELLERS, ids=lambda p: p.name.split()[1])
def prop_and_solution(request):
    return request.param, solve_hover(request.param)


# ---- physics sanity -------------------------------------------------------

def test_a_weighting_matches_iec_table():
    """IEC 61672-1 Table 3: -19.1 dB at 100 Hz, 0.0 at 1 kHz, +1.0 at 4 kHz."""
    np.testing.assert_allclose(a_weighting_dB([100, 1000, 4000]), [-19.1, 0.0, 1.0], atol=0.05)


def test_doubling_distance_lowers_each_tone_by_6_dB(prop_and_solution):
    prop, sol = prop_and_solution
    op = operating_point(sol, 2.0)
    near = tone_spectrum(op, prop, r_m=1.0)
    far = tone_spectrum(op, prop, r_m=2.0)
    np.testing.assert_allclose(near.spl_dB - far.spl_dB, 20 * np.log10(2), atol=1e-9)


def test_zero_thrust_and_zero_torque_is_silent():
    _, p = harmonic_pressures(thrust_N=0.0, torque_Nm=0.0, omega_rad_s=1300.0,
                              blades=2, radius_m=0.065)
    assert np.all(p == 0.0)


def test_fundamental_sits_at_milestone_1_bpf(prop_and_solution):
    prop, sol = prop_and_solution
    op = operating_point(sol, 2.0)
    s = tone_spectrum(op, prop)
    assert s.freqs_Hz[0] == pytest.approx(op.bpf_Hz)
    np.testing.assert_allclose(s.freqs_Hz, op.bpf_Hz * np.arange(1, 11))


@pytest.mark.parametrize("prop", [
    pytest.param(GEMFAN_5152, id="5152",
                 marks=pytest.mark.xfail(reason=UPSTREAM_CANCELLATION, strict=True)),
    pytest.param(GEMFAN_LR5126, id="LR5126-2"),
])
def test_louder_as_thrust_increases(prop):
    levels = [tone_spectrum(op, prop).total_dBA for op in sweep(prop, EMPA_THRUSTS_N)]
    assert np.all(np.diff(levels) > 0), f"dB(A) vs thrust: {np.round(levels, 1)}"


# ---- Empa checks ----------------------------------------------------------

@pytest.mark.xfail(strict=True, reason=(
    "Empa: 5152 about 5 dB(A) quieter than LR5126-2. Model at theta = 30 deg: "
    "gap is -9.5 dB(A) at 0.5 N (wrong way), +0.6 at 1.0 N, then +11 to +53 "
    "(far too big) from 1.5 N up, all caused by the upstream thrust/torque "
    "cancellation. Wake side (theta = 150 deg) gives +6.5 to +6.7 at every thrust, "
    "but the mic side is not yet confirmed from the paper, so it is not used here."))
def test_high_pitch_is_quieter_in_dBA_at_same_thrust():
    hi = [tone_spectrum(op, GEMFAN_5152).total_dBA for op in sweep(GEMFAN_5152, EMPA_THRUSTS_N)]
    lo = [tone_spectrum(op, GEMFAN_LR5126).total_dBA for op in sweep(GEMFAN_LR5126, EMPA_THRUSTS_N)]
    gap = np.array(lo) - np.array(hi)
    print("LR5126-2 minus 5152, dB(A):", dict(zip(EMPA_THRUSTS_N, np.round(gap, 1))))
    assert np.all(gap > 0), f"gap by thrust: {np.round(gap, 1)}"
