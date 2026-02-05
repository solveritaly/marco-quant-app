import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE ESTETICA "NERO & ARANCIONE" ---
st.set_page_config(page_title="MARCO-QUANT ULTIMATE", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    h1, h2, h3, h4, p, span, label, .stMarkdown { color: #FF8C00 !important; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #FF8C00; color: black; font-weight: bold; border-radius: 5px; border: none; }
    .score-box { border: 2px solid #FF8C00; padding: 10px; border-radius: 10px; text-align: center; background-color: #0a0a0a; }
    .big-num { font-size: 35px; font-weight: bold; display: block; color: #FF8C00; }
    .detail-box { border-left: 3px solid #FF8C00; padding-left: 15px; margin: 10px 0; background-color: #111111; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- FUNZIONE ANALISI AVANZATA ---
@st.cache_data(ttl=3600)
def get_full_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        info = t.info
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Analisi Operativa
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        target_entry = round(close - (atr * 0.5), 2)
        target_exit = round(close + (atr * 1.5), 2)
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        
        # Calcolo Score
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > sma200 else 0), 0, 100))
        
        return {
            "symbol": ticker, "name": info.get('shortName', ticker),
            "price": round(close, 2), "score": score,
            "L": close > sma200, "M": close > df['Close'].rolling(50).mean().iloc[-1], "B": close > sma20,
            "entry": target_entry, "exit": target_exit, "div": div_yield,
            "df": df, "desc": info.get('longBusinessSummary', 'Descrizione non disponibile')[:300] + "..."
        }
    except: return None

st.title("🏹 MARCO-QUANT ULTIMATE TERMINAL")

# 1. TOP 5 AUTOMATICA
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_list = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "NOVO-B.CO"]
cols_top = st.columns(5)
for i, t in enumerate(top_list):
    d = get_full_data(t)
    if d:
        with cols_top[i]:
            st.markdown(f'<div class="score-box"><small>{d["symbol"]}</small><span class="big-num">{d["score"]}</span>'
                        f'<small>L:{"🟢" if d["L"] else "🔴"} M:{"🟢" if d["M"] else "🔴"} B:{"🟢" if d["B"] else "🔴"}</small></div>', unsafe_allow_html=True)

st.divider()

# 2. CATEGORIE MERCATI CON DETTAGLI ESPANDIBILI
tabs = st.tabs(["🇮🇹 ITALIA", "🇺🇸 USA", "📊 ETF/BOND", "🪙 CRYPTO", "💼 PORTAFOGLIO"])

mercati = {
    "🇮🇹 ITALIA": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI"],
    "🇺🇸 USA": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "📊 ETF/BOND": ["SWDA.MI", "CSSPX.MI", "TLT"],
    "🪙 CRYPTO": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

for i, (tab_name, tickers) in enumerate(mercati.items()):
    with tabs[i]:
        for ticker in tickers:
            data = get_full_data(ticker)
            if data:
                # Riga Principale
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{data['name']}** ({data['symbol']})")
                c2.write(f"Score: **{data['score']}**")
                c3.write(f"€{data['price']}")
                
                # Espansore per i dettagli (+)
                with st.expander(f"➕ Dettagli Operativi e Analisi per {ticker}"):
                    d1, d2 = st.columns([2, 1])
                    with d1:
                        st.markdown(f"**Descrizione:** {data['desc']}")
                        st.markdown(f"**📊 Dividendi:** {data['div']:.2f}%")
                        # Grafico
                        fig = go.Figure(data=[go.Candlestick(x=data['df'].index, open=data['df']['Open'], high=data['df']['High'], low=data['df']['Low'], close=data['df']['Close'], increasing_line_color='#FF8C00', decreasing_line_color='#444444')])
                        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', font=dict(color='#FF8C00'), height=250, margin=dict(l=0,r=0,b=0,t=0))
                        st.plotly_chart(fig, use_container_width=True)
                    with d2:
                        st.markdown(f'<div class="detail-box"><b>🎯 TARGET ENTRATA:</b><br>€{data["entry"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><b>💰 TARGET USCITA:</b><br>€{data["exit"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="detail-box"><b>Semafori:</b><br>Lungo: {"🟢" if data["L"] else "🔴"}<br>Medio: {"🟢" if data["M"] else "🔴"}<br>Breve: {"🟢" if data["B"] else "🔴"}</div>', unsafe_allow_html=True)
                        if st.button(f"Aggiungi {ticker} a Portafoglio", key=f"btn_{ticker}"):
                            st.session_state.portfolio.append({"t": ticker, "p": data['price']})
                            st.toast(f"{ticker} aggiunto!")

# 3. PORTAFOGLIO E
