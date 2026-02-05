import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Marco-Quant Terminal", layout="wide")

st.markdown("""
    <style>
    .score-text { font-weight: bold; font-size: 24px; }
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
    /* Rende i nomi delle colonne simili a pulsanti */
    .col-header { font-weight: bold; color: #FF8C00; cursor: pointer; text-align: center; }
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
        if df.empty: return None
        close = df['Close'].iloc[-1]
        sma200 = df['Close'].rolling(200).mean().iloc[-1]
        sma50 = df['Close'].rolling(50).mean().iloc[-1]
        sma20 = df['Close'].rolling(20).mean().iloc[-1]
        
        score = 30
        if close > sma200: score += 40
        if close > sma50: score += 20
        if close > sma20: score += 10
        score = int(np.clip(score, 1, 100))
        
        r = int(255 * (1 - score/100))
        g = int(255 * (score/100))
        
        return {
            "Symbol": ticker, "Nome": t.info.get('shortName', ticker),
            "Score": score, "Color": f'#{r:02x}{g:02x}00', "Prezzo": round(close, 2),
            "L": close > sma200, "M": close > sma50, "B": close > sma20,
            "Div": (t.info.get('dividendYield', 0) or 0) * 100, "History": df
        }
    except: return None

st.title("🏹 MARCO-QUANT GLOBAL TERMINAL")

# --- TOP 5 (Sempre visibile) ---
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

# --- TABELLE CON ORDINAMENTO CLICCABILE ---
tabs = st.tabs(["🇮🇹 Italia", "🇺🇸 USA", "📊 ETF", "🪙 Crypto", "💼 Portafoglio"])
mercati = {
    "🇮🇹 Italia": ["LDO.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "RACE.MI", "ENI.MI"],
    "🇺🇸 USA": ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL"],
    "📊 ETF": ["SWDA.MI", "CSSPX.MI", "EIMI.MI", "TLT"],
    "🪙 Crypto": ["BTC-EUR", "ETH-EUR", "SOL-EUR"]
}

for tab, m_name in zip(tabs[:4], mercati.keys()):
    with tab:
        raw_data = [get_analysis(t) for t in mercati[m_name] if get_analysis(t)]
        df_display = pd.DataFrame(raw_data)
        
        # Logica di ordinamento
        if not df_display.empty:
            df_display = df_display.sort_values(by=st.session_state.sort_col, ascending=st.session_state.sort_asc)

        # Header clikkabili (Simulati con bottoni piatti per invertire l'ordine)
        h1, h2, h3, h4, h5, h6, h7 = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
        if h1.button("NOME ↕️", key=f"h1_{m_name}"): 
            st.session_state.sort_col = "Nome"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
        if h2.button("SCORE ↕️", key=f"h2_{m_name}"): 
            st.session_state.sort_col = "Score"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
        if h3.button("PREZZO ↕️", key=f"h3_{m_name}"): 
            st.session_state.sort_col = "Prezzo"; st.session_state.sort_asc = not st.session_state.sort_asc; st.rerun()
        h4.markdown('<p class="col-header">L</p>', unsafe_allow_html=True)
        h5.markdown('<p class="col-header">M</p>', unsafe_allow_html=True)
        h6.markdown('<p class="col-header">B</p>', unsafe_allow_html=True)
        h7.write("**DETTAGLI**")
        st.write("---")

        for _, row in df_display.iterrows():
            c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 0.6, 0.6, 0.6, 1.2])
            c1.write(f"**{row['Nome']}**")
            c2.markdown(f'<span class="score-text" style="color:{row["Color"]}">{row["Score"]}</span>', unsafe_allow_html=True)
            c3.write(f"€{row['Prezzo']}")
            c4.markdown(f'<div class="semaforo {"bg-green" if row["L"] else "bg-red"}">L</div>', unsafe_allow_html=True)
            c5.markdown(f'<div class="semaforo {"bg-green" if row["M"] else "bg-red"}">M</div>', unsafe_allow_html=True)
            c6.markdown(f'<div class="semaforo {"bg-green" if row["B"] else "bg-red"}">B</div>', unsafe_allow_html=True)
            
            with c7:
                det, car = st.columns(2)
                with det:
                    with st.expander("➕"):
                        st.write(f"Dividendi: {row['Div']:.2f}%")
                        # Mini grafico
                        fig = go.Figure(data=[go.Scatter(y=row['History']['Close'].tail(30), line=dict(color=row['Color']))])
                        fig.update_layout(height=100, margin=dict(l=0,r=0,b=0,t=0), xaxis_visible=False, yaxis_visible=False)
                        st.plotly_chart(fig, use_container_width=True)
                with car:
                    with st.popover("🛒"):
                        q = st.number_input("Quantità", min_value=0.0, key=f"q_{row['Symbol']}")
                        if st.button("Conferma", key=f"a_{row['Symbol']}"):
                            st.session_state.portfolio[row['Symbol']] = {'qty': q, 'price': row['Prezzo'], 'name': row['Nome']}
                            st.toast("Aggiunto!")

# --- PORTAFOGLIO ---
with tabs[4]:
    st.header("💼 Portafoglio Reale")
    if st.session_state.portfolio:
        for tick, info in st.session_state.portfolio.items():
            st.write(f"**{info['name']}**: {info['qty']} quote")
