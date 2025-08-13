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



# cell 2: Email Selection
# Get available emails from environment variable
emails_str = os.getenv("EMAILS", "")
if not emails_str:
    print("No EMAILS found in environment variables. Using DOCUMENT_NAME as fallback.")
    available_emails = [os.getenv("DOCUMENT_NAME")]
else:
    available_emails = [email.strip() for email in emails_str.split(",")]

print("Available emails:")
for i, email in enumerate(available_emails):
    print(f"{i + 1}. {email}")

# Allow user to select email
while True:
    try:
        choice = input(f"\nSelect email (1-{len(available_emails)}): ").strip()
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(available_emails):
            selected_email = available_emails[choice_idx]
            break
        else:
            print(f"Please enter a number between 1 and {len(available_emails)}")
    except ValueError:
        print("Please enter a valid number")
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()

print(f"Selected email: {selected_email}")



# cell 3: Define query parameters
from datetime import datetime, timedelta

# Example: pull from last 400 hours
now = datetime.now()
time_ranges = [(now - timedelta(hours=400), now)]

print(f"Querying EEG data for {selected_email} between {time_ranges[0][0]} and {time_ranges[0][1]}")



# cell 4: Query and process records
raw_records = query_eeg_data(
    firestore_client=firestore_client,
    collection_name=os.getenv("COLLECTION_NAME"),
    document_name=selected_email,  # Use selected email instead of env variable
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



# cell 5: Save data (optional)
if not long_df.empty:
    # Create filename with email name (sanitized for filesystem)
    email_name = selected_email.replace("@", "_").replace(".", "_")
    filename = f"../data/long_df_{email_name}.csv"
    
    save_data = input(f"\nSave data to {filename}? (y/n): ").strip().lower()
    if save_data in ['y', 'yes']:
        # Create data directory if it doesn't exist
        os.makedirs("../data", exist_ok=True)
        long_df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    else:
        print("Data not saved.")
else:
    print("No data to save.")



# cell 6: Visualize waveform using Plotly
if not long_df.empty:
    from awear_neuroscience.utils.plot_utils import plot_eeg_waveform
    
    visualize = input("\nVisualize waveform? (y/n): ").strip().lower()
    if visualize in ['y', 'yes']:
        # Plot one segment
        plot_eeg_waveform(long_df, segment_id="seg_0")
    else:
        print("Skipping visualization.")
else:
    print("No data to visualize.")
