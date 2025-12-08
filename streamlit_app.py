import streamlit as st
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
from datetime import datetime, date
from io import BytesIO
from PIL import Image
import base64

# ===========================================
# LOGO MSE (arquivo real via caminho local)
# ===========================================
LOGO_PATH = "LOGO MSE.png.png"

def carregar_logo():
    try:
        return Image.open(LOGO_PATH)
    except Exception as e:
        st.error("Não foi possível carregar a LOGO MSE.png.")
        return None


# ===========================================
# ESTILOS (CSS)
# ===========================================
st.markdown("""
<style>

body {
    background-color: #f2f2f2 !important;
}

/* Cabeçalho */
.header {
    background-color: #7A0000;
    padding: 25px;
    text-align: center;
    color: white;
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 20px;
}

/* Card Principal */
.main-card {
    max-width: 900px;
    margin: auto;
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

/* Botões */
.big-button {
    background-color: #7A0000;
    color: white !important;
    padding: 18px;
    font-size: 20px;
    font-weight: 600;
    border-radius: 12px;
    width: 100%;
    border: none;
    margin-bottom: 12px;
}

.big-button:hover {
    background-color: #5a0000;
}

/* Títulos de seção */
.section-title {
    font-size: 26px;
    font-weight: bold;
    margin-top: 20px;
    color: #7A0000;
}

/* Card de resultado */
.result-card {
    background-color: #fafafa;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e4e4e4;
    margin-top: 18px;
}

/* Botão PDF */
.pdf-button {
    background-color: #7A0000;
    color: white;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    font-weight: bold;
    width: 100%;
    cursor: pointer;
}

.pdf-button:hover {
    background-color: #5a0000;
}

</style>
""", unsafe_allow_html=True)


# ===========================================
# CONFIGURAÇÕES
# ===========================================
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


# ===========================================
# TABELAS
# ===========================================
TABELA_DIARIA = {"B": 151.92, "EA": 203.44}

TABELA_HOSPEDAGEM = {
    "AC": 200.00, "AM": 350.00, "RR": 300.00,
    "RO": 300.00, "AP": 300.00, "PA": 260.00,
    "MA": 260.00, "PI": 260.00, "CE": 260.00,
    "RN": 260.00, "PB": 260.00, "PE": 260.00,
    "AL": 260.00, "SE": 260.00, "BA": 260.00,
    "MG": 260.00, "ES": 260.00, "RJ": 350.00,
    "SP": 350.00, "PR": 260.00, "SC": 260.00,
    "RS": 260.00
}


# ===========================================
# COTAÇÕES
# ===========================================
def extrair_uf(dest):
    if "-" not in dest:
        return None
    return dest.split("-")[1].strip().upper()


def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    valor = km * PRECO_KM

    return f"""
### 🚌 Passagem Rodoviária
**Distância:** {km:.1f} km  
**Total:** R$ {valor:.2f}
"""


def cotar_hospedagem(dest, ida, volta):
    uf = extrair_uf(dest)
    if not uf or uf not in TABELA_HOSPEDAGEM:
        return "Destino inválido."

    dias = calcular_dias(ida, volta) + 1
    valor = dias * TABELA_HOSPEDAGEM[uf]

    return f"""
### 🏨 Hospedagem
**UF:** {uf}  
**Diárias:** {dias}  
**Total:** R$ {valor:.2f}
"""


def cotar_veiculo(origem, destino, ida, volta, grupo):
    km = get_km(origem, destino)
    dias = calcular_dias(ida, volta)
    diaria = TABELA_DIARIA.get(grupo, 0)
    consumo = 13 if grupo == "B" else 9
    preco_comb = 5.80

    litros = (km * 2) / consumo
    valor_comb = litros * preco_comb
    total = valor_comb + (diaria * dias)

    return f"""
### 🚗 Locação de Veículo
**Dias de uso:** {dias}  
**Valor das diárias:** R$ {diaria * dias:.2f}  
**Valor do combustível:** R$ {valor_comb:.2f}  

💰 **VALOR TOTAL: R$ {total:.2f}**
"""


def cotar_geral(origem, destino, ida, volta, grupo):
    return (
        cotar_rodoviario(origem, destino)
        + cotar_hospedagem(destino, ida, volta)
        + cotar_veiculo(origem, destino, ida, volta, grupo)
    )


# ===========================================
# FASTAPI BACKEND
# ===========================================
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
    origem = data.get("origem")
    destino = data.get("destino")
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
    else:
        resultado = cotar_geral(origem, destino, ida, volta, grupo)

    return {"resultado": resultado}


def iniciar_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=iniciar_api, daemon=True).start()


# ===========================================
# INTERFACE STREAMLIT (FRONTEND)
# ===========================================

st.markdown("<div class='header'>MSE TRAVEL EXPRESS</div>", unsafe_allow_html=True)

# LOGO
logo = carregar_logo()
if logo:
    st.image(logo, width=160)


st.markdown("<div class='main-card'>", unsafe_allow_html=True)


# BOTÕES PRINCIPAIS
col1, col2, col3, col4 = st.columns(4)

tipo = None
with col1:
    if st.button("🚌 Passagem Rodoviária", use_container_width=True):
        tipo = "rodoviario"
with col2:
    if st.button("🏨 Hospedagem", use_container_width=True):
        tipo = "hospedagem"
with col3:
    if st.button("🚗 Veículo", use_container_width=True):
        tipo = "veiculo"
with col4:
    if st.button("📄 Cotação Geral", use_container_width=True):
        tipo = "geral"


if not tipo:
    st.warning("Selecione uma opção acima.")
    st.stop()


# ===========================================
# FORMULÁRIO (CORRIGIDO)
# ===========================================
with st.form("formulario"):

    st.markdown(f"<div class='section-title'>{tipo.upper()}</div>", unsafe_allow_html=True)

    origem = st.text_input("Origem")
    destino = st.text_input("Destino (Cidade - UF)")

    if tipo != "rodoviario":
        ida = st.date_input("Data de Ida", date.today())
        volta = st.date_input("Data de Volta", date.today())
    else:
        ida = None
        volta = None

    grupo = None
    if tipo in ["veiculo", "geral"]:
        grupo_sel = st.selectbox(
            "Grupo do Veículo:",
            ["Grupo B - Hatch Manual (R$ 151,92)", "Grupo EA - Automático (R$ 203,44)"],
        )
        grupo = "B" if grupo_sel.startswith("Grupo B") else "EA"

    submitted = st.form_submit_button("COTAR")

# ===========================================
# RESULTADO
# ===========================================
if submitted:

    st.markdown("<div class='result-card'>", unsafe_allow_html=True)

    if tipo == "rodoviario":
        st.markdown(cotar_rodoviario(origem, destino))
    elif tipo == "hospedagem":
        st.markdown(cotar_hospedagem(destino, ida, volta))
    elif tipo == "veiculo":
        st.markdown(cotar_veiculo(origem, destino, ida, volta, grupo))
    elif tipo == "geral":
        st.markdown("## 📌 COTAÇÃO GERAL")
        st.markdown(cotar_geral(origem, destino, ida, volta, grupo))

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
