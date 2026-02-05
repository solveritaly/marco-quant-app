import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- 1. SETUP ESTETICO (Bianco, Pulito, Professionale) ---
st.set_page_config(page_title="Marco-Quant Global Terminal", layout="wide")

# Database per salvare il portafoglio (Quantità e Prezzi)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# --- 2. IL "CERVELLO" (La Formula Lovable/Quantaste) ---
def get_full_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        
        info = t.info
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # Calcolo Score (0-100) basato su Trend, Momentum e Sconto Statistico
        score = 50 
        if close > sma200: score += 20  # Trend Lungo
        if close > sma50: score += 10   # Trend Medio
        z_score = (sma20 - close) / std20 if std20 > 0 else 0
        if z_score > 1: score += 20     # Sconto statistico (Vantaggio)
        
        return {
            "symbol": ticker, "name": info.get('shortName', ticker),
            "price": round(close, 2), "score": int(np.clip(score, 0, 100)),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "div": (info.get('dividendYield', 0) or 0) * 100,
            "entry": round(close * 0.98, 2), "exit": round(close * 1.12, 2),
            "df": df, "desc": info.get('longBusinessSummary', 'N/A')[:300] + "..."
        }
    except: return None

# --- 3. INTERFACCIA PRINCIPALE ---
st.title("🏹 Marco-Quant: Terminale di Investimento Globale")

# TOP 5 AUTOMATICA (Home)
st.subheader("🔥 Top 5 Opportunità (Aggiornate ora)")
top_basket = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "NOVO-B.CO"]
top_cols = st.columns(5)
for i, ticker in enumerate(top_basket):
    d = get_full_analysis(ticker)
    if d:
        with top_cols[i]:
            color = "green" if d['score'] > 70 else "orange" if d['score'] > 50 else "red"
            st.markdown(f"### :{color}[{d['score']}]")
            st.markdown(f"**{d['symbol']}**")
            st.write(f"€{d['price']}")
            st.write(f"{'🟢' if d['L'] else '🔴'}{'🟢' if d['M'] else '🔴'}{'🟢' if d['B'] else '🔴'}")

st.divider()

# TAB CATEGORIE
t_ita, t_usa, t_etf, t_crypto, t_port = st.tabs(["🇮🇹 Italia", "🇺🇸 USA", "📊 ETF & Bond", "🪙 Crypto", "💼 MIO PORTAFOGLIO"])

mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI", "STMMI.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "TSLA", "META"],
    "📊 ETF & Bond": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT", "IBCI.MI"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

for i, (tab, tickers) in enumerate(zip([t_ita, t_usa, t_etf, t_crypto], mercati.values())):
    with tab:
        for ticker in tickers:
            data = get_full_data = get_full_analysis(ticker)
            if data:
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{data['name']}**")
                c2.write(f"Score: **{data['score']}**")
                c3.write(f"€{data['price']}")
                
                with st.expander(f"➕ Dettagli, Dividendi e Strategia per {ticker}"):
                    col_sx, col_dx = st.columns([2, 1])
                    with col_sx:
                        st.write(f"**Business:** {data['desc']}")
                        st.write(f"**💰 Dividendi:** {data['div']:.2f}%")
                        fig = go.Figure(data=[go.Candlestick(x=data['df'].index, open=data['df']['Open'], high=data['df']['High'], low=data['df']['Low'], close=data['df']['Close'])])
                        fig.update_layout(height=250, template="plotly_white", margin=dict(l=0,r=0,b=0,t=0))
                        st.plotly_chart(fig, use_container_width=True)
                    with col_dx:
                        st.info(f"**TARGET**\n\nEntrata: €{data['entry']}\nUscita: €{data['exit']}")
                        st.write(f"Trend L/M/B: {'🟢' if data['L'] else '🔴'} {'🟢' if data['M'] else '🔴'} {'🟢' if data['B'] else '🔴'}")
                        # INPUT QUANTITA
                        q = st.number_input(f"Quantità posseduta", min_value=0.0, key=f"q_{ticker}")
                        if st.button(f"Aggiungi {ticker} al Portafoglio", key=f"b_{ticker}"):
                            st.session_state.portfolio[ticker] = {'qty': q, 'price': data['price'], 'name': data['name']}
                            st.success("Aggiunto!")

# TAB PORTAFOGLIO E ROAD TO 1M
with t_port:
    st.header("💼 Portafoglio Reale & Road to 1 Million")
    if not st.session_state.portfolio:
        st.info("Aggiungi titoli cliccando sul '+' nelle altre sezioni.")
    else:
        tot_val = 0
        rows = []
        for t, val in st.session_state.portfolio.items():
            current_val = val['qty'] * val['price']
            tot_val += current_val
            rows.append({"Asset": val['name'], "Quantità": val['qty'], "Prezzo": val['price'], "Valore": f"€{current_val:,.2f}"})
        
        st.table(pd.DataFrame(rows))
        st.metric("VALORE TOTALE", f"€{tot_val:,.2f}")
        
        st.divider()
        pac = st.number_input("Tuo PAC Mensile (€)", value=500)
        prog = [tot_val]
        for m in range(240): prog.append((prog[-1] + pac) * 1.008) # Stima 9% annuo
        st.plotly_chart(go.Figure(go.Scatter(y=prog, line=dict(color='green'))).update_layout(title="Proiezione verso il Milione", template="plotly_white"))
