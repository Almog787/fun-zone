import yfinance as yf
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

# מקודד מיוחד למניעת שגיאות סריאליזציה של JSON
class PandasEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M')
        if isinstance(obj, (np.int64, np.int32, np.integer)):
            return int(obj)
        if isinstance(obj, (np.float64, np.float32, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(PandasEncoder, self).default(obj)

def calculate_indicators(df):
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ממוצעים נעים
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # ניקוי ערכים לא חוקיים ל-JSON
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    return df

def update_database():
    file_name = 'nvda_full_history.json'
    ticker = "NVDA"
    stock = yf.Ticker(ticker)

    # 1. השגת נתונים
    if os.path.exists(file_name):
        print("Updating existing database...")
        new_data = stock.history(period="1mo", interval="1h")
        with open(file_name, 'r') as f:
            old_db = json.load(f)
            df_old = pd.DataFrame(old_db['history'])
            df_old['Datetime'] = pd.to_datetime(df_old['Datetime'])
    else:
        print("Downloading full history (Max)...")
        new_data = stock.history(period="max", interval="1d")
        df_old = pd.DataFrame()

    # 2. עיבוד ומיזוג
    new_data.reset_index(inplace=True)
    date_col = 'Date' if 'Date' in new_data.columns else 'Datetime'
    new_data['Datetime'] = pd.to_datetime(new_data[date_col])
    
    combined_df = pd.concat([df_old, new_data]).drop_duplicates(subset=['Datetime'], keep='last')
    combined_df = combined_df.sort_values('Datetime')

    # 3. חישוב אינדיקטורים
    combined_df = calculate_indicators(combined_df)
    
    # 4. הכנת פלט
    latest = combined_df.iloc[-1]
    df_to_save = combined_df.tail(2000).copy() # שמירה על גודל קובץ סביר
    
    output = {
        "metadata": {
            "symbol": ticker,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "current_price": latest['Close'],
            "rsi": latest['RSI'],
            "sma50": latest['SMA50'],
            "sma200": latest['SMA200'],
            "recommendation": str(stock.info.get("recommendationKey", "N/A"))
        },
        "history": df_to_save.to_dict(orient='records')
    }

    with open(file_name, 'w') as f:
        json.dump(output, f, indent=2, cls=PandasEncoder)

if __name__ == "__main__":
    update_database()
    print("Database updated successfully.")
