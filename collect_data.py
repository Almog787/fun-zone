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
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    # SMA
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    return df.fillna(0)

def process_ticker(symbol):
    file_path = os.path.join(DATA_DIR, f"{symbol.lower()}_daily.json")
    stock = yf.Ticker(symbol)
    
    # 1. טעינת המאגר הקיים מהדיסק
    existing_df = pd.DataFrame()
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                old_data = json.load(f)
                existing_df = pd.DataFrame(old_data['history'])
                # המרה לתאריך וניטרול אזור זמן (tz_localize(None))
                existing_df['Date'] = pd.to_datetime(existing_df['Date']).dt.tz_localize(None)
            print(f"Loaded {len(existing_df)} rows for {symbol}")
        except Exception as e:
            print(f"Could not load old data for {symbol}: {e}")

    # 2. משיכת נתונים חדשים
    # מורידים חודש אחרון כדי לוודא שאין חורים
    new_data = stock.history(period="1mo", interval="1d")
    if new_data.empty: return
    
    new_data.reset_index(inplace=True)
    # ניטרול אזור זמן מהנתונים החדשים כדי שיהיו תואמים לישנים
    new_data['Date'] = pd.to_datetime(new_data['Date']).dt.tz_localize(None)

    # 3. מיזוג (Merging)
    # concat מחבר, drop_duplicates מנקה כפילויות תאריכים
    combined_df = pd.concat([existing_df, new_data]).drop_duplicates(subset=['Date'], keep='last')
    combined_df = combined_df.sort_values('Date')

    # 4. חישוב אינדיקטורים מחדש
    combined_df = calculate_manual_indicators(combined_df)

    # 5. הכנת פלט
    latest = combined_df.iloc[-1]
    meta = {
        "symbol": symbol,
        "name": stock.info.get("longName", symbol),
        "price": latest['Close'],
        "score": 50, 
        "rsi": latest['RSI'],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    # המרה חזרה למחרוזת לצורך שמירה ב-JSON
    history_to_save = combined_df[['Date', 'Close', 'SMA200', 'SMA50', 'Volume']].copy()
    history_to_save['Date'] = history_to_save['Date'].dt.strftime('%Y-%m-%d %H:%M')
    
    history_data = history_to_save.to_dict(orient='records')
    
    with open(file_path, 'w') as f:
        json.dump({"meta": meta, "history": history_data}, f, cls=PandasEncoder, indent=0)
    print(f"Successfully updated {symbol}")

if __name__ == "__main__":
    for ticker in TICKERS:
        try:
            process_ticker(ticker)
        except Exception as e:
            print(f"Error on {ticker}: {e}")
        time.sleep(1)
