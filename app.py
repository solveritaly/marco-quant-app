import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE STABILE (NERO & ARANCIONE) ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3, h4, p, span, label, .stMarkdown { color: #FF8C00 !important; }
    .stButton>button { background-color: #FF8C00; color: black; font-weight: bold; border-radius: 5px; }
    .stTextInput>div>div>input { background-color: #111111; color: #FF8C00; border: 1px solid #FF8C00; }
    .score-box { 
        border: 2px solid #FF8C00; 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center; 
        background-color: #111111;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONE ANALISI (Semplice e Veloce) ---
def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Score 0-100
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > sma200 else 0), 0, 100))
        
        return {
            "symbol": ticker, "name": t.info.get('shortName', ticker),
            "price": round(close, 2), "score": score,
            "L": close > sma200, "M": close > df['Close'].rolling(50).mean().iloc[-1], "B": close > sma20,
            "df": df
        }
    except: return None

st.title("🏹 MARCO-QUANT TERMINAL")

# 1. TOP 5 AUTOMATICA
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_list = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "NOVO-B.CO"]
cols = st.columns(5)

for i, t in enumerate(top_list):
    data = get_data(t)
    if data:
        with cols[i]:
            st.markdown(f"""
                <div class="score-box">
                    <small>{data['symbol']}</small><br>
                    <span style="font-size: 40px; font-weight: bold;">{data['score']}</span><br>
                    <small>L:{'🟢' if data['L'] else '🔴'} M:{'🟢' if data['M'] else '🔴'} B:{'🟢' if data['B'] else '🔴'}</small>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# 2. RICERCA E ANALISI
st.subheader("🔍 RICERCA ASSET")
search = st.text_input("Inserisci Ticker (es: LDO.MI, AAPL, BTC-EUR)", "").upper()

if search:
    res = get_data(search)
    if res:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"""
                <div class="score-box">
                    <h2>{res['name']}</h2>
                    <span style="font-size: 60px; font-weight: bold;">{res['score']}</span>
                    <p>PREZZO: €{res['price']}</p>
                </div>
            """, unsafe_allow_html=True)
        
        with c2:
            fig = go.Figure(data=[go.Candlestick(
                x=res['df'].index, open=res['df']['Open'],
                high=res['df']['High'], low=res['df']['Low'], close=res['df']['Close'],
                increasing_line_color='#FF8C00', decreasing_line_color='#444444'
            )])
            fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font=dict(color='#FF8C00'), height=400)
            st.plotly_chart(fig, use_container_width=True)
            


# 3. ROAD TO 1M
st.divider()
st.subheader("🚀 ROAD TO 1 MILLION")
pac = st.number_input("PAC Mensile (€)", value=500)
st.write(f"Stima basata sul tuo piano di accumulo attuale.")
