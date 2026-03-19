import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

st.title("📊 NSE Stock Screener (ALL Stocks + Signals)")

# -----------------------------
# LOAD NSE STOCK LIST
# -----------------------------
@st.cache_data
def load_nse_stocks():
    try:
        df = pd.read_csv("https://archives.nseindia.com/content/equities/EQUITY_L.csv")
        symbols = df["SYMBOL"].tolist()
        tickers = [s + ".NS" for s in symbols]
        return tickers
    except:
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

tickers = load_nse_stocks()

# -----------------------------
# RSI FUNCTION
# -----------------------------
def calculate_rsi(data, window=14):
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# -----------------------------
# STABILIZATION DETECTION
# -----------------------------
def detect_stabilization(df):
    closes = df["Close"].tail(10)

    price_range = closes.max() - closes.min()
    avg_price = closes.mean()

    if avg_price == 0:
        return False

    range_pct = price_range / avg_price

    lows = df["Low"].tail(5).values
    higher_lows = all(x <= y for x, y in zip(lows, lows[1:]))

    return range_pct < 0.01 or higher_lows

# -----------------------------
# SIGNAL LOGIC
# -----------------------------
def generate_signal(rsi, volume, df):
    stabilized = detect_stabilization(df)

    last_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]

    price_up = last_close > prev_close

    if 30 <= rsi <= 45 and volume > 1.5 and stabilized and price_up:
        return "🟢 BUY"
    elif rsi < 30:
        return "🟡 WATCH"
    else:
        return "🔴 AVOID"

# -----------------------------
# SCAN FUNCTION (BATCHED)
# -----------------------------
def run_scan(tickers, batch_size=100):
    results = []

    progress = st.progress(0)
    total = len(tickers)

    for i in range(0, total, batch_size):
        batch = tickers[i:i+batch_size]

        for ticker in batch:
            try:
                df = yf.download(ticker, period="5d", interval="5m", progress=False)

                if df.empty or len(df) < 20:
                    continue

                df["RSI"] = calculate_rsi(df)

                price = df["Close"].iloc[-1]
                rsi = df["RSI"].iloc[-1]

                avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
                current_vol = df["Volume"].iloc[-1]

                volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1

                score = 0
                if 30 <= rsi <= 45:
                    score += 1
                if volume_ratio > 1.5:
                    score += 1
                if price > df["Close"].rolling(20).mean().iloc[-1]:
                    score += 1

                # 🔥 Signal added here
                signal = generate_signal(rsi, volume_ratio, df)

                results.append({
                    "Ticker": ticker,
                    "Price": round(price, 2),
                    "RSI": round(rsi, 2),
                    "Volume": round(volume_ratio, 2),
                    "Score": score,
                    "Signal": signal
                })

            except:
                continue

        # Progress update
        progress.progress(min((i + batch_size) / total, 1.0))
        time.sleep(1)

    return results

# -----------------------------
# UI
# -----------------------------
st.write(f"Total Stocks: {len(tickers)}")

if st.button("Run Full Market Scan 🚀"):

    with st.spinner("Scanning entire NSE (this takes time)..."):
        results = run_scan(tickers)

    if len(results) == 0:
        st.error("No data fetched.")
    else:
        df = pd.DataFrame(results)

        # Sort: BUY first, then high score
        df = df.sort_values(by=["Signal", "Score"], ascending=[True, False])

        st.success("Scan Complete ✅")

        # Top 50
        st.subheader("🔥 Top 50 Stocks")
        st.dataframe(df.head(50))

        # BUY signals
        st.subheader("🟢 BUY Signals")
        buy_df = df[df["Signal"] == "🟢 BUY"]

        if len(buy_df) > 0:
            st.dataframe(buy_df.head(20))
        else:
            st.write("No BUY signals right now.")

        # Optional: Watchlist
        st.subheader("🟡 WATCH (Potential Reversal)")
        watch_df = df[df["Signal"] == "🟡 WATCH"]

        st.dataframe(watch_df.head(20))