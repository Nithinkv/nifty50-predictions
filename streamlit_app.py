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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from paper_trading import PaperTrading
from portfolio_view import show_portfolio
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
# Load custom CSS
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

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
def load_model(symbol):
    """Load the trained LightGBM model for a specific symbol."""
    # Files are named like 'RELIANCE_NS.pkl' (dots replaced by underscores)
    safe_sym = symbol.replace('.', '_')
    model_path = f"models/{safe_sym}.pkl"
    try:
        return joblib.load(model_path)
    except Exception as e1:
        # Try alternative naming if first fails
        try:
            return joblib.load(f"models/{symbol.replace('.NS', '')}.pkl")
        except Exception as e2:
            # Only show error for first few to avoid spam
            # st.error(f"Failed to load model for {symbol}: {e1} | {e2}")
            return None

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
def fetch_all_data(symbols, days=120, refresh_key=None):
    """Fetch data for all symbols with caching using batch download."""
    data = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    status_text = st.empty()
    status_text.text(f"Fetching data for {len(symbols)} stocks...")
    
    try:
        # Batch download
        df_all = yf.download(symbols, start=start_date, end=end_date, group_by='ticker', progress=False)
        
        # Process each symbol
        for sym in symbols:
            try:
                # Handle case where only one symbol is fetched (structure differs)
                if len(symbols) == 1:
                    df = df_all.copy()
                else:
                    df = df_all[sym].copy()
                
                if df.empty:
                    continue
                
                # Drop rows with all NaNs
                df = df.dropna(how='all')
                
                if len(df) == 0:
                    continue

                if 'Adj Close' not in df.columns and 'Close' in df.columns:
                    df['AdjClose'] = df['Close']
                elif 'Adj Close' in df.columns:
                    df['AdjClose'] = df['Adj Close']
                
                df.index.name = 'date'
                df = df.reset_index()
                data[sym] = df
            except Exception:
                continue
                
        status_text.empty()
        return data
        
    except Exception as e:
        status_text.error(f"Error fetching data: {str(e)}")
        return {}

def get_signal(pred_score):
    """Determine trading signal from prediction score."""
    if pred_score > 0.02:  # 2.0% for 5-day return
        return "BUY", "🟢"
    elif pred_score < -0.02:  # -2.0% for 5-day return
        return "SELL", "🔴"
    else:
        return "NEUTRAL", "🟡"

def create_chart(df, symbol, target_price):
    """Create an interactive candlestick chart with overlays."""
    # Filter last 6 months for better visibility
    df_chart = df.iloc[-126:].copy()
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=(f'{symbol} Price', 'Volume'), 
                        row_width=[0.2, 0.7])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df_chart['date'],
                open=df_chart['Open'],
                high=df_chart['High'],
                low=df_chart['Low'],
                close=df_chart['Close'],
                name='Price'), row=1, col=1)

    # Moving Averages
    if 'AdjClose' in df_chart.columns:
        ma_20 = df_chart['AdjClose'].rolling(20).mean()
        fig.add_trace(go.Scatter(x=df_chart['date'], y=ma_20, 
                                 line=dict(color='orange', width=1), 
                                 name='20-Day MA'), row=1, col=1)

    # Target Price Line (dashed horizontal)
    fig.add_hline(y=target_price, line_dash="dash", line_color="blue", 
                  annotation_text=f"Target: {target_price:.2f}", 
                  row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df_chart['date'], y=df_chart['Volume'], 
                         name='Volume', marker_color='teal'), row=2, col=1)

    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def generate_predictions(data):
    """Generate predictions for all symbols using individual models."""
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
            
            # Load model for this specific stock
            model = load_model(symbol)
            if model is None:
                skipped += 1
                continue

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
        status_text.info(f"⚠️ Skipped {skipped} stocks (missing data or model)")
    else:
        status_text.empty()
    return pd.DataFrame(predictions)

# ============================================================================
# MAIN STREAMLIT APP
# ============================================================================

def main():
    st.title("📈 NIFTY 50 Stock Predictions")
    
    # Initialize Paper Trading
    if 'pt' not in st.session_state:
        st.session_state.pt = PaperTrading()
    pt = st.session_state.pt

    # Sidebar Navigation
    view = st.sidebar.radio("Navigation", ["Market Dashboard", "My Portfolio"])
    
    # Paper Trading Sidebar Summary
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💰 Paper Trading")
    st.sidebar.metric("Cash Balance", f"₹{pt.balance:,.2f}")
    if not pt.portfolio.empty:
        st.sidebar.markdown(f"**Invested:** {len(pt.portfolio)} stocks")
    
    if st.sidebar.button("Reset Account", type="primary"):
        pt.reset_account()
        st.sidebar.success("Account reset!")
        st.rerun()

    if view == "My Portfolio":
        show_portfolio(pt, fetch_all_data)
        return

    # --- MARKET DASHBOARD VIEW ---
    st.subheader("Live market analysis powered by LightGBM ML model")
    
    # Sidebar Settings (Only for Dashboard)
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
    
    # Initialize session state key for refresh control
    if 'refresh_data_ts' not in st.session_state:
        st.session_state['refresh_data_ts'] = None

    # If user requested an explicit refresh, clear cached data and rerun so fetch_all_data pulls fresh data
    if refresh_data:
        st.sidebar.info("Refreshing live data...")
        # update session-state refresh key so cached function sees a different argument
        st.session_state['refresh_data_ts'] = datetime.now().timestamp()
        try:
            # clear the cached data function results so next call fetches fresh data
            st.cache_data.clear()
        except Exception:
            # older Streamlit versions may not have cache_data.clear(); attempt global memo clear
            try:
                st.experimental_memo_clear()
            except Exception:
                pass
        st.sidebar.success("Cache cleared — fetching fresh data now.")

    # Fetch and predict
    with st.status("🔄 Analyzing Market Data...", expanded=True) as status:
        st.write("📡 Fetching live prices...")
        # pass session_state refresh key so cache is bypassed when user requested refresh
        data = fetch_all_data(NIFTY_50, refresh_key=st.session_state.get('refresh_data_ts'))
        
        if not data:
            status.update(label="❌ Data Fetch Failed", state="error")
            st.error("Failed to fetch data. Please check your internet connection.")
            return
        
        st.write(f"✓ Fetched {len(data)} stocks")
        st.write("🤖 Running prediction models...")
        predictions_df = generate_predictions(data)
        
        if predictions_df.empty:
            status.update(label="❌ Prediction Failed", state="error")
            st.error("No predictions generated. Please try again.")
            return
        
        status.update(label="✅ Analysis Complete", state="complete", expanded=False)
    
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
    
    # Headers for the list
    h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 1, 1, 2, 0.5])
    h1.markdown("**Stock**")
    h2.markdown("**Price**")
    h3.markdown("**Signal**")
    h4.markdown("**Return**")
    h5.markdown("**Trade**")
    h6.markdown("**Info**")
    
    st.markdown("---")

    # List Layout
    for idx, row in predictions_df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 1, 1, 2, 0.5])
        
        # 1. Symbol
        with c1:
            st.markdown(f"**{row['Symbol']}**")
            st.caption(f"Vol Z: {row['Volume Z']:.1f}")
            
        # 2. Price
        with c2:
            st.write(f"₹{row['Current Price']:.2f}")
            
        # 3. Signal
        with c3:
            signal_color = "green" if row['Signal'] == "BUY" else "red" if row['Signal'] == "SELL" else "gray"
            st.markdown(f":{signal_color}[{row['Signal']}]")
            
        # 4. Return
        with c4:
            color = "green" if row['Return %'] > 0 else "red"
            st.markdown(f":{color}[{row['Return %']:+.2f}%]")
            
        # 5. Trade Controls (Inline)
        with c5:
            tc1, tc2, tc3 = st.columns([1, 1, 1])
            with tc1:
                qty = st.number_input("Qty", min_value=1, value=10, key=f"qty_{row['Symbol']}", label_visibility="collapsed")
            with tc2:
                if st.button("Buy", key=f"buy_{row['Symbol']}", type="primary" if row['Signal'] == "BUY" else "secondary", use_container_width=True):
                    success, msg = pt.buy_stock(row['Symbol'], qty, row['Current Price'])
                    if success:
                        st.toast(f"✅ Bought {qty} {row['Symbol']}")
                        st.rerun()
                    else:
                        st.error(msg)
            with tc3:
                # Check ownership
                owned = pt.portfolio[pt.portfolio['Symbol'] == row['Symbol'].replace('.NS', '')]
                owned_qty = 0 if owned.empty else owned.iloc[0]['Quantity']
                
                if owned_qty > 0:
                    if st.button("Sell", key=f"sell_{row['Symbol']}", type="primary" if row['Signal'] == "SELL" else "secondary", use_container_width=True):
                        success, msg = pt.sell_stock(row['Symbol'], qty, row['Current Price'])
                        if success:
                            st.toast(f"✅ Sold {qty} {row['Symbol']}")
                            st.rerun()
                        else:
                            st.error(msg)
        
        # 6. Details Expander
        with c6:
            with st.popover("📊"):
                st.markdown(f"### {row['Symbol']} Analysis")
                # Interactive Chart
                chart_df = data.get(row['Symbol'] + '.NS')
                if chart_df is not None:
                    fig = create_chart(chart_df, row['Symbol'], row['Target Price'])
                    st.plotly_chart(fig, use_container_width=True)
                
                st.write(f"**Target:** ₹{row['Target Price']:.2f}")
                st.write(f"**RSI:** {row['RSI']:.2f}")
                st.write(f"**MA Trend:** {row['MA Trend']}")
        
        st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
            
    if show_details:
        st.info("""
        **Feature Explanation:**
        - **5-Day Return**: Predicted return over next 5 trading days (not 1 day!)
        - **RSI**: Relative Strength Index (0-100, <30 oversold, >70 overbought)
        - **MA Trend**: Moving Average 5-day vs 20-day (Up/Down)
        - **Volume Z-Score**: Volume relative to 20-day average
        
        **Signal Thresholds:**
        - **BUY**: Predicted return > +2.0% (5-day)
        - **SELL**: Predicted return < -2.0% (5-day)
        - **NEUTRAL**: Return between -2.0% to +2.0%
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
