import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import requests
from bs4 import BeautifulSoup
import numpy as np

# --- Helper Functions ---

@st.cache_data(ttl=86400)
def fetch_sector_pe_map():
    url = "https://fullratio.com/pe-ratio/by-sector"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table")
        sector_pe = {}
        if table:
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    sector = cols[0].text.strip()
                    pe = cols[1].text.strip().replace(",", "")
                    try:
                        sector_pe[sector] = float(pe)
                    except:
                        continue
        return sector_pe
    except:
        return {}

def fetch_broker_rating_asx(ticker):
    url = "https://www.marketindex.com.au/broker-consensus"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table")
        if table:
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 2 and ticker.upper() in cols[0].text:
                    rating = cols[1].text.strip().lower()
                    if "buy" in rating:
                        return 5
                    elif "accumulate" in rating:
                        return 4
                    elif "hold" in rating:
                        return 3
                    elif "reduce" in rating:
                        return 2
                    elif "sell" in rating:
                        return 1
        return 3
    except:
        return 3

def calculate_signal_score(current_price, sma_200, pe_ratio, sector_pe, analyst_upside, broker_score):
    sma_score = max(0, 100 - abs(current_price - sma_200) / sma_200 * 100)
    pe_zscore = (pe_ratio - sector_pe) / sector_pe if sector_pe else 0
    pe_score = max(0, 100 - abs(pe_zscore) * 100)
    upside_score = min(100, analyst_upside)
    broker_score = broker_score * 20
    return round((sma_score * 0.25 + pe_score * 0.2 + upside_score * 0.3 + broker_score * 0.25), 2)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    ema12 = data.ewm(span=12, adjust=False).mean()
    ema26 = data.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

def calculate_bollinger_bands(data, window=20):
    sma = data.rolling(window=window).mean()
    std = data.rolling(window=window).std()
    upper_band = sma + 2 * std
    lower_band = sma - 2 * std
    return upper_band, lower_band

# --- Streamlit App ---

st.set_page_config(page_title="Stock Signal Dashboard", layout="wide")
st.title("📊 Enhanced Stock Signal Score Dashboard")

market = st.selectbox("Select Market", ["ASX", "US"])
ticker_input = st.text_input("Enter Stock Ticker Symbol(s)", "WTC" if market == "ASX" else "AAPL")
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

sector_pe_map = fetch_sector_pe_map()

for ticker_input in tickers:
    ticker_symbol = ticker_input + ".AX" if market == "ASX" and not ticker_input.endswith(".AX") else ticker_input
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="6mo")
        info = ticker.info
    except:
        st.error(f"Failed to fetch data for {ticker_symbol}")
        continue

    if hist.empty:
        st.warning(f"No historical data found for {ticker_symbol}")
        continue

    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    hist['SMA_100'] = hist['Close'].rolling(window=100).mean()
    hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
    hist['RSI'] = calculate_rsi(hist['Close'])
    hist['MACD'], hist['MACD_Signal'] = calculate_macd(hist['Close'])
    hist['BB_Upper'], hist['BB_Lower'] = calculate_bollinger_bands(hist['Close'])

    current_price = hist['Close'].iloc[-1]
    sma_200 = hist['SMA_200'].iloc[-1]
    pe_ratio = info.get('trailingPE', 25.0)
    target_price = info.get('targetMeanPrice', current_price)
    analyst_upside = max(0, (target_price - current_price) / current_price * 100)
    sector = info.get('sector', 'Technology')
    sector_pe = sector_pe_map.get(sector, 20.0)
    broker_score = fetch_broker_rating_asx(ticker_input) if market == "ASX" else 3
    signal_score = calculate_signal_score(current_price, sma_200, pe_ratio, sector_pe, analyst_upside, broker_score)

    st.header(f"📈 {ticker_symbol.upper()} Analysis")
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${current_price:.2f}")
    col2.metric("SMA 200", f"${sma_200:.2f}")
    col3.metric("Signal Score", f"{signal_score}/100")

    col1.metric("PE Ratio", f"{pe_ratio:.2f}")
    col2.metric("Sector PE Avg", f"{sector_pe:.2f}")
    col3.metric("Analyst Upside", f"{analyst_upside:.2f}%")

    col1.metric("Sector", sector)
    col2.metric("RSI", f"{hist['RSI'].iloc[-1]:.2f}")
    col3.metric("Broker Rating", {5: "Strong Buy", 4: "Buy", 3: "Hold", 2: "Sell", 1: "Strong Sell"}.get(broker_score, "Unknown"))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', name='SMA 50'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_100'], mode='lines', name='SMA 100'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], mode='lines', name='SMA 200'))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['BB_Upper'], mode='lines', name='Bollinger Upper', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=hist.index, y=hist['BB_Lower'], mode='lines', name='Bollinger Lower', line=dict(dash='dot')))
    fig.update_layout(title=f"{ticker_symbol.upper()} Price & SMA Chart", xaxis_title="Date", yaxis_title="Price", legend_title="Legend", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💡 Actionable Insight")
    if signal_score > 75:
        st.success("✅ Strong signal score. Consider further analysis.")
    elif signal_score > 55:
        st.info("📊 Moderate signal score. Review fundamentals and technicals.")
    else:
        st.warning("⚠️ Weak signal score. Exercise caution.")

    st.download_button("📥 Download Historical Data", data=hist.to_csv().encode(), file_name=f"{ticker_symbol}_data.csv", mime="text/csv")