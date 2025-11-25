import streamlit as st
import requests
from datetime import datetime

# ============================
# CONFIGURAÇÕES
# ============================
API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"
PRECO_KM = 0.50

# ============================
# TABELA HOSPEDAGEM POR UF
# ============================
TABELA_HOSPEDAGEM = {
    "AC": 180, "AL": 200, "AP": 180, "AM": 220,
    "BA": 220, "CE": 210, "DF": 260, "ES": 230,
    "GO": 210, "MA": 200, "MT": 230, "MS": 230,
    "MG": 250, "PA": 200, "PB": 200, "PR": 250,
    "PE": 220, "PI": 190, "RJ": 280, "RN": 200,
    "RS": 240, "RO": 200, "RR": 200, "SC": 200,
    "SP": 300, "SE": 190, "TO": 190
}

# ============================
# AJUSTAR CIDADE
# ============================
def ajustar_cidade(cidade):
    if "-" in cidade:
        return cidade
    return cidade + ", Brasil"

# ============================
# CALCULAR KM GOOGLE
# ============================
def get_km(origem, destino):
    origem = ajustar_cidade(origem)
    destino = ajustar_cidade(destino)

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?units=metric&origins={origem}&destinations={destino}&key={API_KEY}"
    )

    response = requests.get(url).json()

    try:
        return response["rows"][0]["elements"][0]["distance"]["value"] / 1000
    except:
        return 0

# ============================
# CALCULAR DIAS
# ============================
def calcular_dias(ida, volta):
    if not ida or not volta:
        return 1
    return (volta - ida).days

def calcular_dias_hosp(ida, volta):
    if not ida or not volta:
        return 1
    return (volta - ida).days + 1

# ============================
# STREAMLIT – APLICATIVO
# ============================
st.set_page_config(page_title="MSE Travel Express", layout="centered")

# CSS TEMA MSE
st.markdown("""
<style>
body {
    background-color: #f4f4f4;
}
.header {
    background:#8B0000; 
    padding:20px;
    color:white;
    text-align:center;
    font-size:28px;
    font-weight:bold;
    border-radius:10px;
}
.button {
    background:#8B0000; 
    color:white; 
    padding:12px; 
    width:100%; 
    border:none; 
    border-radius:10px; 
    font-size:20px;
}
.box {
    background:white;
    padding:20px;
    border-radius:10px;
    box-shadow:0 0 10px #ccc;
}
</style>
""", unsafe_allow_html=True)

# ============================
# CABEÇALHO
# ============================
st.markdown('<div class="header">MSE TRAVEL EXPRESS</div>', unsafe_allow_html=True)
st.write("")
st.write("")

# ============================
# BOTÕES PRINCIPAIS
# ============================
opcao = st.radio(
    "Selecione o tipo de cotação:",
    ["Passagem Rodoviária", "Hospedagem", "Veículo"],
    index=0
)

st.write("")

# ============================
# FORMULÁRIOS
# ============================
st.markdown('<div class="box">', unsafe_allow_html=True)

if opcao == "Passagem Rodoviária":
    origem = st.text_input("Cidade de Origem")
    destino = st.text_input("Cidade de Destino (Ex: Curitiba - PR)")

    if st.button("COTAR", use_container_width=True):
        km = get_km(origem, destino)

        if km == 0:
            st.error("Erro ao calcular a distância. Use o formato Cidade - UF.")
        else:
            total = km * PRECO_KM
            st.info(f"""
🚌 **Passagem Rodoviária**

Origem: **{origem}**  
Destino: **{destino}**

Distância: **{km:.1f} km**  
Total estimado: **R$ {total:.2f}**
""")

# -------------------------------------

elif opcao == "Hospedagem":
    destino = st.text_input("Cidade de Destino (Ex: São Paulo - SP)")
    data_ida = st.date_input("Data de Ida")
    data_volta = st.date_input("Data de Volta")

    if st.button("COTAR", use_container_width=True):
        try:
            uf = destino.split("-")[1].strip().upper()
            diaria = TABELA_HOSPEDAGEM[uf]
            dias = calcular_dias_hosp(data_ida, data_volta)
            total = diaria * dias

            st.info(f"""
🏨 **Hospedagem**

Cidade: **{destino}**  
Estado (UF): **{uf}**

Dias de hospedagem: **{dias}**

💰 **Total estimado: R$ {total:.2f}**
""")

        except:
            st.error("Erro: Informe o destino no formato Cidade - UF.")

# -------------------------------------

elif opcao == "Veículo":
    origem = st.text_input("Cidade de Origem")
    destino = st.text_input("Cidade de Destino")
    grupo = st.selectbox("Grupo de veículo", ["B - Hatch Manual", "D - SUV Automático"])
    data_ida = st.date_input("Data de Retirada")
    data_volta = st.date_input("Data de Devolução")

    if st.button("COTAR", use_container_width=True):
        dias = calcular_dias(data_ida, data_volta)
        preco_dia = 134 if grupo.startswith("B") else 203
        total = preco_dia * dias

        st.info(f"""
🚗 **Veículo**

Grupo: **{grupo}**  
Dias: **{dias}**  
Total estimado: **R$ {total:.2f}**
""")

st.markdown('</div>', unsafe_allow_html=True)
