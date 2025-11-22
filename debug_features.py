import pandas as pd
import numpy as np

PRICE_PATH = "combined/price_panel.parquet"
VOLUME_PATH = "combined/volume_panel.parquet"

price = pd.read_parquet(PRICE_PATH)
volume = pd.read_parquet(VOLUME_PATH)

price.index = pd.to_datetime(price.index)
volume.index = pd.to_datetime(volume.index)

symbols = [c.replace("_AdjClose","") for c in price.columns]
print(f"Found {len(symbols)} symbols")

# Convert to long form
price_long = price.stack().reset_index()
price_long.columns = ["date", "symbol", "AdjClose"]

volume_long = volume.stack().reset_index()
volume_long.columns = ["date", "symbol", "Volume"]

df = price_long.merge(volume_long, on=["date","symbol"], how="left")
df = df.sort_values(["symbol","date"]).reset_index(drop=True)

print(f"After merge: {len(df)} rows")
print(f"NaN in AdjClose: {df['AdjClose'].isna().sum()}")
print(f"NaN in Volume: {df['Volume'].isna().sum()}")

# Sample one symbol
sample_sym = df['symbol'].iloc[0]
sample = df[df['symbol'] == sample_sym].head(60)
print(f"\nSample data for {sample_sym} (first 60 rows):")
print(sample[['date', 'AdjClose', 'Volume']].head(10))
print(f"NaNs in sample: AdjClose={sample['AdjClose'].isna().sum()}, Volume={sample['Volume'].isna().sum()}")

# Now test compute_features
def compute_features(group):
    g = group.copy()
    g["ret_1"]  = g["AdjClose"].pct_change(1)
    g["ret_3"]  = g["AdjClose"].pct_change(3)
    g["ret_5"]  = g["AdjClose"].pct_change(5)
    g["ret_10"] = g["AdjClose"].pct_change(10)
    g["ret_20"] = g["AdjClose"].pct_change(20)

    # MA features
    g["ma5"]  = g["AdjClose"].rolling(5).mean()
    g["ma20"] = g["AdjClose"].rolling(20).mean()
    g["ma50"] = g["AdjClose"].rolling(50).mean()

    g["ma_spread_5_20"] = (g["ma5"] - g["ma20"]) / g["ma20"]
    g["ma_spread_5_50"] = (g["ma5"] - g["ma50"]) / g["ma50"]

    # Volatility features
    g["vol_10"] = g["ret_1"].rolling(10).std()
    g["vol_20"] = g["ret_1"].rolling(20).std()

    # Volume z-score
    g["vol_z"] = (g["Volume"] - g["Volume"].rolling(20).mean()) / (g["Volume"].rolling(20).std() + 1e-9)

    # RSI (14-day)
    delta = g["AdjClose"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    rs = up.rolling(14).mean() / (down.rolling(14).mean() + 1e-9)
    g["rsi"] = 100 - (100 / (1 + rs))

    return g

print("\nComputing features...")
df_features = df.groupby("symbol", group_keys=False).apply(compute_features)
print(f"After compute_features: {len(df_features)} rows")
print(f"NaNs after feature computation: {df_features.isna().sum().sum()}")
print(f"NaN per column:\n{df_features.isna().sum()}")

# Test market return
print("\nComputing market returns...")
market_return_5 = (
    price.mean(axis=1).pct_change(5)
    .rename("mkt_ret_5")
    .reset_index()
)
market_return_5.columns = ["date", "mkt_ret_5"]
print(f"Market return shape: {market_return_5.shape}")
print(f"NaNs in market_return_5: {market_return_5.isna().sum().sum()}")

# Merge
df_features = df_features.merge(market_return_5, on="date", how="left")
df_features["rel_mom_5"] = df_features["ret_5"] - df_features["mkt_ret_5"]
print(f"After market merge: {len(df_features)} rows, NaNs: {df_features.isna().sum().sum()}")

# Drop NaNs
before_drop = len(df_features)
df_features = df_features.dropna().reset_index(drop=True)
after_drop = len(df_features)
print(f"\nBefore dropna: {before_drop} rows")
print(f"After dropna: {after_drop} rows")
