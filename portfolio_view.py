import streamlit as st
import pandas as pd

def show_portfolio(pt, fetch_data_func):
    st.header("💰 My Portfolio")
    
    # Calculate Portfolio Value
    if pt.portfolio.empty:
        st.info("Your portfolio is empty. Go to the Dashboard to buy stocks!")
        st.metric("Cash Balance", f"₹{pt.balance:,.2f}")
    else:
        # Fetch current prices for owned stocks
        symbols = [s + ".NS" for s in pt.portfolio['Symbol'].unique()]
        
        # Only fetch if we have symbols
        if symbols:
            with st.spinner("Fetching current prices..."):
                # Use cache_data to avoid re-fetching if possible, or force refresh if needed
                data = fetch_data_func(symbols, days=5)
            
            current_prices = {}
            for sym, df in data.items():
                if not df.empty:
                    current_prices[sym.replace('.NS', '')] = df['Close'].iloc[-1]
            
            # Create Portfolio Table with P&L
            portfolio_df = pt.portfolio.copy()
            portfolio_df['Current Price'] = portfolio_df['Symbol'].map(current_prices)
            portfolio_df['Value'] = portfolio_df['Quantity'] * portfolio_df['Current Price']
            portfolio_df['Invested'] = portfolio_df['Quantity'] * portfolio_df['AvgPrice']
            portfolio_df['P&L'] = portfolio_df['Value'] - portfolio_df['Invested']
            portfolio_df['P&L %'] = (portfolio_df['P&L'] / portfolio_df['Invested']) * 100
            
            # Summary Metrics
            total_invested = portfolio_df['Invested'].sum()
            current_value = portfolio_df['Value'].sum()
            total_pl = current_value - total_invested
            total_pl_pct = (total_pl / total_invested * 100) if total_invested > 0 else 0
            
    # Summary Metrics in a Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Invested", f"₹{total_invested:,.2f}")
    m2.metric("Current Value", f"₹{current_value:,.2f}")
    m3.metric("Total P&L", f"₹{total_pl:,.2f}", delta=f"{total_pl_pct:.2f}%")
    m4.metric("Cash Balance", f"₹{pt.balance:,.2f}")

    st.markdown("### 📊 Holdings")
    
    # Headers
    h1, h2, h3, h4, h5, h6 = st.columns([1.5, 1, 1, 1, 1, 1])
    h1.markdown("**Stock**")
    h2.markdown("**Qty**")
    h3.markdown("**Avg Price**")
    h4.markdown("**Current**")
    h5.markdown("**P&L**")
    h6.markdown("**Action**")
    st.markdown("---")

    for idx, row in portfolio_df.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1, 1, 1, 1, 1])
        
        with c1: st.markdown(f"**{row['Symbol']}**")
        with c2: st.write(f"{row['Quantity']}")
        with c3: st.write(f"₹{row['AvgPrice']:.2f}")
        with c4: st.write(f"₹{row['Current Price']:.2f}")
        with c5: 
            color = "green" if row['P&L'] >= 0 else "red"
            st.markdown(f":{color}[{row['P&L']:+.2f} ({row['P&L %']:.2f}%)]")
        
        with c6:
            if st.button("Sell", key=f"port_sell_{row['Symbol']}", type="secondary", use_container_width=True):
                success, msg = pt.sell_stock(row['Symbol'] + ".NS", row['Quantity'], row['Current Price'])
                if success:
                    st.toast(f"✅ Sold all {row['Quantity']} {row['Symbol']}")
                    st.rerun()
                else:
                    st.error(msg)
        
        st.markdown("<hr style='margin: 5px 0; opacity: 0.1;'>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader("📜 Transaction History")
    if not pt.transactions.empty:
        st.dataframe(pt.transactions.sort_values("Date", ascending=False), use_container_width=True)
    else:
        st.info("No transactions yet.")
