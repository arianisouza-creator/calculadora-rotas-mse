import streamlit as st
import requests

API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"

# ============================================
#                  CSS PROFISSIONAL
# ============================================
css = """
<style>

body {
    background: #f5f7fb !important;
}

/* Cabeçalho com gradiente */
.header {
    background: linear-gradient(90deg, #1e47ff, #1536c8);
    padding: 40px;
    border-radius: 0 0 25px 25px;
    text-align: center;
    color: white !important;
    margin-bottom: 40px;
}

/* Card principal */
.card {
    background: white;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.08);
    margin-top: 10px;
}

/* Títulos */
.card-title {
    font-size: 28px;
    font-weight: bold;
    color: #1e47ff;
    margin-bottom: 10px;
}

.subtitle {
    font-size: 16px;
    color: #555;
    margin-bottom: 20px;
}

/* Inputs */
.stTextInput > div > div > input {
    padding: 14px;
    font-size: 16px;
    border-radius: 12px !important;
    border: 1px solid #cccccc;
}

/* Botão principal */
.stButton > button {
    width: 100%;
    background: #1e47ff !important;
    color: white !important;
    padding: 14px;
    font-size: 18px;
    border-radius: 12px;
    border: none;
}

.stButton > button:hover {
    background: #1536c8 !important;
}

/* Resultados */
.result-box {
    margin-top: 25px;
    padding: 20px;
    border-radius: 15px;
    background: #eef2ff;
    border-left: 5px solid #1e47ff;
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

    preco = dist_km * 0.45  # seu custo por km

    return dist_texto, duracao, preco


# ============================================
#              INTERFACE WEB
# ============================================

# Cabeçalho
st.markdown("""
<div class="header">
    <h1 style="font-size:40px;margin-bottom:5px;">🚌 Portal de Cotações</h1>
    <p style="font-size:20px;margin-top:0;">Sistema de cotação de passagens rodoviárias</p>
</div>
""", unsafe_allow_html=True)

# Card principal
st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown('<div class="card-title">Cotar Passagens Rodoviárias</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Encontre as melhores opções para sua viagem</div>', unsafe_allow_html=True)

origem = st.text_input("Origem", "londrina")
destino = st.text_input("Destino", "sao paulo")

calcular = st.button("🔍 Buscar Rota")

if calcular:
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
