import streamlit as st
import requests
from datetime import date, timedelta
import base64

# =========================================================
# 1. CONFIGURAÇÃO VISUAL (CORPORATIVA MSE)
# =========================================================
st.set_page_config(
    page_title="Portal MSE Travel",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado (Vermelho MSE e Cards)
st.markdown("""
<style>
    /* Cor de Fundo da Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f4f4f4;
        border-right: 1px solid #ddd;
    }
    /* Títulos */
    h1, h2, h3 {
        color: #8B0000; /* Vermelho Sangue */
    }
    /* Botões Principais */
    .stButton>button {
        background-color: #8B0000;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #600000;
        color: white;
    }
    /* Cards de Resultado */
    .result-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #8B0000;
        margin-bottom: 20px;
    }
    .card-title {
        font-weight: bold;
        font-size: 1.1em;
        color: #555;
        margin-bottom: 10px;
        text-transform: uppercase;
    }
    .price-big {
        font-size: 1.8em;
        font-weight: 800;
        color: #2E7D32; /* Verde Dinheiro */
    }
    .info-text {
        color: #666;
        font-size: 0.9em;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CONFIGURAÇÕES E DADOS
# =========================================================

# Tenta pegar dos Segredos (Cloud) ou usa valores vazios/teste
try:
    MAPS_KEY = st.secrets["MAPS_KEY"]
    QP_USER = st.secrets["QP_USER"]
    QP_PASS = st.secrets["QP_PASS"]
except:
    # Fallback para rodar local se não tiver secrets configurado ainda
    MAPS_KEY = "" 
    QP_USER = "mse"
    QP_PASS = "" # Coloque a senha aqui se for rodar local

QP_URL = "https://queropassagem.qpdevs.com/ws_v4"
AFFILIATE = "MSE"

# Mapeamento de Cidades (Nome -> ID API)
DE_PARA_QP = {
    "sao paulo": "ROD_1", "são paulo": "ROD_1", "sp": "ROD_1",
    "rio de janeiro": "ROD_55", "rio": "ROD_55", "rj": "ROD_55",
    "curitiba": "ROD_3",
    "belo horizonte": "ROD_7", "bh": "ROD_7",
    "londrina": "ROD_23",
    "florianopolis": "ROD_6",
    "brasilia": "ROD_2",
    "campinas": "ROD_13",
    "santos": "ROD_10"
}

TABELA_HOSPEDAGEM = { 
    "SP": 350, "RJ": 305, "PR": 250, "SC": 300, "MG": 310, "RS": 280, 
    "BA": 210, "DF": 260, "GO": 230, "PE": 170, "CE": 350 
}

# =========================================================
# 3. FUNÇÕES DE INTEGRAÇÃO (BACKEND)
# =========================================================

def get_km_google(origem, destino):
    """Calcula distância via Google Maps"""
    if not MAPS_KEY: return 0
    
    # Adiciona "Brasil" para melhorar precisão
    orig_fmt = origem if "Brasil" in origem else f"{origem}, Brasil"
    dest_fmt = destino if "Brasil" in destino else f"{destino}, Brasil"

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": orig_fmt,
        "destinations": dest_fmt,
        "mode": "driving",
        "key": MAPS_KEY
    }
    
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if data['status'] == 'OK':
            elem = data['rows'][0]['elements'][0]
            if elem['status'] == 'OK':
                return elem['distance']['value'] / 1000 # Retorna em KM
    except Exception as e:
        print(f"Erro Maps: {e}")
    
    return 0 # Fallback

def buscar_passagem_api(origem, destino, data_iso):
    """Consulta API da Quero Passagem"""
    id_origem = DE_PARA_QP.get(origem.lower().strip())
    id_destino = DE_PARA_QP.get(destino.lower().strip())

    # Se não tiver mapeado, retorna erro controlado
    if not id_origem or not id_destino:
        return {"erro": True, "msg": "Cidade não mapeada (Tente Capitais)."}

    endpoint = f"{QP_URL}/new/search"
    body = {
        "from": id_origem,
        "to": id_destino,
        "travelDate": data_iso,
        "affiliateCode": AFFILIATE
    }

    try:
        # Autenticação Basic Auth Automática do Requests
        r = requests.post(endpoint, json=body, auth=(QP_USER, QP_PASS))
        
        if r.status_code == 200:
            res = r.json()
            # A API pode retornar lista de lista ou lista simples
            lista = res[0] if (isinstance(res, list) and len(res) > 0 and isinstance(res[0], list)) else res
            
            # Filtra e Ordena
            disponiveis = [v for v in lista if v.get('availableSeats', 0) > 0]
            if not disponiveis:
                return {"erro": True, "msg": "Sem viagens disponíveis."}
            
            disponiveis.sort(key=lambda x: x['price'])
            return {"erro": False, "dados": disponiveis[0]} # Retorna a mais barata
            
    except Exception as e:
        return {"erro": True, "msg": f"Erro API: {str(e)}"}
    
    return {"erro": True, "msg": "Erro desconhecido."}

def calcular_dias(ida, volta):
    if not ida or not volta: return 1
    delta = (volta - ida).days
    return delta if delta > 0 else 1

# =========================================================
# 4. INTERFACE DO USUÁRIO (FRONTEND)
# =========================================================

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/723/723955.png", width=50) # Placeholder Logo
    st.markdown("### MSE TRAVEL EXPRESS")
    st.markdown("---")
    menu = st.radio("Navegação", ["Cotação Geral", "Rodoviário", "Veículo", "Hospedagem"])
    st.markdown("---")
    st.info("ℹ️ Sistema integrado com Quero Passagem e Google Maps.")

# Título Principal
st.title(f"📊 {menu}")
st.markdown("Preencha os dados abaixo para realizar a cotação corporativa.")

# Formulário Unificado
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        origem = st.text_input("Cidade de Origem", placeholder="Ex: São Paulo")
        data_ida = st.date_input("Data de Ida", date.today())
    with col2:
        destino = st.text_input("Cidade de Destino", placeholder="Ex: Rio de Janeiro")
        if menu != "Rodoviário": # Ônibus API só vê Ida por enquanto
            data_volta = st.date_input("Data de Volta", date.today() + timedelta(days=1))
        else:
            data_volta = None

    grupo_carro = None
    if menu in ["Veículo", "Cotação Geral"]:
        grupo_carro = st.selectbox("Categoria do Veículo", ["B - Econômico (Manual)", "EA - Executivo (Automático)"])

    btn_calcular = st.button("CALCULAR COTAÇÃO 🚀")

st.markdown("---")

# =========================================================
# 5. LÓGICA DE PROCESSAMENTO E EXIBIÇÃO
# =========================================================

if btn_calcular:
    if not origem or not destino:
        st.error("Por favor, preencha Origem e Destino.")
    else:
        # 1. Obter Distância (Uma vez para todos)
        km_dist = get_km_google(origem, destino)
        
        # Colunas de Resultado
        res_col1, res_col2, res_col3 = st.columns(3)

        # --- A. RODOVIÁRIO ---
        if menu in ["Rodoviário", "Cotação Geral"]:
            with res_col1 if menu == "Cotação Geral" else st.container():
                api_res = buscar_passagem_api(origem, destino, str(data_ida))
                
                if not api_res['erro']:
                    v = api_res['dados']
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="card-title" style="color:#E67E22;">🚌 Melhor Tarifa (Ida)</div>
                        <div class="info-text"><b>Viação:</b> {v['company']['name']}</div>
                        <div class="info-text"><b>Horário:</b> {v['departure']['time'][:5]} ➝ {v['arrival']['time'][:5]}</div>
                        <div class="info-text"><b>Classe:</b> {v['serviceClass']}</div>
                        <div class="price-big">R$ {v['price']:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Fallback (Cálculo KM) se API falhar ou não tiver rota
                    valor_estimado = km_dist * 0.50
                    aviso = api_res['msg']
                    st.markdown(f"""
                    <div class="result-card" style="border-left: 5px solid #ccc;">
                        <div class="card-title">🚌 Estimativa (KM)</div>
                        <div class="info-text" style="color:red;">API: {aviso}</div>
                        <div class="info-text">Distância: {km_dist:.0f} km</div>
                        <div class="price-big" style="color:#666;">R$ {valor_estimado:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- B. HOSPEDAGEM ---
        if menu in ["Hospedagem", "Cotação Geral"]:
            local_exibicao = res_col2 if menu == "Cotação Geral" else st.container()
            with local_exibicao:
                dias = calcular_dias(data_ida, data_volta) + 1
                
                # Tenta extrair UF
                uf = "BR"
                for estado in TABELA_HOSPEDAGEM:
                    if estado in destino.upper():
                        uf = estado
                        break
                
                valor_diaria = TABELA_HOSPEDAGEM.get(uf, 300)
                total_hosp = valor_diaria * dias
                
                st.markdown(f"""
                <div class="result-card">
                    <div class="card-title" style="color:#27AE60;">🏨 Hospedagem ({uf})</div>
                    <div class="info-text"><b>Período:</b> {dias} dia(s)</div>
                    <div class="info-text"><b>Diária Média:</b> R$ {valor_diaria:.2f}</div>
                    <div class="price-big">R$ {total_hosp:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

        # --- C. VEÍCULO ---
        if menu in ["Veículo", "Cotação Geral"]:
            local_exibicao = res_col3 if menu == "Cotação Geral" else st.container()
            with local_exibicao:
                dias = calcular_dias(data_ida, data_volta)
                is_auto = "EA" in (grupo_carro or "")
                
                diaria = 203.44 if is_auto else 151.92
                consumo = 9 if is_auto else 13
                
                total_locacao = diaria * dias
                
                # Combustível (Ida e Volta)
                litros = (km_dist * 2) / consumo
                custo_comb = litros * 5.80
                total_carro = total_locacao + custo_comb
                
                aviso_km = "" if km_dist > 0 else "(Distância não calculada)"

                st.markdown(f"""
                <div class="result-card">
                    <div class="card-title" style="color:#2980B9;">🚗 Veículo + Comb.</div>
                    <div class="info-text"><b>Grupo:</b> {'Automático' if is_auto else 'Econômico'}</div>
                    <div class="info-text"><b>Locação ({dias}d):</b> R$ {total_locacao:.2f}</div>
                    <div class="info-text"><b>Combustível:</b> R$ {custo_comb:.2f} <small>{aviso_km}</small></div>
                    <div class="price-big">R$ {total_carro:.2f}</div>
                </div>
                """, unsafe_allow_html=True)

# =========================================================
# 6. LINKS DE SOLICITAÇÃO (RODAPÉ)
# =========================================================
st.markdown("### 📌 Próximos Passos")
st.write("Selecione o serviço para abrir o formulário de solicitação oficial:")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.link_button("🚌 Solicitar Passagem (Portal MSE)", "https://portalmse.com.br/index.php", use_container_width=True)

with col_b:
    st.link_button("🚗 Solicitar Veículo (Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSc-ImW1hPShhR0dUT2z77rRN0PJtPw93Pz6EBMkybPJW9r8eg/viewform", use_container_width=True)

with col_c:
    st.link_button("🏨 Solicitar Hospedagem (Forms)", "https://docs.google.com/forms/d/e/1FAIpQLSc7K3xq-fa_Hsw1yLel5pKILUVMM5kzhHbNRPDISGFke6aJ4A/viewform", use_container_width=True)
