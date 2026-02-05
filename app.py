import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Marco-Quant Pro Terminal", layout="wide")

# CSS per eliminare freccette dai bottoni e stile semafori
st.markdown("""
    <style>
    /* Rimuove freccette e bordi dai bottoni di ordinamento */
    div.stButton > button {
        border: none !important;
        background-color: transparent !important;
        color: #FF8C00 !important;
        font-weight: bold !important;
        box-shadow: none !important;
        padding: 0px !important;
    }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo {
        display: block; width: 35px; height: 35px; border-radius: 5px;
        text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto;
    }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE MEMORIA ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}
if 'sort_col' not in st.session_state:
    st.session_state.sort_col = "Score"
if 'sort_asc' not in st.session_state:
    st.session_state.sort_asc = False

@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty: return None
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        r = int(255 * (1 - score/100)); g = int(255 * (score/100))
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Div": (t.info.get('dividendYield', 0) or 0) * 100
        }
    except: return None

# --- UI PRINCIPALE ---
st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# LISTA TITOLI ESPANSA
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI", "STMMI.MI", "A2A.MI", "G.MI", "PST.MI", "TEN.MI", "AZM.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "BRK-B", "AMD", "NFLX", "AVGO", "COST"],
    "📊 ETF": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT", "IBCI.MI", "VUSA.L", "SMH"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR", "BNB-EUR", "XRP-EUR", "ADA-EUR"]
}

# TOP 5
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_tickers = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "NOVO-B.CO"]
top_cols = st.columns(5)
for i, t in enumerate(top_tickers):
    data = get_analysis(t)
    if data:
        with top_cols[i]:
            st.markdown(f'<div style="text-align:center; border:2px solid {data["Color"]}; border-radius:10px; padding:10px;">'
                        f'<span style="color:{data["Color"]}; font-size:28px; font-weight:bold;">{data["Score"]}</span><br>'
                        f'<b>{data["Symbol"]}</b></div>', unsafe_allow_html=True)

st.divider()

# TABELLE
tabs = st.tabs(list(mercati.keys()) + ["💼 Portafoglio"])

for i, m_name in enumerate(mercati.keys()):
    with tabs[i]:
        raw_data = [get_analysis(t) for t in mercati[m_name] if get_analysis(t)]
        df_display = pd.DataFrame(raw_data)
        
        if not df_display.empty:
            df_display = df_display.sort_values(by=st.session_state.sort_col, ascending=st.session_state.sort_asc)

            # Header cliccabili senza freccette
            h1, h2, h3, hL, hM, hB, hD = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
            if h1.button("NOME", key=f"n_{m_name}"): st.session_state.sort_col = "Nome"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            if h2.button("SCORE", key=f"s_{m_name}"): st.session_state.sort_col = "Score"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            if h3.button("PREZZO", key=f"p_{m_name}"): st.session_state.sort_col = "Prezzo"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            if hL.button("L", key=f"l_{m_name}"): st.session_state.sort_col = "L"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            if hM.button("M", key=f"m_{m_name}"): st.session_state.sort_col = "M"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            if hB.button("B", key=f"b_{m_name}"): st.session_state.sort_col = "B"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            hD.write("**DETTAGLI**")
            st.write("---")

            for _, row in df_display.iterrows():
                c1, c2, c3, cL, cM, cB, cD = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
                c1.write(f"**{row['Nome']}**")
                c2.markdown(f'<span class="score-text" style="color:{row["Color"]}">{row["Score"]}</span>', unsafe_allow_html=True)
                c3.write(f"€{row['Prezzo']}")
                cL.markdown(f'<div class="semaforo {"bg-green" if row["L"] else "bg-red"}">L</div>', unsafe_allow_html=True)
                cM.markdown(f'<div class="semaforo {"bg-green" if row["M"] else "bg-red"}">M</div>', unsafe_allow_html=True)
                cB.markdown(f'<div class="semaforo {"bg-green" if row["B"] else "bg-red"}">B</div>', unsafe_allow_html=True)
                
                with cD:
                    det, car = st.columns(2)
                    with det:
                        with st.expander("➕"): st.write(f"Dividendi: {row['Div']:.2f}%")
                    with car:
                        with st.popover("🛒"):
                            q = st.number_input("Quantità", min_value=0.0, step=1.0, key=f"q_{row['Symbol']}")
                            if st.button("CONFERMA", key=f"btn_{row['Symbol']}"):
                                st.session_state.portfolio[row['Symbol']] = {
                                    'name': row['Nome'], 'qty': q, 'price': row['Prezzo']
                                }
                                st.toast(f"Aggiunto {row['Symbol']}!")

# TAB PORTAFOGLIO
with tabs[-1]:
    st.header("💼 Il Mio Portafoglio")
    if st.session_state.portfolio:
        totale = 0
        p_data = []
        for sym, info in st.session_state.portfolio.items():
            subtot = info['qty'] * info['price']
            totale += subtot
            p_data.append({"Titolo": info['name'], "Quantità": info['qty'], "Valore": f"€{subtot:,.2f}"})
        
        st.table(pd.DataFrame(p_data))
        st.metric("CAPITALE TOTALE", f"€{totale:,.2f}")
    else:
        st.info("Portafoglio vuoto. Aggiungi titoli con il carrello 🛒")
