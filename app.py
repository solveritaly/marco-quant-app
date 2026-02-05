import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

st.markdown("""
    <style>
    div.stButton > button { border: none; background: transparent; color: #FF8C00; font-weight: bold; }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state: st.session_state.portfolio = {}
if 'sort_col' not in st.session_state: st.session_state.sort_col = "Score"
if 'sort_asc' not in st.session_state: st.session_state.sort_asc = False

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
        r = int(255 * (1 - score/100))
        g = int(255 * (score/100))
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Entry": round(close * 0.99, 2), "TP": round(close + (std20*3), 2), "SL": round(close - (std20*2), 2),
            "History": df
        }
    except: return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- 2. TOP 5 ---
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_tickers = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "ASML"]
t_cols = st.columns(5)
for i, t_name in enumerate(top_tickers):
    d = get_analysis(t_name)
    if d:
        with t_cols[i]:
            st.markdown(f"### {d['Score']}")
            st.write(f"**{d['Symbol']}**")
            st.write(f"€{d['Prezzo']}")

st
