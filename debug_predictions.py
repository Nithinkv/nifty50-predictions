"""Debug script to identify prediction generation issues."""
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import yfinance as yf

# Load model
model = joblib.load("models/short_term_lgb_all.pkl")
print("✓ Model loaded")

# Test with a single stock
symbol = "TCS.NS"
end_date = datetime.now()
start_date = end_date - timedelta(days=120)

# Fetch data
df = yf.download(symbol, start=start_date, end=end_date, progress=False)

# Handle MultiIndex
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

# Create AdjClose
if 'Adj Close' not in df.columns and 'Close' in df.columns:
    df['AdjClose'] = df['Close']
elif 'Adj Close' in df.columns:
    df['AdjClose'] = df['Adj Close']

df.index.name = 'date'
df = df.reset_index()

print(f"\n✓ Fetched {len(df)} rows for {symbol}")
print(f"Columns: {df.columns.tolist()}")
print(f"Last row:\n{df.iloc[-1]}")

# Compute features
def compute_features(symbol_df):
    """Compute all 12 required features for a single symbol."""
    df = symbol_df.copy().sort_values('date').reset_index(drop=True)
    
    if len(df) < 50:
        print(f"  ✗ Not enough data: {len(df)} rows")
        return None
    
    ret_1 = df['AdjClose'].pct_change(1)
    ret_3 = df['AdjClose'].pct_change(3)
    ret_5 = df['AdjClose'].pct_change(5)
    ret_10 = df['AdjClose'].pct_change(10)
    ret_20 = df['AdjClose'].pct_change(20)
    
    ma_5 = df['AdjClose'].rolling(5).mean()
    ma_20 = df['AdjClose'].rolling(20).mean()
    ma_50 = df['AdjClose'].rolling(50).mean()
    ma_spread_5_20 = (ma_5 - ma_20) / ma_20
    ma_spread_5_50 = (ma_5 - ma_50) / ma_50
    
    vol_10 = ret_1.rolling(10).std()
    vol_20 = ret_1.rolling(20).std()
    
    vol_mean = df['Volume'].rolling(20).mean()
    vol_std = df['Volume'].rolling(20).std()
    vol_z = (df['Volume'] - vol_mean) / (vol_std + 1e-8)
    
    delta = df['AdjClose'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / (loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    
    rel_mom_5 = (df['AdjClose'].iloc[-1] - df['AdjClose'].iloc[-5]) / df['AdjClose'].iloc[-5] if len(df) >= 5 else 0
    
    features = pd.Series({
        'ret_1': ret_1.iloc[-1],
        'ret_3': ret_3.iloc[-1],
        'ret_5': ret_5.iloc[-1],
        'ret_10': ret_10.iloc[-1],
        'ret_20': ret_20.iloc[-1],
        'ma_spread_5_20': ma_spread_5_20.iloc[-1],
        'ma_spread_5_50': ma_spread_5_50.iloc[-1],
        'vol_10': vol_10.iloc[-1],
        'vol_20': vol_20.iloc[-1],
        'vol_z': vol_z.iloc[-1],
        'rsi': rsi.iloc[-1],
        'rel_mom_5': rel_mom_5,
    })
    
    return features

print("\n--- Computing features ---")
features = compute_features(df)

if features is not None:
    print("\nFeatures computed:")
    for feat, val in features.items():
        print(f"  {feat:20s}: {val:+.6f} {'(NaN!)' if pd.isna(val) else ''}")
    
    nan_count = features.isna().sum()
    print(f"\nTotal NaN values: {nan_count}/12")
    
    if nan_count > 0:
        print("\n✗ NaN values found! These are the problem.")
        print("These features won't be used for prediction.")
    else:
        print("\n✓ All features valid, making prediction...")
        
        feature_cols = ['ret_1','ret_3','ret_5','ret_10','ret_20',
                        'ma_spread_5_20','ma_spread_5_50',
                        'vol_10','vol_20','vol_z','rsi','rel_mom_5']
        X = features[feature_cols].values.reshape(1, -1)
        pred_score = model.predict(X, num_iteration=model.best_iteration)[0]
        print(f"✓ Prediction: {pred_score:+.4%}")
else:
    print("✗ Failed to compute features")
