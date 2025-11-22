# Streamlit Cloud Deployment Guide

## Quick Start (Local Testing)

Run locally first to verify everything works:

```bash
streamlit run streamlit_app.py
```

Visit: `http://localhost:8501` in your browser or phone (same network)

---

## Deploy to Streamlit Cloud (For Phone Access Anywhere)

### Step 1: Push Code to GitHub

```bash
# Initialize git repo (if not already done)
git init
git add .
git commit -m "Add NIFTY 50 stock prediction dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nifty50-predictions.git
git push -u origin main
```

### Step 2: Create Streamlit Cloud Account

1. Go to **https://streamlit.io/cloud**
2. Click "Sign up" and sign in with GitHub
3. Authorize Streamlit to access your GitHub repos

### Step 3: Deploy App

1. Click "Create app"
2. Select:
   - **Repository:** your-repo/nifty50-predictions
   - **Branch:** main
   - **Main file path:** streamlit_app.py
3. Click "Deploy"

**Your app will be live at:** `https://YOUR-USERNAME-nifty50-predictions.streamlit.app`

### Step 4: Access on Phone

1. Open the Streamlit Cloud URL on your phone
2. Bookmark it for easy access
3. The app is mobile-friendly with buttons and clickable elements

---

## Features

✅ **Live Data Fetching:** Pulls latest NIFTY 50 market data every morning  
✅ **ML Predictions:** LightGBM model predicts 5-day forward returns  
✅ **Interactive Filtering:** Filter by BUY/SELL/NEUTRAL signals  
✅ **Sorting:** Sort by Return %, RSI, Price, or Symbol  
✅ **Detailed View:** Tap any stock for technical analysis  
✅ **Mobile Optimized:** Works perfectly on phones  
✅ **Download CSV:** Export predictions for analysis  

---

## Usage Workflow

### Every Morning (9:15 AM IST)

1. **Open App on Phone**
   - Click bookmark or visit Streamlit Cloud URL
   - App auto-fetches latest market data

2. **Review Signals**
   - See all 50 stocks with color-coded signals
   - BUY (🟢), SELL (🔴), NEUTRAL (🟡)

3. **Filter & Sort**
   - Filter to only BUY signals
   - Sort by highest predicted return

4. **Click Stock Details**
   - Tap to see technical indicators
   - Check RSI, MA trends, volume analysis

5. **Execute Trades**
   - Based on model predictions
   - Implement stop-losses (2-3% below entry)

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit (Python UI) |
| **ML Model** | LightGBM (Gradient Boosting) |
| **Data Source** | Yahoo Finance API |
| **Hosting** | Streamlit Cloud (free tier) |
| **Database** | CSV downloads (optional) |

---

## Performance Metrics

- **Annualized Return:** 137.46%
- **Sharpe Ratio:** 2.59
- **Holding Period:** 5 trading days
- **Strategy:** Top-K long-only ranking

---

## File Structure

```
Market analysis/
├── streamlit_app.py           # Main Streamlit app
├── train_short_term.py        # Model training script
├── make_features.py           # Feature engineering
├── combine_data.py            # Data preprocessing
├── datapull.py                # Data download
├── models/
│   ├── short_term_lgb_all.pkl      # Trained model (86 stocks)
│   └── short_term_lgb_50.pkl       # Trained model (50 stocks)
├── combined/
│   ├── price_panel.parquet    # Price data
│   ├── volume_panel.parquet   # Volume data
│   └── features_long.parquet  # Computed features
├── output/
│   ├── metrics_short.csv      # Performance metrics
│   ├── preds_short_walkfwd.csv # Backtest predictions
│   └── [stock]_prediction.csv # Individual stock predictions
├── requirements.txt           # Python dependencies
├── .streamlit/config.toml     # Streamlit configuration
└── README.md                  # This file
```

---

## Environment Variables (Optional)

For Streamlit Cloud, no special env vars needed. But you can add to `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
toolbarMode = "minimal"
showSidebarNavigation = false
```

---

## Troubleshooting

### App loads slowly
- First time loads all 50 stocks (5-10 minutes)
- Results are cached for 1 hour
- Refresh button forces new data fetch

### Data fetch errors
- Check internet connection
- Yahoo Finance API may be rate-limited
- Try again in 5 minutes

### Model not found error
- Ensure `models/short_term_lgb_all.pkl` exists
- Run `python train_short_term.py` to regenerate

### Phone app not responsive
- Refresh browser
- Clear cache (Settings → Storage → Clear Cache)
- Use latest Chrome/Safari version

---

## Advanced: Schedule Daily Updates

To run predictions daily at 9:15 AM IST and save to a database:

```python
# schedule_predictions.py
import schedule
import time
from streamlit_app import generate_predictions

def daily_job():
    print(f"Running daily predictions at {datetime.now()}")
    # Fetch data and run predictions
    # Save to database or CSV

schedule.every().day.at("09:15").do(daily_job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

Run as background task on your server.

---

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Streamlit Cloud | FREE (up to 1 app) |
| Data (Yahoo Finance) | FREE |
| Model Training (local) | FREE |
| Domain (optional) | $10-15/year |
| **Total** | **FREE** |

---

## Security & Best Practices

✅ Model weights are local (no API keys needed)  
✅ Only reads public market data  
✅ No personal data stored  
✅ HTTPS encryption on Streamlit Cloud  

⚠️ **Disclaimer:** This is NOT financial advice. Always:
- Do your own research
- Implement proper risk management
- Use stop-losses
- Start with small capital
- Test thoroughly before scaling

---

## Next Steps

1. ✅ Test locally: `streamlit run streamlit_app.py`
2. ✅ Push to GitHub (create repo if needed)
3. ✅ Deploy on Streamlit Cloud
4. ✅ Share link with friends/family
5. ✅ Monitor performance and refine signals

---

## Support & Updates

- **Report issues:** GitHub Issues
- **Model updates:** Retrain `train_short_term.py` monthly
- **New stocks:** Add symbols to `NIFTY_50` list in `streamlit_app.py`

---

**Last Updated:** 2025-11-22  
**Version:** 1.0  
**Status:** Production Ready ✅
