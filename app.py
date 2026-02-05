import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE UI ---
st.set_page_config(page_title="Marco-Quant Global Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .status-led { height: 18px; width: 18px; border-radius: 50%; display: inline-block; margin-right: 5px; border: 1px solid #30363d; }
    .led-green { background-color: #23d160; box-shadow: 0 0 10px #23d160; }
    .led-red { background-color: #ff3860; box-shadow: 0 0 10px #ff3860; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #161b22; border-radius: 5px; padding: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI ANALISI ---
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2y", auto_adjust=True)
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Score Vantaggio (Z-Score)
        z = (sma20 - close) / (std20 if std20 > 0 else 1)
        score = int(np.clip((1 / (1 + np.exp(-z)) * 100), 0, 100))
        
        return {
            "Ticker": ticker,
            "Nome": t.info.get('shortName', ticker),
            "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Score": score,
            "History": df
        }
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("💰 Gestione Patrimonio")
    cap_tot = st.number_input("Capitale Totale (€)", value=10000)
    pac = st.number_input("PAC Mensile (€)", value=500)
    st.divider()
    st.info("Logica 30/70: 30% Aggressivo (Azioni/Crypto), 70% Strategico (ETF/Bond/Materie).")

st.title("🏹 Marco-Quant: Global Market Radar")

# --- CATEGORIE MERCATI ---
categorie = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "STMMI.MI", "PST.MI", "AZM.MI"],
    "🇺🇸 USA": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "AVGO"],
    "🇪🇺 Europa": ["NOVO-B.CO", "ASML.AS", "MC.PA", "SAP.DE", "OR.PA", "SIE.DE"],
    "📊 ETF (Strategico)": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "VUSA.L", "IBCI.MI", "TLT", "IEF"],
    "🪙 Crypto & Materie": ["BTC-EUR", "ETH-EUR", "SOL-EUR", "GC=F", "CL=F", "PA=F"]
}

tabs = st.tabs(list(categorie.keys()) + ["📈 Road to 1 Million"])

# --- GENERAZIONE TABELLE PER OGNI MERCATO ---
for i, (label, tickers) in enumerate(categorie.items()):
    with tabs[i]:
        st.subheader(f"Analisi Quantitativa: {label}")
        if st.button(f"Aggiorna {label}"):
            results = [get_analysis(t) for t in tickers if get_analysis(t)]
            df_res = pd.DataFrame(results)
            
            # Header
            c_h = st.columns([2, 2, 1, 1, 1, 1])
            c_h[0].write("**Asset**")
            c_h[1].write("**Score Vantaggio**")
            c_h[2].write("**L**")
            c_h[3].write("**M**")
            c_h[4].write("**B**")
            c_h[5].write("**Prezzo**")
            
            for _, row in df_res.sort_values("Score", ascending=False).iterrows():
                cols = st.columns([2, 2, 1, 1, 1, 1])
                cols[0].write(f"**{row['Nome']}**")
                cols[1].progress(row['Score']/100)
                
                # Semafori
                cols[2].markdown(f'<div class="status-led {"led-green" if row["L"] else "led-red"}"></div>', unsafe_allow_html=True)
                cols[3].markdown(f'<div class="status-led {"led-green" if row["M"] else "led-red"}"></div>', unsafe_allow_html=True)
                cols[4].markdown(f'<div class="status-led {"led-green" if row["B"] else "led-red"}"></div>', unsafe_allow_html=True)
                cols[5].write(f"€{row['Prezzo']}")
                
                with st.expander("Analisi Dettagliata"):
                    col_sx, col_dx = st.columns([3, 2])
                    # Grafico
                    fig = go.Figure(data=[go.Candlestick(x=row['History'].index, open=row['History']['Open'], high=row['History']['High'], low=row['History']['Low'], close=row['History']['Close'])])
                    fig.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,b=0,t=0))
                    col_sx.plotly_chart(fig, use_container_width=True)
                    # Strategia
                    col_dx.write("### 🏹 Operatività")
                    if row['Score'] > 80 and row['B']:
                        col_dx.success("SEGNALE: ACCUMULO IMMEDIATO")
                    elif row['Score'] > 70:
                        col_dx.warning("SEGNALE: ATTENDI VERDE SU BREVE (B)")
                    else:
                        col_dx.error("SEGNALE: ATTENDI SCONTO STATISTICO")
                    col_dx.write(f"**Target Entry:** €{round(row['Prezzo']*0.98, 2)}")
                    col_dx.write(f"**Target Exit:** €{round(row['Prezzo']*1.10, 2)}")

# --- TAB PROIEZIONE 1 MILIONE ---
with tabs[-1]:
    st.header("💰 Obiettivo 1.000.000€")
    anni = st.slider("Seleziona Orizzonte Temporale (Anni)", 5, 40, 25)
    tasso_stimato = 0.09 # 9% annuo medio
    progressione = []
    cap = cap_tot
    for m in range(anni * 12):
        cap = (cap + pac) * (1 + tasso_stimato/12)
        if m % 12 == 0: progressione.append(cap)
    
    fig_m = go.Figure(data=[go.Scatter(y=progressione, line=dict(color='#23d160', width=4))])
    fig_m.add_hline(y=1000000, line_dash="dash", line_color="gold", annotation_text="TARGET 1 MILIONE")
    fig_m.update_layout(template="plotly_dark", title="Proiezione Crescita con Interesse Composto")
    st.plotly_chart(fig_m, use_container_width=True)
