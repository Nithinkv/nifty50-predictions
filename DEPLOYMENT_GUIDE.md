# Live Model Deployment Guide

## Quick Start

Run the live inference script to get trading signals:
```bash
python live_model_inference.py
```

This will:
1. ✓ Fetch latest market data
2. ✓ Compute all required features
3. ✓ Generate predictions
4. ✓ Output top-10 stocks to buy

## Typical Live Trading Workflow

### Pre-Market (8:00 AM - 9:15 AM IST)
```bash
# Run prediction at 9:10 AM (before market open at 9:15)
python live_model_inference.py

# Review output in: output/live_trades.csv
```

### Market Open (9:15 AM onwards)
- Place BUY orders on top-10 stocks from predictions
- Use limit orders slightly above market price
- Equal weight positions: $100k portfolio = $10k per stock

### During Trade (5 business days)
- Model predicts 5-day forward returns
- Monitor positions daily
- Implement stop-loss if price drops 2-3%

### Exit (Day 5 or earlier if target hit)
- Close positions after 5 days
- Record realized returns
- Compare to model predictions for performance tracking

---

## Feature Reference

The model uses 12 technical indicators:

| Feature | Description | Period |
|---------|-------------|--------|
| `ret_1` | 1-day return | 1 bar |
| `ret_3` | 3-day return | 3 bars |
| `ret_5` | 5-day return | 5 bars |
| `ret_10` | 10-day return | 10 bars |
| `ret_20` | 20-day return | 20 bars |
| `ma_spread_5_20` | (MA5 - MA20) / MA20 | 20 bars |
| `ma_spread_5_50` | (MA5 - MA50) / MA50 | 50 bars |
| `vol_10` | 10-day volatility | 10 bars |
| `vol_20` | 20-day volatility | 20 bars |
| `vol_z` | Volume z-score vs 20-day mean | 20 bars |
| `rsi` | Relative Strength Index | 14 bars |
| `rel_mom_5` | 5-day relative momentum | 5 bars |

**Minimum Data Required:** 50 days of historical data per symbol

---

## Model Details

| Parameter | Value |
|-----------|-------|
| **Algorithm** | LightGBM (Gradient Boosting) |
| **Task** | Regression (predicting 5-day forward return) |
| **Training Data** | Original 50 stocks: 125,139 rows |
| **Training Data** | Expanded (86 stocks): 222,070 rows |
| **Output** | Continuous score (predicted 5-day return %) |
| **Holding Period** | 5 business days |
| **Strategy** | Long-only, top-K picks |

---

## Performance Metrics

### Original 50 Universe
- Annual Return: **121.06%**
- Annual Volatility: **46.92%**
- Sharpe Ratio: **2.58**
- Total Return: **232.07%**

### Expanded 86 Universe
- Annual Return: **137.46%**
- Annual Volatility: **53.00%**
- Sharpe Ratio: **2.59**
- Total Return: **325.65%**

---

## Risk Management

### 1. Position Sizing
```python
portfolio_value = 100000  # $100k
top_k = 10
position_size = portfolio_value / top_k  # $10k per stock
```

### 2. Stop-Loss
```python
entry_price = 1000
stop_loss_pct = 0.03  # 3%
stop_loss_price = entry_price * (1 - stop_loss_pct)  # 970
```

### 3. Portfolio Rebalancing
- Rebalance every 5 days (model holding period)
- Or rebalance daily if new predictions significantly differ
- Track cumulative returns and volatility

### 4. Model Drift Detection
```python
# Track prediction accuracy monthly
predicted_5d_return = live_predictions['pred_score']
actual_5d_return = (price_t5 - price_t0) / price_t0
accuracy = correlation(predicted, actual)

# Retrain if accuracy drops below threshold (e.g., r < 0.10)
if accuracy < 0.10:
    print("Model drift detected. Retrain recommended.")
```

---

## Automated Scheduling

### Option 1: Windows Task Scheduler
```powershell
# Create scheduled task to run at 9:10 AM daily
$trigger = New-ScheduledTaskTrigger -Daily -At 9:10AM
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument "C:\path\to\activate.bat; python live_model_inference.py"
Register-ScheduledTask -TaskName "StockPredictions" -Trigger $trigger -Action $action
```

### Option 2: Linux/Mac Cron
```bash
# Edit crontab
crontab -e

# Add line (run at 9:10 AM Mon-Fri)
10 9 * * 1-5 cd /path/to/Market\ analysiis && python live_model_inference.py >> logs/predictions.log 2>&1
```

### Option 3: Python APScheduler
```python
from apscheduler.schedulers.background import BackgroundScheduler

def run_predictions():
    os.system("python live_model_inference.py")

scheduler = BackgroundScheduler()
scheduler.add_job(run_predictions, 'cron', day_of_week='mon-fri', hour=9, minute=10)
scheduler.start()
```

---

## Integration with Broker APIs

### Zerodha (Kite)
```python
from kiteconnect import KiteConnect

kite = KiteConnect(api_key="YOUR_API_KEY")
kite.set_access_token("YOUR_ACCESS_TOKEN")

# Place orders
for symbol, weight in topk_picks.iterrows():
    kite.order_place(
        variety='regular',
        symbol=symbol,
        transaction_type='BUY',
        quantity=int(amount * weight / current_price),
        price=current_price * 1.005,  # 0.5% above market
        order_type='LIMIT'
    )
```

### Angel Broking
```python
from smartapi import SmartConnect

smartApi = SmartConnect(api_key="YOUR_API_KEY")
data = smartApi.generateSession("USER_ID", "PASSWORD", "USER_TOKEN")

# Place orders
smartApi.placeOrder({
    'variety': 'NORMAL',
    'tradingsymbol': symbol,
    'symboltoken': token,
    'transactiontype': 'BUY',
    'quantity': quantity,
    'price': price,
    'pricetype': 'LIMIT'
})
```

---

## Monitoring & Logging

### Track Prediction Performance
```python
import json
from datetime import datetime

log_entry = {
    'timestamp': datetime.now().isoformat(),
    'symbols': topk_picks['symbol'].tolist(),
    'predictions': topk_picks['pred_score'].tolist(),
    'actual_returns': None,  # Fill after 5 days
    'profit_loss': None
}

with open('logs/predictions_log.jsonl', 'a') as f:
    f.write(json.dumps(log_entry) + '\n')
```

### Dashboard (Optional)
- Use Grafana or Streamlit to visualize:
  - Daily predictions and signals
  - Backtested vs live performance
  - Win rate and profit factor
  - Drawdown and Sharpe ratio trends

---

## Important Disclaimers

⚠️ **Risk Warning:**
- Past performance does NOT guarantee future results
- Market conditions change; model may underperform in different regimes
- This is NOT financial advice; consult a financial advisor
- Start with small capital; scale only after validating performance
- Always implement proper risk management (stop-losses, position sizing)
- Monitor for market holidays, circuit breakers, and corporate actions

⚠️ **Model Limitations:**
- Trained on historical data; may not adapt to structural market changes
- Does not account for earnings announcements or major news events
- Assumes normal liquidity; may struggle with low-volume stocks
- Sensitive to data quality; gaps or errors in price data reduce accuracy

---

## Quick Reference Commands

```bash
# Run live predictions
python live_model_inference.py

# View recent trades
cat output/live_trades.csv

# Check all predictions
cat output/live_predictions.csv

# Backtest a specific period (if backtest script available)
python backtest.py --start-date 2025-01-01 --end-date 2025-11-22

# Train/retrain model
python train_short_term.py

# Check model file size and creation time
ls -lh models/short_term_lgb_all.pkl
```

---

**Last Updated:** 2025-11-22  
**Model Version:** short_term_lgb_all.pkl (86 symbols) / short_term_lgb_50.pkl (50 symbols)
