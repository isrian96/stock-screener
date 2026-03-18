import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator

st.title("📊 NSE Stock Screener")

if st.button("Run Scan"):

    url = "https://archives.nseindia.com/content/indices/ind_nifty200list.csv"
    df = pd.read_csv(url)

    tickers = [t + ".NS" for t in df['Symbol'].tolist()]
    results = []

    for ticker in tickers[:100]:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")

            if hist.empty or len(hist) < 50:
                continue

            close = hist['Close']
            volume = hist['Volume']

            rsi = RSIIndicator(close).rsi().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            price = close.iloc[-1]

            vol_ratio = volume.iloc[-1] / volume.tail(20).mean()

            score = 0
            if rsi < 40: score += 1
            if price > ma50: score += 1
            if vol_ratio > 1.5: score += 2

            if score >= 3:
                results.append({
                    "Ticker": ticker,
                    "Price": round(price, 2),
                    "RSI": round(rsi, 2),
                    "Volume": round(vol_ratio, 2),
                    "Score": score
                })

        except:
            continue

    df_result = pd.DataFrame(results).sort_values(by="Score", ascending=False)

    st.success("Scan complete!")
    st.dataframe(df_result)
