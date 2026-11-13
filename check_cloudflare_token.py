
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("CLOUDFLARE_API_TOKEN")

if not token:
    print("Cloudflare token missing from .env")
    exit()

response = requests.get(
    "https://api.cloudflare.com/client/v4/user/tokens/verify",
    headers={
        "Authorization": "Bearer " + token
    },
    timeout=30
)

print("HTTP status:", response.status_code)
print("Response:", response.json())
