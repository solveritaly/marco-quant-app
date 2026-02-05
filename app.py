import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURAZIONE UI AVANZATA ---
st.set_page_config(page_title="Marco-Quant Elite Terminal", layout="wide")

# CSS per Sidebar, Pop-up (Expander) e Score
st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e6edf3; }
    .stApp { background-image: radial-gradient(circle at top right, #1d2129, #0b0e14); }
    .score-card { 
        background: linear-gradient(145deg, #1c2128, #161b22);
        border: 1px solid #30363d;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .score-value { font-size: 54px; font-weight: 800; line-height: 1; margin: 10px 0; }
    .led-box { display: flex; justify-content: center; gap: 10px; margin-top: 10px; }
    .led { height: 12px; width: 12px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.1); }
    .led-on { box-shadow: 0 0 8px currentColor; }
    /* Nascondi scrollbar brutte */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI RICERCA PREDIETTIVA (Dizionario Integrato) ---
# Un elenco dei ticker più comuni per l'auto-completamento
COMMON_TICKERS = [
    "LDO.MI (Leonardo)", "ENEL.MI (Enel)", "ISP.MI (Intesa)", "UCG.MI (Unicredit)", "RACE.MI (Ferrari)",
    "NVDA (Nvidia)", "AAPL (Apple)", "MSFT (Microsoft)", "TSLA (Tesla)", "BTC-EUR (Bitcoin)",
    "GC=F (Oro)", "SWDA.MI (MSCI World)", "NOVO-B.CO (Novo Nordisk)", "ASML.AS (ASML)"
]

# --- ANALISI & CACHE (Aggiornamento ogni ora) ---
@st.cache_data(ttl=3600) # Questa riga garantisce l'aggiornamento automatico ogni ora
def fetch_analysis(ticker):
    try:
        ticker_clean = ticker.split(" ")[0]
        t = yf.Ticker(ticker_clean)
        df = t.history(period="1y")
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        z = (sma20 - close) / std20 if std20 > 0 else 0
        
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > df['Close'].rolling(200).mean().iloc[-1] else 0), 0, 100))
        color = "#23d160" if score > 75 else "#ffdd57" if score > 50 else "#ff3860"
        
        return {
            "ticker": ticker_clean, "nome": t.info.get('shortName', ticker_clean),
            "prezzo": round(close, 2), "score": score, "color": color,
            "L": close > df['Close'].rolling(200).mean().iloc[-1],
            "M": close > df['Close'].rolling(50).mean().iloc[-1],
            "B": close > sma20, "history": df
        }
    except: return None

# --- UI PRINCIPALE ---
st.title("🏹 Marco-Quant Elite")

# 1. TOP 5 AUTOMATICA (In alto, orizzontale)
st.subheader("🔥 Top Picks del Momento")
top_basket = ["LDO.MI", "NVDA", "BTC-EUR", "NOVO-B.CO", "GC=F"]
cols = st.columns(5)
for i, t in enumerate(top_basket):
    data = fetch_analysis(t)
    if data:
        with cols[i]:
            st.markdown(f"""
                <div class="score-card">
                    <div style="color:#8b949e; font-size:12px;">{data['ticker']}</div>
                    <div class="score-value" style="color:{data['color']};">{data['score']}</div>
                    <div class="led-box">
                        <span class="led {'led-on' if data['L'] else ''}" style="color:{'#23d160' if data['L'] else '#ff3860'}; background:{'#23d160' if data['L'] else '#ff3860'};"></span>
                        <span class="led {'led-on' if data['M'] else ''}" style="color:{'#23d160' if data['M'] else '#ff3860'}; background:{'#23d160' if data['M'] else '#ff3860'};"></span>
                        <span class="led {'led-on' if data['B'] else ''}" style="color:{'#23d160' if data['B'] else '#ff3860'}; background:{'#23d160' if data['B'] else '#ff3860'};"></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

st.divider()

# 2. RICERCA PREDITTIVA & POP-UP DETTAGLI
st.subheader("🔍 Ricerca Asset Intelligente")
col_search, col_qty = st.columns([3, 1])

# Qui l'utente può scrivere e scegliere dalla lista
selected_ticker = col_search.selectbox(
    "Inizia a scrivere il nome o il ticker...",
    options=COMMON_TICKERS,
    index=None,
    placeholder="Es: Leo... o LDO.MI",
)

if selected_ticker:
    with st.spinner('Analisi in corso...'):
        res = fetch_analysis(selected_ticker)
        if res:
            # Layout a schede per non scorrere verso il basso
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""
                    <div class="score-card" style="margin-top:20px;">
                        <h3>{res['nome']}</h3>
                        <div class="score-value" style="color:{res['color']}; font-size:80px;">{res['score']}</div>
                        <p>Prezzo attuale: €{res['prezzo']}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("➕ Aggiungi al Portafoglio"):
                    # Logica aggiunta (omessa per brevità, ma presente nel tuo stato)
                    st.toast(f"{res['nome']} aggiunto!")

            with c2:
                # Grafico in una scheda popup
                with st.expander("📈 Visualizza Grafico Tecnico e Volumi", expanded=True):
                    fig = go.Figure(data=[go.Candlestick(
                        x=res['history'].index, open=res['history']['Open'],
                        high=res['history']['High'], low=res['history']['Low'], close=res['history']['Close']
                    )])
                    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,b=0,t=0))
                    st.plotly_chart(fig, use_container_width=True)

# 3. ROAD TO 1 MILLION (In un popup separato)
st.divider()
with st.expander("🚀 PROIEZIONE VERSO IL MILIONE (Clicca per espandere)"):
    # Qui inseriamo la logica del PAC e il grafico della crescita
    st.write("Configura il tuo piano di accumulo basato sugli asset selezionati.")
    # ... (codice proiezione visto prima)
