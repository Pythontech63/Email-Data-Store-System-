# app2.py (Refactored)

from googleapiclient.discovery import build
from authenticate import authenticate_gmail  # Import authenticate function

def fetch_gmail_data():
    """Authenticate Gmail and fetch email data"""
    creds = authenticate_gmail()  # Call the function to authenticate and get credentials
    if creds:
        # Build the Gmail API service with the credentials
        service = build('gmail', 'v1', credentials=creds)
        
        # Fetch a list of the user's emails
        results = service.users().messages().list(userId='me').execute()
        messages = results.get('messages', [])
        return messages
    else:
        return None  # Return None if authentication fails