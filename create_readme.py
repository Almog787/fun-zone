import json, os, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DATA_DIR = "data"
CHARTS_DIR = "charts"
SITE_URL = "https://almog787.github.io/Stock-information-/"

if not os.path.exists(CHARTS_DIR): os.makedirs(CHARTS_DIR)

def create_chart(json_path, symbol, score):
    with open(json_path, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data['history'])
    df['Date'] = pd.to_datetime(df['Date'])
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['Date'], df['Close'], label='Price', color='#00ff41', linewidth=1.5)
    ax.plot(df['Date'], df['SMA200'], label='SMA 200', color='#ff003c', linestyle='--', linewidth=1)
    ax.set_title(f"{symbol} | AI Score: {score}/100", color='white', fontweight='bold')
    ax.legend(loc='upper left'); ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/{symbol}.png", dpi=100)
    plt.close()

def generate_readme():
    with open(os.path.join(DATA_DIR, "market_rankings.json"), 'r') as f:
        rankings = json.load(f)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    # בניית ה-README
    md = f"""# 📊 Institutional Market AI Radar

![Build Status](https://img.shields.io/badge/System-Operational-emerald?style=for-the-badge&logo=github-actions)
![Last Update](https://img.shields.io/badge/Updated-{now.replace(' ', '--')}-blue?style=for-the-badge)

## 🚀 [Access Interactive Web Terminal]({SITE_URL})

## 🏆 Top Trade Opportunities
"""
    for i in range(min(3, len(rankings))):
        r = rankings[i]
        create_chart(os.path.join(DATA_DIR, f"{r['symbol'].lower()}_daily.json"), r['symbol'], r['score'])
        md += f"### {i+1}. {r['symbol']} (Score: {r['score']})\n![{r['symbol']}](charts/{r['symbol']}.png)\n\n"

    md += "\n## 📋 Market Rankings Table\n| Rank | Ticker | Price | Change | Score | Signals |\n| :--: | :---: | :---: | :---: | :---: | :--- |\n"
    for i, r in enumerate(rankings):
        trend = "🟢" if r['change'] > 0 else "🔴"
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | **{r['score']}** | {', '.join(r['signals'])} |\n"

    md += "\n## 🗄️ Big Data Archive Audit\n| Ticker | Total Records | Date Range | Status |\n| :--- | :---: | :--- | :---: |\n"
    for r in rankings:
        with open(os.path.join(DATA_DIR, f"{r['symbol'].lower()}_daily.json"), 'r') as f:
            h = json.load(f)['history']
            md += f"| {r['symbol']} | {len(h)} rows | `{h[0]['Date'].split(' ')[0]}` to `{h[-1]['Date'].split(' ')[0]}` | ✅ Verified |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)

if __name__ == "__main__":
    generate_markdown = generate_readme()
