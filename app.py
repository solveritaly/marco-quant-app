import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

st.markdown("""
    <style>
    .semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state: st.session_state.portfolio = {}

@st.cache_data(ttl=600)
def get_analysis(ticker):
    try:
        # LASCIAMO CHE YFINANCE GESTISCA LA CONNESSIONE DA SOLO
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Entry": round(close * 0.99, 2), "TP": round(close + (std20*3), 2), "SL": round(close - (std20*2), 2),
            "History": df
        }
    except Exception as e:
        return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- 2. TABELLE MERCATI ---
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL", "BRK-B"],
    "🇪🇺 Europa": ["ASML", "MC.PA", "SAP", "NOVO-B.CO"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

tabs = st.tabs(list(mercati.keys()) + ["💼 Portafoglio"])

for i, m_name in enumerate(mercati.keys()):
    with tabs[i]:
        st.write(f"### Analisi Trend {m_name}")
        for t in mercati[m_name]:
            d = get_analysis(t)
            if d:
                c1, c2, c3, cL, cM, cB, cAction = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.5])
                c1.write(f"**{d['Nome']}**")
                c2.write(f"**{d['Score']} pts**")
                c3.write(f"€{d['Price']}" if "MI" in t or "EUR" in t else f"${d['Price']}")
                
                cL.markdown(f'<div class="semaforo {"bg-green" if d["L"] else "bg-red"}">L</div>', unsafe_allow_html=True)
                cM.markdown(f'<div class="semaforo {"bg-green" if d["M"] else "bg-red"}">M</div>', unsafe_allow_html=True)
                cB.markdown(f'<div class="semaforo {"bg-green" if d["B"] else "bg-red"}">B</div>', unsafe_allow_html=True)
                
                with cAction:
                    with st.expander("➕"):
                        st.write(f"**Livelli:** Entry: {d['Entry']} | TP: {d['TP']} | SL: {d['SL']}")
                        fig = go.Figure(data=[go.Candlestick(x=d['History'].index, open=d['History']['Open'], high=d['History']['High'], low=d['History']['Low'], close=d['History']['Close'])])
                        fig.update_layout(height=250, template="plotly_white", margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
            st.divider()

with tabs[-1]:
    st.header("💼 Portafoglio")
    st.info("Qui vedrai il riepilogo Fineco una volta inseriti i titoli.")
