import streamlit as st
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
from datetime import datetime, date
from PIL import Image

# =========================================================
# 🔥 TEMA DARK CORPORATIVO MSE
# =========================================================
st.markdown("""
<style>

    /* ======================== */
    /*   GLOBAL DARK THEME      */
    /* ======================== */

    body, .stApp {
        background-color: #0d0d0d !important;
        color: #e6e6e6 !important;
    }

    /* TÍTULO NEON */
    h1 {
        font-size: 42px !important;
        text-align: center !important;
        color: #ff4d4d !important;
        text-shadow: 0 0 12px #ff1a1a, 0 0 24px #b30000;
        font-weight: 800 !important;
    }

    /* TEXTOS */
    h2, h3, h4, h5, h6, p, label {
        color: #e6e6e6 !important;
        font-weight: 500 !important;
    }

    /* ======================== */
    /*        INPUTS            */
    /* ======================== */
    input, select, textarea {
        background: rgba(255,255,255,0.05) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 10px !important;
        border: 1px solid #333 !important;
        transition: 0.3s ease-in-out;
        backdrop-filter: blur(4px);
    }

    input:focus, select:focus {
        border-color: #ff4d4d !important;
        box-shadow: 0 0 10px #ff3333 !important;
    }

    /* ======================== */
    /*        SELECTBOX         */
    /* ======================== */
    .stSelectbox div {
        background-color: #1a1a1a !important;
        color: white !important;
    }

    /* ======================== */
    /*         BUTTONS          */
    /* ======================== */
    .stButton>button {
        background: linear-gradient(90deg, #7A0000, #cc0000) !important;
        color: white !important;
        border: none !important;
        padding: 12px 18px !important;
        border-radius: 10px !important;
        font-size: 18px !important;
        transition: 0.3s ease-in-out !important;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.4);
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #cc0000, #ff1a1a) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 0 18px rgba(255, 0, 0, 0.8);
    }

    /* ======================== */
    /*       RESULT CARDS       */
    /* ======================== */
    .stMarkdown, .stAlert, .result-card {
        background: rgba(255,255,255,0.06) !important;
        color: white !important;
        padding: 18px !important;
        border-radius: 12px !important;
        border-left: 4px solid #ff3333 !important;
        box-shadow: 0 0 12px rgba(255, 0, 0, 0.15);
        margin-top: 15px !important;
    }

    hr {
        border: 1px solid #333 !important;
    }

</style>
""", unsafe_allow_html=True)

# =========================================================
# LOGO
# =========================================================
try:
    logo = Image.open("LOGO MSE.png")
    st.image(logo, width=180)
except:
    st.warning("⚠ Não foi possível carregar a logo (LOGO MSE.png).")

# =========================================================
# TÍTULO
# =========================================================
st.markdown("<h1 style='text-align:center; color:#ff5555;'>MSE TRAVEL EXPRESS</h1>", unsafe_allow_html=True)


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
    return max((volta - ida).days, 1)


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
        f"🚗 **Locação de Veículo**\n\n"
        f"**Dias:** {dias}\n"
        f"**Diárias:** R$ {valor_diarias:.2f}\n"
        f"**Combustível:** R$ {valor_comb:.2f}\n\n"
        f"💰 **TOTAL:** R$ {total:.2f}"
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
        return "❌ Destino inválido (use Cidade - UF)"

    dias = calcular_dias(ida, volta) + 1
    valor = dias * TABELA_HOSPEDAGEM[uf]

    return (
        f"🏨 **Hospedagem**\n\n"
        f"**UF:** {uf}\n"
        f"**Diárias:** {dias}\n\n"
        f"💰 **TOTAL:** R$ {valor:.2f}"
    )


# =========================================================
# RODOVIÁRIO
# =========================================================
def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    valor = km * PRECO_KM
    return (
        f"🚌 **Passagem Rodoviária**\n\n"
        f"**Distância:** {km:.1f} km\n\n"
        f"💰 **TOTAL:** R$ {valor:.2f}"
    )


# =========================================================
# COTAÇÃO GERAL
# =========================================================
def cotar_geral(origem, destino, ida, volta, grupo):
    return (
        cotar_rodoviario(origem, destino)
        + "\n\n---\n\n"
        + cotar_hospedagem(destino, ida, volta)
        + "\n\n---\n\n"
        + cotar_veiculo(origem, destino, ida, volta, grupo)
    )


# =========================================================
# FASTAPI BACKEND
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


# =========================================================
# INIT API THREAD
# =========================================================
def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=start_api, daemon=True).start()


# =========================================================
# INTERFACE WEB STREAMLIT
# =========================================================
st.subheader("Selecione o tipo de cotação:")

tipo = st.selectbox(
    "Tipo",
    ["rodoviario", "hospedagem", "veiculo", "geral"]
)

origem = st.text_input("Origem")
destino = st.text_input("Destino (Cidade - UF)")

ida = st.date_input("Data de ida", date.today())
volta = st.date_input("Data de volta", date.today())

grupo = None
if tipo in ["veiculo", "geral"]:
    grupo = st.selectbox("Grupo do veículo:", ["B", "EA"])

if st.button("Calcular"):
    if tipo == "rodoviario":
        st.markdown(cotar_rodoviario(origem, destino))
    elif tipo == "hospedagem":
        st.markdown(cotar_hospedagem(destino, ida, volta))
    elif tipo == "veiculo":
        st.markdown(cotar_veiculo(origem, destino, ida, volta, grupo))
    else:
        st.markdown(cotar_geral(origem, destino, ida, volta, grupo))

# =========================================================
# Seleção de Solicitação
# =========================================================
st.subheader("📌 Selecionar solicitação:")

opcao = st.selectbox(
    "Selecione o que deseja solicitar:",
    ["-- Selecionar --", "Passagem Rodoviária", "Hospedagem", "Veículo"]
)

if opcao != "-- Selecionar --":
    if st.button("Abrir Solicitação"):
        if opcao == "Passagem Rodoviária":
            st.markdown("[Abrir Portal Rodoviário](https://portalmse.com.br/index.php)")
        elif opcao == "Veículo":
            st.markdown("[Abrir Solicitação de Veículo](https://docs.google.com/forms/d/e/1FAIpQLSc-ImW1hPShhR0dUT2z77rRN0PJtPw93Pz6EBMkybPJW9r8eg/viewform)")
        elif opcao == "Hospedagem":
            st.markdown("[Abrir Solicitação de Hospedagem](https://docs.google.com/forms/d/e/1FAIpQLSc7K3xq-fa_Hsw1yLel5pKILUVMM5kzhHbNRPDISGFke6aJ4A/viewform)")
     

