import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione UI
st.set_page_config(page_title="Marco-Quant Global Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .score-giant { font-size: 48px; font-weight: bold; text-align: center; border-radius: 12px; padding: 15px; border: 2px solid #30363d; margin: 10px 0; }
    .top-card { background-color: #161b22; border-radius: 15px; padding: 20px; border: 1px solid #30363d; text-align: center; height: 100%; }
    .stMetric { background-color: #1c2128; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state: st.session_state.portfolio = []

# Analisi Multi-Fattore potenziata
@st.cache_data(ttl=3600)
def get_full_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].tail(20).mean()
        
        # Calcolo Score 0-100 (Tecnica, Volumi, Volatilità)
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 60) + (20 if close > sma200 else 0) + (20 if vol_ratio > 1.3 else 0), 0, 100))
        
        color = "#23d160" if score > 75 else "#ffdd57" if score > 50 else "#ff3860"
        
        return {
            "Ticker": ticker, "Nome": t.info.get('shortName', ticker), "Prezzo": round(close, 2),
            "Score": score, "Color": color, "L": close > sma200, "M": close > df['Close'].rolling(50).mean().iloc[-1],
            "B": close > sma20, "History": df, "Div": t.info.get('dividendYield', 0)
        }
    except: return None

st.title("🏹 Marco-Quant Global Terminal v11.0")

# --- HOME: TOP 5 SU PANIERE GLOBALE ---
st.subheader("🔥 Top 5 Opportunità Globali (Scansione su 50+ Asset)")
# Paniere esteso per la scansione della Top 5
global_basket = [
    "LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "STMMI.MI", "ENI.MI", # Italia
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "AVGO", "NFLX", # USA
    "NOVO-B.CO", "ASML.AS", "MC.PA", "SAP.DE", "OR.PA", "SIE.DE", # Europa
    "BTC-EUR", "ETH-EUR", "SOL-EUR", "GC=F", "CL=F", "HG=F", # Crypto & Commodities
    "SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT", "VUSA.L" # ETF & Bond
]

if st.button("🚀 AVVIA SCANSIONE GLOBALE TOP 5"):
    results = []
    bar = st.progress(0)
    for i, t in enumerate(global_basket):
        res = get_full_analysis(t)
        if res: results.append(res)
        bar.progress((i + 1) / len(global_basket))
    
    top_5 = pd.DataFrame(results).sort_values("Score", ascending=False).head(5)
    cols = st.columns(5)
    for i, (_, row) in enumerate(top_5.iterrows()):
        with cols[i]:
            st.markdown(f"""<div class="top-card">
                <p style="margin:0; font-size:12px; color:#8b949e;">{row['Ticker']}</p>
                <h4 style="margin:5px 0;">{row['Nome'][:15]}</h4>
                <div class="score-giant" style="color:{row['Color']}; background:{row['Color']}15;">{row['Score']}</div>
                <p>L:{'🟢' if row['L'] else '🔴'} M:{'🟢' if row['M'] else '🔴'} B:{'🟢' if row['B'] else '🔴'}</p>
            </div>""", unsafe_allow_html=True)

st.divider()

# --- RICERCA E AGGIUNTA ---
st.subheader("🔍 Ricerca Ticker e Aggiunta Portafoglio")
c1, c2, c3 = st.columns([3, 1, 1])
ticker_input = c1.text_input("Cerca Ticker (es: LDO.MI, BTC-EUR, NVDA, GC=F)").upper()
qty_input = c2.number_input("Quantità", min_value=0.0, step=1.0)

if ticker_input:
    data = get_full_analysis(ticker_input)
    if data:
        col_res1, col_res2 = st.columns([2, 1])
        with col_res1:
            st.markdown(f"**Risultato:** {data['Nome']} | Prezzo: **€{data['Prezzo']}**")
            st.markdown(f"<div style='color:{data['Color']}; font-size:24px; font-weight:bold;'>SCORE: {data['Score']}/100</div>", unsafe_allow_html=True)
        if c3.button("➕ Aggiungi"):
            st.session_state.portfolio.append({"ticker": ticker_input, "qty": qty_input, "price": data['Prezzo']})
            st.success("Aggiunto!")
        
        # Grafico Automatico al Click
        fig = go.Figure(data=[go.Candlestick(x=data['History'].index, open=data['History']['Open'], 
                        high=data['History']['High'], low=data['History']['Low'], close=data['History']['Close'])])
        fig.update_layout(template="plotly_dark", height=400, title=f"Trend {data['Nome']}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Ticker non valido. Ricorda: .MI per Italia, .DE per Germania, -EUR per Crypto.")

# --- PORTAFOGLIO E ROAD TO 1M ---
st.divider()
st.subheader("💼 Il Mio Portafoglio & Proiezione Milione")
if st.session_state.portfolio:
    total_val = 0
    p_data = []
    for item in st.session_state.portfolio:
        d = get_full_analysis(item['ticker'])
        v = d['Prezzo'] * item['qty']
        total_val += v
        p_data.append({"Asset": d['Nome'], "Qty": item['qty'], "Valore": f"€{v:,.2f}", "Score": d['Score']})
    
    st.table(pd.DataFrame(p_data))
    st.metric("VALORE TOTALE ATTUALE", f"€{total_val:,.2f}")
    
    # Calcolo Milione
    pac = st.number_input("Tuo PAC Mensile (€)", value=500)
    prog = []
    cap = total_val
    for m in range(480):
        cap = (cap + pac) * (1 + 0.09/12)
        if m % 12 == 0: prog.append(cap)
    st.plotly_chart(go.Figure(data=[go.Scatter(y=prog, line=dict(color='#23d160'))]).update_layout(template="plotly_dark", title="Verso il Milione"))
