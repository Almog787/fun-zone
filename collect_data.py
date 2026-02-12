import yfinance as yf
import pandas as pd
import json
import os
import time
import numpy as np
from datetime import datetime

TICKERS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "LLY", "AVGO"]
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

class PandasEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp): return obj.strftime('%Y-%m-%d %H:%M')
        if isinstance(obj, (np.int64, np.int32, np.integer)): return int(obj)
        if isinstance(obj, (np.float64, np.float32, np.floating)): return round(float(obj), 2)
        return super(PandasEncoder, self).default(obj)

def calculate_manual_indicators(df):
    if df.empty: return df
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    return df.fillna(0)

def calculate_score(row):
    score = 50
    signals = []
    if row['Close'] > row['SMA200']:
        score += 20
        signals.append("📈 Uptrend")
    else:
        score -= 20
        signals.append("📉 Downtrend")
    if row['RSI'] < 35:
        score += 15
        signals.append("🟢 Oversold")
    elif row['RSI'] > 70:
        score -= 15
        signals.append("🔴 Overbought")
    return max(0, min(100, score)), signals

def process_ticker(symbol):
    file_path = os.path.join(DATA_DIR, f"{symbol.lower()}_daily.json")
    stock = yf.Ticker(symbol)
    
    existing_df = pd.DataFrame()
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                old_data = json.load(f)
                existing_df = pd.DataFrame(old_data['history'])
                existing_df['Date'] = pd.to_datetime(existing_df['Date']).dt.tz_localize(None)
        except: pass

    # אם אין נתונים - מוריד הכל (max), אם יש - מוריד רק חודש אחרון לעדכון
    period = "max" if existing_df.empty else "1mo"
    new_data = stock.history(period=period, interval="1d")
    if new_data.empty: return
    
    new_data.reset_index(inplace=True)
    new_data['Date'] = pd.to_datetime(new_data['Date']).dt.tz_localize(None)

    combined_df = pd.concat([existing_df, new_data]).drop_duplicates(subset=['Date'], keep='last')
    combined_df = combined_df.sort_values('Date')
    combined_df = calculate_manual_indicators(combined_df)

    latest = combined_df.iloc[-1]
    score, signals = calculate_score(latest)
    
    meta = {
        "symbol": symbol, "name": stock.info.get("longName", symbol),
        "price": latest['Close'], "change": ((latest['Close'] - combined_df.iloc[-2]['Close']) / combined_df.iloc[-2]['Close']) * 100,
        "score": score, "signals": signals, "rsi": latest['RSI'],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    history_to_save = combined_df[['Date', 'Close', 'SMA200', 'SMA50', 'Volume']].copy()
    history_to_save['Date'] = history_to_save['Date'].dt.strftime('%Y-%m-%d %H:%M')
    
    with open(file_path, 'w') as f:
        json.dump({"meta": meta, "history": history_to_save.to_dict(orient='records')}, f, cls=PandasEncoder, indent=0)
    return meta

if __name__ == "__main__":
    rankings = []
    for ticker in TICKERS:
        try:
            m = process_ticker(ticker)
            if m: rankings.append(m)
        except Exception as e: print(f"Error {ticker}: {e}")
        time.sleep(1)

    rankings.sort(key=lambda x: x['score'], reverse=True)
    with open(os.path.join(DATA_DIR, "market_rankings.json"), 'w') as f:
        json.dump(rankings, f, cls=PandasEncoder, indent=2)
