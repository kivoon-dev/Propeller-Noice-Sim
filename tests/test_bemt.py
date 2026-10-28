"""Milestone 1 checks.

Two kinds of test:
  * physics sanity: things that must be true for any working propeller model
  * Empa checks: orderings reported by Meister et al. (2026). If one of these
    fails, report it honestly. Do NOT tweak the airfoil or geometry just to
    make it pass; that would be fitting the answer.
"""

import numpy as np
import pytest

from propnoise import EMPA_THRUSTS_N
from propnoise.bemt import operating_point, solve_hover, sweep
from propnoise.props import GEMFAN_5152, GEMFAN_LR5126, PROPELLERS


@pytest.fixture(scope="module", params=PROPELLERS, ids=lambda p: p.name.split()[1])
def solution(request):
    return solve_hover(request.param)


# ---- physics sanity -------------------------------------------------------

def test_momentum_balance_converges_at_every_slice(solution):
    assert np.max(np.abs(solution.residual)) < 1e-9


def test_four_times_thrust_needs_twice_the_rpm(solution):
    a = operating_point(solution, 0.5)
    b = operating_point(solution, 2.0)
    assert b.rpm / a.rpm == pytest.approx(2.0, rel=1e-9)


def test_figure_of_merit_between_zero_and_one(solution):
    fm = operating_point(solution, 2.0).figure_of_merit
    assert 0.0 < fm < 1.0


def test_hum_is_blades_times_shaft_frequency(solution):
    op = operating_point(solution, 2.0)
    assert op.bpf_Hz == pytest.approx(solution.prop.blades * op.rpm / 60)


def test_tip_stays_well_below_speed_of_sound():
    for prop in PROPELLERS:
        assert sweep(prop, [3.5])[0].tip_mach < 0.5


def test_spin_speed_in_realistic_range():
    """5-inch props making 0.5-3.5 N run roughly 5,000-25,000 RPM."""
    for prop in PROPELLERS:
        for op in sweep(prop, EMPA_THRUSTS_N):
            assert 5_000 < op.rpm < 25_000


# ---- Empa checks ----------------------------------------------------------

def test_low_pitch_spins_faster_so_its_hum_is_higher():
    """Empa: the low-pitch prop's blade-passing tone sits at a higher frequency."""
    for hi, lo in zip(sweep(GEMFAN_5152, EMPA_THRUSTS_N), sweep(GEMFAN_LR5126, EMPA_THRUSTS_N)):
        assert lo.bpf_Hz > hi.bpf_Hz


def test_low_pitch_is_more_efficient_than_high_pitch():
    """Empa: high-pitch prop had the lowest figure of merit, low-pitch the highest."""
    hi = sweep(GEMFAN_5152, [2.0])[0].figure_of_merit
    lo = sweep(GEMFAN_LR5126, [2.0])[0].figure_of_merit
    assert lo > hi
