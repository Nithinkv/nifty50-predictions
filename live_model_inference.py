"""
LIVE MODEL DEPLOYMENT GUIDE
============================

This guide explains how to use the trained LightGBM model (short_term_lgb_all.pkl or short_term_lgb_50.pkl)
in a real-world live trading scenario.

KEY COMPONENTS:
1. Load the trained model
2. Fetch fresh market data
3. Compute required features
4. Generate predictions
5. Execute trades based on signals
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import yfinance as yf

# ============================================================================
# STEP 1: LOAD THE TRAINED MODEL
# ============================================================================

MODEL_PATH = "models/short_term_lgb_all.pkl"  # Use expanded model or _50.pkl for original
model = joblib.load(MODEL_PATH)
print(f"✓ Loaded model from {MODEL_PATH}")

# ============================================================================
# STEP 2: FETCH LIVE MARKET DATA
# ============================================================================

def fetch_live_data(symbols, days_lookback=60):
    """
    Fetch recent OHLCV data for a list of symbols.
    
    Args:
        symbols: list of ticker symbols (e.g., ['RELIANCE.NS', 'TCS.NS', ...])
        days_lookback: number of historical days to fetch (for feature computation)
    
    Returns:
        dict of symbol -> DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume
    """
    data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_lookback)
    
    for sym in symbols:
        print(f"  Fetching {sym}...", end=" ")
        try:
            df = yf.download(sym, start=start_date, end=end_date, progress=False)
            df.index.name = 'date'
            df = df.reset_index()
            df.rename(columns={'Adj Close': 'AdjClose'}, inplace=True)
            data[sym] = df
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    return data

# Example: Fetch data for original 50 stocks
SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "KOTAKBANK.NS", "ITC.NS", "LT.NS", "SBIN.NS",
    "HDFC.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "BAJFINANCE.NS", "AXISBANK.NS",
    "MARUTI.NS", "SUNPHARMA.NS", "TATASTEEL.NS", "UPL.NS", "TITAN.NS",
    "NTPC.NS", "POWERGRID.NS", "HCLTECH.NS", "M&M.NS", "NESTLEIND.NS",
    "JSWSTEEL.NS", "BRITANNIA.NS", "COALINDIA.NS", "DIVISLAB.NS", "ONGC.NS",
    "BPCL.NS", "GRASIM.NS", "WIPRO.NS", "EICHERMOT.NS", "ULTRACEMCO.NS",
    "TECHM.NS", "TATAMOTORS.NS", "HDFCLIFE.NS", "ADANIPORTS.NS", "ADANIENT.NS",
    "SHREECEM.NS", "SBILIFE.NS", "CIPLA.NS", "INDUSINDBK.NS", "BAJAJ-AUTO.NS",
    "HINDALCO.NS", "COFORGE.NS", "LUPIN.NS", "MRF.NS", "PETRONET.NS",
]

print("Fetching live market data...")
live_data = fetch_live_data(SYMBOLS, days_lookback=60)

# ============================================================================
# STEP 3: COMPUTE REQUIRED FEATURES
# ============================================================================

def compute_live_features(symbol_df):
    """
    Compute all required features for a single symbol's price series.
    
    Args:
        symbol_df: DataFrame with columns including 'date', 'AdjClose', 'Volume'
    
    Returns:
        Series with feature values (single row for latest date)
    """
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

print("Computing features for all symbols...")
feature_cols = ['ret_1','ret_3','ret_5','ret_10','ret_20',
                'ma_spread_5_20','ma_spread_5_50',
                'vol_10','vol_20','vol_z','rsi','rel_mom_5']

X_live = []
symbols_valid = []
for sym, df in live_data.items():
    if len(df) < 50:  # Need enough history for feature computation
        continue
    features = compute_live_features(df)
    if not features.isna().any():  # Only include if all features are valid
        X_live.append(features)
        symbols_valid.append(sym)

X_live = pd.DataFrame(X_live)[feature_cols]
print(f"✓ Computed features for {len(X_live)} symbols")

# ============================================================================
# STEP 4: GENERATE PREDICTIONS
# ============================================================================

print("\nGenerating predictions...")
predictions = model.predict(X_live, num_iteration=model.best_iteration)

# Create results dataframe
results = pd.DataFrame({
    'symbol': symbols_valid,
    'pred_score': predictions,
    'timestamp': datetime.now()
})
results = results.sort_values('pred_score', ascending=False).reset_index(drop=True)

print("\nTop 10 Predicted Stocks (Highest 5-day forward return potential):")
print(results.head(10).to_string(index=False))

# ============================================================================
# STEP 5: GENERATE TRADING SIGNALS
# ============================================================================

TOP_K = 10  # Number of stocks to buy
TRANSACTION_COST_PCT = 0.0008

# Get top-K picks
topk_picks = results.head(TOP_K)

print(f"\n{'='*70}")
print(f"TRADING SIGNALS ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
print(f"{'='*70}")
print(f"\nBUY SIGNAL: Top {TOP_K} stocks to buy (equal weight portfolio):")
for idx, row in topk_picks.iterrows():
    print(f"  {idx+1}. {row['symbol']:20s}  Pred Score: {row['pred_score']:+.6f}")

# Portfolio weights
topk_picks['weight'] = 1.0 / len(topk_picks)
print(f"\nRecommended Allocation:")
print(f"  Weight per stock: {topk_picks['weight'].iloc[0]:.2%}")
print(f"  Position size (for $100k): ${100000 * topk_picks['weight'].iloc[0]:,.2f}")

# Transaction cost
transaction_cost = TRANSACTION_COST_PCT * 2  # Buy + Sell
print(f"\nEstimated Transaction Cost: {transaction_cost:.4%}")

# ============================================================================
# STEP 6: INTEGRATION WITH BROKER/EXECUTION
# ============================================================================

print(f"\n{'='*70}")
print("NEXT STEPS FOR LIVE EXECUTION:")
print(f"{'='*70}")
print("""
Option A: MANUAL EXECUTION
  1. Review the top-K picks above
  2. Place BUY orders on your broker (NSE/BSE)
  3. Use LIMIT orders slightly above current price to ensure execution
  4. Set position sizes: equal weight or customize based on risk

Option B: AUTOMATED EXECUTION (Python + Broker API)
  - Use broker APIs like Zerodha (kiteconnect), Angel Broking, etc.
  - Example (Zerodha):
    from kiteconnect import KiteConnect
    
    kite = KiteConnect(api_key=YOUR_KEY)
    for symbol, weight in zip(topk_picks['symbol'], topk_picks['weight']):
        qty = int(portfolio_value * weight / current_price[symbol])
        kite.order_place(
            variety='regular',
            symbol=symbol,
            transaction_type='BUY',
            quantity=qty,
            price=current_price[symbol],
            order_type='LIMIT'
        )

Option C: SCHEDULED REBALANCING
  - Run this prediction script every morning before market open (9:15 AM IST)
  - Update portfolio positions based on new predictions
  - Example cron job:
    0 9 * * 1-5 /usr/bin/python /path/to/live_model_inference.py

IMPORTANT CONSIDERATIONS:
  ✓ Hold predicted positions for ~5 days (model predicts 5-day forward return)
  ✓ Implement stop-loss (e.g., 2-3% below entry) to manage downside risk
  ✓ Monitor for corporate actions (splits, dividends) affecting predictions
  ✓ Track model performance: compare predicted vs actual returns
  ✓ Recalibrate/retrain model periodically (monthly/quarterly) as market regimes change
  ✓ Test with small capital first before scaling
""")

# ============================================================================
# STEP 7: SAVE PREDICTIONS FOR LOG/ANALYSIS
# ============================================================================

results.to_csv('output/live_predictions.csv', index=False)
topk_picks[['symbol', 'pred_score', 'weight']].to_csv('output/live_trades.csv', index=False)
print(f"\n✓ Predictions saved to output/live_predictions.csv")
print(f"✓ Trade signals saved to output/live_trades.csv")
