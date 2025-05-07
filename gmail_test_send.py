import smtplib
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import base64

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.send'])

if creds.expired and creds.refresh_token:
    creds.refresh(Request())

user = "test@test.com"
oauth2_string = f"user={user}\x01auth=Bearer {creds.token}\x01\x01"
xoauth2 = base64.b64encode(oauth2_string.encode()).decode()

sender = user
recipient = "test@test.com"
subject = "Test Email"
body = "This is a test email sent via SMTP with OAuth2."
msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = sender
msg["To"] = recipient

server = smtplib.SMTP("smtp.gmail.com", 587)
server.ehlo()
server.starttls()
server.ehlo()
server.docmd("AUTH", "XOAUTH2 " + xoauth2)
server.sendmail(sender, recipient, msg.as_string())
server.quit()