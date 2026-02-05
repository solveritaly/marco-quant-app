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
    .score-giant { font-size: 40px; font-weight: bold; text-align: center; border-radius: 10px; padding: 10px; margin: 5px; }
    .top-card { background-color: #161b22; border-radius: 15px; padding: 15px; border: 1px solid #30363d; text-align: center; }
    .led { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-left: 5px; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state: st.session_state.portfolio = []

# --- FUNZIONE DI ANALISI AVANZATA ---
@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        info = t.info
        close = df['Close'].iloc[-1]
        
        # 1. Tecnica & Trend
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        
        # 2. Volatilità & Volumi
        std20 = df['Close'].rolling(20).std().iloc[-1]
        z_score = (sma20 - close) / std20 if std20 > 0 else 0
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].tail(20).mean()
        
        # 3. Calcolo Score Dinamico (0-100)
        score = int(np.clip(((1 / (1 + np.exp(-z_score))) * 60) + (20 if close > sma200 else 0) + (20 if vol_ratio > 1.2 else 0), 0, 100))
        
        return {
            "Ticker": ticker, "Nome": info.get('shortName', ticker), "Prezzo": round(close, 2),
            "Score": score, "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Color": "#23d160" if score > 75 else "#ffdd57" if score > 50 else "#ff3860",
            "History": df, "Div": info.get('dividendYield', 0)
        }
    except: return None

# --- HOME SCREEN: TOP 5 E RICERCA ---
st.title("🏹 Marco-Quant Global Terminal")

tabs = st.tabs(["🏠 Home & Top Picks", "🗺️ Esplora Mercati", "💼 Portafoglio", "📈 Road to 1M"])

with tabs[0]:
    st.subheader("🔥 Top 5 Opportunità del Momento")
    # Scan rapido su una selezione globale per la Home
    seed_list = ["LDO.MI", "NVDA", "BTC-EUR", "NOVO-B.CO", "GC=F", "AAPL", "MSFT", "ETH-EUR", "ASML.AS", "ISP.MI"]
    top_picks = []
    with st.spinner("Analizzando i mercati..."):
        for s in seed_list:
            res = get_analysis(s)
            if res: top_picks.append(res)
    
    top_df = pd.DataFrame(top_picks).sort_values("Score", ascending=False).head(5)
    
    cols = st.columns(5)
    for i, (_, row) in enumerate(top_df.iterrows()):
        with cols[i]:
            st.markdown(f"""<div class="top-card">
                <small>{row['Ticker']}</small>
                <h3>{row['Nome'][:12]}</h3>
                <div class="score-giant" style="color:{row['Color']}; background:{row['Color']}22;">{row['Score']}</div>
                <small>L:{'🟢' if row['L'] else '🔴'} M:{'🟢' if row['M'] else '🔴'} B:{'🟢' if row['B'] else '🔴'}</small>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("🔍 Cerca e Aggiungi Titolo (Tutto il Mondo)")
    c1, c2, c3 = st.columns([3, 1, 1])
    search_ticker = c1.text_input("Inserisci Ticker (es: TSLA, ENI.MI, ETH-EUR, US10Y)").upper()
    qty = c2.number_input("Quantità", min_value=0.0, step=1.0)
    
    if search_ticker:
        res_search = get_analysis(search_ticker)
        if res_search:
            st.markdown(f"**Risultato:** {res_search['Nome']} - Prezzo: €{res_search['Prezzo']}")
            if c3.button("Aggiungi in Portafoglio"):
                st.session_state.portfolio.append({"ticker": search_ticker, "qty": qty, "price": res_search['Prezzo']})
                st.success("Aggiunto!")
        else:
            st.error("Ticker non trovato. Usa i suffissi: .MI (Italia), .DE (Germania), -EUR (Crypto).")

with tabs[1]:
    mercati = {
        "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
        "🇺🇸 USA": ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN"],
        "🇪🇺 Europa": ["NOVO-B.CO", "ASML.AS", "MC.PA"],
        "📊 ETF & Bond": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT"],
        "🪙 Crypto/Materie": ["BTC-EUR", "GC=F", "CL=F"]
    }
    sel = st.selectbox("Seleziona Categoria", list(mercati.keys()))
    m_data = [get_analysis(t) for t in mercati[sel] if get_analysis(t)]
    for row in m_data:
        col = st.columns([2, 1, 1, 1, 1])
        col[0].write(f"**{row['Nome']}**")
        col[1].markdown(f"<span style='color:{row['Color']}; font-weight:bold; font-size:20px;'>{row['Score']}</span>", unsafe_allow_html=True)
        col[2].write(f"L:{'🟢' if row['L'] else '🔴'} M:{'🟢' if row['M'] else '🔴'} B:{'🟢' if row['B'] else '🔴'}")
        col[3].write(f"€{row['Prezzo']}")
        if col[4].button("Grafico", key=row['Ticker']):
            st.plotly_chart(go.Figure(data=[go.Candlestick(x=row['History'].index, open=row['History']['Open'], high=row['History']['High'], low=row['History']['Low'], close=row['History']['Close'])]).update_layout(template="plotly_dark", height=300))

with tabs[2]:
    st.header("💼 Il Mio Portafoglio Reale")
    if not st.session_state.portfolio:
        st.info("Portafoglio vuoto. Cerca un titolo in Home e clicca 'Aggiungi'.")
    else:
        p_list = []
        tot = 0
        for item in st.session_state.portfolio:
            d = get_analysis(item['ticker'])
            val = d['Prezzo'] * item['qty']
            tot += val
            p_list.append({"Asset": d['Nome'], "Quantità": item['qty'], "Valore": f"€{val:,.2f}", "Score": d['Score']})
        st.table(pd.DataFrame(p_list))
        st.metric("Valore Totale", f"€{tot:,.2f}")

with tabs[3]:
    st.header("📈 Road to 1 Million")
    pac = st.number_input("PAC Mensile (€)", value=500)
    current_val = sum([get_analysis(i['ticker'])['Prezzo']*i['qty'] for i in st.session_state.portfolio]) if st.session_state.portfolio else 1000
    prog = []
    for m in range(480):
        current_val = (current_val + pac) * (1 + 0.09/12)
        if m % 12 == 0: prog.append(current_val)
    st.plotly_chart(go.Figure(data=[go.Scatter(y=prog, name="Capitale", line=dict(color='#23d160', width=4))]).update_layout(template="plotly_dark"))
