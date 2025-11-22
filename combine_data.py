import pandas as pd
import glob
import os

DATA_DIR = "data/yfinance"   # CHANGE to your folder path
parquet_files = glob.glob(os.path.join(DATA_DIR, "*.parquet"))
if not parquet_files:
    # fallback: search recursively under data/
    parquet_files = glob.glob(os.path.join("data", "**", "*.parquet"), recursive=True)
if not parquet_files:
    raise SystemExit("No parquet files found in data/yfinance or data subfolders. Run datapull.py first.")

prices = []
volumes = []

for f in parquet_files:
    sym = os.path.basename(f).replace(".parquet","")
    df = pd.read_parquet(f)
    # normalize datetime index
    df.index = pd.to_datetime(df.index)
    # handle MultiIndex columns produced by some yfinance/parquet variants
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # normalize AdjClose column: prefer 'Adj Close', then 'AdjClose', else fallback to 'Close'
    if 'Adj Close' in df.columns:
        df = df.rename(columns={'Adj Close': 'AdjClose'})
    if 'AdjClose' not in df.columns and 'Close' in df.columns:
        df['AdjClose'] = df['Close']
    # Ensure required columns exist
    required = ['Open', 'High', 'Low', 'Close', 'AdjClose', 'Volume']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"Skipping {sym}: missing columns {missing}")
        continue
    # Keep only necessary columns
    df = df[['AdjClose','Volume']]
    # Rename columns to avoid conflict
    df = df.rename(columns={
        'AdjClose': f'{sym}_AdjClose',
        'Volume':   f'{sym}_Volume'
    })

    prices.append(df[[f'{sym}_AdjClose']])
    volumes.append(df[[f'{sym}_Volume']])

# Merge all stocks on date index
price_panel = pd.concat(prices, axis=1).sort_index()
volume_panel = pd.concat(volumes, axis=1).sort_index()

os.makedirs("combined", exist_ok=True)
price_panel.to_parquet("combined/price_panel.parquet")
volume_panel.to_parquet("combined/volume_panel.parquet")

print("Combined dataset saved to combined/ folder.")
