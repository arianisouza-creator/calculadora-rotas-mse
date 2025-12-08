import streamlit as st
import requests
import json
from datetime import datetime, date
from fpdf import FPDF

# ==============================
# CONFIGURAÇÕES
# ==============================
API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"   # coloque a sua
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

# ==============================
# FUNÇÕES BASE
# ==============================
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
        if elem["status"] != "OK":
            return 0
        return elem["distance"]["value"] / 1000
    except:
        return 0


def calcular_dias(ida, volta):
    if not ida or not volta:
        return 1
    return (volta - ida).days or 1


# ==============================
# VEÍCULO
# ==============================
TABELA_DIARIA = {
    "B": 151.92,
    "EA": 203.44
}

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

    texto = (
        f"🚗 Locação de Veículo\n\n"
        f"Dias: {dias}\n"
        f"Diárias: R$ {valor_diarias:.2f}\n"
        f"Combustível: R$ {valor_comb:.2f}\n\n"
        f"TOTAL: R$ {total:.2f}"
    )

    return texto


# ==============================
# HOSPEDAGEM
# ==============================
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
        f"🏨 Hospedagem\n\n"
        f"UF: {uf}\n"
        f"Diárias: {dias}\n"
        f"TOTAL: R$ {valor:.2f}"
    )


# ==============================
# RODOVIÁRIO
# ==============================
def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    valor = km * PRECO_KM

    return (
        f"🚌 Rodoviário\n\n"
        f"Distância: {km:.1f} km\n"
        f"TOTAL: R$ {valor:.2f}"
    )


# ==============================
# COTAÇÃO GERAL
# ==============================
def cotar_geral(origem, destino, ida, volta, grupo):
    rod = cotar_rodoviario(origem, destino)
    hosp = cotar_hospedagem(destino, ida, volta)
    vei = cotar_veiculo(origem, destino, ida, volta, grupo)

    return rod + "\n\n" + hosp + "\n\n" + vei


# ==============================
# API ENDPOINT  /api
# ==============================
def handle_api_request():
    try:
        raw = st.request.body
        data = json.loads(raw.decode("utf-8"))

        tipo = data.get("tipo")
        origem = data.get("origem", "")
        destino = data.get("destino", "")
        ida = data.get("ida", "")
        volta = data.get("volta", "")
        grupo = data.get("grupo", "B")

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

        st.json({"resultado": resultado})
        return True

    except Exception as e:
        st.json({"erro": str(e)})
        return True


# Detectando chamada API
if "request" in st.context and st.context.request.path == "/api":
    handle_api_request()
else:
    # ==============================
    # PAINEL STREAMLIT NORMAL
    # ==============================
    st.title("MSE TRAVEL EXPRESS")

    tipo = st.selectbox("Selecione o tipo:", ["rodoviario", "hospedagem", "veiculo", "geral"])

    origem = st.text_input("Origem")
    destino = st.text_input("Destino (Cidade - UF)")

    ida = st.date_input("Data de ida", date.today())
    volta = st.date_input("Data de volta", date.today())

    grupo = None
    if tipo in ["veiculo", "geral"]:
        grupo = st.selectbox("Grupo do veículo", ["B", "EA"])

    if st.button("Calcular"):
        if tipo == "rodoviario":
            st.text(cotar_rodoviario(origem, destino))

        elif tipo == "hospedagem":
            st.text(cotar_hospedagem(destino, ida, volta))

        elif tipo == "veiculo":
            st.text(cotar_veiculo(origem, destino, ida, volta, grupo))

        elif tipo == "geral":
            st.text(cotar_geral(origem, destino, ida, volta, grupo))
