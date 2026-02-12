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
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, (np.int64, np.int32, np.integer)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32, np.floating)):
            return float(obj)
        return super(PandasEncoder, self).default(obj)

def calculate_indicators(df):
    # RSI 14 ימים
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ממוצעים נעים לטווח קצר וארוך
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # ניקוי ערכים חסרים שנוצרו בתחילת ההיסטוריה
    return df.replace([np.inf, -np.inf], np.nan).fillna(0)

def process_ticker(symbol):
    print(f"Fetching ALL-TIME data for {symbol}...")
    stock = yf.Ticker(symbol)
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    file_path = os.path.join(DATA_DIR, f"{symbol.lower()}_data.json")
    
    # משיכת כל ההיסטוריה מאז ההנפקה
    df = stock.history(period="max", interval="1d")
    if df.empty: 
        print(f"No data found for {symbol}")
        return

    df.reset_index(inplace=True)
    # וידוא עמודת תאריך
    date_col = 'Date' if 'Date' in df.columns else 'Datetime'
    df['Datetime'] = pd.to_datetime(df[date_col])
    
    # חישוב אינדיקטורים על כל המאגר
    df = calculate_indicators(df)
    
    latest = df.iloc[-1]
    
    # המרת הנתונים לפורמט קל משקל לשמירה
    # שומרים את כל ההיסטוריה אך מצמצמים עמודות מיותרות
    history_to_save = df[['Datetime', 'Close', 'RSI', 'SMA50', 'SMA200']].copy()
    history_to_save['Datetime'] = history_to_save['Datetime'].dt.strftime('%Y-%m-%d')

    output = {
        "metadata": {
            "symbol": symbol,
            "name": stock.info.get("longName", symbol),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "first_trade_date": history_to_save['Datetime'].iloc[0],
            "current_price": float(latest['Close']),
            "rsi": float(latest['RSI']),
            "sma200": float(latest['SMA200']),
            "recommendation": str(stock.info.get("recommendationKey", "hold"))
        },
        "history": history_to_save.to_dict(orient='records')
    }

    with open(file_path, 'w') as f:
        json.dump(output, f, cls=PandasEncoder)
    print(f"Saved {len(history_to_save)} days of data for {symbol}")

if __name__ == "__main__":
    for ticker in TICKERS:
        try:
            process_ticker(ticker)
        except Exception as e:
            print(f"Failed to process {ticker}: {e}")
