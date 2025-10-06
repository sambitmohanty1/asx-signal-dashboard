import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import requests

# Finnhub API key placeholder
FINNHUB_API_KEY = d3hjf19r01qi2vu173v0d3hjf19r01qi2vu173vg

# Function to calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to calculate MACD
def calculate_macd(data):
    ema12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema26 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# Function to calculate signal score
def calculate_signal_score(current_price, sma_200, cape_ratio, analyst_upside, rsi, macd):
    sma_score = max(0, 100 - abs(current_price - sma_200) / sma_200 * 100)
    cape_score = max(0, 100 - cape_ratio * 2)
    upside_score = min(100, analyst_upside)
    rsi_score = max(0, 100 - abs(rsi - 50) * 2)
    macd_score = 100 if macd > 0 else 0
    return round((sma_score * 0.2 + cape_score * 0.2 + upside_score * 0.2 + rsi_score * 0.2 + macd_score * 0.2), 2)

# Function to fetch news sentiment from Finnhub
def fetch_news_sentiment(ticker):
    url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            news_items = response.json()
            return news_items[:5]  # Return top 5 news items
        else:
            return []
    except:
        return []

# Streamlit UI
st.title("📈 Stock Signal Score Dashboard")

market = st.selectbox("Select Market", ["ASX", "US"])
ticker_input = st.text_input("Enter Stock Ticker Symbol", "WTC" if market == "ASX" else "AAPL")

if ticker_input:
    ticker_symbol = ticker_input + ".AX" if market == "ASX" and not ticker_input.endswith(".AX") else ticker_input
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period="6mo")
    info = ticker.info

    if not hist.empty:
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_100'] = hist['Close'].rolling(window=100).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
        hist['RSI'] = calculate_rsi(hist)
        hist['MACD'], hist['MACD_Signal'] = calculate_macd(hist)

        current_price = hist['Close'].iloc[-1]
        sma_200 = hist['SMA_200'].iloc[-1]
        rsi = hist['RSI'].iloc[-1]
        macd = hist['MACD'].iloc[-1]

        cape_ratio = info.get('trailingPE', 25.0)
        target_price = info.get('targetMeanPrice', current_price)
        analyst_upside = max(0, (target_price - current_price) / current_price * 100)

        signal_score = calculate_signal_score(current_price, sma_200, cape_ratio, analyst_upside, rsi, macd)

        st.subheader("📊 Technical Indicators")
        st.metric("Current Price", f"${current_price:.2f}")
        st.metric("SMA 200", f"${sma_200:.2f}")
        st.metric("RSI", f"{rsi:.2f}")
        st.metric("MACD", f"{macd:.2f}")
        st.metric("Signal Score", f"{signal_score}/100")

        st.subheader("📈 Fundamental Metrics")
        st.metric("CAPE Ratio (PE Proxy)", f"{cape_ratio:.2f}")
        st.metric("Analyst Upside", f"{analyst_upside:.2f}%")

        st.subheader("📰 News Sentiment")
        news_items = fetch_news_sentiment(ticker_input)
        if news_items:
            for item in news_items:
                st.markdown(f"- [{item['headline']}]({item['url']})")
        else:
            st.info("No news data available or API key missing.")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_100'], mode='lines', name='SMA 100'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], mode='lines', name='SMA 200'))
        fig.update_layout(title=f"{ticker_symbol.upper()} Price & SMA Chart",
                          xaxis_title="Date",
                          yaxis_title="Price",
                          legend_title="Legend",
                          template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        if signal_score > 70:
            st.success("✅ Strong signal score. Consider further analysis.")
        elif signal_score > 50:
            st.info("📊 Moderate signal score. Review fundamentals and technicals.")
        else:
            st.warning("⚠️ Weak signal score. Exercise caution.")
    else:
        st.error("No historical data found for this ticker.")