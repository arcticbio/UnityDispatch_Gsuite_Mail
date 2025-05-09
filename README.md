# UnityDispatch Gsuite Mail – Automated Invoice E‑mails

A small Python utility that **pulls customer statements from SQL Server, finds the matching PDF in your invoice folder, and sends it out via either Gmail (OAuth 2.0 over Gmail API) or Twilio SendGrid**.  
It was written to support block-scheduled monthly billing workflow, but it can be adapted to any business that needs to mail statements in bulk.

---

## ✨ Features

| Module | What it does | How it sends |
|--------|--------------|--------------|
| `send_invoices_gmail.py` | • Queries SQL Server for all open invoices<br>• Builds a personalised e‑mail with the PDF attached<br>• Sends through Gmail with OAuth 2.0 (no “less‑secure apps” needed) | `smtplib` + Gmail OAuth token |
| `send_invoices_twilio.py` | Same as above, but uses Twilio SendGrid instead of Gmail | Via SendGrid REST API |
| `gmail_get_token.py` | One‑off helper that walks you through Google’s OAuth consent screen and stores `token.json` locally | — |
| `gmail_test_send*.py` | Lightweight examples / playground scripts | Gmail API or SMTP |

---

## 🛠 Prerequisites

| Requirement | Notes |
|-------------|-------|
| **Python 3.9+** | Tested on 3.11 |
| ODBC driver for SQL Server | On Windows: *Microsoft ODBC Driver 17 for SQL Server* |
| Google Cloud project with Gmail API enabled | download *OAuth Client ID* credentials JSON |
| Twilio SendGrid account (optional) | grab your **SendGrid API Key** |
| PDF statements stored locally | file names must match pattern in `send_invoices_*` scripts |

### Python packages
pip install pyodbc python-dotenv google-auth google-auth-oauthlib
google-api-python-client sendgrid

## ⚙️ Configuration

Create a `.env` file in the repo root:

```dotenv
# === Database ===
DB_SERVER=MY-SQL-SERVER
DB_NAME=MyDatabase
DB_USER=readonly_user
DB_PASSWORD=********

# === Invoice PDFs ===
INVOICE_DIR=invoices          # relative to project root

# === Gmail (OAuth) ===
GMAIL_USER=account@gmail.com   # used as the “From” address
GMAIL_PASSWORD=                # not needed when using OAuth
CLIENT_SECRET_FILE=client_secret_xxx.json  # optional override

# === SendGrid ===
SENDGRID_API_KEY=SG.********************************
FROM_EMAIL=billing@mycompany.com

🚀 Quick Start

    Clone & install deps

git clone https://github.com/your‑org/UnityDispatch_Gsuite_Mail.git
pip install -r requirements.txt   # or the list above

Generate a Gmail OAuth token:
  python gmail_get_token.py
  Follow the browser pop‑up, grant the “Send e‑mail on your behalf” scope, and a token.json file will be created.

Drop your PDFs into the folder you named in INVOICE_DIR.

Fire away

# Gmail
python send_invoices_gmail.py
# – or –
# SendGrid
python send_invoices_twilio.py
