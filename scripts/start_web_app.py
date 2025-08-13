#!/usr/bin/env python3
"""
Startup script for the EEG Session Browser web application.
This ensures the .env file is in the correct location and starts the Flask app.
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists in the current directory."""
    env_path = Path('.env')
    if not env_path.exists():
        print("ERROR: .env file not found in the current directory!")
        print("Please ensure your .env file is in the same folder as this script.")
        print("The .env file should contain:")
        print("  GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json")
        print("  COLLECTION_NAME=your_collection_name")
        print("  EMAILS=email1@example.com,email2@example.com,...")
        return False
    
    print("✓ .env file found")
    return True

def check_credentials():
    """Check if Google credentials file exists."""
    from dotenv import load_dotenv
    load_dotenv()
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set in .env file!")
        return False
    
    if not os.path.exists(creds_path):
        print(f"ERROR: Credentials file not found at: {creds_path}")
        return False
    
    print("✓ Google credentials file found")
    return True

def main():
    """Main startup function."""
    print("Starting EEG Session Browser Web Application...")
    print("=" * 50)
    
    # Check requirements
    if not check_env_file():
        sys.exit(1)
    
    if not check_credentials():
        sys.exit(1)
    
    # Import and run the Flask app
    try:
        from web_app import app
        print("\n✓ All checks passed!")
        print("Starting web server...")
        print("Access the application at: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"ERROR: Failed to import web_app: {e}")
        print("Make sure all required packages are installed:")
        print("  pip install -r requirements_web.txt")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to start web application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
