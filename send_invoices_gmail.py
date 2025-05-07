import os
import pyodbc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import base64


load_dotenv()  # load vars from .env

# --- determine project root and invoice folder dynamically ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pdf_directory = os.path.join(BASE_DIR, os.getenv("INVOICE_DIR"))

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
    SELECT TOP 3 LTRIM(c.cu_id)
        , c.num
        , c.bill_name
        , c.greeting
        , 'test@test.com' email --c.email
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
except pyodbc.Error as e:
    print(f"Database connection error: {e}")
    exit(1)


# Connect to SMTP server
try:
    server = smtplib.SMTP(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT"))
    server.starttls()
    server.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_PASSWORD'))
except smtplib.SMTPException as e:
    print(f"SMTP connection error: {e}")
    print(f"USER: {os.getenv('GMAIL_USER')} PASS: {os.getenv('GMAIL_PASSWORD')}")
    exit(1)


# Function to send email with PDF attachment
def send_email(to_email, greeting, balance_due, pdf_path):
    msg = MIMEMultipart()
    msg['From'] = os.getenv("GMAIL_USER")
    msg['To'] = to_email
    msg['Subject'] = 'Invoice from JustLawns'
    
    # Email body with formatted balance due
    body = f"{greeting},\n\nPlease find attached your invoice. Your current balance due is ${balance_due:.2f}.\n\nThank you,\nJustLawns Team"
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach the PDF
    try:
        with open(pdf_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(pdf_path)}')
            msg.attach(part)
    except Exception as e:
        raise Exception(f"Error attaching PDF: {e}")
    
    # Send the email
    server.send_message(msg)

# Process each customer
for row in rows:
    try:
        cu_id = row.cu_id
        email = row.email
        greeting = row.greeting
        balance_due = row.BalanceDue
        pdf_path = os.path.join(pdf_directory, f"os_{cu_id}.pdf")
        if os.path.exists(pdf_path):
            send_email(email, greeting, balance_due, pdf_path)
        else:
            print(f"PDF not found for customer {cu_id}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

# Close connections
conn.close()
server.quit()



















for cu_id, num, bill_name, greeting, email, balance in cursor:
    # only send if email exists and balance > 0
    if not email or balance <= 0:
        continue

    pdf_path = os.path.join(invoice_dir, f"os_{cu_id}.pdf")
    if not os.path.isfile(pdf_path):
        print(f"[WARN] No invoice found for CU_ID {cu_id}")
        print(pdf_path)
        continue

    # read & base64-encode the PDF
    with open(pdf_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    # build the email
    subject = f"Just Lawns Statement May 5, 2025 – Balance Due ${balance:.2f}"
    html_content = (
        f"<p>Dear {greeting}</p>"
        f"<p>Your Just Lawns statement balance is <strong>${balance:.2f}</strong>. "
        "Please see your invoice attached.</p>"
    )
    message = Mail(
        from_email=from_email,
        to_emails=email,
        subject=subject,
        html_content=html_content
    )

    message.reply_to='billing@justlawns.net'


    personalization = Personalization()

    personalization.add_to(To("dredmond@tenagolabs.com"))                # primary recipient
 #   personalization.add_bcc(Bcc("dredmond.billing@tenagolabs.com"))    # your BCC address :contentReference[oaicite:0]{index=0}


    attachment = Attachment(
        FileContent(encoded),
        FileName(f"Statement_{cu_id}.pdf"),
        FileType("application/pdf"),
        Disposition("attachment")
    )
    message.attachment = attachment

    # send it
    try:
        resp = sg.send(message)
        print(f"[INFO] Sent to {email}: {resp.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send to {email}: {e}")
