import yfinance as yf
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime, timedelta

# 10 החברות הגדולות ב-S&P 500 (נכון ל-2024)
TICKERS = ["MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", "META", "BRK-B", "LLY", "TSLA", "AVGO"]
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

def save_json(data, filename):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w') as f:
        json.dump(data, f, cls=PandasEncoder, indent=0) # indent=0 לחיסכון במקום

def process_stock(symbol):
    print(f"--- Processing {symbol} ---")
    stock = yf.Ticker(symbol)
    
    # --- חלק 1: היסטוריה מלאה (יומי) ---
    print(f"Fetching MAX Daily history...")
    df_daily = stock.history(period="max", interval="1d")
    
    # חישוב אינדיקטורים לטווח ארוך
    df_daily['SMA200'] = df_daily['Close'].rolling(window=200).mean()
    df_daily['SMA50'] = df_daily['Close'].rolling(window=50).mean()
    df_daily.reset_index(inplace=True)
    
    # שמירת קובץ Macro
    daily_records = df_daily[['Date', 'Close', 'SMA200', 'SMA50', 'Volume']].to_dict(orient='records')
    
    # --- חלק 2: רזולוציה גבוהה (שעתי + דקתי) ---
    print(f"Fetching Intraday (High Res)...")
    
    # נתונים שעתיים (שנתיים אחרונות - המקסימום של יאהו)
    df_hourly = stock.history(period="2y", interval="1h")
    
    # נתונים דקתיים (7 ימים אחרונים - המקסימום של יאהו)
    df_minute = stock.history(period="7d", interval="1m")
    
    # מיזוג: עדיפות לדקות היכן שיש, ושעות לשאר
    df_high_res = pd.concat([df_hourly, df_minute])
    df_high_res = df_high_res[~df_high_res.index.duplicated(keep='last')] # הסרת כפילויות
    df_high_res.sort_index(inplace=True)
    
    # חישוב RSI לטווח קצר
    delta = df_high_res['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_high_res['RSI'] = 100 - (100 / (1 + rs))
    
    df_high_res.reset_index(inplace=True)
    col_name = 'Datetime' if 'Datetime' in df_high_res.columns else 'Date'
    
    # שמירת קובץ Micro
    # שומרים רק את ה-2000 נקודות האחרונות כדי שהדפדפן לא יקרוס
    intraday_records = df_high_res.tail(2000)[[col_name, 'Close', 'RSI', 'Volume']].to_dict(orient='records')

    # מידע כללי
    info = stock.info
    metadata = {
        "symbol": symbol,
        "name": info.get("longName", symbol),
        "market_cap": info.get("marketCap", 0),
        "pe_ratio": info.get("trailingPE", 0),
        "sector": info.get("sector", "N/A"),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # יצירת אובייקט סופי ושמירה בשני קבצים נפרדים
    save_json({"meta": metadata, "data": daily_records}, f"{symbol}_daily.json")
    save_json({"meta": metadata, "data": intraday_records}, f"{symbol}_intraday.json")
    
    print(f"Saved {symbol}: Daily ({len(daily_records)}), Intraday ({len(intraday_records)})")

if __name__ == "__main__":
    for ticker in TICKERS:
        try:
            process_stock(ticker)
        except Exception as e:
            print(f"Error on {ticker}: {e}")
