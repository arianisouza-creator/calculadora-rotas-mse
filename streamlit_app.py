import streamlit as st
import requests

# ============================================
#              CONFIGURAÇÃO
# ============================================

API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"

st.set_page_config(page_title="Portal de Cotações MSE", page_icon="🚌", layout="centered")

# ============================================
#                  CSS MSE
# ============================================

css = """
<style>

body {
    background: #f5f7fb !important;
}

/* Cabeçalho superior */
.header-container {
    background: linear-gradient(90deg, #e4002b, #b30022);
    padding: 45px 20px 50px 20px;
    text-align: center;
    color: white;
    border-radius: 0 0 35px 35px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.18);
}

.header-title {
    font-size: 48px;
    font-weight: 700;
    margin-top: 5px;
    margin-bottom: 0;
}

.header-sub {
    font-size: 22px;
    margin-top: 5px;
    opacity: 0.95;
}

/* Card principal */
.card {
    background: white;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.08);
    margin-top: 25px; /* Ajustado para subir o card */
}

/* Títulos do card */
.card-title {
    font-size: 28px;
    font-weight: bold;
    color: #e4002b;
    margin-bottom: 10px;
}

/* Inputs */
.stTextInput > div > div > input {
    padding: 14px;
    font-size: 16px;
    border-radius: 12px !important;
    border: 1px solid #cccccc;
}

/* Botão Buscar */
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

/* Caixa de resultado */
.result-box {
    margin-top: 25px;
    padding: 25px;
    border-radius: 18px;
    background: #ffe6e9;
    border-left: 6px solid #e4002b;
    color: #000000 !important;
}

.result-box h3,
.result-box p,
.result-box b {
    color: #000000 !important;
    font-size: 18px;
}

/* Remove espaço padrão do streamlit */
.block-container { padding-top: 0 !important; }

</style>
"""
st.markdown(css, unsafe_allow_html=True)

# ============================================
#          FUNÇÕES GOOGLE MAPS
# ============================================

def geocode(local):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={local}&key={API_KEY}"
    resp = requests.get(url).json()

    if resp["status"] != "OK":
        raise Exception(f"Erro Geocoding: {resp}")

    loc = resp["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


def obter_rota(origem, destino):
    lat_o, lng_o = geocode(origem)
    lat_d, lng_d = geocode(destino)

    url = (
        "https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={lat_o},{lng_o}"
        f"&destination={lat_d},{lng_d}"
        "&mode=driving&language=pt-BR"
        f"&key={API_KEY}"
    )

    rota = requests.get(url).json()

    if rota["status"] != "OK":
        raise Exception(f"Erro Directions API: {rota}")

    leg = rota["routes"][0]["legs"][0]

    dist_texto = leg["distance"]["text"]
    dist_km = leg["distance"]["value"] / 1000
    duracao = leg["duration"]["text"]

    preco = dist_km * 0.45

    return dist_texto, duracao, preco

# ============================================
#           CABEÇALHO COMPLETO
# ============================================

st.markdown("""
<div class="header-container">
    <div class="header-title">🚌 Portal de Cotações</div>
    <div class="header-sub">Sistema de cotação de passagens rodoviárias para Facilities</div>
</div>
""", unsafe_allow_html=True)

# ============================================
#                 CARD
# ============================================

st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown('<div class="card-title">Cotar Passagens Rodoviárias</div>', unsafe_allow_html=True)
st.write("Encontre as melhores opções para sua viagem")

origem = st.text_input("Origem", "Londrina")
destino = st.text_input("Destino", "São Paulo")

buscar = st.button("🔍 Buscar Rota")

if buscar:
    try:
        dist, duracao, preco = obter_rota(origem, destino)

        st.markdown(
            f"""
            <div class="result-box">
                <h3>📍 Origem: {origem.title()}</h3>
                <h3>📍 Destino: {destino.title()}</h3>
                <p><b>🛣️ Distância:</b> {dist}</p>
                <p><b>⏳ Duração:</b> {duracao}</p>
                <p><b>💰 Preço Estimado:</b> R$ {preco:.2f}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Erro: {e}")

st.markdown("</div>", unsafe_allow_html=True)
