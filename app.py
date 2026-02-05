import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Global Terminal", layout="wide")

# CSS Migliorato per pulizia e semafori
st.markdown("""
    <style>
    div.stButton > button {
        border: none !important; background-color: transparent !important;
        color: #FF8C00 !important; font-weight: bold !important;
        box-shadow: none !important; padding: 0px !important;
    }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo {
        display: block; width: 35px; height: 35px; border-radius: 5px;
        text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto;
    }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    </style>
    """, unsafe_allow_html=True)

# --- MEMORIA ---
if 'portfolio' not in st.session_state: st.session_state.portfolio = {}
if 'sort_col' not in st.session_state: st.session_state.sort_col = "Score"
if 'sort_asc' not in st.session_state: st.session_state.sort_asc = False

@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        info = t.info
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]; sma50 = df['Close'].rolling(50).mean().iloc[-1]; sma20 = df['Close'].rolling(20).mean().iloc[-1]
        
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        r = int(255 * (1 - score/100)); g = int(255 * (score/100))
        
        return {
            "Symbol": ticker, "Nome": info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Div": (info.get('dividendYield', 0) or 0) * 100,
            "PE": info.get('trailingPE', 'N/A'), "Cap": info.get('marketCap', 0), "Vol": info.get('averageVolume', 0),
            "History": df
        }
    except: return None

# --- UI ---
st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# LISTA MERCATI ESTESA
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI", "STMMI.MI", "G.MI", "PST.MI"],
    "🇪🇺 Europa": ["ASML", "MC.PA", "SAP", "OR.PA", "LIN", "AIR.PA", "TTE", "BMW.DE", "NESN.SW", "NOVN.SW"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "BRK-B", "AMD", "NFLX"],
    "🌍 Emergenti": ["TSM", "BABA", "TCEHY", "VALE", "JD", "MELI", "PDD", "INFY", "CPNG"],
    "📊 ETF": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "VWCE.DE", "VUSA.L", "IBCI.MI"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR", "BNB-EUR", "XRP-EUR"]
}

# TOP 5
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_cols = st.columns(5)
for i, t in enumerate(["LDO.MI", "NVDA", "BTC-EUR", "ASML", "TSM"]):
    data = get_analysis(t)
    if data:
        with top_cols[i]:
            st.markdown(f'<div style="text-align:center; border:2px solid {data["Color"]}; border-radius:10px; padding:10px;">'
                        f'<span style="color:{data["Color"]}; font-size:28px; font-weight:
