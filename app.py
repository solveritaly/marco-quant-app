import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="MARCO-QUANT ULTIMATE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3, h4, p, span, label, .stMarkdown { color: #FF8C00 !important; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #FF8C00; color: black; font-weight: bold; width: 100%; border-radius: 5px; border: none; }
    .stTextInput>div>div>input { background-color: #111111; color: #FF8C00; border: 1px solid #FF8C00; }
    .score-box { border: 2px solid #FF8C00; padding: 15px; border-radius: 10px; text-align: center; background-color: #0a0a0a; margin-bottom: 10px; }
    .big-num { font-size: 45px; font-weight: bold; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE PORTAFOGLIO ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- FUNZIONE ANALISI ---
@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > sma200 else 0), 0, 100))
        return {
            "symbol": ticker, "name": t.info.get('shortName', ticker),
            "price": round(close, 2), "score": score,
            "L": close > sma200, "M": close > df['Close'].rolling(50).mean().iloc[-1], "B": close > sma20,
            "df": df
        }
    except: return None

# --- SIDEBAR: AGGIUNGI AL PORTAFOGLIO ---
with st.sidebar:
    st.header("📥 AGGIUNGI TITOLO")
    new_t = st.text_input("Ticker (es. LDO.MI, BTC-EUR)").upper()
    new_q = st.number_input("Quantità", min_value=0.0, step=1.0)
    if st.button("SALVA IN PORTAFOGLIO"):
        if new_t:
            st.session_state.portfolio.append({"ticker": new_t, "qty": new_q})
            st.success("Aggiunto!")

# --- UI PRINCIPALE ---
st.title("🏹 MARCO-QUANT ULTIMATE TERMINAL")

# 1. TOP 5 AUTOMATICA (Home Screen)
st.subheader("🔥 TOP 5 OPPORTUNITÀ GLOBALI")
top_basket = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "NOVO-B.CO"]
cols_top = st.columns(5)
for i, t in enumerate(top_basket):
    data = get_analysis(t)
    if data:
        with cols_top[i]:
            st.markdown(f'<div class="score-box"><small>{data["symbol"]}</small><span class="big-num">{data["score"]}</span>'
                        f'<small>L:{"🟢" if data["L"] else "🔴"} M:{"🟢" if data["M"] else "🔴"} B:{"🟢" if data["B"] else "🔴"}</small></div>', unsafe_allow_html=True)

st.divider()

# 2. CATEGORIE MERCATI
tabs = st.tabs(["🇮🇹 ITALIA", "🇺🇸 USA", "🇪🇺 EUROPA", "📊 ETF & BOND", "🪙 CRYPTO & COMM", "💼 MIO PORTAFOGLIO"])

mercati = {
    "🇮🇹 ITALIA": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
    "🇺🇸 USA": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
    "🇪🇺 EUROPA": ["ASML.AS", "MC.PA", "SAP.DE", "OR.PA"],
    "📊 ETF & BOND": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT"],
    "🪙 CRYPTO & COMM": ["BTC-EUR", "ETH-EUR", "GC=F", "CL=F"]
}

for i, tab_name in enumerate(list(mercati.keys())):
    with tabs[i]:
        st.subheader(f"RADAR {tab_name}")
        for ticker in mercati[tab_name]:
            res = get_analysis(ticker)
            if res:
                c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
                c1.write(f"**{res['name']}**")
                c2.write(f"Score: {res['score']}")
                c3.write(f"€{res['price']}")
                if c4.button(f"Vedi Grafico {ticker}"):
                    fig = go.Figure(data=[go.Candlestick(x=res['df'].index, open=res['df']['Open'], high=res['df']['High'], low=res['df']['Low'], close=res['df']['Close'], increasing_line_color='#FF8C00', decreasing_line_color='#444444')])
                    fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font=dict(color='#FF8C00'), height=300)
                    st.plotly_chart(fig, use_container_width=True)

# 3. MIO PORTAFOGLIO & ROAD TO 1M
with tabs[5]:
    st.header("💼 PORTAFOGLIO REALE")
    if not st.session_state.portfolio:
        st.info("Aggiungi titoli dalla sidebar.")
    else:
        tot_val = 0
        p_list = []
        for item in st.session_state.portfolio:
            d = get_analysis(item['ticker'])
            if d:
                v = d['price'] * item['qty']
                tot_val += v
                p_list.append({"Asset": d['name'], "Qty": item['qty'], "Valore": f"€{v:,.2f}", "Score": d['score']})
        st.table(pd.DataFrame(p_list))
        st.metric("CAPITALE TOTALE", f"€{tot_val:,.2f}")
        
        st.divider()
        st.subheader("🚀 VERSO IL MILIONE")
        pac = st.number_input("PAC Mensile (€)", value=500)
        # Calcolo simulazione semplificata
        prog = [tot_val]
        for m in range(1, 241): prog.append((prog[-1] + pac) * (1 + 0.008))
        st.plotly_chart(go.Figure(go.Scatter(y=prog, line=dict(color='#FF8C00'))).update_layout(plot_bgcolor='black', paper_bgcolor='black', font=dict(color='#FF8C00')))
