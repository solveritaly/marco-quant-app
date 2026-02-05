import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# CONFIGURAZIONE GRAFICA
st.set_page_config(page_title="Marco-Quant Ultimate", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .status-led { height: 18px; width: 18px; border-radius: 50%; display: inline-block; margin-right: 8px; border: 2px solid #30363d; }
    .led-green { background-color: #23d160; box-shadow: 0 0 10px #23d160; }
    .led-red { background-color: #ff3860; box-shadow: 0 0 10px #ff3860; }
    .score-box { font-size: 20px; font-weight: bold; color: #23d160; }
    </style>
    """, unsafe_allow_html=True)

# MOTORE DI CALCOLO
def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        # Scarichiamo 2 anni per avere la media a 200 giorni corretta
        df = t.history(period="2y", interval="1d", auto_adjust=True)
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Z-Score per Score Vantaggio (0-100)
        z = (sma20 - close) / (std20 if std20 > 0 else 1)
        score = int(np.clip((1 / (1 + np.exp(-z)) * 100), 0, 100))
        
        return {
            "Ticker": ticker,
            "Nome": t.info.get('shortName', ticker),
            "Prezzo": round(close, 2),
            "L": close > sma200,
            "M": close > sma50,
            "B": close > sma20,
            "Score": score,
            "Div": (t.info.get('dividendYield', 0) or 0) * 100,
            "History": df['Close']
        }
    except: return None

# INTERFACCIA
st.title("🏹 Marco-Quant: Clone Quantaste v10.0")

# Input Capitale e PAC
with st.sidebar:
    st.header("💰 Gestione Patrimonio")
    capitale_totale = st.number_input("Capitale Totale Attuale (€)", value=10000)
    pac_mensile = st.number_input("Versamento Mensile (€)", value=500)
    st.divider()
    st.info("Logica 30/70 attiva: 30% Aggressivo, 70% Strategico.")

tabs = st.tabs(["📊 Radar Mercati", "🚀 Road to 1 Million", "💼 Il Mio Portafoglio"])

with tabs[0]:
    mercati = {
        "🇮🇹 ITALIA": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
        "🇺🇸 USA": ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA", "BRK-B"],
        "🇪🇺 EUROPA": ["NOVO-B.CO", "ASML.AS", "MC.PA", "SAP.DE"],
        "🪙 CRYPTO/STRAT": ["BTC-EUR", "ETH-EUR", "GC=F", "CL=F", "SPY", "VGK", "TLT"]
    }
    
    sel_mkt = st.selectbox("Seleziona Mercato", list(mercati.keys()))
    
    if st.button("🔄 AGGIORNA DATI REAL-TIME"):
        data = [get_data(t) for t in mercati[sel_mkt] if get_data(t)]
        df = pd.DataFrame(data)
        
        # Header Tabella
        h1, h2, h3, h4, h5, h6 = st.columns([2, 2, 1, 1, 1, 1])
        h1.write("**Asset**")
        h2.write("**Score Vantaggio**")
        h3.write("**L**")
        h4.write("**M**")
        h5.write("**B**")
        h6.write("**Prezzo**")
        
        for _, row in df.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1, 1, 1, 1])
            c1.write(f"**{row['Nome']}**")
            c2.progress(row['Score']/100)
            
            # Semafori LED
            l_led = "led-green" if row['L'] else "led-red"
            m_led = "led-green" if row['M'] else "led-red"
            b_led = "led-green" if row['B'] else "led-red"
            
            c3.markdown(f'<div class="status-led {l_led}"></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="status-led {m_led}"></div>', unsafe_allow_html=True)
            c5.markdown(f'<div class="status-led {b_led}"></div>', unsafe_allow_html=True)
            c6.write(f"€{row['Prezzo']}")

with tabs[1]:
    st.header("📈 Obiettivo 1.000.000€")
    # Calcolo proiezione
    mesi = 360 # 30 anni
    rendimento_annuo = 0.09 # 9% medio
    progressione = []
    cap = capitale_totale
    for m in range(mesi):
        cap = (cap + pac_mensile) * (1 + rendimento_annuo/12)
        if m % 12 == 0: progressione.append(cap)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=progressione, name="Crescita Portafoglio", line=dict(color='#23d160', width=4)))
    fig.add_hline(y=1000000, line_dash="dash", line_color="gold", annotation_text="IL MILIONE")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.header("⚖️ Ribilanciamento 30/70")
    q_agg = capitale_totale * 0.30
    q_strat = capitale_totale * 0.70
    
    col1, col2 = st.columns(2)
    col1.metric("Quota Azioni/Crypto (30%)", f"€{int(q_agg)}")
    col2.metric("Quota Strategica (70%)", f"€{int(q_strat)}")
    st.info("Usa i 3.000€ su Revolut per colmare il gap del settore che ha lo Score più alto nel Radar.")
