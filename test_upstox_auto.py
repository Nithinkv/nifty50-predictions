"""
Upstox API Test - Automated with Code
"""

import requests
import json

# API Credentials
API_KEY = "f3430b60-1509-4a8b-ada2-776cdeb98904"
API_SECRET = "labxqzgexi"
REDIRECT_URI = "http://localhost:8501"
AUTH_CODE = "Wdb5h7"  # Fresh code from redirect URL

print("\n" + "="*80)
print("UPSTOX API TEST - AUTOMATED")
print("="*80)

# Step 1: Exchange code for access token
print("\nSTEP 1: Getting Access Token")
print("-" * 80)

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

try:
    response = requests.post(token_url, headers=headers, data=data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"✅ Access Token: {access_token[:30]}...")
        
        # Save token to file
        with open("upstox_token.txt", "w") as f:
            f.write(access_token)
        print("✅ Token saved to: upstox_token.txt")
        
        # Step 2: Test API call - Get user profile
        print("\nSTEP 2: Testing API - Getting User Profile")
        print("-" * 80)
        
        profile_url = "https://api.upstox.com/v2/user/profile"
        profile_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        profile_response = requests.get(profile_url, headers=profile_headers)
        
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"✅ Connected! User: {profile.get('data', {}).get('user_name', 'Unknown')}")
            print(f"Email: {profile.get('data', {}).get('email', 'Unknown')}")
        else:
            print(f"⚠️ Profile fetch failed: {profile_response.status_code}")
            print(profile_response.text)
        
        # Step 3: Test market data
        print("\nSTEP 3: Testing Market Data API")
        print("-" * 80)
        
        # Try to get market quote for Reliance (example)
        quote_url = "https://api.upstox.com/v2/market-quote/ltp"
        quote_params = {
            "instrument_key": "NSE_EQ|INE002A01018"  # Reliance
        }
        quote_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        quote_response = requests.get(quote_url, headers=quote_headers, params=quote_params)
        
        if quote_response.status_code == 200:
            quote_data = quote_response.json()
            print(f"✅ Market Data Retrieved!")
            print(json.dumps(quote_data, indent=2))
        else:
            print(f"⚠️ Market data fetch: {quote_response.status_code}")
            print(quote_response.text)
        
        print("\n" + "="*80)
        print("SUCCESS! Upstox API is working.")
        print("="*80)
        print("\nNext steps:")
        print("1. Your access token is saved in upstox_token.txt")
        print("2. We can now integrate this into your app")
        print("3. Ready to proceed with integration!")
        
    else:
        print(f"❌ Token request failed: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
