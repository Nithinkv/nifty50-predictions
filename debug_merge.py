import pandas as pd

PRICE_PATH = "combined/price_panel.parquet"
VOLUME_PATH = "combined/volume_panel.parquet"

price = pd.read_parquet(PRICE_PATH)
volume = pd.read_parquet(VOLUME_PATH)

print("Price shape:", price.shape)
print("Volume shape:", volume.shape)
print("Price index name:", price.index.name)
print("Volume index name:", volume.index.name)
print("\nPrice columns (first 3):", list(price.columns[:3]))
print("Volume columns (first 3):", list(volume.columns[:3]))

# Stack to long form
price_long = price.stack().reset_index()
print("\nAfter stacking price:")
print("  Columns:", list(price_long.columns))
print("  Head:\n", price_long.head())

volume_long = volume.stack().reset_index()
print("\nAfter stacking volume:")
print("  Columns:", list(volume_long.columns))
print("  Head:\n", volume_long.head())

# Check column names before merge
price_long.columns = ["date", "symbol", "AdjClose"]
volume_long.columns = ["date", "symbol", "Volume"]

print("\nBefore merge:")
print("  Price shape:", price_long.shape)
print("  Volume shape:", volume_long.shape)
print("  Unique dates in price:", price_long['date'].nunique())
print("  Unique dates in volume:", volume_long['date'].nunique())
print("  Unique symbols in price:", price_long['symbol'].nunique())
print("  Unique symbols in volume:", volume_long['symbol'].nunique())

# Merge with explicit keys
df = price_long.merge(volume_long, on=["date", "symbol"], how="left")
print("\nAfter merge (LEFT join):")
print("  Shape:", df.shape)
print("  NaNs in Volume:", df['Volume'].isna().sum())
print("  Head:\n", df.head(10))
