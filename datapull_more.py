import yfinance as yf
import pandas as pd
import os
from tqdm import tqdm

# NIFTY Next 50 tickers (may change over time). Edit if you have a custom list.
NEXT50 = [
    "AMBUJACEM.NS","APOLLOHOSP.NS","AUROPHARMA.NS","BANDHANBNK.NS","BERGEPAINT.NS",
    "BOSCHLTD.NS","BRITANNIA.NS","CANBK.NS","CASTROLIND.NS","COLPAL.NS",
    "CONCOR.NS","CUMMINSIND.NS","DABUR.NS","DIXON.NS","DIVISLAB.NS",
    "DRREDDY.NS","EICHERMOT.NS","GAIL.NS","GLAXO.NS","GODREJCP.NS",
    "GRASIM.NS","HAVELLS.NS","IDEA.NS","INDIAMART.NS","INDIGO.NS",
    "INFRATEL.NS","IOCL.NS","LTI.NS","MGL.NS","NMDC.NS",
    "PFF.NS","PEL.NS","PERSISTENT.NS","PIIND.NS","PIL.NS",
    "PNB.NS","PVR.NS","RBLBANK.NS","SRF.NS","SUNTV.NS",
    "TATACHEM.NS","TATACONSUM.NS","TRENT.NS","TVSMOTOR.NS","UPL.NS",
    "VEDL.NS","ZEEL.NS","ZOMATO.NS","MINDTREE.NS","BIOCON.NS"
]

OUT_DIR = "data/yfinance"
os.makedirs(OUT_DIR, exist_ok=True)

for sym in tqdm(NEXT50, desc="Downloading Next50"):
    try:
        df = yf.download(sym, start="2015-01-01", end=pd.Timestamp.today().strftime('%Y-%m-%d'), progress=False)
        if df.empty:
            print(f"No data for {sym}")
            continue
        df = df.rename(columns={"Adj Close":"AdjClose"})
        df.to_parquet(f"{OUT_DIR}/{sym.replace('.','_')}.parquet")
        df.to_csv(f"{OUT_DIR}/{sym.replace('.','_')}.csv")
    except Exception as e:
        print(f"Error downloading {sym}: {e}")

print("Done")
