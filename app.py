import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

# CSS per i semafori quadrati con lettere
st.markdown("""
<style>
.semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
.bg-green { background-color: #23d160; }
.bg-red { background-color: #ff3860; }
div.stButton > button { border: none; background: transparent; color: #FF8C00; font-weight: bold; }
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
        close = float(df['Close'].iloc[-1])
        sma200 = float(df['Close'].rolling(200).mean().iloc[-1])
        sma50 = float(df['Close'].rolling(50).mean().iloc[-1])
        sma20 = float(df['Close'].rolling(20).mean().iloc[-1])
        std20 = float(df['Close'].rolling(20).std().iloc[-1])
        
        # Calcolo Score 1-100
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        
        return {
            "Symbol": ticker,
            "Nome": t.info.get('shortName', ticker),
            "Score": score,
            "Prezzo": round(close, 2),
            "L": bool(close > sma200),
            "M": bool(close > sma50),
            "B": bool(close > sma20),
            "Entry": round(close * 0.99, 2),
            "TP": round(close + (std20 * 3), 2),
            "SL": round(close - (std20 * 2), 2),
            "History": df
        }
    except:
        return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- 2. TOP 5 OPPORTUNITÀ ---
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_tickers = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "ASML"]
t_cols = st.columns(5)
for i, ticker in enumerate(top_tickers):
    d = get_analysis(ticker)
    if d:
        with t_cols[i]:
            st.metric(label=d['Symbol'], value=f"{d['Score']} pts", delta=f"€{d['Prezzo']}")

st
