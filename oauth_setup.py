"""
Run this once on your own computer to obtain a YouTube OAuth refresh token.
Download an OAuth client JSON for a Desktop app from Google Cloud Console,
save it as client_secret.json beside this file, then run:
    python oauth_setup.py
Do not commit client_secret.json or the printed refresh token to GitHub.
"""
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")

print("\nSave these values as GitHub repository Actions secrets:")
print("YOUTUBE_CLIENT_ID =", credentials.client_id)
print("YOUTUBE_CLIENT_SECRET =", credentials.client_secret)
print("YOUTUBE_REFRESH_TOKEN =", credentials.refresh_token)
print("\nKeep these values private. Do not commit them to your repository.")
