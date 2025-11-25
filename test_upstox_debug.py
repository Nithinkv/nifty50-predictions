"""
Upstox API Debug - Show Full Error Details
"""

import requests
import json

# API Credentials
API_KEY = "f3430b60-1509-4a8b-ada2-776cdeb98904"
API_SECRET = "labxqzgexi"
REDIRECT_URI = "http://localhost:8501"
AUTH_CODE = "4_M__o"

print("\n" + "="*80)
print("UPSTOX API DEBUG - DETAILED ERROR INFO")
print("="*80)

print("\nConfiguration:")
print(f"API Key: {API_KEY}")
print(f"Redirect URI: {REDIRECT_URI}")
print(f"Auth Code: {AUTH_CODE}")

token_url = "https://api.upstox.com/v2/login/authorization/token"

headers = {
    "accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded"
}

data = {
    "code": AUTH_CODE,
    "client_id": API_KEY,
    "client_secret": API_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
}

print("\nRequest Details:")
print(f"URL: {token_url}")
print(f"Headers: {json.dumps(headers, indent=2)}")
print(f"Data: {json.dumps(data, indent=2)}")

print("\nSending request...")

try:
    response = requests.post(token_url, headers=headers, data=data)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✅ SUCCESS!")
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # Save token
        with open("upstox_token.txt", "w") as f:
            f.write(access_token)
        print(f"Token saved to: upstox_token.txt")
    else:
        print("\n❌ FAILED")
        print("\nPossible issues:")
        print("1. Authorization code expired (they expire in ~60 seconds)")
        print("2. Code already used (can only use once)")
        print("3. Redirect URI mismatch")
        print("4. API credentials incorrect")
        
except Exception as e:
    print(f"\n❌ Exception: {str(e)}")
    import traceback
    traceback.print_exc()
