"""Milestone 4: score a sound the way listeners judge it.

Plain words
-----------
dB(A) is one number for "how much sound energy, counted the way ears do".
Listeners judge more than that:
  - Loudness (sone): how loud it seems. 2 sone sounds twice as loud as 1 sone.
  - Sharpness (acum): how much the sound is tilted to high, hissy frequencies.
  - Roughness (asper): a fast buzzing flutter, when notes beat against each other.
  - Fluctuation strength (vacil): slow wobbling of loudness.
Annoyance combines them: start from loudness, then add a penalty when the sound
is sharp, rough or wobbly.

Technical
---------
Loudness: Zwicker method, ISO 532-1 (MoSQITo loudness_zwst / loudness_zwtv),
free field. N5 is the 95th percentile of the time-varying loudness, the level
exceeded 5% of the time. Sharpness: DIN 45692 (sharpness_din_st). Roughness:
Daniel & Weber model (roughness_dw), averaged over time.

Psychoacoustic annoyance (Zwicker & Fastl, Psychoacoustics: Facts and Models,
3rd ed., Springer 2007, ch. 16, after Widmann):

    w_S  = (S - 1.75) * 0.25 * log10(N5 + 10)   if S > 1.75 acum, else 0
    w_FR = (2.18 / N5^0.4) * (0.4 F + 0.6 R)
    PA   = N5 * (1 + sqrt(w_S^2 + w_FR^2))

with N5 in sone, S in acum, F in vacil and R in asper.
"""

from dataclasses import dataclass

import numpy as np
from mosqito.sq_metrics import loudness_zwst, loudness_zwtv, roughness_dw, sharpness_din_st

from .audio import FS, measured_levels

FIELD = "free"

# ASSUMPTION: fluctuation strength is not available in MoSQITo 1.2.1. A
# propeller in steady hover has no slow (around 4 Hz) loudness wobble, so F = 0.
FLUCTUATION_VACIL = 0.0


def annoyance(N5, S, R, F=FLUCTUATION_VACIL):
    """Psychoacoustic annoyance PA from N5 (sone), S (acum), R (asper), F (vacil)."""
    if N5 <= 0:
        return 0.0
    w_s = (S - 1.75) * 0.25 * np.log10(N5 + 10.0) if S > 1.75 else 0.0
    w_fr = (2.18 / N5 ** 0.4) * (0.4 * F + 0.6 * R)
    return float(N5 * (1.0 + np.sqrt(w_s ** 2 + w_fr ** 2)))


@dataclass
class Scores:
    spl_dB: float          # measured from the signal
    spl_dBA: float         # measured from the signal (A-weighted FFT)
    N_steady: float        # sone, loudness_zwst
    N5: float              # sone, 95th percentile of loudness_zwtv
    S: float               # acum, DIN
    R: float               # asper, mean over time
    F: float               # vacil (ASSUMPTION: 0)
    PA: float              # psychoacoustic annoyance


def score(signal, fs=FS):
    """All Milestone 4 scores for one signal in pascals."""
    db, dba = measured_levels(signal, fs)
    n_steady = float(loudness_zwst(signal, fs, field_type=FIELD)[0])
    n_t = np.asarray(loudness_zwtv(signal, fs, field_type=FIELD)[0])
    n5 = float(np.percentile(n_t, 95))
    s = float(sharpness_din_st(signal, fs, weighting="din", field_type=FIELD))
    r = float(np.mean(roughness_dw(signal, fs)[0]))
    return Scores(db, dba, n_steady, n5, s, r, FLUCTUATION_VACIL,
                  annoyance(n5, s, r, FLUCTUATION_VACIL))
