import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

SYMBOL = "TATAMOTORS.NS"
end_date = datetime.now()
start_date = end_date - timedelta(days=60)

df = yf.download(SYMBOL, start=start_date, end=end_date, progress=False)
print("Columns:", df.columns.tolist())
print("Column types:", type(df.columns))
print("\nDataFrame head:")
print(df.head())
