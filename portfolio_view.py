import streamlit as st
import pandas as pd

def show_portfolio(pt, fetch_data_func):
    st.header("💰 My Portfolio")
    
    col1, col2, col3, col4 = st.columns(4)
    col4.metric("Cash Balance", f"₹{pt.balance:,.2f}")

    # Calculate Portfolio Value
    if pt.portfolio.empty:
        st.info("Your portfolio is empty. Go to the Dashboard to buy stocks!")
        col1.metric("Total Invested", "₹0.00")
        col2.metric("Current Value", "₹0.00")
        col3.metric("Total P&L", "₹0.00")
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
            
            col1.metric("Total Invested", f"₹{total_invested:,.2f}")
            col2.metric("Current Value", f"₹{current_value:,.2f}")
            col3.metric("Total P&L", f"₹{total_pl:,.2f}", delta=f"{total_pl_pct:.2f}%")
            
            st.subheader("Holdings")
            st.dataframe(portfolio_df.style.format({
                "AvgPrice": "₹{:.2f}",
                "Current Price": "₹{:.2f}",
                "Value": "₹{:.2f}",
                "Invested": "₹{:.2f}",
                "P&L": "₹{:.2f}",
                "P&L %": "{:.2f}%"
            }))
        
    st.markdown("---")
    st.subheader("📜 Transaction History")
    if not pt.transactions.empty:
        st.dataframe(pt.transactions.sort_values("Date", ascending=False), use_container_width=True)
    else:
        st.info("No transactions yet.")
