import streamlit as st
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
from datetime import datetime, date
import base64
from io import BytesIO
from PIL import Image

# =========================================================
# LOGO MSE BASE64 — COLE OS 3 BLOCOS AQUI DENTRO
# =========================================================
LOGO_MSE_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAYAAAACgCAYAAACfF6X6AAAACXBIWXMAAAsTAAALEwEAmpwYAAAK
T2lDQ1BQaG90b3Nob3AgSUNDIHByb2ZpbGUAAHjanVNnVFPZHb934XOSyDYYZICQRAhJCIiAiEi
iIgIiIgISIgIiKgICJyoCCSIiICEiICIiAiIiAgIkAgEhISCEiAiIiAgIiAiAggkAjhvL/fe96X
7959z7mxAMBiIyQSEeP/7etuAxhNpMMEMGASCMF...
…c2ZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZ
mZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZ
mZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZ
mZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZ
mZmZmZmZmZmZmf///wAAAP//AAD///8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA
//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8A
AAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD//wAA//8AAAD/
//8AAAD//wAA//8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAElFTkSuQmCC
"""

# Função que transforma base64 em imagem
def carregar_logo():
    try:
        img_bytes = base64.b64decode(LOGO_MSE_BASE64)
        return Image.open(BytesIO(img_bytes))
    except Exception as e:
        st.error(f"Erro ao carregar a logo: {e}")
        return None

# =========================================================
# CONFIGURAÇÕES
# =========================================================
API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"
PRECO_KM = 0.50

CIDADES_BR = {
    "londrina": "Londrina - PR",
    "curitiba": "Curitiba - PR",
    "maringa": "Maringá - PR",
    "foz do iguacu": "Foz do Iguaçu - PR",
    "sao paulo": "São Paulo - SP",
    "campinas": "Campinas - SP",
    "santos": "Santos - SP",
    "teresina": "Teresina - PI",
    "fortaleza": "Fortaleza - CE",
    "recife": "Recife - PE",
    "salvador": "Salvador - BA",
    "aracaju": "Aracaju - SE",
    "maceio": "Maceió - AL",
    "joao pessoa": "João Pessoa - PB",
    "natal": "Natal - RN",
    "belem": "Belém - PA",
    "macapa": "Macapá - AP",
    "palmas": "Palmas - TO",
    "porto alegre": "Porto Alegre - RS",
    "florianopolis": "Florianópolis - SC",
    "manaus": "Manaus - AM",
    "rio branco": "Rio Branco - AC",
    "boa vista": "Boa Vista - RR",
    "brasilia": "Brasília - DF",
    "goiania": "Goiânia - GO",
    "cuiaba": "Cuiabá - MT",
    "belo horizonte": "Belo Horizonte - MG",
    "bh": "Belo Horizonte - MG",
}

def ajustar_cidade(cidade):
    if not cidade:
        return ""
    cidade = cidade.lower().strip()
    return CIDADES_BR.get(cidade, cidade + ", Brasil")

def get_km(origem, destino):
    origem = ajustar_cidade(origem)
    destino = ajustar_cidade(destino)
    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric"
        f"&origins={origem}&destinations={destino}&key={API_KEY}"
    )
    try:
        res = requests.get(url).json()
        elem = res["rows"][0]["elements"][0]
        return elem["distance"]["value"] / 1000 if elem["status"] == "OK" else 0
    except:
        return 0

def calcular_dias(ida, volta):
    if not ida or not volta:
        return 1
    return (volta - ida).days or 1

# =========================================================
# VEÍCULO
# =========================================================
TABELA_DIARIA = {"B": 151.92, "EA": 203.44}

def cotar_veiculo(origem, destino, ida, volta, grupo):
    km = get_km(origem, destino)
    dias = calcular_dias(ida, volta)
    diaria = TABELA_DIARIA.get(grupo, 0)
    valor_diarias = diaria * dias
    consumo = 13 if grupo == "B" else 9
    preco_comb = 5.80
    litros = (km * 2) / consumo
    valor_comb = litros * preco_comb
    total = valor_diarias + valor_comb

    return (
        f"🚗 VEÍCULO\n\n"
        f"Dias: {dias}\n"
        f"Diárias: R$ {valor_diarias:.2f}\n"
        f"Combustível: R$ {valor_comb:.2f}\n\n"
        f"TOTAL: R$ {total:.2f}"
    )

# =========================================================
# HOSPEDAGEM
# =========================================================
TABELA_HOSPEDAGEM = {
    "AC": 200, "AL": 200, "AP": 300, "AM": 350,
    "BA": 210, "CE": 350, "DF": 260, "ES": 300,
    "GO": 230, "MA": 260, "MT": 260, "MS": 260,
    "MG": 310, "PA": 300, "PB": 300, "PR": 250,
    "PE": 170, "PI": 160, "RJ": 305, "RN": 250,
    "RS": 280, "RO": 300, "RR": 300, "SC": 300,
    "SP": 350, "SE": 190, "TO": 270
}

def extrair_uf(dest):
    if "-" not in dest:
        return None
    return dest.split("-")[1].strip().upper()

def cotar_hospedagem(dest, ida, volta):
    uf = extrair_uf(dest)
    if not uf or uf not in TABELA_HOSPEDAGEM:
        return "Destino inválido."
    dias = calcular_dias(ida, volta) + 1
    valor = dias * TABELA_HOSPEDAGEM[uf]
    return (
        f"🏨 HOSPEDAGEM\n\n"
        f"UF: {uf}\n"
        f"Dias: {dias}\n"
        f"TOTAL: R$ {valor:.2f}"
    )

# =========================================================
# RODOVIÁRIO
# =========================================================
def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    valor = km * PRECO_KM
    return (
        f"🚌 RODOVIÁRIO\n\n"
        f"Distância: {km:.1f} km\n"
        f"TOTAL: R$ {valor:.2f}"
    )

# =========================================================
# COTAÇÃO GERAL
# =========================================================
def cotar_geral(origem, destino, ida, volta, grupo):
    return (
        cotar_rodoviario(origem, destino)
        + "\n\n"
        + cotar_hospedagem(destino, ida, volta)
        + "\n\n"
        + cotar_veiculo(origem, destino, ida, volta, grupo)
    )

# =========================================================
# FASTAPI
# =========================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api")
async def api_calc(request: Request):
    data = await request.json()

    tipo = data.get("tipo")
    origem = data.get("origem", "")
    destino = data.get("destino", "")
    ida = data.get("ida")
    volta = data.get("volta")
    grupo = data.get("grupo")

    ida = datetime.strptime(ida, "%Y-%m-%d").date() if ida else None
    volta = datetime.strptime(volta, "%Y-%m-%d").date() if volta else None

    if tipo == "rodoviario":
        resultado = cotar_rodoviario(origem, destino)
    elif tipo == "hospedagem":
        resultado = cotar_hospedagem(destino, ida, volta)
    elif tipo == "veiculo":
        resultado = cotar_veiculo(origem, destino, ida, volta, grupo)
    elif tipo == "geral":
        resultado = cotar_geral(origem, destino, ida, volta, grupo)
    else:
        resultado = "Tipo inválido."

    return {"resultado": resultado}

def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=start_api, daemon=True).start()

# =========================================================
# INTERFACE STREAMLIT
# =========================================================
st.set_page_config(layout="wide")

# CSS MSE
st.markdown("""
<style>
body { background-color: white; }
.titulo-mse {
    font-size: 34px;
    color: #7A0000;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# LOGO
logo = carregar_logo()
if logo:
    st.image(logo, width=120)
else:
    st.error("Erro ao carregar a logo!")

st.markdown("<div class='titulo-mse'>MSE TRAVEL EXPRESS</div>", unsafe_allow_html=True)
st.write("---")

# BOTÕES
col1, col2, col3, col4 = st.columns(4)

tipo = None
with col1:
    if st.button("Rodoviário"):
        tipo = "rodoviario"
with col2:
    if st.button("Hospedagem"):
        tipo = "hospedagem"
with col3:
    if st.button("Veículo"):
        tipo = "veiculo"
with col4:
    if st.button("Geral"):
        tipo = "geral"

if not tipo:
    st.info("Selecione uma opção acima.")
    st.stop()

# CAMPOS
origem = st.text_input("Origem")
destino = st.text_input("Destino (Cidade - UF)")

if tipo != "rodoviario":
    ida = st.date_input("Data de Ida", date.today())
    volta = st.date_input("Data de Volta", date.today())
else:
    ida, volta = None, None

grupo = None
if tipo in ["veiculo", "geral"]:
    grupo = st.radio("Grupo do Veículo", ["B", "EA"], horizontal=True)

# CALCULAR
if st.button("Calcular Cotação", type="primary"):
    if tipo == "rodoviario":
        st.success(cotar_rodoviario(origem, destino))
    elif tipo == "hospedagem":
        st.success(cotar_hospedagem(destino, ida, volta))
    elif tipo == "veiculo":
        st.success(cotar_veiculo(origem, destino, ida, volta, grupo))
    else:
        st.success(cotar_geral(origem, destino, ida, volta, grupo))
