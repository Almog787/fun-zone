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
        if isinstance(obj, (np.int64, np.int32)): return int(obj)
        if isinstance(obj, (np.float64, np.float32)): return round(float(obj), 2)
        return super(PandasEncoder, self).default(obj)

def calculate_technical_analysis(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # SMAs
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # Bollinger Bands (Volatilty)
    df['STD'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['Close'].rolling(window=20).mean() + (df['STD'] * 2)
    df['BB_Lower'] = df['Close'].rolling(window=20).mean() - (df['STD'] * 2)
    
    # ATR (Volatility)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()

    return df.fillna(0)

def analyze_stock_score(row):
    score = 50 # ציון התחלתי ניטרלי
    signals = []

    # 1. ניתוח מגמה (Trend)
    if row['Close'] > row['SMA200']:
        score += 20
        signals.append("Uptrend (Above SMA200)")
    else:
        score -= 20
        signals.append("Downtrend (Below SMA200)")

    # 2. חציית ממוצעים (Golden Cross)
    if row['SMA50'] > row['SMA200']:
        score += 10
    
    # 3. מומנטום (RSI)
    if row['RSI'] < 30:
        score += 15
        signals.append("Oversold (RSI < 30)")
    elif row['RSI'] > 70:
        score -= 15
        signals.append("Overbought (RSI > 70)")

    # 4. ווליום חריג (Volume Spike)
    # נניח שאנחנו בודקים אם הווליום הנוכחי גדול ב-50% מהממוצע (לא מחושב כאן במדויק בגרסה זו, אבל הלוגיקה קיימת)
    
    # 5. רצועות בולינגר
    if row['Close'] < row['BB_Lower']:
        score += 10
        signals.append("Price below Bollinger (Dip Buy?)")
    
    # נרמול הציון בין 0 ל-100
    score = max(0, min(100, score))
    
    return score, signals

def save_json(data, filename):
    with open(os.path.join(DATA_DIR, filename), 'w') as f:
        json.dump(data, f, cls=PandasEncoder, indent=0)

def process_market():
    rankings = []

    for symbol in TICKERS:
        print(f"Analyzing {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            
            # --- 1. איסוף היסטורי מלא (Daily) ---
            df = stock.history(period="max", interval="1d")
            
            # חישוב אינדיקטורים מתקדמים
            df = calculate_technical_analysis(df)
            df.reset_index(inplace=True)
            
            # שמירת קובץ גרפים
            graph_data = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'SMA200', 'SMA50']].tail(2000).to_dict(orient='records')
            
            # --- 2. ניתוח ודירוג (על בסיס היום האחרון) ---
            latest = df.iloc[-1]
            score, signals = analyze_stock_score(latest)
            
            info = stock.info
            meta = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "price": latest['Close'],
                "change": ((latest['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100,
                "score": score,
                "signals": signals,
                "rsi": latest['RSI'],
                "atr": latest['ATR'],
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            # שמירת קובץ מניה בודד
            save_json({"meta": meta, "history": graph_data}, f"{symbol}_daily.json")
            
            # הוספה לרשימת הדירוג הכללית
            rankings.append(meta)
            
            time.sleep(1) # מניעת חסימה

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    # שמירת קובץ הדירוגים הראשי
    # מיון לפי ציון (מהגבוה לנמוך)
    rankings.sort(key=lambda x: x['score'], reverse=True)
    
    with open(os.path.join(DATA_DIR, "market_rankings.json"), 'w') as f:
        json.dump(rankings, f, cls=PandasEncoder, indent=2)
    
    print("Market Analysis Complete. Rankings generated.")

if __name__ == "__main__":
    process_market()
