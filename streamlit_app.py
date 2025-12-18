import streamlit as st
import requests
from datetime import date, timedelta

# =========================================================
# 1. CONFIGURAÇÃO VISUAL
# =========================================================
st.set_page_config(
    page_title="Portal MSE Travel",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #f4f4f4; border-right: 1px solid #ddd; }
    h1, h2, h3 { color: #8B0000; }
    .stButton>button { background-color: #8B0000; color: white; border-radius: 8px; font-weight: bold; border: none; width: 100%; padding: 10px; transition: 0.3s; }
    .stButton>button:hover { background-color: #600000; color: white; }
    .result-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #8B0000; margin-bottom: 20px; }
    .card-title { font-weight: bold; font-size: 1.1em; color: #555; margin-bottom: 10px; text-transform: uppercase; }
    .price-big { font-size: 1.8em; font-weight: 800; color: #2E7D32; }
    .info-text { color: #666; font-size: 0.9em; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CONFIGURAÇÕES E DADOS
# =========================================================

# Tenta pegar chaves. Se falhar, define vazias.
try:
    MAPS_KEY = st.secrets.get("MAPS_KEY", "")
    QP_USER = st.secrets.get("QP_USER", "mse")
    QP_PASS = st.secrets.get("QP_PASS", "")
except:
    MAPS_KEY = ""
    QP_USER = "mse"
    QP_PASS = ""

QP_URL = "https://queropassagem.qpdevs.com/ws_v4"
AFFILIATE = "MSE"

DE_PARA_QP = {
    "sao paulo": "ROD_1", "são paulo": "ROD_1", "sp": "ROD_1",
    "rio de janeiro": "ROD_55", "rio": "ROD_55", "rj": "ROD_55",
    "curitiba": "ROD_3", "belo horizonte": "ROD_7", "bh": "ROD_7",
    "londrina": "ROD_23", "florianopolis": "ROD_6", "brasilia": "ROD_2",
    "campinas": "ROD_13", "santos": "ROD_10"
}

TABELA_HOSPEDAGEM = { 
    "SP": 350, "RJ": 305, "PR": 250, "SC": 300, "MG": 310, "RS": 280, 
    "BA": 210, "DF": 260, "GO": 230, "PE": 170, "CE": 350 
}

# =========================================================
# 3. INTEGRAÇÕES (COM CORREÇÃO DE DISTÂNCIA)
# =========================================================

def get_km_google(origem, destino):
    """Retorna a distância em KM. Se falhar, retorna 0."""
    if not MAPS_KEY: return 0 # Sem chave = 0 km
    
    orig_fmt = origem if "Brasil" in origem else f"{origem}, Brasil"
    dest_fmt = destino if "Brasil" in destino else f"{destino}, Brasil"
    
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {"origins": orig_fmt, "destinations": dest_fmt, "mode": "driving", "key": MAPS_KEY}
    
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            metros = data['rows'][0]['elements'][0]['distance']['value']
            return metros / 1000.0
    except Exception as e:
        print(f"Erro Maps: {e}")
    
    return 0

def buscar_passagem_api(origem, destino, data_iso):
    id_origem = DE_PARA_QP.get(origem.lower().strip())
    id_destino = DE_PARA_QP.get(destino.lower().strip())

    if not id_origem or not id_destino:
        return {"erro": True, "msg": "Cidade não mapeada (Tente Capitais)."}

    endpoint = f"{QP_URL}/new/search"
    body = {"from": id_origem, "to": id_destino, "travelDate": data_iso, "affiliateCode": AFFILIATE}

    try:
        r = requests.post(endpoint, json=body, auth=(QP_USER, QP_PASS))
        if r.status_code == 200:
            res = r.json()
            lista = res[0] if (isinstance(res, list) and len(res) > 0 and isinstance(res[0], list)) else res
            disponiveis = [v for v in lista if v.get('availableSeats', 0) > 0]
            if not disponiveis: return {"erro": True, "msg": "Sem viagens."}
            disponiveis.sort(key=lambda x: x['price'])
            return {"erro": False, "dados": disponiveis[0]}
    except Exception as e:
        return {"erro": True, "msg": f"Erro API: {str(e)}"}
    return {"erro": True, "msg": "Erro desconhecido."}

def calcular_dias(ida, volta):
    if not ida or not volta: return 1
    delta = (volta - ida).days
    return delta if delta > 0 else 1

# =========================================================
# 4. FRONTEND
# =========================================================

with st.sidebar:
    # AQUI ESTÁ O SEU LOGO (PRECISA SUBIR O ARQUIVO 'LOGO MSE.png' PRO GITHUB)
    try:
        st.image("LOGO MSE.png", width=160)
    except:
        st.warning("Imagem LOGO MSE.png não encontrada.")
        
    st.markdown("### MSE TRAVEL EXPRESS")
    st.markdown("---")
    menu = st.radio("Navegação", ["Cotação Geral", "Rodoviário", "Veículo", "Hospedagem"])
    st.markdown("---")
    st.info("ℹ️ Sistema Integrado.")

st.title(f"📊 {menu}")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        origem = st.text_input("Cidade de Origem", placeholder="Ex: São Paulo")
        data_ida = st.date_input("Data de Ida", date.today())
    with col2:
        destino = st.text_input("Cidade de Destino", placeholder="Ex: Rio de Janeiro")
        data_volta = st.date_input("Data de Volta", date.today() + timedelta(days=1)) if menu != "Rodoviário" else None

    grupo_carro = None
    if menu in ["Veículo", "Cotação Geral"]:
        grupo_carro = st.selectbox("Categoria do Veículo", ["B - Econômico (Manual)", "EA - Executivo (Automático)"])

    btn_calcular = st.button("CALCULAR COTAÇÃO 🚀")

st.markdown("---")

if btn_calcular:
    if not origem or not destino:
        st.error("Preencha Origem e Destino.")
    else:
        # 1. TENTA CALCULAR DISTÂNCIA REAL
        km_dist = get_km_google(origem, destino)
        
        # 2. SE FOR 0 (ERRO API), USA UMA DISTÂNCIA SIMULADA PARA NÃO ZERAR O CÁLCULO
        usou_simulacao = False
        if km_dist == 0:
            km_dist = 450 # Simulação de ~450km (Tipo SP-Rio)
            usou_simulacao = True

        c1, c2, c3 = st.columns(3)

        # RODOVIÁRIO
        if menu in ["Rodoviário", "Cotação Geral"]:
            with (c1 if menu == "Cotação Geral" else st.container()):
                api_res = buscar_passagem_api(origem, destino, str(data_ida))
                if not api_res['erro']:
                    v = api_res['dados']
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="card-title" style="color:#E67E22;">🚌 Melhor Tarifa</div>
                        <div class="info-text"><b>Viação:</b> {v['company']['name']}</div>
                        <div class="info-text"><b>Horário:</b> {v['departure']['time'][:5]} ➝ {v['arrival']['time'][:5]}</div>
                        <div class="price-big">R$ {v['price']:.2f}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    est = km_dist * 0.50
                    aviso = "(API Offline - Valor Estimado)" if usou_simulacao else "(Sem rota ônibus - Valor por KM)"
                    st.markdown(f"""
                    <div class="result-card" style="border-left: 5px solid gray;">
                        <div class="card-title">🚌 Estimativa KM</div>
                        <div class="info-text" style="color:red;">{aviso}</div>
                        <div class="price-big" style="color:#666;">R$ {est:.2f}</div>
                    </div>""", unsafe_allow_html=True)

        # HOSPEDAGEM
        if menu in ["Hospedagem", "Cotação Geral"]:
            with (c2 if menu == "Cotação Geral" else st.container()):
                dias = calcular_dias(data_ida, data_volta) + 1
                uf = next((uf for uf in TABELA_HOSPEDAGEM if uf in destino.upper()), "BR")
                total = TABELA_HOSPEDAGEM.get(uf, 300) * dias
                st.markdown(f"""
                <div class="result-card">
                    <div class="card-title" style="color:#27AE60;">🏨 Hotel ({uf})</div>
                    <div class="info-text"><b>Dias:</b> {dias}</div>
                    <div class="price-big">R$ {total:.2f}</div>
                </div>""", unsafe_allow_html=True)

        # VEÍCULO (AQUI ESTAVA O PROBLEMA)
        if menu in ["Veículo", "Cotação Geral"]:
            with (c3 if menu == "Cotação Geral" else st.container()):
                dias = calcular_dias(data_ida, data_volta)
                is_auto = "EA" in (grupo_carro or "")
                
                diaria = 203.44 if is_auto else 151.92
                consumo = 9 if is_auto else 13
                
                # CÁLCULO COMBUSTÍVEL
                # Ida e Volta (km_dist * 2)
                litros = (km_dist * 2) / consumo
                comb = litros * 5.80
                
                total = (diaria * dias) + comb
                
                texto_km = f"{km_dist:.0f} km"
                if usou_simulacao:
                    texto_km += " (Simulado - Erro API)"

                st.markdown(f"""
                <div class="result-card">
                    <div class="card-title" style="color:#2980B9;">🚗 Carro + Comb.</div>
                    <div class="info-text"><b>Distância:</b> {texto_km}</div>
                    <div class="info-text"><b>Locação:</b> R$ {(diaria*dias):.2f}</div>
                    <div class="info-text"><b>Combustível:</b> R$ {comb:.2f}</div>
                    <div class="price-big">R$ {total:.2f}</div>
                </div>""", unsafe_allow_html=True)

st.markdown("### 📌 Próximos Passos")
ca, cb, cc = st.columns(3)
with ca: st.link_button("🚌 Solicitar Passagem", "https://portalmse.com.br/index.php", use_container_width=True)
with cb: st.link_button("🚗 Solicitar Veículo", "https://docs.google.com/forms/d/e/1FAIpQLSc-ImW1hPShhR0dUT2z77rRN0PJtPw93Pz6EBMkybPJW9r8eg/viewform", use_container_width=True)
with cc: st.link_button("🏨 Solicitar Hotel", "https://docs.google.com/forms/d/e/1FAIpQLSc7K3xq-fa_Hsw1yLel5pKILUVMM5kzhHbNRPDISGFke6aJ4A/viewform", use_container_width=True)
