import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Ultimate Terminal", layout="wide")

# --- DATABASE PORTAFOGLIO (Session State per salvare i dati mentre navighi) ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- FUNZIONE ANALISI MULTI-FATTORE (0-100) ---
def get_full_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="2y")
        if df.empty: return None
        
        # 1. Analisi Tecnica & Momentum (30%)
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        momentum = (close / df['Close'].iloc[-20]) - 1
        
        # 2. Volatilità & Volumi (30%)
        std20 = df['Close'].rolling(20).std().iloc[-1]
        z_score = (sma20 - close) / std20 if std20 > 0 else 0
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].tail(20).mean()
        
        # 3. Stagionalità Statistica (20%)
        month_now = datetime.now().month
        hist_returns = df['Close'].pct_change().groupby(df.index.month).mean()
        seasonality_factor = hist_returns.get(month_now, 0)
        
        # CALCOLO SCORE FINALE (0-100)
        # Più il prezzo è a sconto (z_score alto), momentum positivo e volumi alti, più lo score sale
        score_tech = np.clip((1 / (1 + np.exp(-z_score))) * 50, 0, 50)
        score_mom = 25 if momentum > 0 else 5
        score_vol = 15 if vol_ratio > 1.2 else 5
        score_seas = 10 if seasonality_factor > 0 else 0
        
        total_score = int(score_tech + score_mom + score_vol + score_seas)
        
        return {
            "Ticker": ticker, "Nome": t.info.get('shortName', ticker),
            "Prezzo": round(close, 2), "Score": total_score,
            "L": close > sma200, "M": close > df['Close'].rolling(50).mean().iloc[-1], "B": close > sma20,
            "History": df, "Div": (t.info.get('dividendYield', 0) or 0)
        }
    except: return None

# --- SIDEBAR: CREAZIONE PORTAFOGLIO ---
with st.sidebar:
    st.header("🛒 Gestione Portafoglio")
    with st.form("add_asset"):
        t_input = st.text_input("Ticker (es. LDO.MI, BTC-EUR, NVDA)").upper()
        q_input = st.number_input("Quantità Acquistata", min_value=0.0, step=1.0)
        if st.form_submit_button("Aggiungi al Portafoglio"):
            if t_input:
                asset_data = get_full_analysis(t_input)
                if asset_data:
                    st.session_state.portfolio.append({"ticker": t_input, "qty": q_input, "price": asset_data['Prezzo']})
                    st.success(f"Aggiunto {t_input}")
    
    if st.session_state.portfolio:
        st.write("---")
        if st.button("Svuota Portafoglio"):
            st.session_state.portfolio = []
            st.rerun()

# --- MAIN INTERFACE ---
st.title("🏹 Marco-Quant Master Terminal")

tabs = st.tabs(["🌍 Radar Mercati", "💼 Mio Portafoglio", "📈 Road to 1 Million"])

# TAB 1: RADAR (AUTO-LOAD)
with tabs[0]:
    mercati = {
        "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
        "🇺🇸 USA": ["NVDA", "AAPL", "MSFT", "GOOGL", "TSLA"],
        "📊 ETF & Strategico": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "GC=F", "BTC-EUR"]
    }
    sel_mkt = st.selectbox("Cambia Mercato", list(mercati.keys()))
    
    # Caricamento automatico
    results = []
    with st.spinner('Aggiornamento dati real-time...'):
        for t in mercati[sel_mkt]:
            data = get_full_analysis(t)
            if data: results.append(data)
    
    df_res = pd.DataFrame(results)
    for _, row in df_res.sort_values("Score", ascending=False).iterrows():
        c = st.columns([2, 2, 1, 1, 1, 1])
        c[0].write(f"**{row['Nome']}**")
        c[1].progress(row['Score']/100, text=f"Score: {row['Score']}")
        c[2].markdown(f"L: {'🟢' if row['L'] else '🔴'}")
        c[3].markdown(f"M: {'🟢' if row['M'] else '🔴'}")
        c[4].markdown(f"B: {'🟢' if row['B'] else '🔴'}")
        c[5].write(f"€{row['Prezzo']}")

# TAB 2: PORTAFOGLIO REALE
with tabs[1]:
    st.header("💼 Situazione Attuale")
    if not st.session_state.portfolio:
        st.info("Il tuo portafoglio è vuoto. Aggiungi titoli dalla barra laterale.")
    else:
        total_val = 0
        port_list = []
        for item in st.session_state.portfolio:
            d = get_full_analysis(item['ticker'])
            val = d['Prezzo'] * item['qty']
            total_val += val
            port_list.append({"Asset": d['Nome'], "Quantità": item['qty'], "Valore Attuale": f"€{val:,.2f}", "Score": d['Score']})
        
        st.table(pd.DataFrame(port_list))
        st.metric("VALORE TOTALE PORTAFOGLIO", f"€{total_val:,.2f}")

# TAB 3: ROAD TO 1 MILLION (DINAMICA)
with tabs[2]:
    st.header("🚀 Obiettivo 1.000.000€")
    cap_attuale = total_val if st.session_state.portfolio else 1000
    pac = st.number_input("PAC Mensile (€)", value=500)
    rendimento = st.slider("Rendimento Annuo Stimato (%)", 5, 15, 9) / 100
    
    progressione = []
    temp_cap = cap_attuale
    for m in range(480): # 40 anni
        temp_cap = (temp_cap + pac) * (1 + rendimento/12)
        if m % 12 == 0: progressione.append(temp_cap)
        if temp_cap >= 1000000 and 'traguardo' not in locals():
            traguardo = m // 12
    
    st.plotly_chart(go.Figure(data=[go.Scatter(y=progressione, name="Capitale", line=dict(color='#23d160', width=4))]).update_layout(template="plotly_dark"))
    
    if 'traguardo' in locals():
        st.success(f"🎯 Con questo portafoglio e questo PAC, raggiungerai il Milione in **{traguardo} anni**!")
    else:
        st.warning("Il milione è lontano, prova ad aumentare il PAC o il rendimento degli asset selezionati.")
