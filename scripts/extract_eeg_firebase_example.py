# cell 1: Initialization

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
load_dotenv()

from setup_path import add_src_to_path
add_src_to_path()
from awear_neuroscience.data_extraction.firestore_loader import query_eeg_data, process_eeg_records



# Initialize Firebase app

cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)
firestore_client = firestore.Client()

print("Firebase initialized")



# cell 2: Define query parameters
from datetime import datetime, timedelta

# Example: pull from last 5 hours
now = datetime.now()
time_ranges = [(now - timedelta(hours=400), now)]

print(f"Querying EEG data between {time_ranges[0][0]} and {time_ranges[0][1]}")



# cell 3: Query and process records
raw_records = query_eeg_data(
    firestore_client=firestore_client,
    collection_name=os.getenv("COLLECTION_NAME"),
    document_name=os.getenv("DOCUMENT_NAME"),
    subcollection_name=os.getenv("SUBCOLLECTION_NAME"),
    time_ranges=time_ranges,
)

print(f"Retrieved {len(raw_records)} raw records.")





compact_df = process_eeg_records(raw_records)
print(f"Processed DataFrame shape: {compact_df.shape}")
compact_df.head()



long_df = process_eeg_records(raw_records, return_long=True)
print(f"Processed DataFrame shape: {long_df.shape}, {long_df.shape[0]//256}")
long_df.head()



# cell: Visualize waveform using Plotly
from awear_neuroscience.utils.plot_utils import plot_eeg_waveform

# Plot one segment
plot_eeg_waveform(long_df, segment_id="seg_0")
