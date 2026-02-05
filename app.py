import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione base
st.set_page_config(page_title="Marco-Quant", layout="wide")

# Memoria per il portafoglio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# Funzione Analisi
@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Entry": round(close * 0.99, 2), "TP": round(close + (std20*3), 2), "SL": round(close - (std20*2), 2),
            "History": df
        }
    except:
        return None

st.title("🏹 MARCO-QUANT TERMINAL")

# Liste Titoli
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA"],
    "📊 ETF": ["SWDA.MI", "CSSPX.MI"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR"]
}

tabs = st.tabs(list(mercati.keys()) + ["💼 Portafoglio"])

for i, m_name in enumerate(mercati.keys()):
    with tabs[i]:
        for ticker in mercati[m_name]:
            d = get_analysis(ticker)
            if d:
                c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                c1.write(f"**{d['Nome']}** ({d['Symbol']})")
                c2.write(f"Score: **{d['Score']}**")
                c3.write(
