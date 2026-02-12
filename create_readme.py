import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

DATA_DIR = "data"
CHARTS_DIR = "charts"
SITE_URL = "https://almog787.github.io/Stock-information-/"

if not os.path.exists(CHARTS_DIR): os.makedirs(CHARTS_DIR)

def create_chart_image(json_path, symbol, score, signal):
    with open(json_path, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data['history'])
    df['Date'] = pd.to_datetime(df['Date'])
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['Date'], df['Close'], label='Price', color='#00ff41', linewidth=1.5)
    ax.plot(df['Date'], df['SMA200'], label='SMA 200', color='#ff003c', linestyle='--', linewidth=1)
    ax.set_title(f"{symbol} | Score: {score}/100 | {signal}", fontsize=14, color='white', fontweight='bold')
    ax.grid(True, color='#333333', linestyle='-', linewidth=0.5)
    ax.legend(loc='upper left', frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.tight_layout()
    plt.savefig(f"{CHARTS_DIR}/{symbol}.png", dpi=100)
    plt.close()

def generate_markdown():
    rankings_path = os.path.join(DATA_DIR, "market_rankings.json")
    if not os.path.exists(rankings_path):
        print("Error: market_rankings.json not found. Run collect_data.py first.")
        return

    with open(rankings_path, 'r') as f:
        rankings = json.load(f)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    md = f"# 📊 Market AI Radar\n**Automated Financial Intelligence System**\n\n## 🚀 [Click Here to Open Live Dashboard]({SITE_URL})\n\n> 🔄 **Last Updated:** {now}\n\n## 🏆 Top 3 Opportunities (Charts)\n"
    
    for i in range(3):
        if i < len(rankings):
            r = rankings[i]
            json_path = os.path.join(DATA_DIR, f"{r['symbol']}_daily.json")
            if os.path.exists(json_path):
                create_chart_image(json_path, r['symbol'], r['score'], r['signals'][0] if r['signals'] else "Stable")
                md += f"### {i+1}. {r['symbol']} (Score: {r['score']})\n![{r['symbol']} Chart](charts/{r['symbol']}.png)\n\n"

    md += "## 📋 Full Market Rankings\n| Rank | Ticker | Price | Change | AI Score | Signal |\n| :--: | :----: | :---: | :----: | :------: | :----- |\n"
    for i, r in enumerate(rankings):
        trend = "🟢" if r['change'] > 0 else "🔴"
        score_icon = "🚀" if r['score'] >= 80 else ("⚠️" if r['score'] <= 30 else "⚖️")
        md += f"| {i+1} | **{r['symbol']}** | ${r['price']:.2f} | {trend} {r['change']:.2f}% | {score_icon} **{r['score']}** | {', '.join(r['signals']) if r['signals'] else 'Stable'} |\n"

    md += f"\n\n---\n*Data generated automatically by GitHub Actions | [View Live Site]({SITE_URL})*"
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(md)
    print("Step 2: README & Charts Generation Finished.")

if __name__ == "__main__":
    generate_markdown()
