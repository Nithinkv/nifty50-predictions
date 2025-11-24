import pandas as pd
import json
import os
from datetime import datetime

DATA_DIR = "paper_trading_data"
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.csv")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.csv")
BALANCE_FILE = os.path.join(DATA_DIR, "balance.json")

INITIAL_CAPITAL = 1000000.0

class PaperTrading:
    def __init__(self):
        self._ensure_data_exists()
        self.balance = self._load_balance()
        self.portfolio = self._load_portfolio()
        self.transactions = self._load_transactions()

    def _ensure_data_exists(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        if not os.path.exists(PORTFOLIO_FILE):
            pd.DataFrame(columns=["Symbol", "Quantity", "AvgPrice"]).to_csv(PORTFOLIO_FILE, index=False)
            
        if not os.path.exists(TRANSACTIONS_FILE):
            pd.DataFrame(columns=["Date", "Symbol", "Action", "Quantity", "Price", "Amount"]).to_csv(TRANSACTIONS_FILE, index=False)
            
        if not os.path.exists(BALANCE_FILE):
            with open(BALANCE_FILE, "w") as f:
                json.dump({"cash": INITIAL_CAPITAL}, f)

    def _load_balance(self):
        with open(BALANCE_FILE, "r") as f:
            return json.load(f)["cash"]

    def _save_balance(self):
        with open(BALANCE_FILE, "w") as f:
            json.dump({"cash": self.balance}, f)

    def _load_portfolio(self):
        return pd.read_csv(PORTFOLIO_FILE)

    def _save_portfolio(self):
        self.portfolio.to_csv(PORTFOLIO_FILE, index=False)

    def _load_transactions(self):
        return pd.read_csv(TRANSACTIONS_FILE)

    def _log_transaction(self, symbol, action, qty, price, amount):
        new_tx = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Symbol": symbol,
            "Action": action,
            "Quantity": qty,
            "Price": price,
            "Amount": amount
        }])
        # Append to CSV directly to avoid loading huge history if it grows
        new_tx.to_csv(TRANSACTIONS_FILE, mode='a', header=not os.path.exists(TRANSACTIONS_FILE), index=False)
        # Reload for current session
        self.transactions = self._load_transactions()

    def get_portfolio_value(self, current_prices):
        """Calculate total portfolio value based on current market prices."""
        value = 0.0
        for _, row in self.portfolio.iterrows():
            sym = row['Symbol']
            qty = row['Quantity']
            # current_prices is a dict: {'RELIANCE': 2500.0, ...}
            # Handle .NS suffix if needed
            price = current_prices.get(sym) or current_prices.get(sym + '.NS') or current_prices.get(sym.replace('.NS', ''))
            if price:
                value += qty * price
        return value

    def buy_stock(self, symbol, qty, price):
        total_cost = qty * price
        if total_cost > self.balance:
            return False, "Insufficient funds"

        # Update Balance
        self.balance -= total_cost
        self._save_balance()

        # Update Portfolio
        symbol_clean = symbol.replace('.NS', '')
        existing = self.portfolio[self.portfolio['Symbol'] == symbol_clean]
        
        if not existing.empty:
            idx = existing.index[0]
            old_qty = self.portfolio.at[idx, 'Quantity']
            old_avg = self.portfolio.at[idx, 'AvgPrice']
            
            new_qty = old_qty + qty
            new_avg = ((old_qty * old_avg) + (qty * price)) / new_qty
            
            self.portfolio.at[idx, 'Quantity'] = new_qty
            self.portfolio.at[idx, 'AvgPrice'] = new_avg
        else:
            new_row = pd.DataFrame([{"Symbol": symbol_clean, "Quantity": qty, "AvgPrice": price}])
            self.portfolio = pd.concat([self.portfolio, new_row], ignore_index=True)
        
        self._save_portfolio()
        self._log_transaction(symbol_clean, "BUY", qty, price, total_cost)
        return True, "Buy successful"

    def sell_stock(self, symbol, qty, price):
        symbol_clean = symbol.replace('.NS', '')
        existing = self.portfolio[self.portfolio['Symbol'] == symbol_clean]
        
        if existing.empty:
            return False, "Stock not owned"
        
        idx = existing.index[0]
        current_qty = self.portfolio.at[idx, 'Quantity']
        
        if qty > current_qty:
            return False, "Insufficient quantity"
        
        total_sale = qty * price
        
        # Update Balance
        self.balance += total_sale
        self._save_balance()
        
        # Update Portfolio
        if qty == current_qty:
            self.portfolio = self.portfolio.drop(idx).reset_index(drop=True)
        else:
            self.portfolio.at[idx, 'Quantity'] = current_qty - qty
            
        self._save_portfolio()
        self._log_transaction(symbol_clean, "SELL", qty, price, total_sale)
        return True, "Sell successful"

    def reset_account(self):
        self.balance = INITIAL_CAPITAL
        self.portfolio = pd.DataFrame(columns=["Symbol", "Quantity", "AvgPrice"])
        self.transactions = pd.DataFrame(columns=["Date", "Symbol", "Action", "Quantity", "Price", "Amount"])
        
        self._save_balance()
        self._save_portfolio()
        self.transactions.to_csv(TRANSACTIONS_FILE, index=False)
        return True, "Account reset successful"
