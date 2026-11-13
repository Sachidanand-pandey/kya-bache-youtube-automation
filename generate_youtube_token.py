from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    SCOPES
)

credentials = flow.run_local_server(
    host="localhost",
    port=0,
    access_type="offline",
    prompt="consent"
)

print("\nOAuth authentication successful.")
print("Client ID:", credentials.client_id)
print("Client Secret:", credentials.client_secret)
print("Refresh Token:", credentials.refresh_token)

