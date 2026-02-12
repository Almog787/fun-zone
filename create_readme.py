import json
import os
import pandas as pd
import mplfinance as mpf
from datetime import datetime

# הגדרות נתיבים
DATA_DIR = "data"
CHARTS_DIR = "charts"
SITE_URL = "https://almog787.github.io/Stock-information-/"

# יצירת תיקיית גרפים אם לא קיימת
if not os.path.exists(CHARTS_DIR):
    os.makedirs(CHARTS_DIR)

def create_pro_chart(json_path, symbol, score):
    """יצירת גרף נרות יפניים מקצועי לכל מניה"""
    if not os.path.exists(json_path):
        print(f"Warning: File not found {json_path}")
        return False
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data['history'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # הצגת 100 ימי מסחר אחרונים לתצוגה ברורה
        df_plot = df.tail(100) 

        # הגדרת אינדיקטורים SMA50 ו-SMA200 (מוודא שמות עמודות תקינים)
        apds = []
        if 'SMA50' in df_plot.columns:
            apds.append(mpf.make_addplot(df_plot['SMA50'], color='#2962ff', width=1))
        if 'SMA200' in df_plot.columns:
            apds.append(mpf.make_addplot(df_plot['SMA200'], color='#ff6d00', width=1.5))

        # עיצוב בסגנון Dark Mode
        mc = mpf.make_marketcolors(up='#00ff41', down='#ff003c', edge='inherit', wick='inherit', volume='in')
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridstyle=':', rc={'font.size': 10})

        filename = os.path.join(CHARTS_DIR, f"{symbol.lower()}.png")
        
        mpf.plot(df_plot, type='candle', style=s, addplot=apds, volume=True,
                 savefig=dict(fname=filename, dpi=100, bbox_inches='tight'), figsize=(12, 6))
        
        print(f"Chart created successfully for {symbol}")
        return True
    except Exception as e:
        print(f"Error creating chart for {symbol}: {e}")
        return False

def generate_readme():
    rankings_path = os.path.join(DATA_DIR, "market_rankings.json")
    if not os.path.exists(rankings_path):
        print("Error: market_rankings.json not found")
        return

    with open(rankings_path, 'r') as f:
        rankings = json.load(f)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # כותרת ה-README
    md = f"""# 🧠 Institutional AI Market Radar | מודיעין שוק מבוסס AI

![Last Update](https://img.shields.io/badge/Last_Update-{now.replace(' ', '--').replace(':', ':-')}-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/System-Operational-emerald?style=for-the-badge)

## 🚀 [Open Interactive Terminal | כניסה לטרמינל האינטראקטיבי]({SITE_URL})

---

## 📈 Market Analysis Gallery | גלריית ניתוח שוק
*גרפים עבור כל המניות במעקב (100 ימי מסחר אחרונים)*
\n
"""

    # לולאה על כל המניות ברשימה ליצירת גרפים ותצוגה ב-README
    for i, r in enumerate(rankings):
        symbol = r['symbol']
        json_filename = f"{symbol.lower()}_daily.json"
        json_path = os.path.join(DATA_DIR, json_filename)
        
        # יצירת הקובץ הפיזי (PNG)
        success = create_pro_chart(json_path, symbol, r['score'])
        
        if success:
            sig_en = ", ".join(r['signals']['en']) if isinstance(r['signals'], dict) else "N/A"
            sig_he = ", ".join(r['signals']['he']) if isinstance(r['signals'], dict) else "N/A"
            
            md += f"### {i+1}. {symbol} (AI Score: {r['score']})\n"
            md += f"**Signals:** `{sig_en}` | **איתותים:** `{sig_he}`\n\n"
            md += f"![{symbol} Chart](charts/{symbol.lower()}.png)\n\n"
            md += "---\n"

    # הוספת טבלת הדירוג המרוכזת
    md += """
## 📋 Rankings Summary Table | טבלת דירוג מרוכזת
| Rank | Symbol | Price | Change | AI Score | RSI |
| :--- | :--- | :---: | :---: | :---: | :---: |
"""
    for i, r in enumerate(rankings):
        trend = "🟢" if r['change'] > 0 else "🔴"
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | **{r['score']}** | {r['rsi']:.1f} |\n"

    md += """
---
## 📘 Legend & Definitions | מקרא והסברים

| Term | מונח | Description | תיאור |
| :--- | :--- | :--- | :--- |
| **AI Score** | **ציון AI** | Quality rating (0-100). | דירוג איכות כללי (0-100). |
| **SMA 200** | **ממוצע 200** | Orange line. Long-term trend. | קו כתום. מגמה ארוכת טווח. |
| **RSI** | **מדד חוזק** | Momentum indicator (30-70 range). | מדד מומנטום (טווח 30-70). |

---
## 🗄️ Database Audit | ביקורת נתונים
"""
    md += "| Ticker | Records | Time Range | Status |\n| :--- | :---: | :--- | :---: |\n"
    for r in rankings:
        try:
            file_path = os.path.join(DATA_DIR, f"{r['symbol'].lower()}_daily.json")
            with open(file_path, 'r') as f:
                h = json.load(f)['history']
                md += f"| {r['symbol']} | {len(h)} | `{h[0]['Date'].split(' ')[0]}` - `{h[-1]['Date'].split(' ')[0]}` | ✅ Verified |\n"
        except:
            continue

    md += f"\n\n---\n*Auto-generated by GitHub Actions using Python & yfinance. Last sync: {now}*"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("README.md and all charts generated successfully.")

if __name__ == "__main__":
    generate_readme()
