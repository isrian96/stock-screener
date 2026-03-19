import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.title("📊 NSE Stock Screener (Smart Signals)")

# -----------------------------
# STOCK LIST
# -----------------------------
tickers = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS",
    "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDPETRO.NS", "COFORGE.NS", "CONCOR.NS"
]

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

    # Condition 1: Range is tight (sideways)
    price_range = closes.max() - closes.min()
    avg_price = closes.mean()

    if avg_price == 0:
        return False

    range_pct = price_range / avg_price

    # Condition 2: Higher lows
    lows = df["Low"].tail(5).values
    higher_lows = all(x <= y for x, y in zip(lows, lows[1:]))

    if range_pct < 0.01 or higher_lows:
        return True

    return False

# -----------------------------
# SIGNAL LOGIC
# -----------------------------
def generate_signal(rsi, volume, df):
    stabilized = detect_stabilization(df)

    last_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]

    # Price moving up
    price_up = last_close > prev_close

    if 30 <= rsi <= 45 and volume > 1.5 and stabilized and price_up:
        return "🟢 BUY"
    elif rsi < 30:
        return "🟡 WATCH"
    else:
        return "🔴 AVOID"

# -----------------------------
# SCAN FUNCTION
# -----------------------------
def run_scan():
    results = []

    for ticker in tickers:
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

            # Score
            score = 0
            if 30 <= rsi <= 45:
                score += 1
            if volume_ratio > 1.5:
                score += 1
            if price > df["Close"].rolling(20).mean().iloc[-1]:
                score += 1

            # Signal
            signal = generate_signal(rsi, volume_ratio, df)

            results.append({
                "Ticker": ticker,
                "Price": round(price, 2),
                "RSI": round(rsi, 2),
                "Volume": round(volume_ratio, 2),
                "Score": score,
                "Signal": signal
            })

        except Exception as e:
            st.warning(f"{ticker} error: {e}")
            continue

    return results

# -----------------------------
# UI
# -----------------------------
if st.button("Run Scan 🚀"):

    with st.spinner("Scanning..."):
        results = run_scan()

    if len(results) == 0:
        st.error("No data fetched.")
    else:
        df = pd.DataFrame(results)
        df = df.sort_values(by="Score", ascending=False)

        st.success("Scan Complete ✅")
        st.dataframe(df)

        # Show best signals
        st.subheader("🔥 BUY Signals")

        buy_df = df[df["Signal"] == "🟢 BUY"]

        if len(buy_df) > 0:
            st.dataframe(buy_df)
        else:
            st.write("No BUY signals right now.")