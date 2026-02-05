import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PULITA (SFONDO BIANCO) ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

# Inizializzazione Portafoglio
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- FUNZIONE ANALISI AVANZATA ---
@st.cache_data(ttl=3600)
def get_full_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        info = t.info
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Analisi Operativa (Target basati su ATR/Volatilità)
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        target_entry = round(close - (atr * 0.7), 2)
        target_exit = round(close + (atr * 1.5), 2)
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        
        # Calcolo Score (0-100)
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > sma200 else 0), 0, 100))
        
        return {
            "symbol": ticker, "name": info.get('shortName', ticker),
            "price": round(close, 2), "score": score,
            "L": close > sma200, "M": close
