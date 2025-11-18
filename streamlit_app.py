import streamlit as st
import requests

API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk" 


# ========= GEOCODING =========
def geocode(local):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={local}&key={API_KEY}"
    resp = requests.get(url).json()

    if resp["status"] != "OK":
        raise Exception(f"Erro Geocoding: {resp}")

    loc = resp["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]


# ========= DIRECTIONS (rota real) =========
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



# ================================
#        INTERFACE WEB
# ================================
st.set_page_config(page_title="MSE – Calculadora de Rotas", page_icon="🛣️", layout="centered")

st.markdown("<h1 style='text-align:center;color:#ff3333;'>🛣️ Calculadora de Distância Rodoviária</h1>", unsafe_allow_html=True)

st.write("### Informe origem e destino:")

origem = st.text_input("Origem", "São Paulo - SP")
destino = st.text_input("Destino", "Itapoá - SC")

if st.button("Calcular Rota", type="primary"):
    try:
        dist, duracao, preco = obter_rota(origem, destino)

        st.success("Cálculo realizado com sucesso!")

        st.write(f"### 📍 Origem: {origem}")
        st.write(f"### 📍 Destino: {destino}")

        st.write(f"## 🛣️ Distância: **{dist}**")
        st.write(f"## ⏳ Duração: **{duracao}**")
        st.write(f"## 💰 Preço Estimado: **R$ {preco:.2f}**")

        st.caption("Fonte: Google Directions API")

    except Exception as e:
        st.error(f"Erro: {e}")
