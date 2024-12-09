# authenticate.py

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['google-auth-api']  # Set the required scopes

def authenticate_gmail():
    """Authenticate the user with Gmail API and refresh token if expired"""
    creds = None
    # Check if token.json exists, which stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired token
        else:
            # If no credentials, prompt for login and save the credentials
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)  # Provide the path to credentials.json
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)

    return creds