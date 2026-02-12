import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DATA_DIR = "data"
CHARTS_DIR = "charts"
SITE_URL = "https://almog787.github.io/Stock-information-/" # וודא שזה הקישור הנכון

if not os.path.exists(CHARTS_DIR): os.makedirs(CHARTS_DIR)

def create_chart_image(json_path, symbol, score, signal):
    # טעינת נתונים מה-JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['history'])
    df['Date'] = pd.to_datetime(df['Date'])
    
    # עיצוב הגרף (Dark Theme)
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # ציור קווים
    ax.plot(df['Date'], df['Close'], label='Price', color='#00ff41', linewidth=1.5)
    ax.plot(df['Date'], df['SMA200'], label='SMA 200', color='#ff003c', linestyle='--', linewidth=1)
    
    # כותרת ועיצוב צירים
    ax.set_title(f"{symbol} | Score: {score}/100 | {signal}", fontsize=14, color='white', fontweight='bold')
    ax.grid(True, color='#333333', linestyle='-', linewidth=0.5)
    ax.legend(loc='upper left', frameon=False)
    
    # הסרת מסגרות
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#444')
    ax.spines['left'].set_color('#444')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    
    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/{symbol}.png", dpi=100)
    plt.close()
    print(f"Chart created for {symbol}")

def generate_markdown():
    # קריאת קובץ הדירוגים
    with open(os.path.join(DATA_DIR, "market_rankings.json"), 'r') as f:
        rankings = json.load(f)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    md = f"""# 📊 Market AI Radar
**Automated Financial Intelligence System**

## 🚀 [Click Here to Open Live Dashboard]({SITE_URL})

> 🔄 **Last Updated:** {now}

## 🏆 Top 3 Opportunities (Charts)
"""
    
    # יצירת גרפים רק ל-3 המניות המובילות
    for i in range(3):
        if i < len(rankings):
            r = rankings[i]
            # יצירת התמונה בפועל
            json_path = os.path.join(DATA_DIR, f"{r['symbol']}_daily.json")
            if os.path.exists(json_path):
                create_chart_image(json_path, r['symbol'], r['score'], r['signals'][0] if r['signals'] else "Neutral")
                
                md += f"### {i+1}. {r['symbol']} (Score: {r['score']})\n"
                md += f"![{r['symbol']} Chart](charts/{r['symbol']}.png)\n\n"

    md += """## 📋 Full Market Rankings
| Rank | Ticker | Price | Change | AI Score | Signal |
| :--: | :----: | :---: | :----: | :------: | :----- |
"""
    
    for i, r in enumerate(rankings):
        trend = "🟢" if r['change'] > 0 else "🔴"
        score_icon = "🚀" if r['score'] >= 80 else ("⚠️" if r['score'] <= 30 else "⚖️")
        signals_str = ", ".join(r['signals']) if r['signals'] else "Stable"
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | {score_icon} **{r['score']}** | {signals_str} |\n"

    md += f"\n\n---\n*Data generated automatically by GitHub Actions | [View Live Site]({SITE_URL})*"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("README.md updated.")

if __name__ == "__main__":
    generate_markdown()
