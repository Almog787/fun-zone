import yfinance as yf
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

def calculate_indicators(df):
    # חישוב RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ממוצעים נעים
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # ניקוי ערכי NaN שנוצרים בגלל החישובים (JSON לא אוהב NaN)
    df = df.fillna(0)
    return df

def update_database():
    file_name = 'nvda_full_history.json'
    ticker = "NVDA"
    stock = yf.Ticker(ticker)

    # 1. השגת נתונים
    if os.path.exists(file_name):
        # מוריד חודש אחרון לעדכון
        new_data = stock.history(period="1mo", interval="1h")
        with open(file_name, 'r') as f:
            old_db = json.load(f)
            df_old = pd.DataFrame(old_db['history'])
            df_old['Datetime'] = pd.to_datetime(df_old['Datetime'])
    else:
        # פעם ראשונה - מוריד הכל
        new_data = stock.history(period="max", interval="1d")
        df_old = pd.DataFrame()

    # 2. מיזוג נתונים
    new_data.reset_index(inplace=True)
    # טיפול בעמודת התאריך (לוודא אחידות בין אינטרוול יומי לשעתי)
    date_col = 'Date' if 'Date' in new_data.columns else 'Datetime'
    new_data['Datetime'] = pd.to_datetime(new_data[date_col])
    
    combined_df = pd.concat([df_old, new_data]).drop_duplicates(subset=['Datetime'], keep='last')
    combined_df = combined_df.sort_values('Datetime')

    # 3. חישוב אינדיקטורים
    combined_df = calculate_indicators(combined_df)
    
    # 4. הכנת הנתונים לשמירה (המרה לטיפוסים שניתנים לסריאליזציה)
    latest = combined_df.iloc[-1]
    
    # חיתוך 2000 השורות האחרונות
    df_to_save = combined_df.tail(2000).copy()
    
    # המרת התאריכים למחרוזות (Strings) - פותר את שגיאת ה-Timestamp
    df_to_save['Datetime'] = df_to_save['Datetime'].dt.strftime('%Y-%m-%d %H:%M')
    
    # המרת כל הטבלה לרשימת מילונים תוך הפיכת מספרי NumPy למספרי פייתון רגילים
    history_records = df_to_save.to_dict(orient='records')
    
    output = {
        "metadata": {
            "symbol": ticker,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "current_price": float(latest['Close']), # המרה ל-float רגיל
            "rsi": float(latest['RSI']),
            "sma50": float(latest['SMA50']),
            "sma200": float(latest['SMA200']),
            "recommendation": str(stock.info.get("recommendationKey", "N/A"))
        },
        "history": history_records
    }

    # 5. שמירה סופית
    with open(file_name, 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    try:
        update_database()
        print("Successfully updated NVDA history database.")
    except Exception as e:
        print(f"Error occurred: {e}")
        exit(1)
