# ============================================================
# MSE TRAVEL EXPRESS – STREAMLIT + PYTHON + FPDF (SEM ERROS)
# ============================================================

import streamlit as st
import requests
from fpdf import FPDF
import tempfile
from datetime import date

# ============================
# CONFIGURAÇÕES
# ============================
API_KEY = "SUA_API_KEY_GOOGLE"
PRECO_KM = 0.50

# ============================
# BANCO DE CIDADES
# ============================
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
    cidade = cidade.strip().lower()
    return CIDADES_BR.get(cidade, cidade + ", Brasil")

# ============================
# KM COM GOOGLE MAPS
# ============================
def get_km(origem, destino):
    origem = ajustar_cidade(origem)
    destino = ajustar_cidade(destino)

    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric"
        f"&origins={origem}&destinations={destino}&key={API_KEY}"
    )

    res = requests.get(url).json()
    try:
        elem = res["rows"][0]["elements"][0]
        if elem["status"] != "OK":
            return 0
        return elem["distance"]["value"] / 1000
    except:
        return 0

# ============================
# CÁLCULO DE DIAS
# ============================
def calcular_dias(ida, volta):
    return (volta - ida).days if ida and volta else 1

# ============================
# VEÍCULO
# ============================
TABELA_DIARIA_VEICULO = {
    "B": 151.92,
    "EA": 203.44,
}

def cotar_veiculo(origem, destino, ida, volta, grupo):
    km = get_km(origem, destino)
    dias = calcular_dias(ida, volta)

    diaria = TABELA_DIARIA_VEICULO.get(grupo, 0)
    valor_diarias = diaria * dias

    preco_comb = 5.80
    consumo = 13 if grupo == "B" else 9

    km_total = km * 2
    litros = km_total / consumo
    valor_comb = litros * preco_comb

    total = valor_diarias + valor_comb

    texto = f"""
🚗 LOCAÇÃO DE VEÍCULO
Dias: {dias}
Diárias: R$ {valor_diarias:.2f}
Combustível: R$ {valor_comb:.2f}

TOTAL: R$ {total:.2f}
"""
    return texto, total

# ============================
# HOSPEDAGEM
# ============================
TABELA_HOSPEDAGEM = {
    "AC": 200, "AL": 200, "AP": 300, "AM": 350,
    "BA": 210, "CE": 350, "DF": 260, "ES": 300,
    "GO": 230, "MA": 260, "MT": 260, "MS": 260,
    "MG": 310, "PA": 300, "PB": 300, "PR": 250,
    "PE": 170, "PI": 160, "RJ": 305, "RN": 250,
    "RS": 280, "RO": 300, "RR": 300, "SC": 300,
    "SP": 350, "SE": 190, "TO": 270,
}

def extrair_uf(dest):
    if "-" not in dest:
        return None
    return dest.split("-")[1].strip().upper()

def cotar_hospedagem(destino, ida, volta):
    uf = extrair_uf(destino)
    if not uf or uf not in TABELA_HOSPEDAGEM:
        return "UF inválida. Use formato Cidade - UF.", 0

    dias = calcular_dias(ida, volta) + 1
    diaria = TABELA_HOSPEDAGEM[uf]
    total = diaria * dias

    texto = f"""
🏨 HOSPEDAGEM
UF: {uf}
Diárias: {dias}
TOTAL: R$ {total:.2f}
"""
    return texto, total

# ============================
# RODOVIÁRIO
# ============================
def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    total = km * PRECO_KM

    texto = f"""
🚌 RODOVIÁRIO
Distância: {km:.1f} km
TOTAL: R$ {total:.2f}
"""
    return texto, total

# ============================
# GERAR PDF (FPDF)
# ============================
def gerar_pdf(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for linha in texto.split("\n"):
        pdf.cell(0, 10, txt=linha, ln=True)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# ============================
# INTERFACE STREAMLIT
# ============================
st.title("MSE TRAVEL EXPRESS")

opcao = st.selectbox("Selecione o tipo:", ["Rodoviário", "Hospedagem", "Veículo", "Cotação Geral"])

origem = st.text_input("Origem")
destino = st.text_input("Destino (Ex: Curitiba - PR)")

ida = st.date_input("Data de ida", date.today())
volta = st.date_input("Data de volta", date.today())

grupo = None
if opcao in ["Veículo", "Cotação Geral"]:
    grupo = st.selectbox("Grupo do veículo", ["B", "EA"])

if st.button("Calcular"):
    if opcao == "Rodoviário":
        texto, _ = cotar_rodoviario(origem, destino)

    elif opcao == "Hospedagem":
        texto, _ = cotar_hospedagem(destino, ida, volta)

    elif opcao == "Veículo":
        texto, _ = cotar_veiculo(origem, destino, ida, volta, grupo)

    else:
        rod, _ = cotar_rodoviario(origem, destino)
        hosp, _ = cotar_hospedagem(destino, ida, volta)
        vei, _ = cotar_veiculo(origem, destino, ida, volta, grupo)
        texto = f"{rod}\n\n{hosp}\n\n{vei}"

    st.text(texto)

    if st.button("Gerar PDF"):
        pdf_file = gerar_pdf(texto)
        with open(pdf_file, "rb") as f:
            st.download_button("📄 Baixar PDF", f, "cotacao_mse.pdf")
