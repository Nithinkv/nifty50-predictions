"""
train_short_term.py

Train a short-term LightGBM model to predict 5-day forward returns using
features produced by make_features.py (combined/features_long.parquet).

Outputs:
 - output/preds_short_walkfwd.csv
 - output/backtest_short.csv
 - models/short_term_lgb_all.pkl
 - output/metrics_short.csv
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
import joblib
import lightgbm as lgb
from sklearn.metrics import mean_squared_error

# CONFIG
FEATURES_PATH = "combined/features_long.parquet"
OUTPUT_DIR = "output"
MODEL_DIR = "models"
SHORT_DAYS = 5
TOP_K = 10
TRANSACTION_COST_PCT = 0.0008  # 0.08% per side (example)
SEED = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# UTIL: prepare expanding-window date splits
def prepare_date_splits(dates_sorted, min_train_days=252*2, test_window_days=126):
    """
    dates_sorted: sorted list/array of unique dates (pd.Timestamp)
    returns list of (train_dates_set, test_dates_set)
    """
    splits = []
    train_end = min_train_days
    while train_end + test_window_days <= len(dates_sorted):
        train_dates = set(dates_sorted[:train_end])
        test_dates = set(dates_sorted[train_end:train_end+test_window_days])
        splits.append((train_dates, test_dates))
        train_end += test_window_days
    return splits

# LIGHTGBM trainer
def train_lgb(X_train, y_train, X_val=None, y_val=None, params=None, num_round=1000, early_stopping=50):
    params = params or {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 50,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "seed": SEED,
        "verbosity": -1
    }
    lgb_train = lgb.Dataset(X_train, y_train)
    valid_sets = [lgb_train]
    valid_names = ["train"]
    # prepare callbacks for compatibility across LightGBM versions
    callbacks = [lgb.log_evaluation(False)]
    valid_kwargs = {}
    if X_val is not None and y_val is not None:
        lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train)
        valid_sets.append(lgb_val)
        valid_names.append("valid")
        valid_kwargs["valid_sets"] = valid_sets
        valid_kwargs["valid_names"] = valid_names
        if early_stopping and early_stopping > 0:
            try:
                # preferred: use callback API
                callbacks.insert(0, lgb.early_stopping(early_stopping))
            except Exception:
                # fallback: some lightgbm versions accept early_stopping_rounds kwarg
                valid_kwargs["early_stopping_rounds"] = early_stopping
    model = lgb.train(params, lgb_train, num_round, callbacks=callbacks, **valid_kwargs)
    return model

# LOAD features
print("Loading features from:", FEATURES_PATH)
df = pd.read_parquet(FEATURES_PATH)
# ensure correct dtypes
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['date','symbol']).reset_index(drop=True)

# create 5-day forward return label
print(f"Creating {SHORT_DAYS}-day forward return label...")
# We need forward return computed per symbol. We'll pivot, compute, then merge back.
price_wide = df.pivot(index='date', columns='symbol', values='AdjClose')
fwd = price_wide.pct_change(SHORT_DAYS).shift(-SHORT_DAYS)  # at date t, fwd_ret is (t+SHORT)/t - 1
fwd_long = fwd.stack().reset_index().rename(columns={0:'fwd_ret'})
# merge to df
df = df.merge(fwd_long, on=['date','symbol'], how='left')
# drop rows where forward return is NaN (near the end or sparse)
df = df.dropna(subset=['fwd_ret']).reset_index(drop=True)
print("Rows after merging label:", len(df))

# choose features
feature_cols = ['ret_1','ret_3','ret_5','ret_10','ret_20',
                'ma_spread_5_20','ma_spread_5_50',
                'vol_10','vol_20','vol_z','rsi','rel_mom_5']

# drop rows with missing feature values (conservative)
df_model = df.dropna(subset=feature_cols + ['fwd_ret']).reset_index(drop=True)
print("Rows after dropping NA features:", len(df_model))

# get sorted unique dates for splitting
dates_sorted = sorted(df_model['date'].unique())
print("Date range:", dates_sorted[0], "to", dates_sorted[-1], " - total trading dates:", len(dates_sorted))

# build splits (2yr train, 6mo test windows)
splits = prepare_date_splits(dates_sorted, min_train_days=252*2, test_window_days=126)
print("Number of WF splits:", len(splits))

# Walk-forward training & predictions collection
preds_list = []
fold = 0
for train_dates, test_dates in tqdm(splits, desc="Walk-forward"):
    fold += 1
    train_mask = df_model['date'].isin(train_dates)
    test_mask = df_model['date'].isin(test_dates)
    X_train = df_model.loc[train_mask, feature_cols]
    y_train = df_model.loc[train_mask, 'fwd_ret']
    X_test = df_model.loc[test_mask, feature_cols]
    y_test = df_model.loc[test_mask, 'fwd_ret']

    if len(X_train) < 200 or len(X_test) == 0:
        continue

    model = train_lgb(X_train, y_train, X_val=X_test, y_val=y_test)
    # predict for test window
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    out = df_model.loc[test_mask, ['date','symbol','fwd_ret']].copy()
    out['pred_score'] = y_pred
    out['fold'] = fold
    preds_list.append(out)

# assemble predictions
if not preds_list:
    raise RuntimeError("No predictions produced in walk-forward.")
preds_wf = pd.concat(preds_list, ignore_index=True)
preds_wf.to_parquet(os.path.join(OUTPUT_DIR, "preds_short_walkfwd.parquet"), index=False)
print("Saved walk-forward predictions:", os.path.join(OUTPUT_DIR, "preds_short_walkfwd.parquet"))

# Simple rank-based backtest: on each prediction date pick top-K by pred_score and take actual fwd_ret as realized return
print("Running rank-based backtest (top-K long-only)...")
rets = []
unique_pred_dates = sorted(preds_wf['date'].unique())
for dt in unique_pred_dates:
    sub = preds_wf[preds_wf['date']==dt].dropna(subset=['pred_score','fwd_ret'])
    if sub.shape[0] < TOP_K:
        # skip dates with too few tickers
        continue
    topk = sub.nlargest(TOP_K, 'pred_score')
    gross = topk['fwd_ret'].mean()  # mean realized 5-day return for top-k picks (since fwd_ret is that)
    tc = TRANSACTION_COST_PCT * 2  # conservative flat cost per rebalance
    net = gross - tc
    rets.append({'date':dt, 'gross':gross, 'tc':tc, 'net':net, 'n':len(topk)})
bt = pd.DataFrame(rets).set_index('date')
bt['cum_net'] = (1 + bt['net']).cumprod() - 1
# metrics
periods = len(bt)
avg_daily = bt['net'].mean()
ann_ret = (1 + avg_daily) ** 252 - 1 if periods>0 else 0.0
ann_vol = bt['net'].std() * (252 ** 0.5) if periods>0 else 0.0
sharpe = ann_ret / ann_vol if ann_vol>0 else np.nan
metrics = {'ann_return':ann_ret, 'ann_vol':ann_vol, 'sharpe':sharpe, 'total_return': bt['cum_net'].iloc[-1] if len(bt)>0 else 0.0}
print("Backtest metrics:", metrics)

# save backtest and preds
bt.to_csv(os.path.join(OUTPUT_DIR, "backtest_short.csv"))
pd.DataFrame([metrics]).to_csv(os.path.join(OUTPUT_DIR, "metrics_short.csv"), index=False)
preds_wf.to_csv(os.path.join(OUTPUT_DIR, "preds_short_walkfwd.csv"), index=False)
print("Saved backtest and metrics to output/")

# TRAIN final model for EACH stock
print("Training final models for EACH stock...")
unique_symbols = df_model['symbol'].unique()

for sym in tqdm(unique_symbols, desc="Training per-stock models"):
    # Filter data for this symbol
    mask = df_model['symbol'] == sym
    X_sym = df_model.loc[mask, feature_cols]
    y_sym = df_model.loc[mask, 'fwd_ret']
    
    if len(X_sym) < 50:
        print(f"Skipping {sym} (not enough data: {len(X_sym)})")
        continue
        
    # Train model
    model = train_lgb(X_sym, y_sym, params=None, num_round=200) # Reduced rounds for speed per stock
    
    # Save model
    safe_sym = sym.replace('.NS', '')
    joblib.dump(model, os.path.join(MODEL_DIR, f"{safe_sym}.pkl"))

print(f"Saved {len(unique_symbols)} models to {MODEL_DIR}/")
print("Done.")
