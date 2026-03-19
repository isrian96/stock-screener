import pandas as pd
import yfinance as yf
import time
from ta.momentum import RSIIndicator

# ==============================
# 📥 LOAD NSE STOCK LIST (NIFTY 200)
# ==============================

nse_url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"

print("📥 Downloading NIFTY 200 stock list...")
df = pd.read_csv(nse_url)

tickers = df['Symbol'].tolist()
tickers = [t.strip().upper() + ".NS" for t in tickers]

print(f"🔍 Total stocks loaded: {len(tickers)}")

# ==============================
# 📊 ANALYSIS
# ==============================

results = []

for i, ticker in enumerate(tickers):
    try:
        print(f"[{i+1}/{len(tickers)}] Checking {ticker}")

        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")

        if hist.empty or len(hist) < 50:
            continue

        close = hist['Close']
        volume = hist['Volume']

        # RSI
        rsi = RSIIndicator(close).rsi().iloc[-1]

        # Moving averages
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1] if len(close) > 200 else None

        price = close.iloc[-1]

        # Volume breakout
        avg_vol = volume.tail(20).mean()
        vol_today = volume.iloc[-1]
        vol_ratio = vol_today / avg_vol if avg_vol != 0 else 0

        # ==============================
        # 📈 SMART SIGNAL LOGIC (UPGRADED)
        # ==============================

        score = 0

        # RSI condition
        if 30 <= rsi <= 45:
            score += 1

        # Trend condition
        if price > ma50:
            score += 1

        # Volume breakout
        if vol_ratio > 1.5:
            score += 1

        # Strong trend bonus
        if ma200 and price > ma200:
            score += 1

        # ------------------------------
        # 🧠 STABILIZATION DETECTION
        # ------------------------------
        recent_closes = close.tail(5)
        price_range = recent_closes.max() - recent_closes.min()
        avg_price = recent_closes.mean()

        stabilized = False
        if avg_price > 0:
            if (price_range / avg_price) < 0.01:
                stabilized = True

        # ------------------------------
        # 🎯 FINAL SIGNAL
        # ------------------------------
        if score >= 3 and stabilized and rsi >= 30:
            signal = "🟢 BUY"

        elif rsi < 30:
            signal = "🟡 WATCH"

        elif rsi > 60:
            signal = "🔴 AVOID"

        else:
            signal = "HOLD"

        # Save result
        results.append({
            "Ticker": ticker,
            "Price": round(price, 2),
            "RSI": round(rsi, 2),
            "MA50": round(ma50, 2),
            "Volume Ratio": round(vol_ratio, 2),
            "Score": score,
            "Signal": signal
        })

        time.sleep(0.2)  # prevent API throttling

    except Exception as e:
        print(f"❌ Error: {ticker}")

# ==============================
# 📄 SAVE RESULTS
# ==============================

result_df = pd.DataFrame(results)

# Sort best first
result_df = result_df.sort_values(by=["Signal", "Score"], ascending=[True, False])

# Filters
buy_df = result_df[result_df["Signal"] == "🟢 BUY"]
watch_df = result_df[result_df["Signal"] == "🟡 WATCH"]

# Save to Excel
output_file = "nse_stock_screener.xlsx"

with pd.ExcelWriter(output_file) as writer:
    result_df.to_excel(writer, sheet_name="All Stocks", index=False)
    buy_df.to_excel(writer, sheet_name="BUY Signals", index=False)
    watch_df.to_excel(writer, sheet_name="WATCH List", index=False)

print("\n✅ Done!")
print(f"📊 Results saved to {output_file}")

# ==============================
# 📌 SUMMARY
# ==============================

print("\n📈 Signal Summary:")
print(result_df["Signal"].value_counts())

print("\n🔥 Top 10 Stocks:")
print(result_df.head(10)[["Ticker", "Price", "RSI", "Volume Ratio", "Score", "Signal"]])
