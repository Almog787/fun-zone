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
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    df['STD'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['Close'].rolling(window=20).mean() + (df['STD'] * 2)
    df['BB_Lower'] = df['Close'].rolling(window=20).mean() - (df['STD'] * 2)
    
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = true_range.rolling(14).mean()

    return df.fillna(0)

def analyze_stock_score(row):
    score = 50
    signals = []

    if row['Close'] > row['SMA200']:
        score += 20
        signals.append("📈 Uptrend")
    else:
        score -= 20
        signals.append("📉 Downtrend")

    if row['SMA50'] > row['SMA200']: score += 10
    
    if row['RSI'] < 30:
        score += 15
        signals.append("🟢 Oversold")
    elif row['RSI'] > 70:
        score -= 15
        signals.append("🔴 Overbought")

    if row['Close'] < row['BB_Lower']:
        score += 10
        signals.append("🛒 Dip Buy Zone")
    
    return max(0, min(100, score)), signals

def save_json(data, filename):
    with open(os.path.join(DATA_DIR, filename), 'w') as f:
        json.dump(data, f, cls=PandasEncoder, indent=0)

# --- פונקציה חדשה ליצירת README ---
def generate_readme(rankings):
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    md = f"""# 📊 Market AI Radar
**Automated Financial Intelligence System**
\n> 🔄 **Last Updated:** {now}
\n## 🏆 Top Opportunities (Live Analysis)
| Rank | Ticker | Price | Change | AI Score | Signal |
| :--: | :----: | :---: | :----: | :------: | :----- |
"""
    
    for i, r in enumerate(rankings):
        # עיצוב אימוג'ים לפי נתונים
        trend = "🟢" if r['change'] > 0 else "🔴"
        score_icon = "🚀" if r['score'] >= 80 else ("⚠️" if r['score'] <= 30 else "⚖️")
        signals_str = ", ".join(r['signals']) if r['signals'] else "Stable"
        
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | {score_icon} **{r['score']}** | {signals_str} |\n"

    md += "\n\n---\n*This data is generated automatically by GitHub Actions using yfinance & Python analysis.*"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("README.md updated successfully.")

def process_market():
    rankings = []

    for symbol in TICKERS:
        print(f"Analyzing {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="max", interval="1d")
            df = calculate_technical_analysis(df)
            df.reset_index(inplace=True)
            
            graph_data = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'SMA200', 'SMA50']].tail(2000).to_dict(orient='records')
            
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

            save_json({"meta": meta, "history": graph_data}, f"{symbol}_daily.json")
            rankings.append(meta)
            time.sleep(1)

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")

    rankings.sort(key=lambda x: x['score'], reverse=True)
    
    with open(os.path.join(DATA_DIR, "market_rankings.json"), 'w') as f:
        json.dump(rankings, f, cls=PandasEncoder, indent=2)
        
    # קריאה לפונקציה שמעדכנת את ה-README
    generate_readme(rankings)

if __name__ == "__main__":
    process_market()
