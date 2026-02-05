import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Marco-Quant Global Terminal", layout="wide")

st.markdown("""
    <style>
    div.stButton > button { border: none !important; background-color: transparent !important; color: #FF8C00 !important; font-weight: bold !important; }
    .score-text { font-weight: bold; font-size: 24px; }
    .semaforo { display: block; width: 35px; height: 35px; border-radius: 5px; text-align: center; line-height: 35px; font-weight: bold; color: white; margin: auto; }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state: st.session_state.portfolio = {}
if 'sort_col' not in st.session_state: st.session_state.sort_col = "Score"
if 'sort_asc' not in st.session_state: st.session_state.sort_asc = False

@st.cache_data(ttl=3600)
def get_analysis(ticker):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y")
        if df.empty or len(df) < 50: return None
        info = t.info
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        score = int(np.clip(30 + (40 if close > sma200 else 0) + (20 if close > sma50 else 0) + (10 if close > sma20 else 0), 1, 100))
        r = int(255 * (1 - score/100)); g = int(255 * (score/100))
        return {
            "Symbol": ticker, "Nome": info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Div": (info.get('dividendYield', 0) or 0) * 100, "History": df
        }
    except Exception: return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- TABELLE MERCATI ---
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
        raw_list = []
        with st.spinner(f'Caricamento {m_name}...'):
            for t in mercati[m_name]:
                res = get_analysis(t)
                if res: raw_list.append(res)
        
        if raw_list:
            df_display = pd.DataFrame(raw_list).sort_values(by=st.session_state.sort_col, ascending=st.session_state.sort_asc)
            h = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
            if h[0].button("NOME", key=f"n_{m_name}"): st.session_state.sort_col = "Nome"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            if h[1].button("SCORE", key=f"s_{m_name}"): st.session_state.sort_col = "Score"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
            h[6].write("**DETTAGLI**")
            st.write("---")

            for _, row in df_display.iterrows():
                c = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
                c[0].write(f"**{row['Nome']}**")
                c[1].markdown(f'<span class="score-text" style="color:{row["Color"]}">{row["Score"]}</span>', unsafe_allow_html=True)
                c[2].write(f"€{row['Prezzo']}")
                c[3].markdown(f'<div class="semaforo {"bg-green" if row["L"] else "bg-red"}">L</div>', unsafe_allow_html=True)
                c[4].markdown(f'<div class="semaforo {"bg-green" if row["M"] else "bg-red"}">M</div>', unsafe_allow_html=True)
                c[5].markdown(f'<div class="semaforo {"bg-green" if row["B"] else "bg-red"}">B</div>', unsafe_allow_html=True)
                with c[6]:
                    det, car = st.columns(2)
                    with det:
                        with st.expander("➕"):
                            st.write(f"**Dividendi:** {row['Div']:.2f}%")
                            fig = go.Figure(data=[go.Candlestick(x=row['History'].index, open=row['History']['Open'], high=row['History']['High'], low=row['History']['Low'], close=row['History']['Close'])])
                            fig.update_layout(height=250, margin=dict(l=0,r=0,b=0,t=0), template="plotly_white", xaxis_rangeslider_visible=False)
                            st.plotly_chart(fig, use_container_width=True)
                    with car:
                        with st.popover("🛒"):
                            q = st.number_input("Qtà", min_value=0.0, key=f"q_{row['Symbol']}")
                            if st.button("OK", key=f"btn_{row['Symbol']}"):
                                st.session_state.portfolio[row['Symbol']] = {'qty': q, 'price': row['Prezzo'], 'name': row['Nome']}
                                st.toast(f"Aggiunto {row['Symbol']}!")
        else:
            st.warning(f"Impossibile recuperare i titoli per {m_name}. Verifica la connessione o il file requirements.")

# --- PORTAFOGLIO ---
with tabs[-1]:
    st.header("💼 Portafoglio")
    if st.session_state.portfolio:
        for s, v in st.session_state.portfolio.items():
            st.write(f"**{v['name']}**: {v['qty']} pz - €{v['qty']*v['price']:,.2f}")
    else: st.info("Vuoto.")
