import json
import os
import pandas as pd
import mplfinance as mpf
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# הגדרות נתיבים
DATA_DIR = "data"
CHARTS_DIR = "charts"
SITE_URL = "https://almog787.github.io/Stock-information-/"

# יצירת תיקיית גרפים אם לא קיימת
if not os.path.exists(CHARTS_DIR):
    os.makedirs(CHARTS_DIR)

def get_file_size(file_path):
    try:
        size_bytes = os.path.getsize(file_path)
        return f"{size_bytes / 1024:.1f} KB"
    except:
        return "0 KB"

def generate_data_audit():
    """סורק את קבצי ה-JSON ומפיק דוח סטטיסטי על המאגר"""
    audit_results = []
    if not os.path.exists(DATA_DIR): return []
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('_daily.json')]
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
                history = content.get('history', [])
                if not history: continue
                df = pd.DataFrame(history)
                audit_results.append({
                    "symbol": file.split('_')[0].upper(),
                    "records": len(history),
                    "start": str(df['Date'].min()).split(' ')[0],
                    "end": str(df['Date'].max()).split(' ')[0],
                    "size": get_file_size(file_path)
                })
        except:
            continue
    return audit_results

def create_pro_chart(json_path, symbol, score):
    """יצירת גרף נרות יפניים מקצועי"""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data['history'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # הצגת 120 ימי מסחר אחרונים (כחצי שנה)
        df_plot = df.tail(120).copy()

        # הגדרת אינדיקטורים להצגה - תיקון שמות ללא קו תחתי
        apds = []
        if 'SMA50' in df_plot.columns:
            apds.append(mpf.make_addplot(df_plot['SMA50'], color='#2962ff', width=1))
        
        if 'SMA200' in df_plot.columns:
            apds.append(mpf.make_addplot(df_plot['SMA200'], color='#ff6d00', width=1.5))

        # עיצוב בסגנון Dark Mode
        mc = mpf.make_marketcolors(up='#00ff41', down='#ff003c', edge='inherit', wick='inherit', volume='in')
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridstyle=':', rc={'font.size': 10})

        filename = f"{CHARTS_DIR}/{symbol.lower()}.png"
        
        # יצירת הגרף
        mpf.plot(df_plot, type='candle', style=s, addplot=apds, volume=True,
                 savefig=dict(fname=filename, dpi=100, bbox_inches='tight'), 
                 figsize=(12, 6), title=f"\n{symbol.upper()} Institutional Analysis")
        
        print(f"Chart created successfully for {symbol}")
    except Exception as e:
        print(f"Error creating chart for {symbol}: {e}")

def generate_readme():
    # טעינת הדירוגים
    rankings_path = os.path.join(DATA_DIR, "market_rankings.json")
    if not os.path.exists(rankings_path):
        print("Missing market_rankings.json")
        return
    
    try:
        with open(rankings_path, 'r') as f:
            rankings = json.load(f)
    except:
        return
    
    audit_data = generate_data_audit()
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # --- בניית ה-Markdown ---
    md = f"""# 🧠 Institutional AI Market Radar | מודיעין שוק מבוסס בינה מלאכותית

![System Status](https://img.shields.io/badge/System-Operational-emerald?style=for-the-badge&logo=github-actions&logoColor=white)
![Last Update](https://img.shields.io/badge/Last_Update-{now.replace(' ', '--').replace(':', ':-')}-blue?style=for-the-badge)

## 🚀 [Access Interactive Web Terminal | כניסה לטרמינל האינטראקטיבי]({SITE_URL})

---

### 🇺🇸 English Summary
Automated technical analysis on the Top 10 US stocks. The system monitors long-term trends and momentum to generate AI-driven trade signals.

### 🇮🇱 תקציר בעברית
ניתוח טכני אוטומטי ל-10 המניות הגדולות בארה"ב. המערכת מנטרת מגמות ארוכות טווח ומומנטום כדי להפיק איתותי מסחר מבוססי בינה מלאכותית.

---

## 🏆 Top Trade Opportunities | הזדמנויות מסחר מובילות
"""

    # יצירת גרפים ל-3 המניות המובילות
    for i in range(min(3, len(rankings))):
        r = rankings[i]
        symbol = r['symbol']
        json_path = os.path.join(DATA_DIR, f"{symbol.lower()}_daily.json")
        
        if os.path.exists(json_path):
            create_pro_chart(json_path, symbol, r['score'])
            signals = ", ".join(r['signals']) if r.get('signals') else "Stable Trend"
            md += f"### {i+1}. {symbol} (AI Score: {r['score']})\n"
            md += f"**Signals:** `{signals}`\n\n"
            md += f"![{symbol} Analysis](charts/{symbol.lower()}.png)\n\n"

    md += """
---

## 📋 Market Rankings Table | טבלת דירוג שוק
| Rank | Symbol | Price | Change | AI Score | Trend | RSI |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for i, r in enumerate(rankings):
        trend = "🟢" if r['change'] > 0 else "🔴"
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | **{r['score']}** | {r.get('signals', ['-'])[0]} | {r['rsi']:.1f} |\n"

    md += """
---

## 📘 Legend & Definitions | מקרא והסברים

| Term | מונח | Description | תיאור |
| :--- | :--- | :--- | :--- |
| **AI Score** | **ציון AI** | Overall rating (0-100). >70 is Bullish, <30 is Bearish. | דירוג כללי (0-100). מעל 70 חיובי, מתחת ל-30 שלילי. |
| **RSI** | **מדד חוזק** | Below 30 = Oversold (Buy), Above 70 = Overbought (Sell). | מתחת ל-30 = מכירת יתר, מעל 70 = קניית יתר. |
| **SMA 200** | **ממוצע 200** | The orange dashed line. Primary long-term trend indicator. | הקו המקווקו הכתום. אינדיקטור מגמה ארוך טווח. |

---

## 🗄️ Database Audit | ביקורת מאגר הנתונים
| Ticker | Records | Date Range | File Size | Status |
| :--- | :---: | :--- | :---: | :---: |
"""
    for a in sorted(audit_data, key=lambda x: x['records'], reverse=True):
        md += f"| {a['symbol']} | {a['records']} | `{a['start']}` to `{a['end']}` | {a['size']} | ✅ Sync |\n"

    md += f"\n---\n*Automated system powered by Python & GitHub Actions. Last Sync: {now}*"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("README generated successfully.")

if __name__ == "__main__":
    generate_readme()
