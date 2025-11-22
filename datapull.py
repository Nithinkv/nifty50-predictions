import yfinance as yf
import pandas as pd
from tqdm import tqdm
import os

SYMBOLS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","KOTAKBANK.NS","ITC.NS","LT.NS","SBIN.NS",
    "HDFC.NS","BHARTIARTL.NS","ASIANPAINT.NS","BAJFINANCE.NS","AXISBANK.NS",
    "MARUTI.NS","SUNPHARMA.NS","TATASTEEL.NS","UPL.NS","TITAN.NS",
    "NTPC.NS","POWERGRID.NS","HCLTECH.NS","M&M.NS","NESTLEIND.NS",
    "JSWSTEEL.NS","BRITANNIA.NS","COALINDIA.NS","DIVISLAB.NS","ONGC.NS",
    "BPCL.NS","GRASIM.NS","WIPRO.NS","EICHERMOT.NS","ULTRACEMCO.NS",
    "TECHM.NS","TATAMOTORS.NS","HDFCLIFE.NS","ADANIPORTS.NS","ADANIENT.NS",
    "SHREECEM.NS","SBILIFE.NS","CIPLA.NS","INDUSINDBK.NS","BAJAJ-AUTO.NS",
    "HINDALCO.NS","COFORGE.NS","LUPIN.NS","MRF.NS","PETRONET.NS",
]
START = "2015-01-01"
END = "2025-11-20"  # use today's date

OUT_DIR = "data/yfinance"
os.makedirs(OUT_DIR, exist_ok=True)

for sym in tqdm(SYMBOLS):
    df = yf.download(sym, start=START, end=END, progress=False)
    if df.empty:
        print("No data for", sym)
        continue
    # keep adjusted close column (Adj Close) and volume
    df = df.rename(columns={"Adj Close":"AdjClose"})
    df.to_parquet(f"{OUT_DIR}/{sym.replace('.','_')}.parquet")
    # also save CSV if you prefer
    df.to_csv(f"{OUT_DIR}/{sym.replace('.','_')}.csv")
print("Done")

