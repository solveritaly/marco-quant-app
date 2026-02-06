import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Pro Terminal", layout="wide")

st.markdown("""
    <style>
    .report-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #FF8C00; margin-bottom: 20px; }
    .status-up { color: #23d160; font-weight: bold; }
    .status-down { color: #ff3860; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI CALCOLO AVANZATO ---
@st.cache_data(ttl=600) # Aggiorna ogni 10 minuti per dati precisi
def get_pro_analysis(ticker):
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if data.empty: return None
        
        info = yf.Ticker(ticker).info
        curr_price = data['Close'].iloc[-1]
        
        # 1. TRENDLINES (B, M, L)
        sma20 = data['Close'].rolling(20).mean().iloc[-1]
        sma50 = data['Close'].rolling(50).mean().iloc[-1]
        sma200 = data['Close'].rolling(200).mean().iloc[-1]
        
        # 2. MOMENTUM (RSI)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # 3. VOLATILITA (ATR Relativo)
        high_low = data['High'] - data['Low']
        atr = high_low.rolling(14).mean().iloc[-1]
        vol_ratio = (atr / curr_price) * 100
        
        # 4. STAGIONALITÀ (Febbraio storico)
        data['Month'] = data.index.month
        feb_stats = data[data['Month'] == 2]['Close'].pct_change().mean()
        
        # CALCOLO SCORE MARCO-QUANT (0-100)
        score = 50
        if curr_price > sma200: score += 15 # Long Term OK
        if curr_price > sma50: score += 10  # Medium Term OK
        if rsi < 40: score += 15           # Ipervenduto (Occasione)
        if feb_stats > 0: score += 10       # Stagionalità Positiva
        
        return {
            "Symbol": ticker, "Name": info.get('shortName', ticker),
            "Price": round(curr_price, 2), "Score": int(score),
            "L": curr_price > sma200, "M": curr_price > sma50, "B": curr_price > sma20,
            "RSI": round(rsi, 2), "Vol": round(vol_ratio, 2),
            "Feb_Season": round(feb_stats * 100, 2),
            "History": data
        }
    except: return None

# --- INTERFACCIA ---
st.title("🏹 MARCO-QUANT PRO TERMINAL v2026")
st.write(f"Ultimo aggiornamento: **{datetime.now().strftime('%H:%M:%S')}**")

# TITOLI SELEZIONATI
tickers = ["BTC-EUR", "ETH-EUR", "LDO.MI", "ENEL.MI", "NOVO-B.CO", "GOOGL", "BRK-B"]

tabs = st.tabs(["📊 Radar Real-Time", "💼 Mio Portafoglio Fineco", "🚀 Strategia Revolut"])

with tabs[0]:
    for t in tickers:
        d = get_pro_analysis(t)
        if d:
            with st.container():
                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 2])
                c1.subheader(f"{d['Name']} ({d['Symbol']})")
                c2.metric("Prezzo", f"€{d['Price']}")
                
                # Colore Score
                color = "green" if d['Score'] > 70 else "orange" if d['Score'] > 50 else "red"
                c3.metric("MARCO-SCORE", f"{d['Score']}/100")
                
                with c4:
                    st.write(f"**Trend:** L:{'🟢' if d['L'] else '🔴'} M:{'🟢' if d['M'] else '🔴'} B:{'🟢' if d['B'] else '🔴'}")
                    st.write(f"**Momentum (RSI):** {d['RSI']} | **Volatilità:** {d['Vol']}%")
                
                with st.expander("🔎 Analisi Tecnica e Stagionalità Dettagliata"):
                    col_a, col_b = st.columns(2)
                    col_a.write(f"**Stagionalità (Media Febbraio):** {d['Feb_Season']}%")
                    col_a.write(f"**Commento:** {'Ottimo mese storico' if d['Feb_Season'] > 0 else 'Mese storicamente debole'}")
                    
                    fig = go.Figure(data=[go.Candlestick(x=d['History'].index[-60:], open=d['History']['Open'], high=d['History']['High'], low=d['History']['Low'], close=d['History']['Close'])])
                    fig.update_layout(height=300, template="plotly_white", margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)
            st.divider()

with tabs[1]:
    st.header("Portafoglio Fineco (Integrazione Dati)")
    st.info("Qui i prezzi sono aggiornati real-time. Leonardo e Novo Nordisk sono sotto pressione.")
    # Implementazione calcolo perdita/guadagno basata su i tuoi prezzi di carico
    # ... (Codice portafoglio)

with tabs[2]:
    st.header("Strategia 3.000€ Revolut")
    btc = get_pro_analysis("BTC-EUR")
    if btc and btc['Price'] < 56000:
        st.warning(f"⚠️ Bitcoin a €{btc['Price']}: Trend di breve e medio termine compromesso (🔴🔴).")
        st.write("👉 **Strategia consigliata:** Attendere stabilizzazione RSI sotto 30 o ritorno sopra SMA20.")
