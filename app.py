import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

# CSS per i semafori con lettere e lo Score colorato
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 5px;
        text-align: center;
        line-height: 30px;
        font-weight: bold;
        color: white;
        margin-right: 5px;
    }
    .bg-green { background-color: #23d160; box-shadow: 0 0 5px #23d160; }
    .bg-red { background-color: #ff3860; box-shadow: 0 0 5px #ff3860; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# --- FUNZIONE DI ANALISI ---
@st.cache_data(ttl=3600)
def get_data(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Formula Score (1-100)
        z = (sma20 - close) / std20 if std20 > 0 else 0
        score = int(np.clip(((1 / (1 + np.exp(-z))) * 70) + (30 if close > sma200 else 0), 1, 100))
        
        # Colore dinamico Score (da Rosso 1 a Verde 100)
        r = int(255 * (1 - score/100))
        g = int(200 * (score/100))
        color_hex = f'#{r:02x}{g:02x}00'
        
        return {
            "symbol": ticker, "name": t.info.get('shortName', ticker),
            "price": round(close, 2), "score": score, "color": color_hex,
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "div": (t.info.get('dividendYield', 0) or 0) * 100,
            "df": df, "entry": round(close * 0.98, 2), "exit": round(close * 1.15, 2)
        }
    except: return None

st.title("🏹 MARCO-QUANT TERMINAL v14.0")

# --- LAYOUT A TAB ---
t_ita, t_usa, t_etf, t_crypto, t_port = st.tabs(["🇮🇹 Italia", "🇺🇸 USA", "📊 ETF & Bond", "🪙 Crypto", "💼 Portafoglio"])

mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL"],
    "📊 ETF & Bond": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

for i, (tab, tickers) in enumerate(zip([t_ita, t_usa, t_etf, t_crypto], mercati.values())):
    with tab:
        # Header Tabella
        h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 2, 1])
        h1.write("**NOME TITOLO**")
        h2.write("**SCORE**")
        h3.write("**PREZZO**")
        h4.write("**SEMAFORI (L M B)**")
        h5.write("**AZIONE**")
        st.divider()

        for ticker in tickers:
            d = get_data(ticker)
            if d:
                c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 2, 1])
                
                # 1. Nome
                c1.write(f"**{d['name']}**")
                
                # 2. Score Grande e Colorato
                c2.markdown(f'<span class="score-text" style="color:{d["color"]}">{d["score"]}</span>', unsafe_allow_html=True)
                
                # 3. Prezzo
                c3.write(f"€{d['price']}")
                
                # 4. Semafori con lettere
                l_class = "bg-green" if d['L'] else "bg-red"
                m_class = "bg-green" if d['M'] else "bg-red"
                b_class = "bg-green" if d['B'] else "bg-red"
                
                c4.markdown(f"""
                    <div class="semaforo {l_class}">L</div>
                    <div class="semaforo {m_class}">M</div>
                    <div class="semaforo {b_class}">B</div>
                """, unsafe_allow_html=True)
                
                # 5. Dettagli (+) e Aggiunta
                with c5:
                    with st.expander("+"):
                        st.write(f"Dividendi: {d['div']:.2f}%")
                        st.write(f"Target Entrata: €{d['entry']}")
                        q = st.number_input("Qty", min_value=0.0, key=f"q_{ticker}")
                        if st.button("Add", key=f"b_{ticker}"):
                            st.session_state.portfolio[ticker] = {'qty': q, 'price': d['price'], 'name': d['name']}
                            st.success("Ok!")

# --- TAB PORTAFOGLIO ---
with t_port:
    st.header("💼 Situazione Portafoglio")
    if st.session_state.portfolio:
        tot = 0
        for t, v in st.session_state.portfolio.items():
            val = v['qty'] * v['price']
            tot += val
            st.write(f"**{v['name']}**: {v['qty']} pz - Valore: €{val:,.2f}")
        st.metric("TOTALE CAPITALE", f"€{tot:,.2f}")
