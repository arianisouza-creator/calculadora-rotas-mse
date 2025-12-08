# ============================================================
# MSE TRAVEL EXPRESS – SISTEMA COMPLETO (STREAMLIT + PYTHON)
# ============================================================

import streamlit as st
import requests
import pdfkit
import tempfile

# ============================
# CONFIGURAÇÕES
# ============================
API_KEY = "SUA_API_KEY_DO_GOOGLE"
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
        elemento = res["rows"][0]["elements"][0]
        if elemento["status"] != "OK":
            return 0
        return elemento["distance"]["value"] / 1000
    except:
        return 0


# ============================
# CÁLCULO DE DIAS
# ============================
def calcular_dias(ida, volta):
    if not ida or not volta:
        return 1
    return (volta - ida).days


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

    html = f"""
    <h3>🚗 Locação de Veículo</h3>
    Dias: <b>{dias}</b><br>
    Diárias: R$ {valor_diarias:.2f}<br>
    Combustível: R$ {valor_comb:.2f}<br><br>
    <b>TOTAL: R$ {total:.2f}</b>
    """
    return html, total


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

def extrair_uf(destino):
    if "-" not in destino:
        return None
    return destino.split("-")[1].strip().upper()

def cotar_hospedagem(destino, ida, volta):
    uf = extrair_uf(destino)
    if not uf or uf not in TABELA_HOSPEDAGEM:
        return "<b>❌ UF inválida. Use: Cidade - UF</b>", 0

    diaria = TABELA_HOSPEDAGEM[uf]
    dias = calcular_dias(ida, volta) + 1
    total = diaria * dias

    html = f"""
    <h3>🏨 Hospedagem</h3>
    UF: {uf}<br>
    Diárias: {dias}<br><br>
    <b>Total: R$ {total:.2f}</b>
    """
    return html, total


# ============================
# RODOVIÁRIO
# ============================
def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    total = km * PRECO_KM

    html = f"""
    <h3>🚌 Passagem Rodoviária</h3>
    KM: {km:.1f}<br>
    Total: R$ {total:.2f}
    """
    return html, total


# ============================
# PDF
# ============================
def gerar_pdf(html_content):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdfkit.from_string(html_content, tmp.name)
        return tmp.name


# ============================
# INTERFACE STREAMLIT
# ============================
st.title("MSE TRAVEL EXPRESS")

opcao = st.selectbox(
    "Selecione a cotação:",
    ["Rodoviário", "Hospedagem", "Veículo", "Cotação Geral"]
)

origem = st.text_input("Origem")
destino = st.text_input("Destino (Ex: Curitiba - PR)")

ida = st.date_input("Data ida")
volta = st.date_input("Data volta")

grupo = None
if opcao in ["Veículo", "Cotação Geral"]:
    grupo = st.selectbox("Grupo veículo:", ["B", "EA"])

if st.button("CALCULAR"):
    resultado = ""

    if opcao == "Rodoviário":
        resultado, _ = cotar_rodoviario(origem, destino)

    elif opcao == "Hospedagem":
        resultado, _ = cotar_hospedagem(destino, ida, volta)

    elif opcao == "Veículo":
        resultado, _ = cotar_veiculo(origem, destino, ida, volta, grupo)

    elif opcao == "Cotação Geral":
        rod, _ = cotar_rodoviario(origem, destino)
        hosp, _ = cotar_hospedagem(destino, ida, volta)
        vei, _ = cotar_veiculo(origem, destino, ida, volta, grupo)

        resultado = f"<h2>COTAÇÃO GERAL</h2>{rod}<hr>{hosp}<hr>{vei}"

    st.markdown(resultado, unsafe_allow_html=True)

    if st.button("Gerar PDF"):
        pdf_path = gerar_pdf(resultado)
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Baixar PDF", f, file_name="Cotacao_MSE.pdf")
