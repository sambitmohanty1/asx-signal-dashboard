import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from signal_scoring import calculate_signal_score_enhanced, calculate_signal_score_tech

# --- Helper Functions ---
def compute_indicators(df):
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Upper_BB'] = df['Close'].rolling(window=20).mean() + 2 * df['Close'].rolling(window=20).std()
    df['Lower_BB'] = df['Close'].rolling(window=20).mean() - 2 * df['Close'].rolling(window=20).std()
    return df

# --- Streamlit App ---
st.title("📊 Stock Signal Score Dashboard")

ticker_input = st.text_input("Enter Stock Ticker Symbol", "AVGO")

if ticker_input:
    ticker = yf.Ticker(ticker_input)
    hist = ticker.history(period="6mo")
    info = ticker.info

    if not hist.empty:
        hist = compute_indicators(hist)
        current_price = hist['Close'].iloc[-1]
        sma_200 = hist['SMA_200'].iloc[-1]
        forward_pe = info.get('forwardPE', 20.0)
        peg_ratio = info.get('pegRatio', 1.5)
        eps_growth = info.get('earningsQuarterlyGrowth', 0.0) * 100
        revenue_growth = info.get('revenueGrowth', 0.0) * 100
        target_price = info.get('targetMeanPrice', current_price)
        analyst_upside = max(0, (target_price - current_price) / current_price * 100)
        sector = info.get('sector', 'Technology')
        rsi = hist['RSI'].iloc[-1]
        macd_signal_alignment = hist['MACD'].iloc[-1] > hist['Signal_Line'].iloc[-1]

        if sector.lower() == 'technology':
            signal_score = calculate_signal_score_tech(forward_pe, peg_ratio, eps_growth,
                                                       revenue_growth, analyst_upside,
                                                       rsi, macd_signal_alignment)
        else:
            signal_score = calculate_signal_score_enhanced(forward_pe, peg_ratio, eps_growth,
                                                           revenue_growth, analyst_upside)

        st.subheader("📈 Technical Indicators")
        st.metric("Current Price", f"${current_price:.2f}")
        st.metric("SMA 200", f"${sma_200:.2f}")
        st.metric("RSI", f"{rsi:.2f}")
        st.metric("MACD > Signal", "Yes" if macd_signal_alignment else "No")

        st.subheader("📊 Fundamental Metrics")
        st.metric("Forward PE", f"{forward_pe:.2f}")
        st.metric("PEG Ratio", f"{peg_ratio:.2f}")
        st.metric("EPS Growth", f"{eps_growth:.2f}%")
        st.metric("Revenue Growth", f"{revenue_growth:.2f}%")
        st.metric("Analyst Upside", f"{analyst_upside:.2f}%")
        st.metric("Sector", sector)

        st.subheader("📌 Signal Score")
        st.metric("Signal Score", f"{signal_score}/100")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], mode='lines', name='Close Price'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_50'], mode='lines', name='SMA 50'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA_200'], mode='lines', name='SMA 200'))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Upper_BB'], mode='lines', name='Upper BB', line=dict(dash='dot')))
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Lower_BB'], mode='lines', name='Lower BB', line=dict(dash='dot')))
        fig.update_layout(title=f"{ticker_input.upper()} Price & Indicators",
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
