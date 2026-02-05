import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Marco-Quant Trading Terminal", layout="wide")

st.markdown("""
    <style>
    div.stButton > button { border: none !important; background-color: transparent !important; color: #FF8C00 !important; font-weight: bold !important; font-size: 18px; }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    .trading-label { font-size: 14px; font-weight: bold; color: #555; }
    .trading-value { font-size: 18px; font-weight: bold; color: #FF8C00; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE MEMORIA ---
if 'portfolio' not in st.session_state: st.session_state.portfolio = {}
if 'sort_col' not in st.session_state: st.session_state.sort_col = "Score"
if 'sort_asc' not in st.session_state: st.session_state.sort_asc = False

@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        close = df['Close'].iloc[-1]
        
        # Indicatori per Semafori e Livelli
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Calcolo Score (1-100)
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        r = int(255 * (1 - score/100)); g = int(255 * (score/100))
        
        # CALCOLO LIVELLI TRADING (Basati su Volatilità ATR-like)
        range_val = std20 * 2
        entry = close * 0.985 # Entry a -1.5%
        tp = close + (range_val * 2.5) # Take Profit basato su estensione
        sl = close - (range_val * 1.5) # Stop Loss protettivo
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Entry": round(entry, 2), "TP": round(tp, 2), "SL": round(sl, 2), "History": df
        }
    except: return None

st.title("🏹 MARCO-QUANT TRADING TERMINAL")

# --- 1. TOP 5 OPPORTUNITÀ (RIPRISTINATE) ---
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_tickers = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "ASML"]
top_cols = st.columns(5)
for i, t in enumerate(top_tickers):
    data = get_analysis(t)
    if data:
        with top_cols[i]:
            st.markdown(f"""
                <div style="text-align:center; border:2px solid {data['Color']}; border-radius:10px; padding:10px; background-color: #f9f9f9;">
                    <span style="color:{data['Color']}; font-size:28px; font-weight:bold;">{data['Score']}</span><br>
                    <b>{data['Symbol']}</b><br>€{data['Prezzo']}
                </div>
            """, unsafe_allow_html=True)

st.divider()

# --- 2. TABELLE MERCATI ---
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI"],
    "🇪🇺 Europa": ["ASML", "MC.PA", "SAP", "OR.PA", "BMW.DE"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL"],
    "🌍 Emergenti": ["TSM", "BABA", "TCEHY", "MELI"],
    "📊 ETF": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

tabs = st.tabs(list(mercati.keys()) + ["💼 Portafoglio"])

for i, m_name in enumerate(mercati.keys()):
    with tabs[i]:
        raw_list = [get_analysis(t) for t in mercati[m_name] if get_analysis(t)]
        if raw_list:
            df = pd.DataFrame(raw_list).sort_values(by=st.session_state.sort_col, ascending=st.session_state.sort_asc)
            
            # Header cliccabili (Nome, Score, Prezzo, L, M, B)
            h = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
            if h[0].button("NOME", key=f"
