"""
Upstox API Test Script
Tests authentication and data fetching for NIFTY 50 stocks
"""

import requests
import json
from datetime import datetime

# API Credentials
API_KEY = "f3430b60-1509-4a8b-ada2-776cdeb98904"
API_SECRET = "labxqzgexi"
REDIRECT_URI = "http://localhost:8501"

# Step 1: Generate Authorization URL
def get_auth_url():
    """Generate the authorization URL for OAuth"""
    auth_url = f"https://api.upstox.com/v2/login/authorization/dialog"
    params = {
        "client_id": API_KEY,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code"
    }
    
    url = f"{auth_url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&response_type={params['response_type']}"
    print("=" * 80)
    print("STEP 1: Authorization")
    print("=" * 80)
    print("\nPlease visit this URL to authorize:")
    print(url)
    print("\nAfter authorization, you'll be redirected to a URL like:")
    print(f"{REDIRECT_URI}?code=XXXXXX")
    print("\nCopy the 'code' parameter from that URL and paste it below:")
    
    return input("\nEnter authorization code: ").strip()

# Step 2: Exchange code for access token
def get_access_token(auth_code):
    """Exchange authorization code for access token"""
    token_url = "https://api.upstox.com/v2/login/authorization/token"
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "code": auth_code,
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    print("\n" + "=" * 80)
    print("STEP 2: Getting Access Token")
    print("=" * 80)
    
    response = requests.post(token_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"✅ Access Token obtained: {access_token[:20]}...")
        return access_token
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

# Step 3: Fetch market quotes
def get_market_quotes(access_token, symbols):
    """Fetch live market quotes for given symbols"""
    quote_url = "https://api.upstox.com/v2/market-quote/quotes"
    
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Upstox uses instrument_key format: NSE_EQ|INE002A01018
    # For testing, let's use a few common stocks
    params = {
        "instrument_key": ",".join(symbols)
    }
    
    print("\n" + "=" * 80)
    print("STEP 3: Fetching Market Quotes")
    print("=" * 80)
    print(f"Requesting quotes for: {symbols}")
    
    response = requests.get(quote_url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Market Data Retrieved:")
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

# Step 4: Get instrument list (to find NIFTY 50 symbols)
def get_instruments(access_token):
    """Fetch instrument master list"""
    instruments_url = "https://api.upstox.com/v2/market-quote/instruments"
    
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    print("\n" + "=" * 80)
    print("STEP 4: Fetching Instrument List")
    print("=" * 80)
    
    response = requests.get(instruments_url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Instrument list downloaded")
        # Save to file for reference
        with open("upstox_instruments.json", "w") as f:
            json.dump(response.json(), f, indent=2)
        print("Saved to: upstox_instruments.json")
        return response.json()
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def main():
    print("\n" + "=" * 80)
    print("UPSTOX API TEST SCRIPT")
    print("=" * 80)
    
    # Step 1: Get authorization code
    auth_code = get_auth_url()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return
    
    # Step 2: Get access token
    access_token = get_access_token(auth_code)
    
    if not access_token:
        print("❌ Failed to get access token")
        return
    
    # Step 3: Test with a few sample stocks
    # These are example instrument keys - we'll need to find the correct ones
    sample_symbols = [
        "NSE_EQ|INE002A01018",  # Reliance (example)
    ]
    
    quotes = get_market_quotes(access_token, sample_symbols)
    
    # Step 4: Get full instrument list
    instruments = get_instruments(access_token)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Check upstox_instruments.json for NIFTY 50 instrument keys")
    print("2. Create symbol mapping file")
    print("3. Integrate into streamlit_app.py")

if __name__ == "__main__":
    main()
