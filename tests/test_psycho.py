"""Milestone 4 checks: synthesis is calibrated, and the scores behave.

Signals are 1 second long so CI stays fast.
"""

import numpy as np
import pytest

from propnoise.audio import (FS, measured_levels, save_wav, synthesize, tones_from_spectrum,
                             whoosh, whoosh_dBA)
from propnoise.bemt import operating_point, solve_hover
from propnoise.gutin import P_REF, energetic_sum_dB, tone_spectrum
from propnoise.props import GEMFAN_5152, PROPELLERS
from propnoise.psycho import annoyance, score
from mosqito.sq_metrics import loudness_zwst

SECONDS = 1.0


def _sine(level_dB, f=1000.0):
    t = np.arange(int(SECONDS * FS)) / FS
    return np.sqrt(2.0) * P_REF * 10 ** (level_dB / 20) * np.sin(2 * np.pi * f * t)


@pytest.fixture(scope="module")
def hum_2N():
    op = operating_point(solve_hover(GEMFAN_5152), 2.0)
    spec = tone_spectrum(op, GEMFAN_5152)
    return spec, synthesize(tones_from_spectrum(spec), SECONDS)


@pytest.fixture(scope="module")
def hum_and_whoosh_scores(hum_2N):
    spec, hum = hum_2N
    noise = whoosh(SECONDS, spec.total_dBA)       # the "high" level for the 5152 at 2 N
    return score(hum), score(hum + noise)


# ---- calibration ----------------------------------------------------------

def test_1kHz_40dB_is_1_sone():
    assert loudness_zwst(_sine(40.0), FS, field_type="free")[0] == pytest.approx(1.0, abs=0.05)


def test_10_dB_more_sounds_twice_as_loud():
    n40 = loudness_zwst(_sine(40.0), FS, field_type="free")[0]
    n50 = loudness_zwst(_sine(50.0), FS, field_type="free")[0]
    assert n50 / n40 == pytest.approx(2.0, rel=0.10)


@pytest.mark.parametrize("prop", PROPELLERS, ids=lambda p: p.name.split()[1])
def test_synthesized_level_matches_milestone_2(prop):
    op = operating_point(solve_hover(prop), 2.0)
    spec = tone_spectrum(op, prop)
    db, dba = measured_levels(synthesize(tones_from_spectrum(spec), SECONDS))
    assert db == pytest.approx(spec.total_dB, abs=0.2)
    assert dba == pytest.approx(spec.total_dBA, abs=0.2)


def test_whoosh_has_the_requested_level_and_adds_by_energy(hum_2N):
    spec, hum = hum_2N
    noise = whoosh(SECONDS, spec.total_dBA - 10.0)
    assert measured_levels(noise)[1] == pytest.approx(spec.total_dBA - 10.0, abs=0.01)
    expected = energetic_sum_dB([spec.total_dBA, spec.total_dBA - 10.0])
    assert measured_levels(hum + noise)[1] == pytest.approx(expected, abs=0.2)


def test_whoosh_scales_with_tip_speed_to_the_fifth():
    assert whoosh_dBA(200.0, 50.0, 100.0) == pytest.approx(50.0 + 50 * np.log10(2))


def test_synthesis_is_repeatable(hum_2N):
    spec, hum = hum_2N
    np.testing.assert_array_equal(hum, synthesize(tones_from_spectrum(spec), SECONDS))


def test_wav_is_16_bit_and_normalised(tmp_path, hum_2N):
    from scipy.io import wavfile
    _, hum = hum_2N
    save_wav(tmp_path / "hum.wav", hum)
    fs, data = wavfile.read(tmp_path / "hum.wav")
    assert fs == FS and data.dtype == np.int16
    assert np.max(np.abs(data)) == pytest.approx(0.9 * 32767, rel=0.01)


# ---- scores ---------------------------------------------------------------

def test_hum_only_is_not_sharp_or_rough(hum_and_whoosh_scores):
    """Hum-only: low S and R, so annoyance follows loudness."""
    hum, _ = hum_and_whoosh_scores
    assert hum.S < 1.75
    assert hum.R < 0.05
    assert hum.PA == pytest.approx(hum.N5, rel=0.01)


def test_adding_whoosh_raises_sharpness(hum_and_whoosh_scores):
    hum, both = hum_and_whoosh_scores
    assert both.S > hum.S


def test_annoyance_is_at_least_loudness(hum_and_whoosh_scores):
    for s in hum_and_whoosh_scores:
        assert s.PA >= s.N5


@pytest.mark.parametrize("N5, S", [(1.0, 0.5), (5.0, 1.75), (20.0, 1.2)])
def test_annoyance_equals_loudness_when_not_sharp_rough_or_wobbly(N5, S):
    assert annoyance(N5, S, R=0.0, F=0.0) == pytest.approx(N5)


def test_annoyance_formula_by_hand():
    """N5 = 10 sone, S = 2.75 acum, R = 0.1 asper, F = 0."""
    w_s = 1.0 * 0.25 * np.log10(20.0)
    w_fr = 2.18 / 10 ** 0.4 * 0.06
    assert annoyance(10.0, 2.75, 0.1) == pytest.approx(10 * (1 + np.hypot(w_s, w_fr)))
