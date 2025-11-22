"""
Streamlit App: NIFTY 50 Stock Prediction Dashboard
Live predictions for all NIFTY 50 stocks with interactive filtering and details.

Run: streamlit run streamlit_app.py
Deploy: Push to GitHub and connect to Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIG & STYLING
# ============================================================================

st.set_page_config(
    page_title="NIFTY 50 Stock Predictions",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile-friendly design
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .signal-buy {
        background-color: #28a745;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .signal-sell {
        background-color: #dc3545;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .signal-neutral {
        background-color: #ffc107;
        color: black;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .price-up {
        color: #28a745;
        font-weight: bold;
    }
    .price-down {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# NIFTY 50 SYMBOLS
# ============================================================================

NIFTY_50 = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
    "HINDUNILVR.NS","KOTAKBANK.NS","ITC.NS","LT.NS","SBIN.NS",
    "HDFCAMC.NS","BHARTIARTL.NS","ASIANPAINT.NS","BAJFINANCE.NS","AXISBANK.NS",
    "MARUTI.NS","SUNPHARMA.NS","TATASTEEL.NS","UPL.NS","TITAN.NS",
    "NTPC.NS","POWERGRID.NS","HCLTECH.NS","M&M.NS","NESTLEIND.NS",
    "JSWSTEEL.NS","BRITANNIA.NS","COALINDIA.NS","DIVISLAB.NS","ONGC.NS",
    "BPCL.NS","GRASIM.NS","WIPRO.NS","EICHERMOT.NS","ULTRACEMCO.NS",
    "TECHM.NS","TATAMOTORS.NS","HDFCLIFE.NS","ADANIPORTS.NS","ADANIENT.NS",
    "SHREECEM.NS","SBILIFE.NS","CIPLA.NS","INDUSINDBK.NS","BAJAJ-AUTO.NS",
    "HINDALCO.NS","COFORGE.NS","LUPIN.NS","MRF.NS","PETRONET.NS",
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_resource
def load_model():
    """Load the trained LightGBM model."""
    return joblib.load("models/short_term_lgb_all.pkl")

def compute_features(symbol_df):
    """Compute all 12 required features for a single symbol."""
    df = symbol_df.copy().sort_values('date').reset_index(drop=True)
    
    if len(df) < 51:
        return None
    
    try:
        ret_1 = df['AdjClose'].pct_change(1)
        ret_3 = df['AdjClose'].pct_change(3)
        ret_5 = df['AdjClose'].pct_change(5)
        ret_10 = df['AdjClose'].pct_change(10)
        ret_20 = df['AdjClose'].pct_change(20)
        
        ma_5 = df['AdjClose'].rolling(5).mean()
        ma_20 = df['AdjClose'].rolling(20).mean()
        ma_50 = df['AdjClose'].rolling(50).mean()
        ma_spread_5_20 = (ma_5 - ma_20) / (ma_20 + 1e-8)
        ma_spread_5_50 = (ma_5 - ma_50) / (ma_50 + 1e-8)
        
        vol_10 = ret_1.rolling(10).std()
        vol_20 = ret_1.rolling(20).std()
        
        vol_mean = df['Volume'].rolling(20).mean()
        vol_std = df['Volume'].rolling(20).std()
        vol_z = (df['Volume'] - vol_mean) / (vol_std + 1e-8)
        
        delta = df['AdjClose'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / (loss + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        
        rel_mom_5 = (df['AdjClose'].iloc[-1] - df['AdjClose'].iloc[-5]) / (df['AdjClose'].iloc[-5] + 1e-8) if len(df) >= 5 else 0
        
        features = pd.Series({
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
        })
        
        # Fill any NaN values with 0
        features = features.fillna(0)
        return features
    except Exception as e:
        return None

@st.cache_data(ttl=3600)
def fetch_all_data(symbols, days=120):
    """Fetch data for all symbols with caching. Use 120 calendar days for ~90 trading days."""
    data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    failed_symbols = []
    
    for idx, sym in enumerate(symbols):
        try:
            status_text.text(f"Fetching {sym}... ({idx+1}/{len(symbols)})")
            df = yf.download(sym, start=start_date, end=end_date, progress=False)
            
            if df.empty or len(df) == 0:
                failed_symbols.append(sym)
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            if 'Adj Close' not in df.columns and 'Close' in df.columns:
                df['AdjClose'] = df['Close']
            elif 'Adj Close' in df.columns:
                df['AdjClose'] = df['Adj Close']
            
            df.index.name = 'date'
            df = df.reset_index()
            data[sym] = df
        except Exception as e:
            failed_symbols.append(sym)
        
        progress_bar.progress((idx + 1) / len(symbols))
    
    progress_bar.empty()
    if failed_symbols:
        status_text.warning(f"⚠️ Failed to fetch {len(failed_symbols)} stocks: {', '.join(failed_symbols)}")
    else:
        status_text.empty()
    return data

def get_signal(pred_score):
    """Determine trading signal from prediction score."""
    if pred_score > 0.005:  # 0.5% for 5-day return
        return "BUY", "🟢"
    elif pred_score < -0.005:  # -0.5% for 5-day return
        return "SELL", "🔴"
    else:
        return "NEUTRAL", "🟡"

def generate_predictions(model, data):
    """Generate predictions for all symbols."""
    predictions = []
    feature_cols = ['ret_1','ret_3','ret_5','ret_10','ret_20',
                    'ma_spread_5_20','ma_spread_5_50',
                    'vol_10','vol_20','vol_z','rsi','rel_mom_5']
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    skipped = 0
    
    for idx, (symbol, df) in enumerate(data.items()):
        try:
            status_text.text(f"Predicting {symbol}... ({idx+1}/{len(data)})")
            features = compute_features(df)
            
            if features is None:
                skipped += 1
                progress_bar.progress((idx + 1) / len(data))
                continue
            
            # Check for remaining NaN values
            if features.isna().any():
                skipped += 1
                progress_bar.progress((idx + 1) / len(data))
                continue
            
            current_price = df['Close'].iloc[-1]
            X = features[feature_cols].values.reshape(1, -1)
            pred_score = model.predict(X, num_iteration=model.best_iteration)[0]
            target_price = current_price * (1 + pred_score)
            signal, emoji = get_signal(pred_score)
            
            predictions.append({
                'Symbol': symbol.replace('.NS', ''),
                'Current Price': current_price,
                'Pred Score': pred_score,
                'Target Price': target_price,
                'Price Move': target_price - current_price,
                'Return %': pred_score * 100,
                'Signal': signal,
                'Emoji': emoji,
                'RSI': features['rsi'],
                'MA Trend': 'Up' if features['ma_spread_5_20'] > 0 else 'Down',
                'Volume Z': features['vol_z'],
                'Date': df['date'].iloc[-1],
            })
        except Exception as e:
            skipped += 1
            continue
        
        progress_bar.progress((idx + 1) / len(data))
    
    progress_bar.empty()
    if skipped > 0:
        status_text.info(f"⚠️ Skipped {skipped} stocks due to insufficient data")
    else:
        status_text.empty()
    return pd.DataFrame(predictions)

# ============================================================================
# MAIN STREAMLIT APP
# ============================================================================

def main():
    st.title("📈 NIFTY 50 Stock Predictions")
    st.subheader("Live market analysis powered by LightGBM ML model")
    
    # Sidebar
    st.sidebar.markdown("### ⚙️ Settings")
    refresh_data = st.sidebar.button("🔄 Refresh Data", use_container_width=True)
    show_details = st.sidebar.checkbox("📊 Show Technical Details", value=False)
    
    filter_signal = st.sidebar.multiselect(
        "Filter by Signal:",
        options=["BUY", "SELL", "NEUTRAL"],
        default=["BUY", "SELL", "NEUTRAL"]
    )
    
    sort_by = st.sidebar.selectbox(
        "Sort by:",
        options=["Return %", "RSI", "Current Price", "Symbol"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 📖 How to Use
    1. **Refresh Data**: Pull latest market data
    2. **Filter**: Select signals you want to see
    3. **Sort**: Arrange by different metrics
    4. **Click**: Tap a stock for detailed analysis
    
    ### ⚠️ Disclaimer
    This is NOT financial advice. Past performance ≠ future results.
    Always use stop-losses and proper risk management.
    """)
    
    # Load model
    model = load_model()
    
    # Fetch and predict
    st.info("📡 Fetching live market data for all NIFTY 50 stocks...")
    data = fetch_all_data(NIFTY_50)
    
    if not data:
        st.error("Failed to fetch data. Please check your internet connection.")
        return
    
    st.success(f"✓ Fetched data for {len(data)} stocks")
    st.info("🤖 Generating predictions...")
    predictions_df = generate_predictions(model, data)
    
    if predictions_df.empty:
        st.error("No predictions generated. Please try again.")
        return
    
    st.success(f"✓ Generated predictions for {len(predictions_df)} stocks")
    
    # Filter predictions
    predictions_df = predictions_df[predictions_df['Signal'].isin(filter_signal)]
    
    # Sort predictions
    if sort_by == "Return %":
        predictions_df = predictions_df.sort_values('Return %', ascending=False)
    elif sort_by == "RSI":
        predictions_df = predictions_df.sort_values('RSI', ascending=False)
    elif sort_by == "Current Price":
        predictions_df = predictions_df.sort_values('Current Price', ascending=False)
    else:
        predictions_df = predictions_df.sort_values('Symbol')
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        buy_count = len(predictions_df[predictions_df['Signal'] == 'BUY'])
        st.metric("🟢 BUY Signals", buy_count)
    with col2:
        sell_count = len(predictions_df[predictions_df['Signal'] == 'SELL'])
        st.metric("🔴 SELL Signals", sell_count)
    with col3:
        neutral_count = len(predictions_df[predictions_df['Signal'] == 'NEUTRAL'])
        st.metric("🟡 NEUTRAL Signals", neutral_count)
    with col4:
        avg_return = predictions_df['Return %'].mean()
        st.metric("📊 Avg Return %", f"{avg_return:.2f}%")
    
    # Display predictions table
    st.markdown("### 📋 Stock Predictions")
    
    # Create interactive display
    for idx, row in predictions_df.iterrows():
        signal_class = f"signal-{row['Signal'].lower()}"
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown(f"<div class='{signal_class}'>{row['Emoji']} {row['Signal']}</div>", 
                       unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"**{row['Symbol']}**")
            st.caption(f"Price: ₹{row['Current Price']:.2f}")
        
        with col3:
            if row['Return %'] > 0:
                st.markdown(f"<div class='price-up'>+{row['Return %']:.2f}%</div>", 
                           unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='price-down'>{row['Return %']:.2f}%</div>", 
                           unsafe_allow_html=True)
        
        # Expandable details
        with st.expander(f"📊 Details for {row['Symbol']}"):
            det_col1, det_col2 = st.columns(2)
            
            with det_col1:
                st.write(f"**Current Price:** ₹{row['Current Price']:.2f}")
                st.write(f"**Target Price (5D):** ₹{row['Target Price']:.2f}")
                st.write(f"**Price Move:** ₹{row['Price Move']:.2f}")
                st.write(f"**5-Day Return:** {row['Return %']:.2f}%")
            
            with det_col2:
                st.write(f"**RSI (14):** {row['RSI']:.2f}")
                st.write(f"**MA Trend (5/20):** {row['MA Trend']}")
                st.write(f"**Volume Z-Score:** {row['Volume Z']:.2f}")
                st.write(f"**Last Updated:** {row['Date'].strftime('%Y-%m-%d %H:%M')}")
            
            if show_details:
                st.info("""
                **Feature Explanation:**
                - **5-Day Return**: Predicted return over next 5 trading days (not 1 day!)
                - **RSI**: Relative Strength Index (0-100, <30 oversold, >70 overbought)
                - **MA Trend**: Moving Average 5-day vs 20-day (Up/Down)
                - **Volume Z-Score**: Volume relative to 20-day average
                
                **Signal Thresholds:**
                - **BUY**: Predicted return > +0.5% (5-day)
                - **SELL**: Predicted return < -0.5% (5-day)
                - **NEUTRAL**: Return between -0.5% to +0.5%
                """)
    
    # Download results
    st.markdown("---")
    csv = predictions_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Predictions CSV",
        data=csv,
        file_name=f"nifty50_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")

if __name__ == "__main__":
    main()
