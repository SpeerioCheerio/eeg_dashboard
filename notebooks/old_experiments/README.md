# EEG Analysis Experiments

This repository contains a collection of Jupyter notebooks documenting various EEG signal processing & analysis techniques and ML models developed throughout our project. These notebooks explore different approaches to extracting meaningful features from EEG data across various emotional states and experimental conditions.

> **Note:**  All of the code produced here was developed under the instruction to be very “scrappy” and only focused on obtaining quick results. Thus, the code is a bit messy at times and needs more documentation. Also, file paths need to be updated for each .ipynb file to run. Feel free to adapt and improve any portion of the code for your own purposes.

## Setup Requirements

Before running these notebooks, you'll need to:
1. Update file paths in each notebook to match your directory structure
2. Install required Python libraries (standard scientific libraries plus custom functions from `awear_function_lib.py` where noted)

## Notebook Descriptions

### 250107_initial_analysis_and_pipeline
- Focused on Luisa and Antonio datasets across 4 emotional states
- Implemented outlier removal using linear interpolation
- Created and tested various IIR and FIR filters
- Developed functions for:
  - Time and frequency domain analysis
  - Time-frequency analysis using STFT
  - Calculating average power in frequency bands
- Generated visualizations including bar plots, heatmaps, and comparisons of high vs. low arousal/valence states
- Calculated temporal variability metrics (std dev, range, coefficient of variation, skewness, kurtosis, median absolute deviation)
- Results documented in presentations: "250109_Luisa_Antonio_Time_and_Freq_Plots", "250113_Luisa_Antonio_STFT"

### 250120_feature_analysis_other_four_subjects
- Extended previous analysis to four additional subjects (Ana, Ale, Jenny, and John)
- Created comparative plots of gamma values in Happy vs. Sad conditions across all participants
- Generated box plots comparing gamma/alpha ratios across all videos for Antonio
- Results documented in presentation: "250122_Early Biomarker for Differentiating Happy and Sad"

### 250128_time_and_freq_filtered_data_eoec
- Performed time and frequency domain analysis on Luisa and Antonio data including eyes open/closed datasets
- Plotted time domain data with various filters and rolling windows for smoothing
- Extracted and plotted the signal envelope of the power spectrum for Luisa and Antonio using different methods (FFT/PSD and various smoothing filters)

### 250130_test_on_openbci_data
- Data was collected by Antonio using the OpenBCI ganglion device for testing purposes, several different filters were tested
- Established default filtering pipeline: 4th order Butterworth filter with bandpass (0.5-54Hz) plus 50Hz and 60Hz notch filters
- Importantly, frequency domain plots should always be represented as a power spectral density (PSD) 
- Results documented in presentation: "250131_Time_and_Frequency_Antonio_OpenBCI"

### 250204_ucsf_data_analysis
- Analyzed data collected using AWEAR device (dubbed "UCSF Data")
- Compared three experimental conditions: horror movie, vipassana meditation, hot tub
- Developed visualization functions for:
  - PSD for each emotional state
  - Band ratio comparisons
  - STFT spectrograms
  - Temporal band ratio tracking
  - Forgetting factor tests
  - Box plots of band ratios over time
  - Implemented Lempel-Ziv Compression (LZC) analysis
- Results documented in presentation: "250205_UCSF_Data_Plots"

### 250210_Full_Pipeline_Architecture
- Created framework for generating all plots from the UCSF data analysis in a unified pipeline

### 250217_Signal_Synchronicity
- Functions used included imports from `awear_function_lib.py`
- Implemented phase-amplitude coupling (PAC) analysis with options for:
  - Full-dataset analysis
  - Time-resolved analysis with variable window sizes
- Built statistical analysis functions for PAC comparisons:
  - Cohen's d effect size
  - Rank-biserial correlation
  - Mann-Whitney U test
- Developed entropy analysis approaches (applied to either full dataset or time-resolved approach):
  - Sample Entropy
  - Approximate Entropy
  - Multi-Scale Entropy
- Statistical analysis was applied to the entropy calculations as well
- Results documented in presentations: 
  - "250220_PAC_Statistical_Analysis_Delta_Gamma_Only"
  - "250226_Full_PAC_Statistical_Analysis_Valence"
  - "250226_Sample_Entropy_Analysis"
  - "250227_Approximate_Entropy_Analysis"
  - "250304_Multi_Scale_Entropy_Analysis"
  - "250305_PAC_Time_Resolved_All_Participants"

### 250217_state_identification_algorithm
- Functions used included imports from `awear_function_lib.py`
- Main purpose of this python notebook was to try and quickly identify a subset of features that could be used to produce an
  algorithm for identifying emotional states using only spectral features
- Analysis included all participants except John (excluded due to data quality issues)

### 250228_UCSF_PAC_En_Analysis
- Functions used included imports from `awear_function_lib.py`
- Applied both PAC and entropy analyses to the UCSF dataset
- Used time-resolved PAC with 30-second windows
- Tested multiple Multi-Scale Entropy (MSE) approaches:
  - Standard MSE
  - Modified coarse-graining methods
  - Downsampling from 256Hz to 128Hz without coarse-graining
- Results documented in presentation: "250305_PAC_Time_Resolved_UCSF"

### 250307_phase_locking_value
- Functions used included imports from `awear_function_lib.py`
- This python notebook was created during some downtime to quickly test whether phase locking value could be beneficial and provide us with useful information 
- Note: This was a rapid exploration and requires further validation

### 250318_SVM_model_project_updated
- In this python notebook, feature extraction is performed and an SVM model is built using those features as inputs
- Built SVM classification models based on architecture in "250318_Feature_Extraction_Block_Diagram"
- Applied forgetting factor smoothing to feature vectors (tested various factors, final results used FF=0.05)
- A time-based split is used instead of the train_test_split function from sklearn so that the EEG data is not 
  randomly shuffled and temporal relationships are better preserved, feel free to play around with best methods here
- Performed hyperparameter tuning with GridSearch and StratifiedKFold cross-validation to identify the best model
- The best model is then selected and tested on unseen data (indepedent test set)
- Achieved median classification accuracy across all particpants:
  - 85% for arousal
  - 83% for valence
- For future users, the instruction here was to use an FFT for feature extraction, however, 
  using a PSD is more standard so feel free to test out different methods
- Results documented in presentation: "250327_Final_SVM_Updates"
