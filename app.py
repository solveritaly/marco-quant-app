import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Marco-Quant Global Terminal", layout="wide")

# CSS per pulizia visiva e semafori L M B
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

# --- GESTIONE MEMORIA ---
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
        
        # Medie Mobili per i Semafori
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        
        # Score (1-100) basato su trend e momentum
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        r = int(255 * (1 - score/100)); g = int(255 * (score/100))
        
        return {
            "Symbol": ticker, "Nome": info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Div": (info.get('dividendYield', 0) or 0) * 100,
            "PE": info.get('trailingPE', 'N/A'), "History": df
        }
    except: return None

# --- UI PRINCIPALE ---
st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# 1. TOP 5 OPPORTUNITÀ
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_cols = st.columns(5)
for i, t in enumerate(["LDO.MI", "NVDA", "BTC-EUR", "ASML", "TSM"]):
    data = get_analysis(t)
    if data:
        with top_cols[i]:
            st.markdown(f'<div style="text-align:center; border:2px solid {data["Color"]}; border-radius:10px; padding:10px;">'
                        f'<span style="color:{data["Color"]}; font-size:28px; font-weight:bold;">{data["Score"]}</span><br>'
                        f'<b>{data["Symbol"]}</b>
