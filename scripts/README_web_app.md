# EEG Session Browser Web Application

A simple Flask-based web application for browsing and analyzing EEG sessions from Firebase.

## Features

- **User Selection**: Choose from available users/emails
- **Session Browsing**: View recent sessions with metadata
- **EEG Analysis**: Automatic EEG data retrieval and processing
- **Visualization**: Interactive Plotly charts for EEG waveforms
- **Debug Information**: Detailed logging for troubleshooting

## Setup

### Prerequisites

1. **Environment File**: Ensure your `.env` file is in the `scripts/` directory with:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/firebase-credentials.json
   COLLECTION_NAME=your_firestore_collection_name
   EMAILS=email1@example.com,email2@example.com,email3@example.com,email4@example.com
   FLASK_SECRET_KEY=your-secret-key-here
   ```

2. **Install Dependencies**:
   ```bash
   cd scripts/
   pip install -r requirements_web.txt
   ```

### Running the Application

1. **Navigate to the scripts directory**:
   ```bash
   cd scripts/
   ```

2. **Start the application**:
   ```bash
   python start_web_app.py
   ```

3. **Access the web interface**:
   Open your browser and go to: `http://localhost:5000`

## Usage

1. **Login**: Select a user from the dropdown list
2. **Browse Sessions**: View the list of recent sessions for the selected user
3. **View Session Details**: Click on any session to:
   - See detailed session information
   - Automatically process EEG data (if available)
   - View interactive EEG waveform plots
   - See debug information for troubleshooting

## File Structure

```
scripts/
├── web_app.py              # Main Flask application
├── start_web_app.py        # Startup script with checks
├── requirements_web.txt    # Python dependencies
├── templates/              # HTML templates
│   ├── base.html          # Base template with CSS
│   ├── login.html         # User selection page
│   ├── sessions.html      # Sessions listing page
│   └── session_detail.html # Session details and EEG analysis
└── .env                   # Environment variables (you create this)
```

## Troubleshooting

- **"No EEG data found"**: The application will automatically try alternative time ranges and provide debug information
- **Firebase connection issues**: Check that your credentials file path is correct in the `.env` file
- **Missing sessions**: Verify the collection name and user emails in your `.env` file

## Notes

- The application replicates the functionality of `session_browser.py` in a web interface
- All EEG processing happens server-side using the existing pipeline
- The interface is intentionally simple and clean without fancy styling
- Debug information is available via the expandable section on session detail pages
