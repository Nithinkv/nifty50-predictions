# NIFTY 50 Stock Prediction Dashboard

A real-time ML-powered stock prediction dashboard for NIFTY 50 stocks using LightGBM.

## Features

✅ **Live Market Data** - Fetches real-time data for all 50 NIFTY stocks  
✅ **ML Predictions** - LightGBM model predicts 5-day forward returns  
✅ **Trading Signals** - Color-coded BUY (🟢), SELL (🔴), NEUTRAL (🟡) signals  
✅ **Interactive Filtering** - Filter by signal type  
✅ **Technical Analysis** - RSI, moving averages, volume analysis  
✅ **Mobile Optimized** - Works perfectly on phones  
✅ **Download Results** - Export predictions as CSV  

## Performance

| Metric | Value |
|--------|-------|
| **Annualized Return** | 137.46% |
| **Sharpe Ratio** | 2.59 |
| **Holding Period** | 5 trading days |
| **Strategy** | Top-K long-only ranking |
| **Avg Return per Trade** | ~0.29% (5-day) |

## Installation

### Local Testing

1. Clone repository:
```bash
git clone https://github.com/YOUR_USERNAME/nifty50-predictions.git
cd nifty50-predictions
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
streamlit run streamlit_app.py
```

Visit: `http://localhost:8501`

## Streamlit Cloud Deployment

### Step 1: Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit: NIFTY 50 prediction dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nifty50-predictions.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to **https://streamlit.io/cloud**
2. Sign in with GitHub account
3. Click "New app"
4. Select:
   - **Repository:** your-username/nifty50-predictions
   - **Branch:** main
   - **Main file:** streamlit_app.py
5. Click "Deploy"

### Step 3: Access Your App

Your app will be live at:
```
https://YOUR-USERNAME-nifty50-predictions.streamlit.app
```

Share this URL with anyone to access the dashboard!

## File Structure

```
nifty50-predictions/
├── streamlit_app.py           # Main dashboard app
├── train_short_term.py        # Model training script
├── make_features.py           # Feature engineering
├── combine_data.py            # Data preprocessing
├── datapull.py                # Download historical data
├── requirements.txt           # Dependencies
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── models/
│   └── short_term_lgb_all.pkl # Trained model (86 stocks)
├── combined/
│   ├── price_panel.parquet
│   ├── volume_panel.parquet
│   └── features_long.parquet
├── output/
│   ├── metrics_short.csv
│   └── preds_short_walkfwd.csv
└── README.md
```

## Usage

### Morning Trading Workflow (9:15 AM IST)

1. **Open Dashboard** on phone: https://YOUR-USERNAME-nifty50-predictions.streamlit.app
2. **Review Signals** - See all NIFTY 50 stocks with BUY/SELL/NEUTRAL
3. **Filter Results** - Sidebar to filter by signal type
4. **Click Stock** - Tap any stock for technical analysis
5. **Execute Trades** - Based on model predictions
6. **Risk Management** - Use stop-losses (2-3% below entry)

### Technical Indicators Explained

- **RSI (14):** Relative Strength Index (0-100)
  - < 30: Oversold (potential bounce)
  - > 70: Overbought (potential pullback)
  - 30-70: Neutral

- **MA Trend (5/20):** Moving average spread
  - Positive: Uptrend
  - Negative: Downtrend

- **Volume Z-Score:** Volume relative to 20-day average
  - > 1: High volume (strong move)
  - < -1: Low volume (weak move)

- **5-Day Return:** Predicted return over next 5 trading days

## Model Details

**Algorithm:** LightGBM (Gradient Boosting)  
**Training Data:** 86 NIFTY stocks, 222,070 rows  
**Features:** 12 technical indicators  
**Output:** Continuous prediction (5-day forward return)  
**Backtest:** Walk-forward expanding window (2yr train, 6mo test)

## Features Used

1. `ret_1`, `ret_3`, `ret_5`, `ret_10`, `ret_20` - Historical returns
2. `ma_spread_5_20`, `ma_spread_5_50` - Moving average spreads
3. `vol_10`, `vol_20` - Volatility measures
4. `vol_z` - Volume z-score
5. `rsi` - Relative Strength Index
6. `rel_mom_5` - 5-day relative momentum

## API & Data Sources

- **Market Data:** Yahoo Finance API (yfinance)
- **Model:** LightGBM library
- **Deployment:** Streamlit Cloud
- **Frontend:** Streamlit framework

## Performance Tracking

The app caches data for 1 hour to prevent excessive API calls. Use the "Refresh Data" button to force a fresh fetch.

Monitor accuracy by:
1. Downloading predictions daily (CSV)
2. Comparing predicted vs actual returns after 5 days
3. Tracking win rate and profit factor

## Risk Management

✅ **Position Sizing:** Equal weight (10% per stock for top-10)  
✅ **Stop-Loss:** Set at 2-3% below entry price  
✅ **Take-Profit:** Consider closing at 1-2% gain  
✅ **Rebalance:** Every 5 days (holding period)  
✅ **Max Drawdown:** Monitor cumulative performance  

## Important Disclaimers

⚠️ **This is NOT financial advice.** Past performance does not guarantee future results.

- Test with small capital first
- Always implement stop-losses
- Don't risk more than you can afford to lose
- Monitor model performance regularly
- Be aware of market holidays and corporate actions
- Use proper risk management

## Troubleshooting

### App loads slowly
- First run takes 5-10 minutes to fetch all data
- Results cached for 1 hour
- Click "Refresh Data" to force new fetch

### No predictions generated
- Check internet connection
- Yahoo Finance API may be rate-limited
- Try again in 5 minutes

### "Model not found" error
- Ensure `models/short_term_lgb_all.pkl` exists
- Run `python train_short_term.py` to regenerate

### Streamlit Cloud deployment fails
- Check `requirements.txt` has all dependencies
- Verify model file is in correct path
- Check GitHub repo is public

## Support & Feedback

- Report issues: GitHub Issues
- Suggestions: GitHub Discussions
- Model updates: Retrain monthly with latest data

## License

MIT License - Feel free to use and modify

## Author

Created with Python, LightGBM, and Streamlit

---

**Status:** ✅ Production Ready  
**Last Updated:** 2025-11-22  
**Version:** 1.0
