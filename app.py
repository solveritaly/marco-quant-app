import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

@st.cache_data(ttl=600)
def get_pro_data(ticker):
    try:
        # Scarico dati con gestione errore
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 200: return None
        
        info = yf.Ticker(ticker).info
        last_p = df['Close'].iloc[-1]
        
        # Medie per Trendline (B, M, L)
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        
        # Volatilità e Momentum
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        return {
            "name": info.get('shortName', ticker),
            "price": round(last_p, 2),
            "L": last_p > sma200, "M": last_p > sma50, "B": last_p > sma20,
            "score": int(np.clip(30 + (40 if last_p > sma200 else 0) + (20 if last_p > sma50 else 0), 0, 100)),
            "df": df
        }
    except: return None

st.title("🏹 MARCO-QUANT PRO TERMINAL")
st.write("Verifica Trendline: **L** (200gg), **M** (50gg), **B** (20gg)")

# Liste asset
assets = ["BTC-EUR", "ETH-EUR", "LDO.MI", "ENEL.MI", "NOVO-B.CO", "GOOGL", "BRK-B"]
tabs = st.tabs(["📊 Radar Mercati", "💼 Portafoglio Fineco"])

with tabs[0]:
    for a in assets:
        d = get_pro_data(a)
        if d:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
            col1.write(f"**{d['name']}**")
            col2.metric("Prezzo", f"€{d['price']}")
            col3.write(f"Score: **{d['score']}**")
            
            # Semafori Trendline
            with col4:
                l_mark = "🟢" if d['L'] else "🔴"
                m_mark = "🟢" if d['M'] else "🔴"
                b_mark = "🟢" if d['B'] else "🔴"
                st.write(f"Trend L:{l_mark} M:{m_mark} B:{b_mark}")
            st.divider()

with tabs[1]:
    st.write("Inserisci qui i tuoi dati Fineco per monitorare le perdite reali.")
