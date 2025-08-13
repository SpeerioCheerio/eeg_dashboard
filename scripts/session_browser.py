# Session Browser Script
# Browse and select specific EEG sessions for analysis

import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd

load_dotenv()

from setup_path import add_src_to_path
add_src_to_path()
from awear_neuroscience.data_extraction.firestore_loader import query_eeg_data, process_eeg_records
from awear_neuroscience.data_extraction.reshape import normalize_session
from awear_neuroscience.data_extraction.utils import convert_string_to_utc_timestamp


# Initialize Firebase app
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)
firestore_client = firestore.Client()

print("Firebase initialized")
print("=" * 50)


def get_recent_sessions(
    firestore_client: firestore.Client,
    collection_name: str,
    document_name: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get the most recent sessions for a user from the focus_sessions subcollection.
    
    Args:
        firestore_client: Firestore client
        collection_name: Main collection name
        document_name: User email
        limit: Maximum number of sessions to retrieve
    
    Returns:
        List of session metadata dictionaries, sorted by timestamp (newest first)
    """
    col_ref = firestore_client.collection(collection_name)
    subcol = col_ref.document(document_name).collection("focus_sessions")
    
    # Query sessions ordered by timestamp descending (newest first)
    query = subcol.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    
    sessions = []
    for doc in query.stream():
        session_data = doc.to_dict()
        session_data['doc_id'] = doc.id  # Store document ID for reference
        sessions.append(session_data)
    
    return sessions


def display_sessions(sessions: List[Dict[str, Any]], email: str) -> None:
    """Display sessions in a user-friendly format."""
    if not sessions:
        print(f"No sessions found for {email}")
        return
    
    print(f"\nRecent sessions for {email}:")
    print("-" * 80)
    print(f"{'#':<3} {'Date':<12} {'Time':<12} {'Type':<15} {'Duration':<10} {'Status'}")
    print("-" * 80)
    
    for i, session in enumerate(sessions):
        # Parse timestamp
        try:
            ts = datetime.fromisoformat(session["timestamp"].replace("Z", "+00:00"))
            date_str = ts.strftime("%Y-%m-%d")
            time_str = ts.strftime("%H:%M:%S")
        except:
            date_str = "Unknown"
            time_str = "Unknown"
        
        # Get session type
        session_type = session.get("session_type", "") or session.get("focus_type", "Unknown")
        
        # Get duration
        duration = session.get("duration_minutes", "Unknown")
        if duration != "Unknown":
            duration = f"{duration} min"
        
        # Check if session has valid time data
        start_time = session.get("start_time", "")
        end_time = session.get("end_time", "")
        status = "✓ Ready" if start_time and end_time else "⚠ Incomplete"
        
        print(f"{i+1:<3} {date_str:<12} {time_str:<12} {session_type:<15} {duration:<10} {status}")


def get_session_eeg_data(
    firestore_client: firestore.Client,
    collection_name: str,
    document_name: str,
    session: Dict[str, Any],
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Get EEG data for a specific session.
    
    Args:
        firestore_client: Firestore client
        collection_name: Main collection name  
        document_name: User email
        session: Session metadata dictionary
        debug: Whether to print debugging information
    
    Returns:
        List of EEG data records for the session
    """
    try:
        # Normalize session to get time ranges
        start_dt, end_dt, start_fmt, end_fmt, session_time_ranges = normalize_session(session)
        
        if debug:
            print(f"\nDEBUG: Session normalization results:")
            print(f"  Original session timestamp: {session.get('timestamp')}")
            print(f"  Original start_time: {session.get('start_time')}")
            print(f"  Original end_time: {session.get('end_time')}")
            print(f"  Original duration: {session.get('duration_minutes')} minutes")
            print(f"  Normalized start_dt: {start_dt}")
            print(f"  Normalized end_dt: {end_dt}")
            print(f"  Formatted start: {start_fmt}")
            print(f"  Formatted end: {end_fmt}")
            print(f"  Time range for query: {session_time_ranges}")
        
        # Query EEG data for this session's time range
        eeg_records = query_eeg_data(
            firestore_client=firestore_client,
            collection_name=collection_name,
            document_name=document_name,
            subcollection_name="live_data",
            time_ranges=session_time_ranges,
        )
        
        if debug:
            print(f"  EEG query returned {len(eeg_records)} records")
            if len(eeg_records) == 0:
                print(f"  No EEG data found in time range {session_time_ranges[0][0]} to {session_time_ranges[0][1]}")
                
                # Try a broader time range to see if there's data nearby
                print(f"\nDEBUG: Trying broader time range...")
                broader_start = start_dt - timedelta(minutes=5)
                broader_end = end_dt + timedelta(minutes=5)
                broader_records = query_eeg_data(
                    firestore_client=firestore_client,
                    collection_name=collection_name,
                    document_name=document_name,
                    subcollection_name="live_data",
                    time_ranges=[(broader_start, broader_end)],
                )
                print(f"  Broader range ({broader_start} to {broader_end}) found {len(broader_records)} records")
                if broader_records:
                    print(f"  Sample timestamps from broader range:")
                    for i, rec in enumerate(broader_records[:3]):
                        print(f"    {i+1}: {rec.get('timestamp', 'No timestamp')}")
        
        # Annotate records with session metadata
        for record in eeg_records:
            record["session_type"] = session.get("session_type", "") or session.get("focus_type", "")
            record["document_name"] = document_name
            record["session_start"] = session.get("start_time")
            record["session_end"] = session.get("end_time") 
            record["session_duration"] = session.get("duration_minutes")
            record["session_timestamp"] = session.get("timestamp")
        
        return eeg_records
        
    except Exception as e:
        print(f"Error fetching EEG data for session: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return []


def main():
    # Email Selection
    emails_str = os.getenv("EMAILS", "")
    if not emails_str:
        print("No EMAILS found in environment variables. Using DOCUMENT_NAME as fallback.")
        available_emails = [os.getenv("DOCUMENT_NAME")]
    else:
        available_emails = [email.strip() for email in emails_str.split(",")]

    print("Available users:")
    for i, email in enumerate(available_emails):
        print(f"{i + 1}. {email}")

    # Allow user to select email
    while True:
        try:
            choice = input(f"\nSelect user (1-{len(available_emails)}): ").strip()
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
            return

    print(f"\nSelected user: {selected_email}")
    
    # Get recent sessions
    print("Fetching recent sessions...")
    sessions = get_recent_sessions(
        firestore_client=firestore_client,
        collection_name=os.getenv("COLLECTION_NAME"),
        document_name=selected_email,
        limit=20
    )
    
    # Display sessions
    display_sessions(sessions, selected_email)
    
    if not sessions:
        return
    
    # Allow user to select session
    while True:
        try:
            choice = input(f"\nSelect session to analyze (1-{len(sessions)}, or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return
                
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(sessions):
                selected_session = sessions[choice_idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(sessions)}")
        except ValueError:
            print("Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\nExiting...")
            return
    
    # Display selected session details
    print(f"\nSelected session:")
    print(f"  Date: {selected_session.get('timestamp', 'Unknown')}")
    print(f"  Type: {selected_session.get('session_type', '') or selected_session.get('focus_type', 'Unknown')}")
    print(f"  Duration: {selected_session.get('duration_minutes', 'Unknown')} minutes")
    print(f"  Start: {selected_session.get('start_time', 'Unknown')}")
    print(f"  End: {selected_session.get('end_time', 'Unknown')}")
    
    # Get EEG data for selected session
    print("\nFetching EEG data for selected session...")
    raw_records = get_session_eeg_data(
        firestore_client=firestore_client,
        collection_name=os.getenv("COLLECTION_NAME"),
        document_name=selected_email,
        session=selected_session,
        debug=True  # Enable debugging
    )
    
    print(f"Retrieved {len(raw_records)} EEG records for this session.")
    
    if len(raw_records) == 0:
        print("No EEG data found for this session.")
        
        # Offer alternative approaches
        print("\nTrying alternative approaches...")
        
        # Try using a time window around the session timestamp
        try_alt = input("Try using a broader time window around the session timestamp? (y/n): ").strip().lower()
        if try_alt in ['y', 'yes']:
            session_ts = datetime.fromisoformat(selected_session["timestamp"].replace("Z", "+00:00"))
            duration_min = selected_session.get("duration_minutes", 1)
            
            # Create a window: 1 minute before session timestamp to session timestamp + duration
            alt_start = session_ts - timedelta(minutes=1)
            alt_end = session_ts + timedelta(minutes=duration_min)
            
            print(f"Trying alternative time range: {alt_start} to {alt_end}")
            
            alt_records = query_eeg_data(
                firestore_client=firestore_client,
                collection_name=os.getenv("COLLECTION_NAME"),
                document_name=selected_email,
                subcollection_name="live_data",
                time_ranges=[(alt_start, alt_end)],
            )
            
            print(f"Alternative approach found {len(alt_records)} EEG records.")
            
            if len(alt_records) > 0:
                # Annotate records
                for record in alt_records:
                    record["session_type"] = selected_session.get("session_type", "") or selected_session.get("focus_type", "")
                    record["document_name"] = selected_email
                    record["session_start"] = selected_session.get("start_time")
                    record["session_end"] = selected_session.get("end_time")
                    record["session_duration"] = selected_session.get("duration_minutes")
                    record["session_timestamp"] = selected_session.get("timestamp")
                
                raw_records = alt_records
                print("Using alternative time range data.")
            else:
                print("Alternative approach also found no data.")
                return
        else:
            return
    
    # Process the data
    print("Processing data...")
    compact_df = process_eeg_records(raw_records)
    print(f"Compact DataFrame shape: {compact_df.shape}")
    
    long_df = process_eeg_records(raw_records, return_long=True)
    print(f"Long DataFrame shape: {long_df.shape}")
    if long_df.shape[0] > 0:
        print(f"Estimated segments: {long_df.shape[0]//256}")
    
    # Save data (optional)
    if not long_df.empty:
        # Create filename with email and session info
        email_name = selected_email.replace("@", "_").replace(".", "_")
        session_type = selected_session.get('session_type', '') or selected_session.get('focus_type', 'unknown')
        session_date = selected_session.get('timestamp', '').split('T')[0] if selected_session.get('timestamp') else 'unknown_date'
        filename = f"../data/session_{email_name}_{session_type}_{session_date}.csv"
        
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
    
    # Visualize waveform (optional)
    if not long_df.empty:
        visualize = input("\nVisualize waveform? (y/n): ").strip().lower()
        if visualize in ['y', 'yes']:
            try:
                from awear_neuroscience.utils.plot_utils import plot_eeg_waveform
                # Plot first segment
                plot_eeg_waveform(long_df, segment_id="seg_0")
            except ImportError as e:
                print(f"Could not import plotting utilities: {e}")
            except Exception as e:
                print(f"Error creating plot: {e}")
        else:
            print("Skipping visualization.")
    else:
        print("No data to visualize.")


if __name__ == "__main__":
    main()
