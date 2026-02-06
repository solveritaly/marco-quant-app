import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="DEBUG Marco-Quant", layout="wide")
st.title("🔍 DIAGNOSTICA TERMINALE")

# CONTROLLO 1: Le librerie sono caricate?
st.write("### 1. Verifica Ambiente")
st.success(f"Libreria yfinance versione: {yf.__version__}")

# CONTROLLO 2: Test Connessione a Yahoo
st.write("### 2. Test Scansione Mercato")
test_ticker = "BTC-EUR"

try:
    # Usiamo un header per non farci bloccare da Yahoo
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    st.write(f"Tentativo di scarico dati per {test_ticker}...")
    data = yf.download(test_ticker, period="1d", session=session)
    
    if data.empty:
        st.error(f"⚠️ Yahoo ha risposto, ma i dati per {test_ticker} sono VUOTI. (Possibile blocco IP)")
    else:
        st.success(f"✅ Dati Ricevuti! Ultimo prezzo: {data['Close'].iloc[-1]}")
        st.write(data.tail())

except Exception as e:
    st.error(f"❌ ERRORE CRITICO: {str(e)}")

# CONTROLLO 3: Verifica File Requirements
st.write("### 3. Istruzioni per te")
st.info("Se vedi un errore 'ModuleNotFoundError', significa che il file requirements.txt su GitHub non è stato letto correttamente.")
