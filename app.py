import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

st.markdown("""
    <style>
    .semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state: st.session_state.portfolio = {}

@st.cache_data(ttl=600)
def get_analysis(ticker):
    try:
        # Lasciamo che YF gestisca la connessione
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        close = float(df['Close'].iloc[-1])
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Score Marco-Quant
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        
        return {
            "Symbol": ticker, 
            "Nome": t.info.get('shortName', ticker),
            "Score": score, 
            "Prezzo": round(close, 2),
            "L": close > sma200, 
            "M": close > sma50, 
            "B": close > sma20,
            "Entry": round(close * 0.99, 2), 
            "TP": round(close + (std20 * 3), 2), 
            "SL": round(close - (std20 * 2), 2),
            "History": df
        }
    except Exception:
        return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- 2. TABELLE MERCATI ---
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL", "BRK-B"],
    "🇪🇺 Europa": ["ASML", "MC.PA", "SAP", "NOVO-B.CO"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

tabs = st.tabs(list(mercati.keys()) + ["💼 Portafoglio"])

for i, m_name in enumerate(mercati.keys()):
    with tabs[i]:
        st.write(f"### Analisi Trend {m_name}")
        for t in mercati[m_name]:
            d = get_analysis(t)
            if d:
                c1, c2, c3, cL, cM, cB, cAction = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.5])
                c1.write(f"**{d['Nome']}**")
                c2.write(f"**{d['Score']} pts**")
                
                # Simbolo valuta corretto
                valuta = "€" if any(x in t for x in ["MI", "EUR", "PA", "CO"]) else "$"
                c3.write(f"{valuta}{d['Prezzo']}")
