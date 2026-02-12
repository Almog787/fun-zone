import yfinance as yf
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

# רשימת 10 הגדולות
TICKERS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "LLY", "AVGO"]
DATA_DIR = "data"

class PandasEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M')
        if isinstance(obj, (np.int64, np.int32, np.integer)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32, np.floating)):
            return float(obj)
        return super(PandasEncoder, self).default(obj)

def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    return df.replace([np.inf, -np.inf], np.nan).fillna(0)

def process_ticker(symbol):
    print(f"Processing {symbol}...")
    stock = yf.Ticker(symbol)
    
    # יצירת נתיב לקובץ בתוך תיקיית data
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    file_path = os.path.join(DATA_DIR, f"{symbol.lower()}_data.json")
    
    df = stock.history(period="1y", interval="1d")
    if df.empty: return

    df.reset_index(inplace=True)
    date_col = 'Date' if 'Date' in df else 'Datetime'
    df['Datetime'] = pd.to_datetime(df[date_col])
    df = calculate_indicators(df)
    
    latest = df.iloc[-1]
    history_to_save = df.tail(500).copy()
    history_to_save['Datetime'] = history_to_save['Datetime'].dt.strftime('%Y-%m-%d')

    output = {
        "metadata": {
            "symbol": symbol,
            "name": stock.info.get("longName", symbol),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "current_price": float(latest['Close']),
            "rsi": float(latest['RSI']),
            "sma200": float(latest['SMA200']),
            "recommendation": str(stock.info.get("recommendationKey", "N/A"))
        },
        "history": history_to_save.to_dict(orient='records')
    }

    with open(file_path, 'w') as f:
        json.dump(output, f, indent=2, cls=PandasEncoder)

if __name__ == "__main__":
    for ticker in TICKERS:
        try:
            process_ticker(ticker)
        except Exception as e:
            print(f"Failed to process {ticker}: {e}")
