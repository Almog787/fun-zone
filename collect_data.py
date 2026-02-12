import yfinance as yf
import pandas as pd
import pandas_ta as ta  # הספרייה הכבדה לניתוח טכני
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

def advanced_analysis(df):
    # שימוש באסטרטגיית pandas-ta
    # 1. מגמה: EMA (אקספוננציאלי - מגיב מהר יותר)
    df.ta.ema(length=50, append=True)
    df.ta.ema(length=200, append=True)
    
    # 2. מומנטום: MACD (Moving Average Convergence Divergence)
    df.ta.macd(append=True) # יוצר עמודות MACD_12_26_9, MACDh, MACDs
    
    # 3. תנודתיות: Bollinger Bands
    df.ta.bbands(length=20, std=2, append=True)
    
    # 4. כוח מגמה: ADX (Average Directional Index)
    df.ta.adx(length=14, append=True)
    
    # 5. מתנד: RSI
    df.ta.rsi(length=14, append=True)

    return df.fillna(0)

def calculate_score(row):
    score = 50
    reasons = []

    # ניתוח EMA (מגמה ראשית)
    if row['EMA_50'] > row['EMA_200']:
        score += 15
        if row['Close'] > row['EMA_50']:
            score += 10
            reasons.append("Bullish Trend")
    else:
        score -= 15
        if row['Close'] < row['EMA_50']:
            score -= 10
            reasons.append("Bearish Trend")

    # ניתוח MACD (מומנטום)
    # MACD_12_26_9 הוא קו ה-MACD, MACDs_12_26_9 הוא ה-Signal
    if row['MACD_12_26_9'] > row['MACDs_12_26_9']:
        score += 10
        reasons.append("MACD Crossover (Pos)")
    
    # ניתוח ADX (עוצמת מגמה)
    if row['ADX_14'] > 25:
        score += 5 # מגמה חזקה
        
    # ניתוח RSI
    if row['RSI_14'] < 30:
        score += 20
        reasons.append("Oversold (RSI)")
    elif row['RSI_14'] > 70:
        score -= 20
        reasons.append("Overbought (RSI)")

    # בולינגר (פריצה)
    if row['Close'] < row['BBL_20_2.0']:
        score += 15
        reasons.append("Price < Lower BB (Discount)")

    return max(0, min(100, score)), reasons

def process_market():
    rankings = []
    
    for symbol in TICKERS:
        print(f"Deep analyzing {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="2y", interval="1d")
            
            if df.empty: continue

            # הפעלת המנוע הכבד
            df = advanced_analysis(df)
            
            latest = df.iloc[-1]
            score, signals = calculate_score(latest)
            
            # הכנת נתונים (שומרים רק את מה שצריך לגרף ולממשק)
            # אנו שומרים את השמות המקוריים של yfinance ומוסיפים את המחושבים
            graph_data = df.tail(500).reset_index().to_dict(orient='records')

            info = stock.info
            meta = {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "price": latest['Close'],
                "change": ((latest['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100,
                "score": score,
                "signals": signals,
                "rsi": latest['RSI_14'],
                "macd": latest['MACD_12_26_9'], # ערך ה-MACD
                "adx": latest['ADX_14'],
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            with open(os.path.join(DATA_DIR, f"{symbol}_daily.json"), 'w') as f:
                json.dump({"meta": meta, "history": graph_data}, f, cls=PandasEncoder)
            
            rankings.append(meta)
            time.sleep(1)

        except Exception as e:
            print(f"Failed {symbol}: {e}")

    rankings.sort(key=lambda x: x['score'], reverse=True)
    with open(os.path.join(DATA_DIR, "market_rankings.json"), 'w') as f:
        json.dump(rankings, f, cls=PandasEncoder, indent=2)

if __name__ == "__main__":
    process_market()
