import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

def calculate_signal_score(current_price, sma_200, cape_ratio, analyst_upside):
    sma_score = max(0, 100 - abs(current_price - sma_200) / sma_200 * 100)
    cape_score = max(0, 100 - cape_ratio * 2)
    upside_score = min(100, analyst_upside)
    return round((sma_score * 0.4 + cape_score * 0.3 + upside_score * 0.3), 2)

st.title("📈 ASX Stock Signal Score Dashboard")
ticker_input = st.text_input("Enter ASX Stock Ticker Symbol (e.g., WTC.AX, NXT.AX):", "WTC.AX")

if ticker_input:
    ticker = yf.Ticker(ticker_input)
    hist = ticker.history(period="6mo")
    info = ticker.info

    if not hist.empty:
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_100'] = hist['Close'].rolling(window=100).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()

        current_price = hist['Close'][-1]
        sma_50 = hist['SMA_50'][-1]
        sma_100 = hist['SMA_100'][-1]
        sma_200 = hist['SMA_200'][-1]

        cape_ratio = info.get('trailingPE', 25.0)
        target_price = info.get('targetMeanPrice', current_price)
        analyst_upside = max(0, (target_price - current_price) / current_price * 100)

        signal_score = calculate_signal_score(current_price, sma_200, cape_ratio, analyst_upside)

        st.metric("Current Price", f"${current_price:.2f}")
        st.metric("SMA 50", f"${sma_50:.2f}")
        st.metric("SMA 100", f"${sma_100:.2f}")
        st.metric("SMA 200", f"${sma_200:.2f}")
        st.metric("CAPE Ratio (PE Proxy)", f"{cape_ratio:.2f}")
        st.metric("Analyst Upside", f"{analyst_upside:.2f}%")
        st.metric("Signal Score", f"{signal_score}/100")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_100'], mode='lines', name='SMA 100'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], mode='lines', name='SMA 200'))

        fig.update_layout(title=f"{ticker_input.upper()} Price & SMA Chart",
                          xaxis_title="Date",
                          yaxis_title="Price (AUD)",
                          legend_title="Legend",
                          template="plotly_white")

        st.plotly_chart(fig, use_container_width=True)

        if current_price <= sma_200 * 1.05:
            st.success("✅ This stock is near its 200-day SMA. Potential entry opportunity!")
        elif signal_score > 70:
            st.info("📊 Strong signal score. Consider further analysis.")
        else:
            st.warning("⚠️ Signal score is moderate. Review fundamentals and technicals.")
    else:
        st.error("No historical data found for this ticker.")
