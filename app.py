import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Pro Terminal", layout="wide")

# Bottone per forzare l'aggiornamento dei dati
if st.sidebar.button("🔄 AGGIORNA DATI REAL-TIME"):
    st.cache_data.clear()
    st.toast("Dati ricaricati dal mercato!")

@st.cache_data(ttl=300) # Aggiornamento ogni 5 minuti
def get_full_analysis(ticker):
    try:
        # Scarichiamo dati più ampi per SMA200
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if data.empty: return None
        
        info = yf.Ticker(ticker).info
        curr_p = float(data['Close'].iloc[-1])
        
        # 1. TRENDLINES (Breve, Medio, Lungo)
        sma20 = data['Close'].rolling(20).mean().iloc[-1]
        sma50 = data['Close'].rolling(50).mean().iloc[-1]
        sma200 = data['Close'].rolling(200).mean().iloc[-1]
        
        # 2. MOMENTUM (RSI 14)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
        
        # 3. VOLATILITÀ (ATR su 14 giorni)
        high_low = data['High'] - data['Low']
        atr = high_low.rolling(14).mean().iloc[-1]
        vol_score = (atr / curr_p) * 100
        
        # 4. STAGIONALITÀ (Media Febbraio ultimi 5 anni)
        data['Month'] = data.index.month
        feb_avg = data[data['Month'] == 2]['Close'].pct_change().mean() * 100

        # CALCOLO MARCO-SCORE (Ponderato)
        score = 50
        if curr_p > sma200: score += 15 # Trend Lungo OK
        if curr_p > sma50: score += 10  # Trend Medio OK
        if rsi < 35: score += 15       # Ipervenduto (Accumulo)
        if vol_score < 2: score += 10   # Bassa volatilità (Stabilità)

        return {
            "Symbol": ticker, "Nome": info.get('shortName', ticker),
            "Prezzo": round(curr_p, 2), "Score": int(score),
            "L": curr_p > sma200, "M": curr_p > sma50, "B": curr_p > sma20,
            "RSI": round(rsi, 2), "Vol": round(vol_score, 2),
            "Season": round(feb_avg, 2), "History": data
        }
    except: return None

# --- UI ---
st.title("🏹 MARCO-QUANT GLOBAL TERMINAL v2.0")
st.write(f"Dati aggiornati al: **{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}**")

# TITOLI RICHIESTI
watchlist = ["BTC-EUR", "ETH-EUR", "LDO.MI", "ENEL.MI", "NOVO-B.CO", "GOOGL", "BRK-B"]

tab1, tab2, tab3 = st.tabs(["📊 RADAR OPERATIVO", "💼 PORTAFOGLIO FINECO", "🚀 REVOLUT 3K"])

with tab1:
    for t in watchlist:
        d = get_full_analysis(t)
        if d:
            with st.container():
                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 2.5])
                c1.subheader(f"{d['Nome']} ({d['Symbol']})")
                c2.metric("Prezzo", f"€{d['Prezzo']}")
                
                # Visualizzazione Trend B M L
                trend_html = f"""
                <div style='display:flex; gap:10px;'>
                    <div style='background:{"#23d160" if d["L"] else "#ff3860"}; padding:5px; border-radius:5px; color:white;'>L</div>
                    <div style='background:{"#23d160" if d["M"] else "#ff3860"}; padding:5px; border-radius:5px; color:white;'>M</div>
                    <div style='background:{"#23d160" if d["B"] else "#ff3860"}; padding:5px; border-radius:5px; color:white;'>B</div>
                </div>
                """
                c3.markdown(trend_html, unsafe_allow_html=True)
                c3.write(f"**Score:** {d['Score']}/100")
                
                with c4:
                    exp = st.expander("Vedi Analisi Tecnica e Stagionalità")
                    with exp:
                        st.write(f"**RSI:** {d['RSI']} | **Volatilità:** {d['Vol']}% | **Media Febbraio:** {d['Season']}%")
                        fig = go.Figure(data=[go.Candlestick(x=d['History'].index[-60:], open=d['History']['Open'], high=d['History']['High'], low=d['History']['Low'], close=d['History']['Close'])])
                        fig.update_layout(height=250, margin=dict(l=0,r=0,b=0,t=0), template="plotly_white", xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
            st.divider()

with tab3:
    st.header("Strategia Revolut (3.000€)")
    btc = get_full_analysis("BTC-EUR")
    if btc and btc['Prezzo'] < 56000:
        st.error(f"⚠️ ALLERTA CRASH: Bitcoin a €{btc['Prezzo']}. RSI a {btc['RSI']}.")
        st.write("L'inversione crypto **NON** è confermata. I semafori B e M sono Rossi 🔴. Usare i 3.000€ ora è puro 'Catching the Falling Knife'.")
        st.info("💡 Attendi che il semaforo B (Breve periodo) torni verde o che l'RSI scenda sotto 30 (Ipervenduto estremo) prima di entrare.")
