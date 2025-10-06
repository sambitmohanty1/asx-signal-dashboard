import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import requests
from bs4 import BeautifulSoup

# --- Helper Functions ---

def calculate_signal_score(current_price, sma_200, pe_ratio, sector_pe, analyst_upside, broker_score):
    sma_score = max(0, 100 - abs(current_price - sma_200) / sma_200 * 100)
    pe_score = max(0, 100 - abs(pe_ratio - sector_pe) / sector_pe * 100)
    upside_score = min(100, analyst_upside)
    broker_score = broker_score * 20  # Normalize to 0-100
    return round((sma_score * 0.3 + pe_score * 0.2 + upside_score * 0.3 + broker_score * 0.2), 2)

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
        return 3  # Neutral default
    except:
        return 3

# --- Streamlit App ---

st.title("📊 Stock Signal Score Dashboard")

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

        current_price = hist['Close'].iloc[-1]
        sma_200 = hist['SMA_200'].iloc[-1]
        pe_ratio = info.get('trailingPE', 25.0)
        target_price = info.get('targetMeanPrice', current_price)
        analyst_upside = max(0, (target_price - current_price) / current_price * 100)
        sector = info.get('sector', 'Technology')

        sector_pe_map = fetch_sector_pe_map()
        sector_pe = sector_pe_map.get(sector, 20.0)

        broker_score = fetch_broker_rating_asx(ticker_input) if market == "ASX" else 3

        signal_score = calculate_signal_score(current_price, sma_200, pe_ratio, sector_pe, analyst_upside, broker_score)

        st.subheader("📈 Technical Indicators")
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
        fig.update_layout(title=f"{ticker_symbol.upper()} Price & SMA Chart",
                          xaxis_title="Date",
                          yaxis_title="Price",
                          legend_title="Legend",
                          template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("💡 Actionable Insight")
        if signal_score > 75:
            st.success("✅ Strong signal score. Consider further analysis.")
        elif signal_score > 55:
            st.info("📊 Moderate signal score. Review fundamentals and technicals.")
        else:
            st.warning("⚠️ Weak signal score. Exercise caution.")
    else:
        st.error("No historical data found for this ticker.")