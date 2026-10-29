"""Milestone 3 checks: blade spacing and blade-to-blade loading differences.

The uneven layout and the 5% mismatch are ESTIMATES. Do NOT change them to make
a check pass; that would be fitting the answer.
"""

import numpy as np
import pytest

from propnoise.bemt import operating_point, solve_hover
from propnoise.gutin import harmonic_pressures, to_dB, tone_spectrum
from propnoise.props import GEMFAN_5152, GEMFAN_5152_4BLADE
from propnoise.spacing import (MISMATCH_SWEEP, UNEVEN_4_DEG, SpacingCase, array_factor,
                               even_angles_deg, half_turn_symmetric, m3_cases,
                               mismatched, shaft_spectrum)

THRUST_N = 2.0   # Empa Fig. 9


@pytest.fixture(scope="module")
def ops():
    return {2: operating_point(solve_hover(GEMFAN_5152), THRUST_N),
            4: operating_point(solve_hover(GEMFAN_5152_4BLADE), THRUST_N)}


def _prop(blades):
    return GEMFAN_5152 if blades == 2 else GEMFAN_5152_4BLADE


def _spectrum(case, ops):
    return shaft_spectrum(ops[case.blades], _prop(case.blades), case.angles_deg, case.weights)


# ---- the blade sum itself -------------------------------------------------

def test_array_factor_of_uneven_layout_matches_hand_check():
    """Hand-checked values of |Σ e^(i n φ)| for 0/85/180/265, n = 1..8."""
    np.testing.assert_allclose(array_factor(range(1, 9), UNEVEN_4_DEG),
                               [0, 0.35, 0, 3.94, 0, 1.04, 0, 3.76], atol=0.005)


def test_even_spacing_array_factor_is_B_or_zero():
    for blades in (2, 3, 4, 5):
        af = array_factor(range(1, 21), even_angles_deg(blades))
        n = np.arange(1, 21)
        np.testing.assert_allclose(af, np.where(n % blades == 0, blades, 0), atol=1e-12)


# ---- physics sanity -------------------------------------------------------

@pytest.mark.parametrize("prop", [GEMFAN_5152, GEMFAN_5152_4BLADE], ids=["2-blade", "4-blade"])
def test_even_blades_match_milestone_2_gutin(prop):
    """At n = m B the shaft-order sum must reproduce M2 within 0.01 dB."""
    op = operating_point(solve_hover(prop), THRUST_N)
    s = shaft_spectrum(op, prop)
    omega = op.rpm * 2 * np.pi / 60
    _, p_m2 = harmonic_pressures(op.thrust_N, op.torque_Nm, omega, prop.blades, prop.radius_m)
    m2_db = to_dB(p_m2)
    np.testing.assert_allclose(s.spl_dB[prop.blades - 1::prop.blades][:10], m2_db, atol=0.01)
    if prop.blades == 4:   # 40 shaft orders = exactly M2's 10 BPF tones
        assert s.total_dBA == pytest.approx(tone_spectrum(op, prop).total_dBA, abs=0.01)


def test_two_blade_has_no_odd_shaft_orders(ops):
    a = m3_cases()[0]
    s = _spectrum(a, ops)
    assert np.all(s.p_rms_Pa[s.n % 2 == 1] == 0.0)
    assert np.all(s.p_rms_Pa[s.n % 2 == 0] > 0.0)


def test_symmetric_uneven_layout_has_zero_shaft_tone(ops):
    """Finding: 0/85/180/265 maps onto itself under a half-turn, so it cancels
    every odd shaft order, the shaft frequency (n = 1) included. Its new tone is
    at n = 2, which is not what Empa saw for the Donut."""
    c = m3_cases()[2]
    s = _spectrum(c, ops)
    assert s.p_rms_Pa[0] == 0.0
    assert np.all(s.p_rms_Pa[s.n % 2 == 1] == 0.0)
    assert s.p_rms_Pa[1] > 0.0            # n = 2 appears; even 4-blade has none
    assert _spectrum(m3_cases()[1], ops).p_rms_Pa[1] == 0.0


@pytest.mark.parametrize("mismatch", MISMATCH_SWEEP)
@pytest.mark.parametrize("base_key", ["a", "b", "c"])
def test_any_loading_mismatch_creates_a_shaft_tone(ops, base_key, mismatch):
    base = {c.key: c for c in m3_cases()}[base_key]
    weights = mismatched(base.weights, mismatch)
    s = shaft_spectrum(ops[base.blades], _prop(base.blades), base.angles_deg, weights)
    assert s.p_rms_Pa[0] > 0.0


def test_shaft_tone_grows_6_dB_per_doubling_of_mismatch(ops):
    """Small mismatch: the n = 1 pressure is proportional to the mismatch."""
    c = m3_cases()[2]
    levels = [shaft_spectrum(ops[4], GEMFAN_5152_4BLADE, c.angles_deg,
                             mismatched(c.weights, m)).spl_dB[0] for m in (0.01, 0.02)]
    assert levels[1] - levels[0] == pytest.approx(20 * np.log10(2), abs=0.1)


def test_loading_share_keeps_total_thrust():
    """Weights only redistribute load: equal weights of any size give the same sound."""
    op = operating_point(solve_hover(GEMFAN_5152), THRUST_N)
    one = shaft_spectrum(op, GEMFAN_5152, weights=(1.0, 1.0))
    three = shaft_spectrum(op, GEMFAN_5152, weights=(3.0, 3.0))
    np.testing.assert_allclose(one.p_rms_Pa, three.p_rms_Pa, rtol=1e-12)


# ---- Empa check 3 ---------------------------------------------------------

def test_shaft_tone_appears_only_when_half_turn_symmetry_is_broken(ops):
    """Empa check 3: a shaft-frequency (n = 1) tone appears only when half-turn
    symmetry is broken. Checked on the five cases, plus a spacing that is not
    half-turn symmetric even with equal blades."""
    cases = list(m3_cases()) + [
        SpacingCase("x", "4-blade 0/80/180/270", 4, (0.0, 80.0, 180.0, 270.0), (1.0,) * 4)]
    seen = {}
    for c in cases:
        symmetric = half_turn_symmetric(c.angles_deg, c.weights)
        has_shaft_tone = _spectrum(c, ops).p_rms_Pa[0] > 0.0
        seen[c.key] = (symmetric, has_shaft_tone)
        assert has_shaft_tone == (not symmetric), f"{c.label}: symmetric={symmetric}"
    assert seen["a"] == seen["b"] == seen["c"] == (True, False)
    assert seen["d"] == seen["e"] == seen["x"] == (False, True)
