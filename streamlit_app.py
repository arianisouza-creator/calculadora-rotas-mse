import streamlit as st
import requests

# =========================
# CONFIGURAÇÃO INICIAL
# =========================
API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"


# =========================
# FUNÇÕES DE API
# =========================
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

    distancia_texto = leg["distance"]["text"]
    distancia_km = leg["distance"]["value"] / 1000
    duracao = leg["duration"]["text"]
    preco = distancia_km * 0.45

    return distancia_texto, duracao, preco


# =========================
# SETUP DA PÁGINA
# =========================
st.set_page_config(
    page_title="MSE – Calculadora de Rotas",
    page_icon="🛣️",
    layout="centered"
)

# CSS personalizado com tema MSE
st.markdown("""
<style>

html, body, [class*="css"]  {
    background-color: #1a1a1a;
    color: white;
    font-family: Arial, sans-serif;
}

h1 {
    color: #ff3333 !important;
    text-align: center;
    font-weight: 800;
}

h2, h3 {
    color: #ffffff !important;
}

input {
    border-radius: 12px !important;
    border: 2px solid #444444 !important;
}

button {
    border-radius: 10px !important;
}

</style>
""", unsafe_allow_html=True)


# =========================
# CABEÇALHO COM LOGO
# =========================
st.markdown(
    """
    <div style="text-align:center;">
        <img src="https://i.imgur.com/6gK2Fne.png" width="120">
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1>Calculadora de Distância Rodoviária</h1>", unsafe_allow_html=True)


# =========================
# ENTRADAS DO USUÁRIO
# =========================
st.write("### Informe os dados abaixo:")

origem = st.text_input("Origem:", placeholder="Ex.: São Paulo - SP")
destino = st.text_input("Destino:", placeholder="Ex.: Itapoá - SC")

botao = st.button("Calcular Rota", type="primary")


# =========================
# LÓGICA PRINCIPAL
# =========================
if botao:
    try:
        distancia, duracao, preco = obter_rota(origem, destino)

        st.markdown("---")

        st.markdown(
            f"""
            <div style="
                background-color:#2b2b2b;
                padding:20px;
                border-radius:15px;
                box-shadow: 0px 0px 10px #00000070;
            ">

            <h3>Resultado da Rota</h3>
            <p><b>Origem:</b> {origem}</p>
            <p><b>Destino:</b> {destino}</p>

            <p>🛣️ <b>Distância:</b> {distancia}</p>
            <p>⏳ <b>Duração:</b> {duracao}</p>
            <p>💰 <b>Preço Estimado:</b> <span style="color:#ff3333;"><b>R$ {preco:.2f}</b></span></p>

            <p style="font-size:12px;color:#888;">Fonte: Google Directions API</p>

            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Erro: {e}")


