import os
import pyodbc
import base64
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Personalization, To, Bcc,
    Attachment, FileContent, FileName, FileType, Disposition, Email
)

load_dotenv()  # load vars from .env

# --- Database connection ---
conn_str = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};PWD={os.getenv('DB_PASSWORD')}"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# --- SendGrid client setup ---
sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
from_email = os.getenv("FROM_EMAIL")


# --- determine project root and invoice folder dynamically ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
invoice_dir = os.path.join(BASE_DIR, os.getenv("INVOICE_DIR"))

# ensure it exists
os.makedirs(invoice_dir, exist_ok=True)

# --- Query our view for customers owing money ---
query = """
SELECT TOP 3 LTRIM(c.cu_id), c.num, c.bill_name, c.greeting, 'test@test.com',
       SUM(inv_total) - SUM(inv_paid) AS BalanceDue
FROM JUSTLAWNS_CLIP...[INV_HEAD] ih
JOIN JUSTLAWNS_CLIP...[customer] c
  ON ih.inv_cu_id = c.cu_id
WHERE inv_total > inv_paid
  AND c.p_grp_code = 'ECRE'
GROUP BY c.cu_id, c.num, c.bill_name, c.greeting, c.email
ORDER BY c.cu_id
"""
cursor.execute(query)

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

    message.reply_to='test@test.com'


    personalization = Personalization()

    personalization.add_to(To("test@test.com"))                # primary recipient


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
