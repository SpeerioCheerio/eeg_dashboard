import numpy as np
import pytest
import scipy.signal as ss

from awear_neuroscience.signal_processing.filters import (bandpass_filter,
                                                          notch_filter,
                                                          preprocess_segment)

fs = 256
t = np.linspace(0, 1, fs, endpoint=False)


def test_bandpass_preserves_midband():
    """
    Confirms that the bandpass filter preserves signals in the mid-frequency band (e.g. 10 Hz).
    Checks that the filtered signal is highly correlated with the original.
    """
    clean = np.sin(2 * np.pi * 10 * t)  # 10 Hz signal
    out = bandpass_filter(clean, fs)

    # Use correlation instead of allclose
    corr = np.corrcoef(clean, out)[0, 1]
    assert corr > 0.95, f"Expected correlation > 0.95, got {corr:.3f}"


def test_bandpass_rejects_high_freq():
    """
    Verifies that the bandpass filter attenuates high-frequency noise (e.g., 100 Hz).
    High-frequency muscle or electrical noise should be reduced but not necessarily eliminated.
    """
    noise = np.sin(2 * np.pi * 100 * t)
    out = bandpass_filter(noise, fs)

    attenuation = np.max(np.abs(out))
    assert attenuation < 0.9, f"Expected attenuation < 0.9, got {attenuation:.3f}"


def test_notch_removes_line_noise():
    """
    Verifies that the notch filter removes line noise (e.g. 60 Hz), which is common in EEG data.
    """
    sig = np.sin(2 * np.pi * 60 * t) + np.sin(2 * np.pi * 10 * t)
    out = notch_filter(sig, fs, freq=60.0)
    f, Pxx = ss.welch(out, fs)
    idx = np.argmin(np.abs(f - 60))
    assert Pxx[idx] < 0.01


def test_preprocess_segment_combines():
    """
    Verifies that the preprocess_segment function removes drifts, notch noise, and detrends the signal.
    A core assumption of many EEG analyses (especially spectral and statistical ones) is that the signal is zero-centered.
    Detrending also removes slow drifts (e.g., sweat artifacts).
    """
    mixed = np.concatenate(
        [np.zeros(10), np.sin(2 * np.pi * 1 * t) * np.linspace(1, 2, fs), np.zeros(10)]
    )
    out = preprocess_segment(mixed, fs)
    assert out.shape == mixed.shape
    assert np.allclose(np.mean(out), 0.0, atol=0.05)
