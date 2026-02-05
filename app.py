import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

# CSS per Score, Semafori e Icone
st.markdown("""
    <style>
    .score-text { font-weight: bold; font-size: 26px; }
    .semaforo {
        display: block;
        width: 35px;
        height: 35px;
        border-radius: 5px;
        text-align: center;
        line-height: 35px;
        font-weight: bold;
        color: white;
        margin: auto;
    }
    .bg-green { background-color: #23d160; }
    .bg-red { background-color: #ff3860; }
    .stButton>button { border: none; background: transparent; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}

# --- FUNZIONE ANALISI ---
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
        
        # Calcolo Score
        score = 30
        if close > sma200: score += 40
        if close > sma50: score += 20
        if close > sma20: score += 10
        score = int(np.clip(score, 1, 100))
        
        # Colore Score (1 Rosso -> 100 Verde)
        r = int(255 * (1 - score/100))
        g = int(255 * (score/100))
        color = f'#{r:02x}{g:02x}00'
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Color": color, "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Div": (t.info.get('dividendYield', 0) or 0) * 100
        }
    except: return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- SEZIONE TOP 5 ---
st.subheader("🔥 TOP 5 OPPORTUNITÀ")
top_tickers = ["LDO.MI", "NVDA", "BTC-EUR", "GC=F", "UCG.MI"]
top_cols = st.columns(5)
for i, t in enumerate(top_tickers):
    data = get_analysis(t)
    if data:
        with top_cols[i]:
            st.markdown(f'<div style="text-align:center; border:1px solid #ddd; border-radius:10px; padding:10px;">'
                        f'<span style="color:{data["Color"]}; font-size:30px; font-weight:bold;">{data["Score"]}</span><br>'
                        f'<b>{data["Symbol"]}</b><br>€{data["Prezzo"]}</div>', unsafe_allow_html=True)

st.divider()

# --- TABELLE MERCATI ---
tabs = st.tabs(["🇮🇹 Italia", "🇺🇸 USA", "📊 ETF", "🪙 Crypto", "💼 Portafoglio"])
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META"],
    "📊 ETF": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

for tab, m_name in zip(tabs[:4], mercati.keys()):
    with tab:
        # Recupero dati per la tabella
        raw_data = [get_analysis(t) for t in mercati[m_name] if get_analysis(t)]
        df_display = pd.DataFrame(raw_data)
        
        # Header con selezione ordinamento
        sort_col = st.selectbox(f"Ordina {m_name} per:", ["Score", "L", "M", "B", "Prezzo"], key=f"sort_{m_name}")
        df_display = df_display.sort_values(by=sort_col, ascending=False)

        # Tabella visuale
        for _, row in df_display.iterrows():
            c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.5])
            
            c1.write(f"**{row['Nome']}**")
            c2.markdown(f'<span class="score-text" style="color:{row["Color"]}">{row["Score"]}</span>', unsafe_allow_html=True)
            c3.write(f"€{row['Prezzo']}")
            
            # Colonne Semafori L M B divise
            c4.markdown(f'<div class="semaforo {"bg-green" if row["L"] else "bg-red"}">L</div>', unsafe_allow_html=True)
            c5.markdown(f'<div class="semaforo {"bg-green" if row["M"] else "bg-red"}">M</div>', unsafe_allow_html=True)
            c6.markdown(f'<div class="semaforo {"bg-green" if row["B"] else "bg-red"}">B</div>', unsafe_allow_html=True)
            
            # Dettagli (+) e Carrello (🛒)
            with c7:
                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    with st.expander("➕"):
                        st.write(f"Dividendi: {row['Div']:.2f}%")
                        st.write(f"Ticker: {row['Symbol']}")
                with sub_c2:
                    with st.popover("🛒"):
                        qty = st.number_input("Quantità", min_value=0.0, key=f"qty_{row['Symbol']}")
                        if st.button("Conferma", key=f"add_{row['Symbol']}"):
                            st.session_state.portfolio[row['Symbol']] = {'qty': qty, 'price': row['Prezzo'], 'name': row['Nome']}
                            st.success("Aggiunto")

# --- PORTAFOGLIO ---
with tabs[4]:
    st.header("💼 Il mio Portafoglio")
    if st.session_state.portfolio:
        tot_cap = 0
        for tick, info in st.session_state.portfolio.items():
            v = info['qty'] * info['price']
            tot_cap += v
            st.write(f"**{info['name']}**: {info['qty']} pz | Valore: €{v:,.2f}")
        st.metric("CAPITALE TOTALE", f"€{tot_cap:,.2f}")
    else:
        st.info("Il carrello è vuoto.")
