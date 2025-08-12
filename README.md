# AWEAR Function Library

## Overview

This library is designed for analyzing EEG data from single participants, with a focus on extracting and visualizing neural features across different experimental conditions or emotional states. It provides a modular pipeline for loading, preprocessing, segmenting, filtering, and analyzing EEG data using a wide range of features, including: power spectral density (PSD), band ratio comparisons, spectrograms, box plots, heatmaps, Lempel-Ziv Complexity (LZC), band ratios over time, entropy-based measures, time-resolved PAC measures, and statistical analysis.

Data is loaded into a dictionary structure, where each key corresponds to a labeled condition (e.g., "Happy", "Sad"), and the value is a 1D NumPy array representing the EEG signal for that state. The pipeline supports both AWEAR and OpenBCI data formats; for OpenBCI, a specific channel (0–3) can be selected.

For multi-participant analysis, the code will need to be extended. Recommendation is to use a multi-indexed pandas.DataFrame or a nested dictionary structure to enable participant-level aggregation and group-level statistical testing.

This library was developed for internal research purposes using OpenBCI and AWEAR EEG datasets, and it can be easily extended for other platforms.

## Table of Contents

1. [Installation](#installation)
2. [Data Loading](#data-loading)
3. [Preprocessing](#preprocessing)
4. [Filtering](#filtering)
5. [Spectral Feature Extraction](#spectral-feature-extraction)
6. [Entropy Measures](#entropy-measures)
7. [Phase-Amplitude Coupling (PAC)](#phase-amplitude-coupling-pac)
8. [Statistical Analysis](#statistical-analysis)
9. [Visualization](#visualization)
10. [Running the Full Pipeline](#running-the-full-pipeline)

## Installation

```bash
pip install numpy pandas scipy matplotlib seaborn statsmodels
```

## Data Loading

### `load_eeg_data(file_paths, data_type, segments=None, fs=256, labels=None, channel=0)`

Loads EEG data from multiple files, optionally extracting a time segment from each file. Supports both AWEAR and OpenBCI formats.

Returns: a dictionary where each key is a condition label and each value is a 1D NumPy array of EEG data.

Arguments:

- file_paths: List of EEG file paths
- data_type: 'awear' or 'openbci'
- segments: Time segment(s) to extract, in seconds. Can be:
  - A single tuple (e.g., (60, 120)) applied to all files
  - A list of tuples (e.g., [(60, 120), None, (30, 90)]) for per-file control
  - None to load the full signal
- fs: Sampling frequency (default: 256 Hz)
- labels: Optional custom labels for each file (default: filename-based)
- channel: For OpenBCI files, selects channel 0–3 (default: 0)

### `apply_segment(data, segment, fs)`

Helper function that extracts a time-based segment from a single EEG signal.

Returns: A 1D NumPy array containing only the desired time window.

Arguments:
- data: 1D NumPy array of EEG samples
- segment: Tuple (start_time, end_time) in seconds (can be negative for backward indexing)
- fs: Sampling frequency (Hz)

## Preprocessing

### `remove_outliers(data_dict, threshold=2)`

Detects and removes statistical outliers (e.g., ±2 standard deviations) in EEG data and replaces them using linear interpolation.

- data_dict: Dictionary of EEG signals with states as keys and 1D NumPy arrays as values.
- threshold: Number of standard deviations from the mean to classify an outlier (default = 2).

Returns: cleaned dictionary with outliers replaced

## Filtering

### `apply_filters(data, fs, bandpass_range=None, notch_frequencies=None, bandpass_order=None, Q=None)`

Applies both bandpass and notch filtering to EEG data. Works with single signals or dictionaries of signals.
- Default bandpass: 0.5–54 Hz
- Default notch filters: 50 Hz and 60 Hz

### `butter_bandpass_filter(data, lowcut, highcut, fs, order=4)`  
### `notch_filter(data, freq, fs, Q=10)`  
Internal helper functions used by apply_filters.

## Spectral Feature Extraction

### `compute_band_power(freqs, psd, band)`

Computes the power within a specified frequency band from a PSD estimate. Supports hierarchical bands (e.g., alpha includes alpha1, alpha2).
- freqs: Array of frequency bins from PSD
- psd: Array of power spectral density values
- band: Name of band (e.g., 'theta', 'alpha', 'beta2', etc.)

### `calculate_ratios(data_dict, fs, selected_ratios)`

Computes the ratio of power between two frequency bands (e.g., gamma/alpha, beta/delta) across all conditions.
- data_dict: Dictionary of EEG signals
- fs: Sampling frequency (Hz)
- selected_ratios: List of band pairs (e.g., [("gamma", "alpha")])

### `apply_lzc_to_data(data_dict)`

Computes Lempel-Ziv Complexity (LZC), a non-linear measure of signal complexity, for each EEG trace using median binarization.
- data_dict: Dictionary of EEG signals per condition

## Phase-Amplitude Coupling (PAC)

### `compute_time_resolved_pac(data, fs=200, window_length=1, overlap=0.5, freq_range_phase=(8,12), freq_range_amplitude=(30,50), num_bins=18, smooth_window=8, zscore_threshold=2)`

Calculates time-resolved PAC using KL-divergence based Modulation Index.
- Internally applies bandpass filters
- Computes phase and amplitude using the Hilbert transform
- Cleans data using Z-score thresholding
- Returns smoothed PAC traces
- Plots PAC traces per condition

Parameters:
- data: Dictionary of EEG traces (e.g., {state: signal})
- fs: Sampling frequency (Hz)
- window_length: Length of time window in seconds
- overlap: Fractional overlap between windows (0–1)
- freq_range_phase: Frequency band for extracting phase (e.g., theta = (4, 8))
- freq_range_amplitude: Frequency band for amplitude (e.g., gamma = (30, 50))
- num_bins: Number of bins to compute PAC
- smooth_window: Moving average smoothing window (in time bins)
- zscore_threshold: Threshold for excluding extreme PAC values

### `compute_effect_sizes(pac_data, name)`

Compares PAC values between all condition pairs using:
- Cohen's d
- Rank-Biserial Correlation
- Mann-Whitney U test

Parameters:
- pac_data: Dictionary of PAC traces (e.g., {state: PAC values})
- name: Participant identifier used in printed Returns

Prints results in a clean DataFrame format.

## Entropy Measures

### `compute_sample_entropy(data_dict, fs, window_size=1000, overlap=0.5, m=2, r=0.2)`

Computes Sample Entropy (SampEn) for each condition using a sliding window approach.
- data_dict: EEG dictionary by condition
- fs: Sampling frequency (Hz)
- window_size: Window length in samples
- overlap: Overlap between consecutive windows (0–1)
- m: Embedding dimension
- r: Tolerance threshold (as a % of signal std)

Returns a DataFrame of entropy values over time windows for each condition.

### `compute_approximate_entropy(data_dict, fs, window_size=1000, overlap=0.5, m=2, r=0.2)`

Computes Approximate Entropy (ApEn) using the same sliding window approach as above.
- data_dict: EEG dictionary by condition
- fs: Sampling frequency (Hz)
- window_size: Window length in samples
- overlap: Overlap between consecutive windows (0–1)
- m: Embedding dimension
- r: Tolerance threshold (as a % of signal std)

Returns a DataFrame of ApEn values over time windows for each condition.

### `compute_average_entropy(entropy_df, entropy_type)`

Computes the mean and standard error of entropy values per state (and per participant, if present). Handles both single- and multi-participant formats.
- entropy_df: DataFrame Returns from entropy functions
- entropy_type: String 'Sample' or 'Approximate' (used to select correct column)

## Statistical Analysis

### `compute_anova_entropy(entropy_df, entropy_type)`

Runs a one-way ANOVA on entropy values (either Sample or Approximate) across emotional states for each participant.
- entropy_df: DataFrame of entropy values
- entropy_type: 'Sample' or 'Approximate'

Returns a DataFrame with F-statistics and p-values.

### `compute_pairwise_tests(entropy_df, entropy_type)`

Performs pairwise t-tests between emotional states for each participant, with Bonferroni correction applied for multiple comparisons.
- entropy_df: DataFrame of entropy values
- entropy_type: 'Sample' or 'Approximate'

Returns a DataFrame of raw and corrected p-values.


## Visualization

All plotting functions support dictionary-style input (e.g., `{"Happy": data1, "Sad": data2}`):

### `plot_psd(data_dict, fs, name=None, y_axis_limits=None)`

Plots the Power Spectral Density (PSD) for each EEG condition using Welch's method.
- data_dict: Dictionary of EEG signals per condition
- fs: Sampling frequency (Hz)
- name: Optional string for plot title (e.g., participant name)
- y_axis_limits: Optional tuple (ymin, ymax) to set y-axis range

### `plot_ratios_bar(ratios, name=None, y_axis_limits=None)`

Creates grouped bar plots for selected band ratios (e.g., gamma/alpha) across EEG states.
- ratios: Dictionary of band power ratios per condition
- name: Optional label for plot title
- y_axis_limits: Optional y-axis limits (e.g., (1e-6, 1e2))

### `plot_spectrogram(data_dict, fs, name=None, vmax=None)`

Displays short-time Fourier transform (STFT) of EEG data as a spectrogram.
- data_dict: Dictionary of EEG traces per condition
- fs: Sampling frequency (Hz)
- name: Optional string for plot title
- vmax: Optional max scale value for the color map (power axis)

### `plot_band_ratios_spectrogram(data_dict, fs, selected_ratios, name=None, y_axis_limits=None)`

Visualizes time-varying band ratios over the full EEG duration for each dataset.
- data_dict: EEG signal dictionary
- fs: Sampling frequency (Hz)
- selected_ratios: List of tuples (e.g., [("gamma", "alpha"), ("beta", "delta")])
- name: Optional plot title
- y_axis_limits: Optional limits for the ratio plot's y-axis

### `plot_band_ratios_box_whisker(data_dict, fs, selected_ratios, name=None, y_axis_limits=None)`

Plots distributions (box-and-whisker) of band ratios across conditions.
- data_dict: EEG dictionary per condition
- fs: Sampling frequency (Hz)
- selected_ratios: List of band pairs
- name: Optional plot label
- y_axis_limits: Optional y-axis bounds

### `plot_lzc_values(lzc_results)`

Plots a bar chart of Lempel-Ziv Complexity (LZC) values across conditions.
- lzc_results: Dictionary of condition → LZC value

### `plot_avg_power_heatmap(data_dict, fs, name=None, channel=None)`

Displays a heatmap of average power across bands (rows) and conditions (columns).
- data_dict: EEG data dictionary
- fs: Sampling frequency (Hz)
- name: Optional subject name for the plot
- channel: Optional OpenBCI channel (for label purposes)

### `plot_band_ratio_heatmap(data_dict, fs, name=None, channel=None)`

Plots a heatmap of pairwise band ratios (e.g., gamma/alpha, beta/theta) across EEG states.
- data_dict: EEG dictionary by condition
- fs: Sampling frequency
- name: Subject name for the heatmap title
- channel: Optional channel number

Note: ** This function needs to be improved, currently displays duplicate band ratios or is missing some. **

## Running the Full Pipeline

### `run_pipeline(...)`

A convenience function that chains together data loading, filtering, and visualizations (PSD, band ratios, spectrograms, box plots, LZC). Additional functions (entropy,PAC, statistical analysis) were not included in this full pipeline because a decision was made to discontinue this function. 

**Includes options for:**
- File loading
- Filtering
- PSD and spectrogram plotting
- Band ratio comparisons
- LZC computation

Customize which plots to run via the `plots` argument.


### Example Of How To Get Started

```python
from awear_function_lib import load_eeg_data, apply_filters, plot_psd

# Load EEG data from two files
data = load_eeg_data(
	file_paths=["happy.txt","tense.txt","relaxed.txt","sad.txt"], data_type="awear", fs=256,
	labels=["Happy","Tense","Relaxed","Sad"], segments=[(-60,0)]
)

# Apply default filtering
filtered = apply_filters(data, fs=256)

# Plot the power spectral density
plot_psd(filtered, fs=256)
```

