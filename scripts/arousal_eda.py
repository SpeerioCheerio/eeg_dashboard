import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()
from setup_path import add_src_to_path
add_src_to_path()

from awear_neuroscience.data_extraction.constants import (
    WAVEFORM_KEY, SAMPLING_RATE, FIELD_KEYS
)

from awear_neuroscience.data_extraction.firestore_loader import  process_eeg_records
from awear_neuroscience.pipeline.preprocess import process_long_df, extract_features_from_long_df, process_features
from awear_neuroscience.statistical_analysis.statistical_tests import compare_session_types
from awear_neuroscience.data_extraction.firestore_loader import get_selreport_data







import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)
firestore_client = firestore.Client()




# Download all the EEG records for sessions_of_interest

emails=["cristiana.principato@gmail.com", "f.morrone980@gmail.com", "antonio.forenza@gmail.com", "simone.balatti@gmail.com"]
# emails=["simone.balatti@gmail.com"]
sessions_of_interest=["calm", "stressed"]
now = datetime.now()
start=datetime.fromisocalendar(2025, 1, 1)
time_ranges = [(start, now)] 
raw_records=[]
for email in emails:
    raw_records.extend(get_selreport_data(
            firestore_client=firestore_client, 
            collection_name=os.getenv("COLLECTION_NAME"), 
            document_name=email, 
            time_ranges=time_ranges, 
            sessions_of_interest=sessions_of_interest))





# Transform raw records into a DataFrame 
long_df = process_eeg_records(raw_records, return_long=True)
# Apply segment-wise filtering and artifacts detection
long_df = process_long_df(long_df,SAMPLING_RATE, artifacts_detection_method='amplitude', amplitude_threshold=20)




# Extract features
features_df = extract_features_from_long_df(long_df, SAMPLING_RATE)

# Apply exponential moving averavge, normalization and generates time-based features
N=15 # window size for the ema filter
alpha=2/(N+1) # smoothing factor for the ema filter - rule of thumb
print(f'smoothing factor: {alpha}')
columns_to_normalize = ['gamma_fil', 'gamma1_fil', 'gamma2_fil' ]
features_df = process_features(features_df, alpha, columns_to_normalize)
features_df.head()