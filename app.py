import streamlit as st
import pandas as pd
import yfinance as yf
import time
from ta.momentum import RSIIndicator

st.set_page_config(page_title="NSE Screener", layout="wide")

st.title("📊 NIFTY 200 Smart Stock Screener")

# -----------------------------
# LOAD NSE STOCK LIST
# -----------------------------
@st.cache_data
def load_nifty200():
    url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
    df = pd.read_csv(url)
    tickers = df["Symbol"].tolist()
    tickers = [t.strip().upper() + ".NS" for t in tickers]
    return tickers

tickers = load_nifty200()

st.write(f"Total Stocks: {len(tickers)}")

# -----------------------------
# MAIN BUTTON
# -----------------------------
if st.button("🚀 Run Scanner"):

    results = []
    progress = st.progress(0)

    with st.spinner("Scanning stocks... please wait ⏳"):

        for i, ticker in enumerate(tickers):

            try:
                data = yf.Ticker(ticker).history(period="6mo")

                if data.empty or len(data) < 50:
                    continue

                close = data["Close"]
                volume = data["Volume"]

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

                # -----------------------------
                # SCORE
                # -----------------------------
                score = 0

                if 30 <= rsi <= 45:
                    score += 1

                if price > ma50:
                    score += 1

                if vol_ratio > 1.5:
                    score += 1

                if ma200 and price > ma200:
                    score += 1

                # -----------------------------
                # STABILIZATION
                # -----------------------------
                recent = close.tail(5)
                price_range = recent.max() - recent.min()
                avg_price = recent.mean()

                stabilized = False
                if avg_price > 0 and (price_range / avg_price) < 0.01:
                    stabilized = True

                # -----------------------------
                # SIGNAL
                # -----------------------------
                if score >= 3 and stabilized and rsi >= 30:
                    signal = "🟢 BUY"

                elif rsi < 30:
                    signal = "🟡 WATCH"

                elif rsi > 60:
                    signal = "🔴 AVOID"

                else:
                    signal = "HOLD"

                results.append({
                    "Ticker": ticker,
                    "Price": round(price, 2),
                    "RSI": round(rsi, 2),
                    "MA50": round(ma50, 2),
                    "Volume Ratio": round(vol_ratio, 2),
                    "Score": score,
                    "Signal": signal
                })

                time.sleep(0.1)  # avoid API block

            except:
                continue

            progress.progress((i + 1) / len(tickers))

    # -----------------------------
    # RESULTS
    # -----------------------------
    if len(results) == 0:
        st.error("No data fetched ❌")
    else:
        df = pd.DataFrame(results)

        # Sort: BUY first
        df = df.sort_values(by=["Signal", "Score"], ascending=[True, False])

        st.success("✅ Scan Complete!")

        # FULL TABLE
        st.subheader("📊 All Stocks")
        st.dataframe(df, use_container_width=True)

        # BUY
        st.subheader("🟢 BUY Signals")
        buy_df = df[df["Signal"] == "🟢 BUY"]
        st.dataframe(buy_df, use_container_width=True)

        # WATCH
        st.subheader("🟡 WATCH List")
        watch_df = df[df["Signal"] == "🟡 WATCH"]
        st.dataframe(watch_df, use_container_width=True)

        # DOWNLOAD
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results",
            data=csv,
            file_name="nifty200_screener.csv",
            mime="text/csv"
        )
