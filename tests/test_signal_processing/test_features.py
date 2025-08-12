import numpy as np

from awear_neuroscience.signal_processing.features import (
    bandpower, bands, compute_psd, extract_band_features)


def test_compute_psd_returns_correct_shape():
    signal = np.random.randn(256)
    fs = 256
    freqs, psd = compute_psd(signal, fs)
    assert len(freqs) == len(psd)
    assert freqs[0] >= 0
    assert all(np.diff(freqs) > 0)


def test_bandpower_matches_known_band():
    fs = 256
    t = np.arange(0, 1, 1 / fs)
    signal = np.sin(2 * np.pi * 10 * t)  # 10 Hz signal -> alpha band
    freqs, psd = compute_psd(signal, fs)
    alpha_power = bandpower(freqs, psd, bands["alpha"])
    other_power = bandpower(freqs, psd, bands["delta"]) + bandpower(
        freqs, psd, bands["theta"]
    )
    assert alpha_power > other_power


def test_extract_band_features_metadata_and_keys():
    fs = 256
    t = np.arange(0, 1, 1 / fs)
    signal = np.sin(2 * np.pi * 6 * t)
    freqs, psd = compute_psd(signal, fs)
    features = extract_band_features(
        freqs,
        psd,
        signal,
        document_name="test@eeg.com",
        segment=1,
        session_id="abc",
        timestamp="2025-07-01T12:00:00Z",
    )
    assert "alpha" in features and "beta" in features
    assert features["document_name"] == "test@eeg.com"
    assert features["segment"] == 1
