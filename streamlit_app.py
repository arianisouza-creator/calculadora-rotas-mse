import streamlit as st
import threading
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
from datetime import datetime, date


# ===============================================================
# HOOK DE ESTILO MSE (LAYOUT COMPLETO)
# ===============================================================
st.markdown("""
<style>

body {
    background-color: #f2f2f2 !important;
}

/* Cabeçalho fixo */
.header {
    background-color: #7A0000;
    padding: 22px;
    text-align: center;
    color: white;
    font-size: 30px;
    font-weight: bold;
    width: 100%;
}

/* Card central */
.main-card {
    max-width: 900px;
    margin: 30px auto;
    background: white;
    padding: 35px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.12);
}

/* Botões grandes */
.big-button {
    background-color: #7A0000;
    color: white !important;
    padding: 18px;
    font-size: 20px;
    font-weight: 600;
    border-radius: 10px;
    width: 100%;
    border: none;
    margin-bottom: 12px;
}

.big-button:hover {
    background-color: #5a0000;
}

/* Título das seções */
.section-title {
    font-size: 26px;
    font-weight: bold;
    margin-top: 20px;
    color: #7A0000;
}

/* Resultados estilizados */
.result-card {
    background-color: #fafafa;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #e4e4e4;
    margin-top: 18px;
    font-size: 18px;
}

/* Botão PDF */
.pdf-button {
    background-color: #7A0000;
    color: white;
    padding: 14px;
    border-radius: 10px;
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


# ===============================================================
# CABEÇALHO + LOGO
# ===============================================================
st.markdown("<div class='header'>MSE TRAVEL EXPRESS</div>", unsafe_allow_html=True)

# Exibir logo MSE
try:
    st.image("LOGO MSE.png", width=140)
except:
    st.error("⚠ Não foi possível carregar LOGO MSE.png — coloque o arquivo na raiz do projeto.")


# ===============================================================
# CONFIGURAÇÕES DO BACKEND
# ===============================================================
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
    dias = (volta - ida).days
    return dias if dias > 0 else 1


# ===============================================================
# FUNÇÕES DE COTAÇÃO
# ===============================================================
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

    return f"""
🚗 **Locação de Veículo**

Dias de uso: **{dias} dia(s)**  

Valor das diárias: **R$ {valor_diarias:.2f}**  
Valor do combustível: **R$ {valor_comb:.2f}**

💰 **VALOR TOTAL: R$ {total:.2f}**
"""


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

    return f"""
🏨 **Hospedagem**

UF: **{uf}**  
Diárias: **{dias}**

Total: **R$ {valor:.2f}**
"""


def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    valor = km * PRECO_KM

    return f"""
🚌 **Passagem Rodoviária**

Distância: **{km:.1f} km**  
Total: **R$ {valor:.2f}**
"""


def cotar_geral(origem, destino, ida, volta, grupo):
    return (
        cotar_rodoviario(origem, destino)
        + "\n\n"
        + cotar_hospedagem(destino, ida, volta)
        + "\n\n"
        + cotar_veiculo(origem, destino, ida, volta, grupo)
    )


# ===============================================================
# FASTAPI SERVER
# ===============================================================
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


# ===============================================================
# INTERFACE PRINCIPAL
# ===============================================================
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

# BOTÕES DO MENU
tipo = None

if st.button("🚌 Passagem Rodoviária", key="rod", use_container_width=True):
    tipo = "rodoviario"

if st.button("🏨 Hospedagem", key="hosp", use_container_width=True):
    tipo = "hospedagem"

if st.button("🚗 Veículo", key="veic", use_container_width=True):
    tipo = "veiculo"

if st.button("📋 Cotação Geral", key="geral", use_container_width=True):
    tipo = "geral"


if not tipo:
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ===============================================================
# FORM DE CADA TIPO
# ===============================================================
st.markdown(f"<div class='section-title'>{tipo.upper()}</div>", unsafe_allow_html=True)

origem = st.text_input("Origem")
destino = st.text_input("Destino (Cidade - UF)")

if tipo != "rodoviario":
    ida = st.date_input("Data de ida", date.today())
    volta = st.date_input("Data de volta", date.today())
else:
    ida = None
    volta = None

grupo = None
if tipo in ["veiculo", "geral"]:
    grupo = st.selectbox(
        "Grupo do Veículo:",
        [
            "B - Hatch Manual (R$ 151,92)",
            "EA - Automático (R$ 203,44)"
        ]
    )
    grupo = "B" if grupo.startswith("B") else "EA"


if st.button("COTAR", use_container_width=True):
    st.markdown("<div class='result-card'>", unsafe_allow_html=True)

    if tipo == "rodoviario":
        st.markdown(cotar_rodoviario(origem, destino))
    elif tipo == "hospedagem":
        st.markdown(cotar_hospedagem(destino, ida, volta))
    elif tipo == "veiculo":
        st.markdown(cotar_veiculo(origem, destino, ida, volta, grupo))
    elif tipo == "geral":
        st.markdown(cotar_geral(origem, destino, ida, volta, grupo))

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("</div>", unsafe_allow_html=True)
