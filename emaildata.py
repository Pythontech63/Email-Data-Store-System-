import os
import base64
import re
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from fpdf import FPDF
from bs4 import BeautifulSoup  # For parsing HTML emails

SCOPES = ['google-auth-api', 'api-of-drive.file']  # Gmail and Google Drive access

def authenticate_google_services():
    """Authenticate the user with Gmail and Google Drive APIs."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    gmail_service = build('gmail', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    return gmail_service, drive_service

def sanitize_filename(filename):
    """Sanitize the filename by removing or replacing invalid characters."""
    sanitized_filename = re.sub(r'[<>:"/\|?*]', '_', filename)
    return sanitized_filename

def generate_pdf(sender, subject, body):
    """Generate a PDF from the email content."""
    sanitized_filename = sanitize_filename(f"{sender}_{subject}.pdf")

    # Create the PDF content (using FPDF to generate a simple PDF)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Sender: {sender}", ln=True)
    pdf.cell(200, 10, f"Subject: {subject}", ln=True)
    pdf.multi_cell(200, 10, f"Body:\n{body}")

    # Save the PDF to a binary stream
    pdf_output = pdf.output(dest='S').encode('latin1')

    return pdf_output, sanitized_filename

def upload_to_google_drive(drive_service, pdf_output, sanitized_filename):
    """Upload the generated PDF to Google Drive."""
    file_metadata = {'name': sanitized_filename}
    media = MediaIoBaseUpload(io.BytesIO(pdf_output), mimetype='application/pdf')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"PDF uploaded to Google Drive with the name: {sanitized_filename}")

def fetch_emails_via_gmail_api(gmail_service, subject_filter):
    """Fetch emails from Gmail with a specific subject."""
    query = f"subject:{subject_filter}"  # Gmail query to search by subject

    try:
        results = gmail_service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No emails found with the given subject.")
            return {}

        emails = {}
        for message in messages:
            msg = gmail_service.users().messages().get(userId='me', id=message['id']).execute()
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])

            # Extract sender and subject
            sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

            # Extract body
            body = ""
            parts = payload.get('parts', [])
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part.get('mimeType') == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    body = BeautifulSoup(body, 'html.parser').get_text()
                    break

            # Avoid duplicates
            if sender not in emails:
                emails[sender] = (subject, body)

        return emails

    except Exception as e:
        print(f"Error fetching emails: {e}")
        return {}