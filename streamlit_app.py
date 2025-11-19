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

    preco = dist_km * 0.45  # custo por km

    return dist_texto, duracao, preco


# ============================================
#              INTERFACE WEB MSE
# ============================================

# Cabeçalho com logo
st.markdown(f"""
<div class="header">
    <img src="file:///mnt/data/a0a83793-ab60-4ee4-961d-245d3a84551c.png">
    <div class="header-title">Portal de Cotações</div>
    <div class="header-sub">Sistema de cotação de rotas rodoviárias</div>
</div>
""", unsafe_allow_html=True)


# Card principal
st.markdown('<div class="card">', unsafe_allow_html=True)

st.markdown('<div class="card-title">Cotar Passagens Rodoviárias</div>', unsafe_allow_html=True)
st.write("Encontre as melhores opções para sua viagem")

origem = st.text_input("Origem", "londrina")
destino = st.text_input("Destino", "são paulo")

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
