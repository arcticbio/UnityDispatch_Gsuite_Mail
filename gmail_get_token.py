import os
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "client_secret_846337948363-0s1dk5ql45gb552egkobaf74o9i6lhve.apps.googleusercontent.com.json")


flow = InstalledAppFlow.from_client_secrets_file(
    json_path,  # Update with your credentials.json path
    scopes=['https://www.googleapis.com/auth/gmail.send']
)
creds = flow.run_local_server(port=0)
with open('token.json', 'w') as token:
    token.write(creds.to_json())