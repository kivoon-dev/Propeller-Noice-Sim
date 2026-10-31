"""Milestone 4: turn the predicted sound into a signal you can play and score.

Plain words
-----------
Milestones 2 and 3 give a list of notes (tones) and how strong each one is at
the microphone. Here we play all those notes at once, as pure sine waves, to
build the sound pressure the microphone would record, second by second. The
signal is in pascals, so the scoring code (psycho.py) hears it at the right
loudness. A second, optional ingredient is the "whoosh": the rushing-air noise
of real propellers, which our physics does not predict, so it is added as a
clearly labelled guess.

Technical
---------
Tones: sum of sines, amplitude √2·p_rms, with fixed random phases (seeded) so
the result is repeatable. Whoosh: seeded Gaussian noise shaped in the frequency
domain, then scaled so its A-weighted level, measured from the signal itself by
FFT (Parseval), equals the requested dB(A).
"""

import numpy as np
from scipy.io import wavfile

from .gutin import P_REF, a_weighting_dB

FS = 48000

# ASSUMPTION: the broadband "whoosh" is NOT predicted by the physics in this
# project. Its shape and size below are guesses, chosen to be typical of small
# propellers (trailing-edge noise). The three levels let us see whether the
# conclusions depend on the guess.
WHOOSH_BAND_HZ = (500.0, 12000.0)    # ESTIMATE
WHOOSH_PEAK_HZ = 3000.0              # ESTIMATE: broad hump at 3 kHz
WHOOSH_SLOPE_DB_PER_OCT = 6.0        # ESTIMATE: falls 6 dB per octave each side
WHOOSH_SPEED_EXPONENT = 5.0          # trailing-edge noise: level ~ tip speed^5

# Whoosh level of the 5152 at 2 N, relative to that prop's own tonal dB(A).
# None = no whoosh. Other props and thrusts scale from this by tip speed^5.
WHOOSH_LEVELS = {"none": None, "low": -10.0, "high": 0.0}


def tones_from_spectrum(spectrum):
    """(frequency Hz, p_rms Pa) pairs from an M2 ToneSpectrum or M3 ShaftSpectrum."""
    return [(float(f), float(p)) for f, p in zip(spectrum.freqs_Hz, spectrum.p_rms_Pa) if p > 0]


def synthesize(tones, seconds, fs=FS, seed=0):
    """Sum of sines in pascals. tones: iterable of (frequency Hz, p_rms Pa).

    Each tone gets a fixed random phase from `seed`. Tones at or above the
    Nyquist frequency (fs / 2) cannot be represented and are left out.
    """
    t = np.arange(int(round(seconds * fs))) / fs
    rng = np.random.default_rng(seed)
    signal = np.zeros_like(t)
    for f, p in tones:
        phase = rng.uniform(0.0, 2.0 * np.pi)
        if 0 < f < fs / 2 and p > 0:
            signal += np.sqrt(2.0) * p * np.sin(2.0 * np.pi * f * t + phase)
    return signal


def measured_levels(signal, fs=FS):
    """(dB, dB(A)) measured from the signal itself with an A-weighted FFT."""
    n = len(signal)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    power = np.abs(np.fft.rfft(signal)) ** 2 / n ** 2
    power[1:] *= 2.0
    if n % 2 == 0:
        power[-1] /= 2.0            # the Nyquist bin has no mirror image
    with np.errstate(divide="ignore"):
        weight = 10.0 ** (a_weighting_dB(freqs) / 10.0)
    weight[0] = 0.0
    total, total_a = power.sum(), (power * weight).sum()
    with np.errstate(divide="ignore"):
        return (float(10.0 * np.log10(total / P_REF ** 2)),
                float(10.0 * np.log10(total_a / P_REF ** 2)))


def whoosh(seconds, level_dBA, fs=FS, seed=1):
    """Broadband noise (ASSUMPTION) in pascals with the given A-weighted level.

    Shape: band WHOOSH_BAND_HZ, third-octave band level peaking at
    WHOOSH_PEAK_HZ and falling WHOOSH_SLOPE_DB_PER_OCT per octave each side.
    A third-octave band is 23% of its centre frequency wide, so the level per
    hertz falls a further 3 dB per octave: PSD(f) ~ 10^(L(f)/10) / f.
    """
    n = int(round(seconds * fs))
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    lo, hi = WHOOSH_BAND_HZ
    inside = (freqs >= lo) & (freqs <= hi)
    band_level = np.zeros_like(freqs)
    band_level[inside] = -WHOOSH_SLOPE_DB_PER_OCT * np.abs(np.log2(freqs[inside] / WHOOSH_PEAK_HZ))
    psd = np.zeros_like(freqs)
    psd[inside] = 10.0 ** (band_level[inside] / 10.0) / freqs[inside]
    rng = np.random.default_rng(seed)
    spectrum = (rng.standard_normal(len(freqs)) + 1j * rng.standard_normal(len(freqs))) * np.sqrt(psd)
    noise = np.fft.irfft(spectrum, n)
    _, now_dBA = measured_levels(noise, fs)
    return noise * 10.0 ** ((level_dBA - now_dBA) / 20.0)


def whoosh_dBA(tip_speed_ms, ref_dBA, ref_tip_speed_ms):
    """Whoosh level scaled from a reference by tip speed^5: +50 log10(U / U_ref)."""
    return ref_dBA + 10.0 * WHOOSH_SPEED_EXPONENT * np.log10(tip_speed_ms / ref_tip_speed_ms)


def save_wav(path, signal, fs=FS, full_scale_Pa=None, peak=0.9):
    """Write a 16-bit WAV for listening.

    By default the signal is normalised so its own peak is `peak` of full scale.
    Pass the same full_scale_Pa to several files to keep their loudness
    differences audible (the loudest file's peak is a good choice).
    """
    scale = full_scale_Pa if full_scale_Pa is not None else np.max(np.abs(signal)) / peak
    if scale == 0:
        scale = 1.0
    data = np.clip(signal / scale, -1.0, 1.0)
    wavfile.write(path, fs, (data * 32767).astype(np.int16))

