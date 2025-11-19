import streamlit as st
import requests

API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"

# ============================================
#                  CSS MSE
# ============================================
css = """
<style>

body {
    background: #f5f7fb !important;
}

/* Cabeçalho MSE vermelho */
.header {
    background: #e4002b; /* vermelho MSE */
    padding: 40px;
    border-radius: 0 0 25px 25px;
    text-align: center;
    color: white !important;
    margin-bottom: 40px;
}

/* Logo */
.header img {
    width: 120px;
    margin-bottom: 10px;
}

/* Título */
.header-title {
    font-size: 40px;
    font-weight: bold;
    margin-top: 5px;
}

/* Subtítulo */
.header-sub {
    font-size: 20px;
    margin-top: -5px;
}

/* Card de conteúdo */
.card {
    background: white;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.08);
    margin-top: 10px;
}

/* Titulo do card */
.card-title {
    font-size: 28px;
    font-weight: bold;
    color: #e4002b; /* vermelho MSE */
    margin-bottom: 10px;
}

/* Inputs */
.stTextInput > div > div > input {
    padding: 14px;
    font-size: 16px;
    border-radius: 12px !important;
    border: 1px solid #cccccc;
}

/* Botão primário */
.stButton > button {
    width: 100%;
    background: #e4002b !important;
    color: white !important;
    padding: 14px;
    font-size: 18px;
    border-radius: 12px;
    border: none;
}

.stButton > button:hover {
    background: #b90022 !important;
}

/* Caixa de resultados */
.result-box {
    margin-top: 25px;
    padding: 20px;
    border-radius: 15px;
    background: #ffe6e9;
    border-left: 5px solid #e4002b;
}

</style>
"""

# Aplica o CSS
st.markdown(css, unsafe_allow_html=True)


# ============================================
#          FUNÇÕES GOOGLE MAPS
# ============================================
def geocode(local):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={local}&key={API_KEY}"
    resp = requests.get(url).json()

    if resp["status"] != "OK":
