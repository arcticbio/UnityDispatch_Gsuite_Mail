#import smtplib
from email.mime.text import MIMEText
import base64
import os
import pyodbc
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging
from datetime import datetime

# OAuth2 scope for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


load_dotenv()  # load vars from .env

# --- determine project root and invoice folder dynamically ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pdf_directory = os.path.join(BASE_DIR, os.getenv("INVOICE_DIR"))
logs_directory = os.path.join(BASE_DIR, "logs")

# --- set up logging ---
if not os.path.exists(logs_directory):
    os.makedirs(logs_directory)

log_file = os.path.join(logs_directory, f'email_log_{datetime.now().strftime("%Y%m%d")}.txt')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_customers():
    # Connect to SQL Server
    try:
        # --- Database connection ---
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASSWORD')}"
        )

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 3 LTRIM(c.cu_id) cu_id
                , c.num
                , c.bill_name
                , c.greeting
                , 'dredmond@tenagolabs.com' email --c.email
                , SUM(inv_total) - SUM(inv_paid) AS BalanceDue
            FROM [JUSTLAWNS_CLIP]...[INV_HEAD] ih
                INNER JOIN [JUSTLAWNS_CLIP]...[customer] c ON ih.inv_cu_id = c.cu_id
            WHERE inv_total > inv_paid
                AND c.p_grp_code = 'ECRE'
            GROUP BY c.cu_id, c.num, c.bill_name, c.greeting, c.email
            HAVING SUM(inv_total) - SUM(inv_paid) > 0
            ORDER BY cu_id
        """)
        rows = cursor.fetchall()
        logging.info("Successfully retrieved customer data from database")
    except pyodbc.Error as e:
        logging.error(f"Database connection error: {e}")
        print(f"Database connection error: {e}")
        exit(1)

    conn.close()
    return rows

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
    logging.info("Gmail service initialized successfully")
    return service

def create_message(to, subject, message_text, file):
    msg = MIMEMultipart()
    msg['to'] = to
#    msg['bcc'] = 'dredmond@tenagolabs.com'  # Add BCC recipient
    msg['From'] = os.getenv("GMAIL_USER")
    msg['subject'] = subject
    msg.attach(MIMEText(message_text, 'plain'))
    
    if file and os.path.exists(file):
        with open(file, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file)}')
            msg.attach(part)
        logging.info(f"Attached PDF: {file}")
    else:
        logging.warning(f'PDF not found: {file}')
        print(f'PDF not found: {file}')
        return None
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {'raw': raw}

def main():
    service = get_gmail_service()
    customers = get_customers()
    
    for row in customers:
        cu_id = row.cu_id
        email = row.email
        greeting = row.greeting
        balance_due = row.BalanceDue
        
        pdf_path = os.path.join(pdf_directory, f'os_{cu_id}.pdf')
        if not os.path.exists(pdf_path):
            logging.warning(f'PDF not found for cu_id {cu_id}: {pdf_path}')
            print(f'PDF not found for cu_id {cu_id}: {pdf_path}')
            continue
        
        subject = 'Your Invoice from JUSTLAWNS'
        message_text = f'Dear {greeting},\n\nPlease find attached your invoice. Your current balance due is {balance_due}.\n\nThank you.'
        
        message = create_message(email, subject, message_text, pdf_path)
        if message:
            try:
                service.users().messages().send(userId='me', body=message).execute()
                logging.info(f'Email sent to {email} for cu_id {cu_id}')
                print(f'Email sent to {email}')
            except Exception as e:
                logging.error(f'Failed to send email to {email} for cu_id {cu_id}: {e}')
                print(f'Failed to send email to {email}: {e}')

if __name__ == '__main__':
    main()