# quick check
import pandas as pd

df = pd.read_parquet("data/yfinance/RELIANCE_NS.parquet")
print(df.index.min(), df.index.max(), len(df))

assert df.index.is_unique
# check weekend/holiday pattern
missing = pd.bdate_range(df.index.min(), df.index.max()).difference(df.index)
len(missing), missing[:5]


