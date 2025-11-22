"""Quick test of Streamlit app dependencies and model."""
import sys
import pandas as pd
import numpy as np
import joblib
import yfinance as yf
from datetime import datetime, timedelta

print("✓ All imports successful")

# Test model loading
try:
    model = joblib.load("models/short_term_lgb_all.pkl")
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Model load error: {e}")
    sys.exit(1)

# Test data fetch
symbol = "TCS.NS"
print(f"\n✓ Testing data fetch for {symbol}...")
try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    print(f"✓ Fetched {len(df)} rows for {symbol}")
except Exception as e:
    print(f"✗ Data fetch error: {e}")
    sys.exit(1)

print("\n✅ All tests passed! Streamlit app should work correctly.")
