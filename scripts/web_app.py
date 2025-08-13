#!/usr/bin/env python3
"""
Simple Flask web application for browsing EEG sessions.
Replicates the functionality of session_browser.py in a web interface.
"""

import os
import json
import base64
from io import BytesIO
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import plotly.graph_objects as go
import plotly.utils

# Load environment variables
load_dotenv()

# Add src to path for imports
from setup_path import add_src_to_path
add_src_to_path()

from awear_neuroscience.data_extraction.firestore_loader import query_eeg_data, process_eeg_records
from awear_neuroscience.data_extraction.reshape import normalize_session

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize Firebase
cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
firebase_admin.initialize_app(cred)
firestore_client = firestore.Client()

print("Firebase initialized for web app")


def get_available_emails() -> List[str]:
    """Get list of available emails from environment variable."""
    emails_str = os.getenv("EMAILS", "")
    if not emails_str:
        return [os.getenv("DOCUMENT_NAME", "")]
    return [email.strip() for email in emails_str.split(",")]


def get_recent_sessions(email: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent sessions for a user."""
    col_ref = firestore_client.collection(os.getenv("COLLECTION_NAME"))
    subcol = col_ref.document(email).collection("focus_sessions")
    
    query = subcol.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    
    sessions = []
    for doc in query.stream():
        session_data = doc.to_dict()
        session_data['doc_id'] = doc.id
        sessions.append(session_data)
    
    return sessions


def get_session_eeg_data(email: str, session: Dict[str, Any]) -> tuple[List[Dict[str, Any]], str]:
    """
    Get EEG data for a session.
    Returns tuple of (eeg_records, debug_info)
    """
    debug_info = ""
    
    try:
        # Normalize session to get time ranges
        start_dt, end_dt, start_fmt, end_fmt, session_time_ranges = normalize_session(session)
        
        debug_info += f"Session normalization:\n"
        debug_info += f"  Original timestamp: {session.get('timestamp')}\n"
        debug_info += f"  Original start/end: {session.get('start_time')} - {session.get('end_time')}\n"
        debug_info += f"  Normalized range: {start_dt} to {end_dt}\n"
        
        # Query EEG data
        eeg_records = query_eeg_data(
            firestore_client=firestore_client,
            collection_name=os.getenv("COLLECTION_NAME"),
            document_name=email,
            subcollection_name="live_data",
            time_ranges=session_time_ranges,
        )
        
        debug_info += f"  Found {len(eeg_records)} EEG records\n"
        
        # If no records found, try alternative approach
        if len(eeg_records) == 0:
            debug_info += "  Trying alternative time range...\n"
            session_ts = datetime.fromisoformat(session["timestamp"].replace("Z", "+00:00"))
            duration_min = session.get("duration_minutes", 1)
            
            alt_start = session_ts - timedelta(minutes=1)
            alt_end = session_ts + timedelta(minutes=duration_min)
            
            debug_info += f"  Alternative range: {alt_start} to {alt_end}\n"
            
            eeg_records = query_eeg_data(
                firestore_client=firestore_client,
                collection_name=os.getenv("COLLECTION_NAME"),
                document_name=email,
                subcollection_name="live_data",
                time_ranges=[(alt_start, alt_end)],
            )
            
            debug_info += f"  Alternative approach found {len(eeg_records)} records\n"
        
        # Annotate records
        for record in eeg_records:
            record["session_type"] = session.get("session_type", "") or session.get("focus_type", "")
            record["document_name"] = email
            record["session_start"] = session.get("start_time")
            record["session_end"] = session.get("end_time")
            record["session_duration"] = session.get("duration_minutes")
            record["session_timestamp"] = session.get("timestamp")
        
        return eeg_records, debug_info
        
    except Exception as e:
        debug_info += f"Error: {str(e)}\n"
        return [], debug_info


def create_eeg_plot(long_df):
    """Create a Plotly EEG waveform plot."""
    if long_df.empty:
        return None
    
    # Get first segment data
    seg_data = long_df[long_df['segment'] == 'seg_0']
    if seg_data.empty:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=seg_data['time_sample'],
        y=seg_data['waveform_value'],
        mode='lines',
        name='EEG Signal',
        line=dict(color='blue', width=1)
    ))
    
    fig.update_layout(
        title='EEG Waveform - First Segment',
        xaxis_title='Time (normalized)',
        yaxis_title='Amplitude',
        width=800,
        height=400,
        template='simple_white'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


@app.route('/')
def login():
    """Login page - email selection."""
    emails = get_available_emails()
    return render_template('login.html', emails=emails)


@app.route('/select_email', methods=['POST'])
def select_email():
    """Handle email selection."""
    selected_email = request.form.get('email')
    if not selected_email:
        return redirect(url_for('login'))
    
    session['email'] = selected_email
    return redirect(url_for('sessions'))


@app.route('/sessions')
def sessions():
    """Sessions listing page."""
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))
    
    sessions_list = get_recent_sessions(email)
    
    # Format sessions for display
    formatted_sessions = []
    for i, sess in enumerate(sessions_list):
        try:
            ts = datetime.fromisoformat(sess["timestamp"].replace("Z", "+00:00"))
            date_str = ts.strftime("%Y-%m-%d")
            time_str = ts.strftime("%H:%M:%S")
        except:
            date_str = "Unknown"
            time_str = "Unknown"
        
        session_type = sess.get("session_type", "") or sess.get("focus_type", "Unknown")
        duration = sess.get("duration_minutes", "Unknown")
        if duration != "Unknown":
            duration = f"{duration} min"
        
        start_time = sess.get("start_time", "")
        end_time = sess.get("end_time", "")
        status = "Ready" if start_time and end_time else "Incomplete"
        
        formatted_sessions.append({
            'index': i,
            'date': date_str,
            'time': time_str,
            'type': session_type,
            'duration': duration,
            'status': status,
            'data': sess
        })
    
    return render_template('sessions.html', 
                         email=email, 
                         sessions=formatted_sessions)


@app.route('/session/<int:session_index>')
def session_detail(session_index):
    """Session detail page with EEG processing."""
    email = session.get('email')
    if not email:
        return redirect(url_for('login'))
    
    sessions_list = get_recent_sessions(email)
    if session_index >= len(sessions_list):
        return "Session not found", 404
    
    selected_session = sessions_list[session_index]
    
    # Get EEG data
    eeg_records, debug_info = get_session_eeg_data(email, selected_session)
    
    context = {
        'email': email,
        'session': selected_session,
        'session_type': selected_session.get("session_type", "") or selected_session.get("focus_type", "Unknown"),
        'duration': selected_session.get("duration_minutes", "Unknown"),
        'start_time': selected_session.get("start_time", "Unknown"),
        'end_time': selected_session.get("end_time", "Unknown"),
        'timestamp': selected_session.get("timestamp", "Unknown"),
        'has_data': len(eeg_records) > 0,
        'record_count': len(eeg_records),
        'debug_info': debug_info,
        'plot_json': None
    }
    
    if len(eeg_records) > 0:
        # Process data
        try:
            long_df = process_eeg_records(eeg_records, return_long=True)
            context['segments_count'] = long_df.shape[0] // 256 if not long_df.empty else 0
            
            # Create plot
            plot_json = create_eeg_plot(long_df)
            context['plot_json'] = plot_json
            
        except Exception as e:
            context['error'] = f"Error processing EEG data: {str(e)}"
    
    return render_template('session_detail.html', **context)


@app.route('/logout')
def logout():
    """Clear session and return to login."""
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
