import streamlit as st
import requests
from datetime import date, datetime
from io import BytesIO
from PIL import Image

# ==========================================
# CONFIGURAÇÕES
# ==========================================
API_KEY = "AIzaSyA6B_wPkGZ0-jMoKxahLLpwhWFiyLdmxFk"
PRECO_KM = 0.50

# LOGO NO MESMO DIRETÓRIO
LOGO_PATH = "LOGO MSE.png"

def carregar_logo():
    try:
        return Image.open(LOGO_PATH)
    except:
        return None

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


# ==========================================
# FUNÇÕES BASE
# ==========================================
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
    dias = (volta - ida).days
    return dias if dias > 0 else 1


# ==========================================
# RODOVIÁRIO
# ==========================================
def cotar_rodoviario(origem, destino):
    km = get_km(origem, destino)
    total = km * PRECO_KM

    return f"""
### 🚌 Passagem Rodoviária
**Distância:** {km:.1f} km  
**Total:** R$ {total:.2f}
"""


# ==========================================
# HOSPEDAGEM
# ==========================================
TABELA_HOSPEDAGEM = {
    "AC": 200, "AL": 200, "AP": 300, "AM": 350,
    "BA": 210, "CE": 350, "DF": 260, "ES": 300,
    "GO": 230, "MA": 260, "MT": 260, "MS": 260,
    "MG": 310, "PA": 300, "PB": 300, "PR": 250,
    "PE": 170, "PI": 160, "RJ": 305, "RN": 250,
    "RS": 280, "RO": 300, "RR": 300, "SC": 300,
    "SP": 350, "SE": 190, "TO": 270
}

def extrair_uf(destino):
    if "-" not in destino:
        return None
    return destino.split("-")[1].strip().upper()


def cotar_hospedagem(destino, ida, volta):
    uf = extrair_uf(destino)
    if uf not in TABELA_HOSPEDAGEM:
        return "**Destino inválido. Use o formato Cidade - UF**"

    diaria = TABELA_HOSPEDAGEM[uf]
    dias = calcular_dias(ida, volta) + 1
    total = dias * diaria

    return f"""
### 🏨 Hospedagem
**UF:** {uf}  
**Diárias:** {dias}  
**Total:** R$ {total:.2f}
"""


# ==========================================
# VEÍCULO
# ==========================================
TABELA_DIARIA = {
    "B": 151.92,
    "EA": 203.44,
}

def cotar_veiculo(origem, destino, ida, volta, grupo):
    km = get_km(origem, destino)
    dias = calcular_dias(ida, volta)

    diaria = TABELA_DIARIA[grupo]
    valor_diarias = dias * diaria

    consumo = 13 if grupo == "B" else 9
    preco_comb = 5.80
    litros = (km * 2) / consumo
    valor_comb = litros * preco_comb

    total = valor_comb + valor_diarias

    return f"""
### 🚗 Locação de Veículo
**Dias:** {dias}  
**Diárias:** R$ {valor_diarias:.2f}  
**Combustível:** R$ {valor_comb:.2f}  

### 💰 TOTAL: R$ {total:.2f}
"""


# ==========================================
# COTAÇÃO GERAL
# ==========================================
def cotar_geral(origem, destino, ida, volta, grupo):
    return (
        cotar_rodoviario(origem, destino)
        + "\n---\n"
        + cotar_hospedagem(destino, ida, volta)
        + "\n---\n"
        + cotar_veiculo(origem, destino, ida, volta, grupo)
    )


# ==========================================
# INTERFACE STREAMLIT
# ==========================================
st.set_page_config(layout="wide")

# LOGO
logo = carregar_logo()
if logo:
    st.image(logo, width=160)
else:
    st.error("Não foi possível carregar a LOGO MSE.png")

st.markdown("<h1 style='text-align:center; color:#7A0000;'>MSE TRAVEL EXPRESS</h1>", unsafe_allow_html=True)
st.write("---")

# BOTÕES DE NAVEGAÇÃO
cols = st.columns(4)
with cols[0]: rod = st.button("🚌 Passagem Rodoviária")
with cols[1]: hos = st.button("🏨 Hospedagem")
with cols[2]: vei = st.button("🚗 Veículo")
with cols[3]: ger = st.button("🧾 Cotação Geral")

tipo = None
if rod: tipo = "rodoviario"
if hos: tipo = "hospedagem"
if vei: tipo = "veiculo"
if ger: tipo = "geral"

if not tipo:
    st.info("Selecione uma opção acima.")
    st.stop()

# FORMULÁRIO
with st.form("form_main", clear_on_submit=False):

    st.subheader(tipo.upper())

    origem = st.text_input("Origem")
    destino = st.text_input("Destino (Cidade - UF)")

    ida = volta = None

    if tipo != "rodoviario":
        ida = st.date_input("Data de Ida", date.today())
        volta = st.date_input("Data de Volta", date.today())

    grupo = None
    if tipo in ["veiculo", "geral"]:
        grupo_label = st.selectbox(
            "Grupo do Veículo",
            ["B - Manual (151,92)", "EA - Automático (203,44)"]
        )
        grupo = "B" if grupo_label.startswith("B") else "EA"

    submit = st.form_submit_button("COTAR")

# RESULTADO
if submit:

    if tipo == "rodoviario":
        st.markdown(cotar_rodoviario(origem, destino))

    elif tipo == "hospedagem":
        st.markdown(cotar_hospedagem(destino, ida, volta))

    elif tipo == "veiculo":
        st.markdown(cotar_veiculo(origem, destino, ida, volta, grupo))

    elif tipo == "geral":
        st.markdown(cotar_geral(origem, destino, ida, volta, grupo))
