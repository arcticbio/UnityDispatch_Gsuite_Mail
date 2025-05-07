import smtplib
from email.mime.text import MIMEText
import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth2 scope for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
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
    service = build('gmail', 'v1', credentials=creds)
    return service

def create_message(to, subject, message_text):
    msg = MIMEMultipart()
    msg['to'] = to
    msg['from'] = 'test@test.com'
    msg['subject'] = subject
    msg.attach(MIMEText(message_text, 'plain'))
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {'raw': raw}

def main():
    service = get_gmail_service()

    message = create_message('test@test.com', 'Test Invoice', "message_text - Hello?")
    if message:
        try:
            service.users().messages().send(userId='me', body=message).execute()
            print(f'Email sent to test@test.com')
        except Exception as e:
            print(f'Failed to send email to test@test.com: {e}')

if __name__ == '__main__':
    main()