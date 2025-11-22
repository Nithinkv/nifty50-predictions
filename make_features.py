import pandas as pd
import numpy as np
import os

PRICE_PATH = "combined/price_panel.parquet"
VOLUME_PATH = "combined/volume_panel.parquet"

print("Loading data...")
price = pd.read_parquet(PRICE_PATH)
volume = pd.read_parquet(VOLUME_PATH)

# ensure datetime index
price.index = pd.to_datetime(price.index)
volume.index = pd.to_datetime(volume.index)

# Extract the base symbol names (remove suffixes)
price_symbols = [c.replace("_AdjClose","") for c in price.columns]
volume_symbols = [c.replace("_Volume","") for c in volume.columns]

print(f"Found {len(price_symbols)} symbols in prices")

# convert wide to long form WITH the correct symbol names
price_long = price.stack().reset_index()
price_long.columns = ["date", "full_col", "AdjClose"]
price_long["symbol"] = price_long["full_col"].str.replace("_AdjClose", "")
price_long = price_long[["date", "symbol", "AdjClose"]]

volume_long = volume.stack().reset_index()
volume_long.columns = ["date", "full_col", "Volume"]
volume_long["symbol"] = volume_long["full_col"].str.replace("_Volume", "")
volume_long = volume_long[["date", "symbol", "Volume"]]

df = price_long.merge(volume_long, on=["date","symbol"], how="left")
df = df.sort_values(["symbol","date"]).reset_index(drop=True)

# --- Feature Engineering ---
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

print("Computing features per symbol...")
df_features = df.groupby("symbol").apply(compute_features).reset_index(drop=True)

# relative strength vs market (index proxy = average of all stocks)
print("Computing relative strength...")
market_return_5 = (
    price.mean(axis=1).pct_change(5)
    .rename("mkt_ret_5")
    .reset_index()
)
market_return_5.columns = ["date", "mkt_ret_5"]  # Explicitly name the columns

df_features = df_features.merge(market_return_5, on="date", how="left")
df_features["rel_mom_5"] = df_features["ret_5"] - df_features["mkt_ret_5"]

# Drop rows where features cannot be computed
df_features = df_features.dropna().reset_index(drop=True)

os.makedirs("combined", exist_ok=True)
OUTPUT_PATH = "combined/features_long.parquet"
df_features.to_parquet(OUTPUT_PATH)

print("Feature file created:", OUTPUT_PATH)
print(df_features.head())
print("Total rows:", len(df_features))
