import streamlit as st
from data_fetching import fetch_sector_pe_map, fetch_broker_rating_asx
from signal_scoring import calculate_signal_score
from technical_indicators import compute_indicators
from backtesting import run_backtest
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(page_title="Stock Signal Dashboard", layout="wide")
st.title("📊 Stock Signal Score Dashboard")

market = st.selectbox("Select Market", ["ASX", "US"])
tickers_input = st.text_input("Enter Stock Ticker Symbols (comma-separated)", "WTC" if market == "ASX" else "AAPL")
threshold = st.slider("Signal Score Threshold for Backtesting", 50, 100, 75)

if tickers_input:
    tickers = [t.strip().upper() for t in tickers_input.split(",")]
    sector_pe_map = fetch_sector_pe_map()

    for ticker_input in tickers:
        ticker_symbol = ticker_input + ".AX" if market == "ASX" and not ticker_input.endswith(".AX") else ticker_input
        ticker = yf.Ticker(ticker_symbol)
        try:
            hist = ticker.history(period="12mo")
            info = ticker.info
        except:
            st.error(f"Failed to fetch data for {ticker_symbol}")
            continue

        if hist.empty:
            st.warning(f"No historical data for {ticker_symbol}")
            continue

        hist = compute_indicators(hist)
        current_price = hist['Close'].iloc[-1]
        sma_200 = hist['SMA_200'].iloc[-1]
        pe_ratio = info.get('trailingPE', 25.0)
        target_price = info.get('targetMeanPrice', current_price)
        analyst_upside = max(0, (target_price - current_price) / current_price * 100)
        sector = info.get('sector', 'Technology')
        sector_pe = sector_pe_map.get(sector, 20.0)
        broker_score = fetch_broker_rating_asx(ticker_input) if market == "ASX" else 3

        signal_score = calculate_signal_score(current_price, sma_200, pe_ratio, sector_pe, analyst_upside, broker_score)

        st.subheader(f"📈 {ticker_symbol} Technical Indicators")
        st.metric("Current Price", f"${current_price:.2f}")
        st.metric("SMA 200", f"${sma_200:.2f}")
        st.metric("Signal Score", f"{signal_score}/100")

        st.subheader("📊 Fundamental Metrics")
        st.metric("PE Ratio", f"{pe_ratio:.2f}")
        st.metric("Sector PE Avg", f"{sector_pe:.2f}")
        st.metric("Analyst Upside", f"{analyst_upside:.2f}%")
        st.metric("Sector", sector)

        st.subheader("🧠 Broker Consensus")
        broker_labels = {5: "Strong Buy", 4: "Buy", 3: "Hold", 2: "Sell", 1: "Strong Sell"}
        st.write(f"Broker Rating: {broker_labels.get(broker_score, 'Unknown')}")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_100'], mode='lines', name='SMA 100'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], mode='lines', name='SMA 200'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Upper Band'], mode='lines', name='Upper Band'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Lower Band'], mode='lines', name='Lower Band'))
        fig.update_layout(title=f"{ticker_symbol.upper()} Price & SMA Chart",
                          xaxis_title="Date",
                          yaxis_title="Price",
                          legend_title="Legend",
                          template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📉 Backtesting Results")
        results = run_backtest(hist, signal_score, threshold)
        for k, v in results.items():
            st.write(f"{k}: {v}")