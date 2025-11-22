"""
Single Stock Inference: Tata Motors (TATAMOTORS.NS)
Fetch live data and generate prediction using trained model.
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import yfinance as yf

# ============================================================================
# LOAD THE TRAINED MODEL
# ============================================================================

MODEL_PATH = "models/short_term_lgb_all.pkl"
model = joblib.load(MODEL_PATH)
print(f"✓ Loaded model from {MODEL_PATH}")

# ============================================================================
# FETCH TATA MOTORS DATA
# ============================================================================

SYMBOL = "TATAMOTORS.NS"
DAYS_LOOKBACK = 60

print(f"\nFetching {DAYS_LOOKBACK} days of data for {SYMBOL}...")
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_LOOKBACK)

df = yf.download(SYMBOL, start=start_date, end=end_date, progress=False)

# Handle MultiIndex columns (flatten to single level)
if isinstance(df.columns, pd.MultiIndex):
    # For single-symbol download, columns are like ('Close', 'TATAMOTORS.NS')
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

# If Adj Close not in columns, use Close as substitute
if 'Adj Close' not in df.columns and 'Close' in df.columns:
    df['AdjClose'] = df['Close']
elif 'Adj Close' in df.columns:
    df['AdjClose'] = df['Adj Close']

df.index.name = 'date'
df = df.reset_index()

print(f"✓ Fetched {len(df)} trading days")
print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
print(f"\nLatest price data:")
print(df[['date', 'Close', 'Volume']].tail(5).to_string(index=False))

# ============================================================================
# COMPUTE FEATURES FOR TATA MOTORS
# ============================================================================

def compute_features(symbol_df):
    """Compute all 12 required features for a single symbol."""
    df = symbol_df.copy().sort_values('date').reset_index(drop=True)
    
    # Compute returns
    ret_1 = df['AdjClose'].pct_change(1)
    ret_3 = df['AdjClose'].pct_change(3)
    ret_5 = df['AdjClose'].pct_change(5)
    ret_10 = df['AdjClose'].pct_change(10)
    ret_20 = df['AdjClose'].pct_change(20)
    
    # Moving average spreads
    ma_5 = df['AdjClose'].rolling(5).mean()
    ma_20 = df['AdjClose'].rolling(20).mean()
    ma_50 = df['AdjClose'].rolling(50).mean()
    ma_spread_5_20 = (ma_5 - ma_20) / ma_20
    ma_spread_5_50 = (ma_5 - ma_50) / ma_50
    
    # Volatility (standard deviation of returns)
    vol_10 = ret_1.rolling(10).std()
    vol_20 = ret_1.rolling(20).std()
    
    # Volume z-score (relative to 20-day average)
    vol_mean = df['Volume'].rolling(20).mean()
    vol_std = df['Volume'].rolling(20).std()
    vol_z = (df['Volume'] - vol_mean) / (vol_std + 1e-8)
    
    # RSI (Relative Strength Index)
    delta = df['AdjClose'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / (loss + 1e-8)
    rsi = 100 - (100 / (1 + rs))
    
    # Relative momentum
    rel_mom_5 = (df['AdjClose'].iloc[-1] - df['AdjClose'].iloc[-5]) / df['AdjClose'].iloc[-5] if len(df) >= 5 else 0
    
    # Assemble features for the latest date
    features = {
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
    }
    
    return pd.Series(features)

print("\n" + "="*70)
print("COMPUTING FEATURES")
print("="*70)

features = compute_features(df)
feature_cols = ['ret_1','ret_3','ret_5','ret_10','ret_20',
                'ma_spread_5_20','ma_spread_5_50',
                'vol_10','vol_20','vol_z','rsi','rel_mom_5']

print("\nFeature values for", SYMBOL)
print("-" * 70)
for feat, val in features.items():
    print(f"  {feat:20s}: {val:+.6f}")

# ============================================================================
# GENERATE PREDICTION
# ============================================================================

print("\n" + "="*70)
print("MODEL PREDICTION")
print("="*70)

X = features[feature_cols].values.reshape(1, -1)
pred_score = model.predict(X, num_iteration=model.best_iteration)[0]

print(f"\nSymbol:                  {SYMBOL}")
print(f"Current Price:           ₹{df['Close'].iloc[-1]:.2f}")
print(f"Date:                    {df['date'].iloc[-1].strftime('%Y-%m-%d')}")
print(f"Prediction Timestamp:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"\n{'Predicted 5-Day Return':30s}: {pred_score:+.4%}")

# Calculate predicted target price
current_price = df['Close'].iloc[-1]
predicted_target = current_price * (1 + pred_score)
print(f"Predicted Target Price:  ₹{predicted_target:.2f}")
print(f"Price Move (₹):          {predicted_target - current_price:+.2f}")

# ============================================================================
# INTERPRETATION & TRADING SIGNAL
# ============================================================================

print("\n" + "="*70)
print("INTERPRETATION & SIGNAL")
print("="*70)

if pred_score > 0.02:
    signal = "BUY"
    strength = "Strong"
    if pred_score > 0.05:
        strength = "Very Strong"
elif pred_score < -0.02:
    signal = "SELL"
    strength = "Strong"
    if pred_score < -0.05:
        strength = "Very Strong"
else:
    signal = "NEUTRAL"
    strength = "Weak"

print(f"\nSignal:                  {signal} ({strength})")
print(f"Expected Return:         {pred_score:+.2%} over 5 trading days")
print(f"Annualized Equivalent:   {((1 + pred_score) ** (252/5)) - 1:+.2%}")

# Risk considerations
print(f"\nTechnical Indicators:")
print(f"  RSI (14):              {features['rsi']:.2f} {'(Overbought >70)' if features['rsi'] > 70 else '(Oversold <30)' if features['rsi'] < 30 else '(Neutral 30-70)'}")
print(f"  MA Spread (5/20):      {features['ma_spread_5_20']:+.4f} {'(Uptrend)' if features['ma_spread_5_20'] > 0 else '(Downtrend)'}")
print(f"  MA Spread (5/50):      {features['ma_spread_5_50']:+.4f} {'(Uptrend)' if features['ma_spread_5_50'] > 0 else '(Downtrend)'}")
print(f"  Volatility (20d):      {features['vol_20']:.4f}")
print(f"  Volume Z-Score:        {features['vol_z']:+.2f} {'(High volume)' if features['vol_z'] > 1 else '(Low volume)' if features['vol_z'] < -1 else '(Normal volume)'}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

result_df = pd.DataFrame({
    'symbol': [SYMBOL],
    'date': [df['date'].iloc[-1]],
    'current_price': [current_price],
    'pred_score': [pred_score],
    'predicted_target': [predicted_target],
    'signal': [signal],
    'timestamp': [datetime.now()]
})

result_df.to_csv('output/tatamotors_prediction.csv', index=False)
print(f"\n✓ Prediction saved to: output/tatamotors_prediction.csv")

# ============================================================================
# HISTORICAL CONTEXT (Last 10 days)
# ============================================================================

print("\n" + "="*70)
print("PRICE HISTORY (Last 10 Days)")
print("="*70)
recent = df[['date', 'Close', 'Volume']].tail(10).copy()
recent['Daily Return'] = recent['Close'].pct_change().fillna(0)
print(recent.to_string(index=False))

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"""
The model predicts {SYMBOL} will {signal.lower()} over the next 5 trading days.

Predicted Return:     {pred_score:+.2%}
Current Price:        ₹{current_price:.2f}
Target Price:         ₹{predicted_target:.2f}
Signal Strength:      {strength}

This is based on 12 technical indicators including:
  - Price momentum (1, 3, 5, 10, 20-day returns)
  - Moving average trends (5/20 and 5/50 spreads)
  - Volatility measures
  - RSI and volume analysis

⚠️  Disclaimer: This is a model-based prediction and NOT financial advice.
Past performance does not guarantee future results. Always implement proper
risk management and stop-losses before trading.
""")
