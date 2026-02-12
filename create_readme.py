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

def get_file_size(file_path):
    size_bytes = os.path.getsize(file_path)
    return f"{size_bytes / 1024:.1f} KB"

def generate_data_audit():
    """סורק את קבצי ה-JSON ומפיק דוח סטטיסטי על המאגר"""
    audit_results = []
    if not os.path.exists(DATA_DIR): return []
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('_daily.json')]
    for file in files:
        file_path = os.path.join(DATA_DIR, file)
        with open(file_path, 'r') as f:
            content = json.load(f)
            history = content.get('history', [])
            if not history: continue
            df = pd.DataFrame(history)
            audit_results.append({
                "symbol": file.split('_')[0].upper(),
                "records": len(history),
                "start": df['Date'].min().split(' ')[0],
                "end": df['Date'].max().split(' ')[0],
                "size": get_file_size(file_path)
            })
    return audit_results

def create_pro_chart(json_path, symbol, score):
    """יצירת גרף נרות יפניים מקצועי"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['history'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df = df.tail(120) # הצגת 4 חודשים אחרונים

    # הגדרת אינדיקטורים להצגה על הגרף
    apds = [
        mpf.make_addplot(df['SMA_50'], color='#2962ff', width=1),
        mpf.make_addplot(df['SMA_200'], color='#ff6d00', width=1.5),
    ]

    # עיצוב בסגנון Dark Mode מקצועי
    mc = mpf.make_marketcolors(up='#00ff41', down='#ff003c', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridstyle=':', rc={'font.size': 10})

    filename = f"{CHARTS_DIR}/{symbol}.png"
    mpf.plot(df, type='candle', style=s, addplot=apds, volume=True,
             savefig=dict(fname=filename, dpi=100, bbox_inches='tight'), figsize=(12, 6))

def generate_readme():
    # טעינת הדירוגים
    rankings_path = os.path.join(DATA_DIR, "market_rankings.json")
    if not os.path.exists(rankings_path):
        print("Missing market_rankings.json")
        return
    with open(rankings_path, 'r') as f:
        rankings = json.load(f)
    
    audit_data = generate_data_audit()
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # --- התחלת כתיבת ה-Markdown ---
    md = f"""# 🧠 Institutional AI Market Radar | מודיעין שוק מבוסס בינה מלאכותית

![System Status](https://img.shields.io/badge/System-Operational-emerald?style=for-the-badge&logo=github-actions&logoColor=white)
![Last Update](https://img.shields.io/badge/Last_Update-{now.replace(' ', '--').replace(':', ':-')}-blue?style=for-the-badge)
![Language](https://img.shields.io/badge/Language-Bilingual-purple?style=for-the-badge)

## 🚀 [Access Interactive Web Terminal | כניסה לטרמינל האינטראקטיבי]({SITE_URL})

---

### 🇺🇸 English Summary
This system performs automated technical analysis on the Top 10 US stocks. Using institutional-grade libraries, it calculates momentum, trend strength, and volatility to provide an objective **AI Quality Score**.

### 🇮🇱 תקציר בעברית
מערכת זו מבצעת ניתוח טכני אוטומטי ל-10 המניות הגדולות ביותר בארה"ב. באמצעות שימוש בספריות מתקדמות, המערכת מחשבת מומנטום, חוזק מגמה ותנודתיות כדי להפיק **ציון איכות AI** אובייקטיבי.

---

## 🏆 Top Trade Opportunities | הזדמנויות מסחר מובילות
"""

    # יצירת גרפים ל-3 המניות המובילות
    for i in range(min(3, len(rankings))):
        r = rankings[i]
        json_path = os.path.join(DATA_DIR, f"{r['symbol'].lower()}_daily.json")
        if os.path.exists(json_path):
            create_pro_chart(json_path, r['symbol'], r['score'])
            signals = ", ".join(r['signals']) if r['signals'] else "Stable Trend"
            md += f"### {i+1}. {r['symbol']} (AI Score: {r['score']})\n"
            md += f"**Signals:** `{signals}`\n\n"
            md += f"![{r['symbol']} Analysis](charts/{r['symbol']}.png)\n\n"

    md += """
---

## 📋 Market Intelligence Table | טבלת דירוג שוק
| Rank | Symbol | Price | Change | AI Score | Trend (ADX) | RSI |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for i, r in enumerate(rankings):
        trend = "🟢" if r['change'] > 0 else "🔴"
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | **{r['score']}** | {r['adx']:.0f} | {r['rsi']:.1f} |\n"

    md += """
---

## 📘 Legend & Definitions | מקרא והסברים

| Term | מונח | Description | תיאור |
| :--- | :--- | :--- | :--- |
| **AI Score** | **ציון AI** | Overall rating (0-100) based on 15+ indicators. | דירוג כללי (0-100) המבוסס על מעל 15 אינדיקטורים. |
| **RSI** | **מדד חוזק** | Momentum indicator. Below 30 = Oversold, Above 70 = Overbought. | מדד מומנטום. מתחת ל-30 = מכירת יתר, מעל 70 = קניית יתר. |
| **ADX** | **עוצמת מגמה** | Measures trend strength. >25 indicates a strong trend. | מודד את עוצמת המגמה. מעל 25 מעיד על מגמה חזקה. |
| **SMA 200** | **ממוצע 200** | Long-term trend baseline (Golden Line). | קו בסיס למגמה ארוכת טווח (קו הזהב). |

---

## 🗄️ Database Audit | ביקורת מאגר הנתונים
**Transparency Report: Current state of local JSON storage.**

| Ticker | Records | Date Range | File Size | Status |
| :--- | :---: | :--- | :---: | :---: |
"""
    for a in sorted(audit_data, key=lambda x: x['records'], reverse=True):
        md += f"| {a['symbol']} | {a['records']} | `{a['start']}` to `{a['end']}` | {a['size']} | ✅ Sync | \n"

    md += f"""
---
*Automated system powered by Python, GitHub Actions, and yfinance. Generated at: {now}*
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Bilingual README generated successfully.")

if __name__ == "__main__":
    generate_readme()
