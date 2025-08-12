# Unit tests
import numpy as np
import pytest

from awear_neuroscience.signal_processing.artifacts import detect_artifacts


def test_amplitude_artifact_detection():
    """
    Amplitude Thresholding - rejects segments with high peak amplitude.
    """
    clean = np.sin(2 * np.pi * 10 * np.linspace(0, 1, 256))
    noisy = clean.copy()
    noisy[100] = 100  # Introduce spike

    assert not detect_artifacts(clean, fs=256, method="amplitude", amp_thresh=50.0)
    assert detect_artifacts(noisy, fs=256, method="amplitude", amp_thresh=50.0)


def test_zscore_artifact_detection():
    """Test z-score based artifact detection."""
    np.random.seed(42)  # For reproducible tests
    clean = np.random.normal(0, 1, 256)

    # Test exact boundary case
    edge_case = clean.copy()
    max_allowed = int(256 * 0.05)  # Should be 12 samples
    edge_case[np.random.choice(256, max_allowed, replace=False)] = 20

    # Should pass - exactly at threshold (12 samples = 4.69%)
    assert detect_artifacts(edge_case, fs=256, method="zscore", z_thresh=3.0)

    # Should fail - one more than allowed (13 samples = 5.08%)
    edge_case[np.random.choice(256, 1)] = 20
    assert detect_artifacts(edge_case, fs=256, method="zscore", z_thresh=3.0)


def test_gamma_power_artifact_detection():
    """Comprehensive gamma power artifact testing."""
    fs = 256
    t = np.linspace(0, 1, fs, endpoint=False)
    np.random.seed(42)

    # Test signals
    pure_gamma = np.sin(2 * np.pi * 40 * t)
    eeg_like = np.random.normal(0, 1, fs)
    mixed = eeg_like + 0.5 * pure_gamma

    # Test cases with combined thresholds
    test_cases = [
        # (signal, should_detect, thresholds)
        (pure_gamma, True, {"gamma_power_thresh": 0.25, "min_gamma_power": 0.1}),
        (eeg_like, False, {"gamma_power_thresh": 0.25}),
        (mixed, True, {"gamma_power_thresh": 0.2, "min_gamma_power": 0.05}),
    ]

    for signal, should_detect, params in test_cases:
        result = detect_artifacts(signal, fs=fs, method="gamma_power", **params)
        if should_detect:
            assert result, f"Failed to detect artifact in {params}"
        else:
            assert not result, f"False positive detection in {params}"
