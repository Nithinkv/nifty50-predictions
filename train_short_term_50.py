import os
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
import joblib
import lightgbm as lgb

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

# Original 50 tickers from datapull.py converted to underscore format used in features
ORIGINAL_SYMBOLS = [
    "RELIANCE_NS","TCS_NS","HDFCBANK_NS","INFY_NS","ICICIBANK_NS",
    "HINDUNILVR_NS","KOTAKBANK_NS","ITC_NS","LT_NS","SBIN_NS",
    "HDFC_NS","BHARTIARTL_NS","ASIANPAINT_NS","BAJFINANCE_NS","AXISBANK_NS",
    "MARUTI_NS","SUNPHARMA_NS","TATASTEEL_NS","UPL_NS","TITAN_NS",
    "NTPC_NS","POWERGRID_NS","HCLTECH_NS","M_M_NS","NESTLEIND_NS",
    "JSWSTEEL_NS","BRITANNIA_NS","COALINDIA_NS","DIVISLAB_NS","ONGC_NS",
    "BPCL_NS","GRASIM_NS","WIPRO_NS","EICHERMOT_NS","ULTRACEMCO_NS",
    "TECHM_NS","TATAMOTORS_NS","HDFCLIFE_NS","ADANIPORTS_NS","ADANIENT_NS",
    "SHREECEM_NS","SBILIFE_NS","CIPLA_NS","INDUSINDBK_NS","BAJAJ-AUTO_NS",
    "HINDALCO_NS","COFORGE_NS","LUPIN_NS","MRF_NS","PETRONET_NS",
]

# UTIL: prepare expanding-window date splits
def prepare_date_splits(dates_sorted, min_train_days=252*2, test_window_days=126):
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
                callbacks.insert(0, lgb.early_stopping(early_stopping))
            except Exception:
                valid_kwargs["early_stopping_rounds"] = early_stopping
    model = lgb.train(params, lgb_train, num_round, callbacks=callbacks, **valid_kwargs)
    return model

print("Loading features from:", FEATURES_PATH)
df = pd.read_parquet(FEATURES_PATH)
# ensure correct dtypes
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['date','symbol']).reset_index(drop=True)

# filter to original 50 symbols
print('Filtering to original 50 symbols...')
df = df[df['symbol'].isin(ORIGINAL_SYMBOLS)].copy()
print('Symbols in filtered data:', sorted(df['symbol'].unique()))

# create 5-day forward return label
print(f"Creating {SHORT_DAYS}-day forward return label...")
price_wide = df.pivot(index='date', columns='symbol', values='AdjClose')
fwd = price_wide.pct_change(SHORT_DAYS).shift(-SHORT_DAYS)
fwd_long = fwd.stack().reset_index().rename(columns={0:'fwd_ret'})
# merge to df
df = df.merge(fwd_long, on=['date','symbol'], how='left')
# drop rows where forward return is NaN
df = df.dropna(subset=['fwd_ret']).reset_index(drop=True)
print('Rows after merging label:', len(df))

feature_cols = ['ret_1','ret_3','ret_5','ret_10','ret_20',
                'ma_spread_5_20','ma_spread_5_50',
                'vol_10','vol_20','vol_z','rsi','rel_mom_5']

# drop rows with missing feature values (conservative)
df_model = df.dropna(subset=feature_cols + ['fwd_ret']).reset_index(drop=True)
print('Rows after dropping NA features:', len(df_model))

# build splits
dates_sorted = sorted(df_model['date'].unique())
print('Date range:', dates_sorted[0], 'to', dates_sorted[-1], ' - total trading dates:', len(dates_sorted))
splits = prepare_date_splits(dates_sorted, min_train_days=252*2, test_window_days=126)
print('Number of WF splits:', len(splits))

# Walk-forward training & predictions collection
preds_list = []
fold = 0
for train_dates, test_dates in tqdm(splits, desc='Walk-forward'):
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
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    out = df_model.loc[test_mask, ['date','symbol','fwd_ret']].copy()
    out['pred_score'] = y_pred
    out['fold'] = fold
    preds_list.append(out)

if not preds_list:
    raise RuntimeError('No predictions produced in walk-forward.')

preds_wf = pd.concat(preds_list, ignore_index=True)
preds_wf.to_parquet(os.path.join(OUTPUT_DIR, "preds_short_walkfwd_50.parquet"), index=False)
print('Saved walk-forward predictions:', os.path.join(OUTPUT_DIR, 'preds_short_walkfwd_50.parquet'))

# backtest
print('Running rank-based backtest (top-K long-only)...')
rets = []
unique_pred_dates = sorted(preds_wf['date'].unique())
for dt in unique_pred_dates:
    sub = preds_wf[preds_wf['date']==dt].dropna(subset=['pred_score','fwd_ret'])
    if sub.shape[0] < TOP_K:
        continue
    topk = sub.nlargest(TOP_K, 'pred_score')
    gross = topk['fwd_ret'].mean()
    tc = TRANSACTION_COST_PCT * 2
    net = gross - tc
    rets.append({'date':dt, 'gross':gross, 'tc':tc, 'net':net, 'n':len(topk)})
bt = pd.DataFrame(rets).set_index('date')
bt['cum_net'] = (1 + bt['net']).cumprod() - 1
periods = len(bt)
avg_daily = bt['net'].mean()
ann_ret = (1 + avg_daily) ** 252 - 1 if periods>0 else 0.0
ann_vol = bt['net'].std() * (252 ** 0.5) if periods>0 else 0.0
sharpe = ann_ret / ann_vol if ann_vol>0 else np.nan
metrics = {'ann_return':ann_ret, 'ann_vol':ann_vol, 'sharpe':sharpe, 'total_return': bt['cum_net'].iloc[-1] if len(bt)>0 else 0.0}
print('Backtest metrics (50-only):', metrics)

bt.to_csv(os.path.join(OUTPUT_DIR, "backtest_short_50.csv"))
pd.DataFrame([metrics]).to_csv(os.path.join(OUTPUT_DIR, "metrics_short_50.csv"), index=False)
preds_wf.to_csv(os.path.join(OUTPUT_DIR, "preds_short_walkfwd_50.csv"), index=False)
print('Saved backtest and metrics to output/')

# TRAIN final model on all available 50-only data and save
print('Training final model on ALL 50-only data...')
X_all = df_model[feature_cols]
y_all = df_model['fwd_ret']
final_model = train_lgb(X_all, y_all, params=None, num_round=500)
joblib.dump(final_model, os.path.join(MODEL_DIR, "short_term_lgb_50.pkl"))
print('Saved final 50-only model:', os.path.join(MODEL_DIR, 'short_term_lgb_50.pkl'))

print('Done.')
