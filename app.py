import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="Marco-Quant Trading Terminal", layout="wide")

st.markdown("""
    <style>
    div.stButton > button { border: none !important; background-color: transparent !important; color: #FF8C00 !important; font-weight: bold !important; font-size: 16px; }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    .trading-box { background-color: #fffaf5; padding: 15px; border-radius: 10px; border-left: 5px solid #FF8C00; }
    </style>
    """, unsafe_allow_html=True)

# Memoria Portafoglio e Ordinamento
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
        
        # Indicatori Tecnici
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Calcolo Score (1-100)
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        r = int(255 * (1 - score/100)); g = int(255 * (score/100))
        
        # Livelli Operativi
        entry = close * 0.99
        tp = close + (std20 * 3)
        sl = close - (std20 * 2)
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Entry": round(entry, 2), "TP
