from flask import Flask, request, render_template
from emaildata import fetch_emails_via_gmail_api, generate_pdf, upload_to_google_drive, authenticate_google_services
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a random secret key for the app

# Authenticate Gmail and Drive services once
gmail_service, drive_service = authenticate_google_services()

@app.route('/')
def home():
    """Render the login page."""
    return render_template('login.html')

@app.route('/process', methods=['POST'])
def process_email():
    """Process the email fetching and PDF generation."""
    subject_filter = request.form.get('subject', 'Default Subject')  # Get subject filter from the form

    # Fetch the emails via Gmail API
    emails = fetch_emails_via_gmail_api(gmail_service, subject_filter)

    if not emails:
        return "No emails found with the given subject."

    for sender, (subject, body) in emails.items():
        # Generate PDF as a binary stream
        pdf_output, sanitized_filename = generate_pdf(sender, subject, body)

        # Upload PDF directly to Google Drive
        upload_to_google_drive(drive_service, pdf_output, sanitized_filename)

    return "PDFs generated and uploaded to Google Drive successfully!"

if __name__ == "__main__":
    app.run(debug=True)