import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ESTETICA "NERO & ARANCIONE" ---
st.set_page_config(page_title="MARCO-QUANT ORANGE", layout="wide")

st.markdown("""
    <style>
    /* Sfondo nero e testi arancioni */
    .stApp { background-color: #000000; color: #FF8C00; }
    h1, h2, h3, h4, p, span, label { color: #FF8C00 !important; font-family: 'Courier New', Courier, monospace; }
    
    /* Box dei titoli */
    .stMetric, .score-card { 
        background-color: #111111; 
        border: 2px solid #FF8C00; 
        border-radius: 10px; 
        padding: 15px;
        text-align: center;
    }
    
    /* Score Gigante */
    .big-score { font-size: 60px; font-weight: bold; color: #FF8C00; text-shadow: 0 0 10px #FF4500; }
    
    /* Bottoni */
    .stButton>button { 
        background-color: #FF8C00; color: black; border-radius: 5px; 
        font-weight: bold; width: 100%; border: none;
    }
    .stButton>button:hover { background-color: #FF4500; color: white; }

    /* Input text */
    input { background-color: #222222 !important; color: #FF8C00 !important; border: 1px solid #FF8C00 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONE ANALISI ---
@st.cache_data(ttl=3600)
def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Calcolo Score
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > sma200 else 0), 0, 100))
        
        return {
            "symbol": ticker, "name": t.info.get('shortName', ticker),
            "price": round(close, 2), "score": score,
            "L": close > sma200, "M": close > df['Close'].rolling(50).mean().iloc[-1], "B": close > sma20,
            "df": df
        }
    except: return None

# --- UI PRINCIPALE ---
st.title("🏹 MARCO-QUANT ELITE TERMINAL")

# 1. TOP 5 AUTOMATICA (Aggiornamento orario)
st.subheader("🔥 TOP 5 OPPORTUNITÀ (AUTO-UPDATE)")
top_list = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "NOVO-B.CO"]
cols = st.columns(5)

for i, t in enumerate(top_list):
    data = get_data(t)
    if data:
        with cols[i]:
            st.markdown(f"""
                <div class="score-card">
                    <small>{data['symbol']}</small><br>
                    <span class="big-score">{data['score']}</span><br>
                    <small>L:{'🟢' if data['L'] else '🔴'} M:{'🟢' if data['M'] else '🔴'} B:{'🟢' if data['B'] else '🔴'}</small>
                </div>
            """, unsafe_allow_html=True)

st.write("---")

# 2. RICERCA CON SUGGERIMENTI
st.subheader("🔍 RICERCA GLOBALE & PORTAFOGLIO")
all_suggestions = ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "NVDA", "AAPL", "TSLA", "BTC-EUR", "ETH-EUR", "GC=F"]
search = st.selectbox("Inizia a scrivere o seleziona un titolo:", [""] + all_suggestions)

if search:
    res = get_data(search)
    if res:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""
                <div class="score-card">
                    <h2>{res['name']}</h2>
                    <span class="big-score">{res['score']}</span>
                    <p>PREZZO: €{res['prezzo' if 'prezzo' in res else 'price']}</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("AGGIUNGI A PORTAFOGLIO"):
                st.success(f"{res['name']} salvato!")
        
        with c2:
            # Grafico Arancione
            fig = go.Figure(data=[go.Candlestick(
                x=res['df'].index, open=res['df']['Open'],
                high=res['df']['High'], low=res['df']['Low'], close=res['df']['Close'],
                increasing_line_color='#FF8C00', decreasing_line_color='#444444'
            )])
            fig.update_layout(
                plot_bgcolor='black', paper_bgcolor='black',
                font=dict(color='#FF8C00'), xaxis=dict(gridcolor='#222222'), yaxis=dict(gridcolor='#222222'),
                height=400, margin=dict(l=0,r=0,b=0,t=0)
            )
            st.plotly_chart(fig, use_container_width=True)

# 3. ROAD TO 1 MILLION (POPUP)
st.write("---")
with st.expander("🚀 PROIEZIONE 1 MILIONE (CLICCA PER APRIRE)"):
    pac = st.number_input("PAC MENSILE (€)", value=500)
    st
