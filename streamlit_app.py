import streamlit as st
import requests
import base64
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

# CSS: Visual Corporativo
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none; visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden; height: 0%;}
    [data-testid="stDecoration"] {display: none;}
    .block-container {padding-top: 2rem;}

    [data-testid="stSidebar"] { 
        background-color: #f4f4f4; 
        border-right: 1px solid #ddd; 
    }
    
    h1, h2, h3 { color: #8B0000; }
    
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
        color: #2E7D32; 
    }
    
    .info-text { 
        color: #666; 
        font-size: 0.9em; 
        margin-bottom: 5px; 
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 2. SEGURANÇA E DADOS
# =========================================================

try:
    MAPS_KEY = st.secrets["MAPS_KEY"]
    QP_USER = st.secrets.get("QP_USER", "mse")
    QP_PASS = st.secrets.get("QP_PASS", "")
except:
    st.error("⚠️ Configure as chaves no .streamlit/secrets.toml")
    st.stop()

# --- URL DE PRODUÇÃO (OFICIAL) ---
QP_URL = "https://queropassagem.com.br/ws_v4"
AFFILIATE = "MSE" 

# --- LISTA DE CIDADES (Atualize aqui com os IDs numéricos que descobrir) ---
DE_PARA_QP = {
    "sao paulo": "ROD_1", "são paulo": "ROD_1", "sp": "ROD_1",
    "rio de janeiro": "ROD_55", "rio": "ROD_55", "rj": "ROD_55",
    "curitiba": "ROD_3", "belo horizonte": "ROD_7", "bh": "ROD_7",
    "florianopolis": "ROD_6", "brasilia": "ROD_2",
    "campinas": "ROD_13", "santos": "ROD_10", "maringa": "ROD_16", "foz do iguacu": "ROD_17",
    
    # IDs Provisórios (Use a ferramenta 'Descobrir IDs' para corrigir se der erro)
    "londrina": "ROD_23" 
}

TABELA_HOSPEDAGEM = { 
    "SP": 350, "RJ": 305, "PR": 250, "SC": 300, "MG": 310, "RS": 280, 
    "BA": 210, "DF": 260, "GO": 230, "PE": 170, "CE": 350 
}

# =========================================================
# 3. INTEGRAÇÕES
# =========================================================

def get_auth_headers():
    """Gera os headers blindados para evitar erro 403"""
    auth_str = f"{QP_USER.strip()}:{QP_PASS.strip()}"
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    return {
        "Authorization": f"Basic {auth_base64}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://queropassagem.com.br/",
        "Origin": "https://queropassagem.com.br"
    }

def buscar_id_cidade(termo):
    """NOVA FUNÇÃO: Busca o ID correto da cidade na API"""
    endpoint = f"{QP_URL}/stops" # Endpoint que lista todas as cidades
    try:
        r = requests.get(endpoint, headers=get_auth_headers())
        if r.status_code == 200:
            cidades = r.json()
            # Filtra cidades que contenham o termo digitado
            encontradas = [c for c in cidades if termo.lower() in c.get('name', '').lower()]
            return encontradas
        else:
            return {"erro": True, "msg": f"Erro {r.status_code}"}
    except Exception as e:
        return {"erro": True, "msg": str(e)}

def get_km_google(origem, destino):
    if not MAPS_KEY: return 0
    orig_fmt = origem.strip() + (", Brasil" if "Brasil" not in origem else "")
    dest_fmt = destino.strip() + (", Brasil" if "Brasil" not in destino else "")
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    try:
        r = requests.get(url, params={"origins": orig_fmt, "destinations": dest_fmt, "units": "metric", "mode": "driving", "key": MAPS_KEY})
        data = r.json()
        if data.get('status') == 'OK':
            elem = data['rows'][0]['elements'][0]
            if elem.get('status') == 'OK':
                return elem['distance']['value'] / 1000.0
    except:
        pass
    return 0

def buscar_passagem_api(origem, destino, data_iso):
    id_origem = DE_PARA_QP.get(origem.lower().strip())
    id_destino = DE_PARA_QP.get(destino.lower().strip())
    
    if not id_origem or not id_destino:
        return {"erro": True, "msg": f"Cidade não mapeada. Use a aba 'Descobrir IDs' para achar o código de {origem}/{destino}."}

    endpoint = f"{QP_URL}/new/search"
    
    body = {
        "from": id_origem, 
        "to": id_destino, 
        "travelDate": data_iso, 
        "affiliateCode": AFFILIATE
    }

    try:
        r = requests.post(endpoint, json=body, headers=get_auth_headers())
        
        # MODO DEBUG SILENCIOSO
        if r.status_code == 200:
            res = r.json()
            
            # Se vier vazio, é porque o ID da cidade está errado ou não tem ônibus
            if not res or len(res) == 0:
                 st.warning(f"⚠️ A API retornou lista vazia. Verifique se existem ônibus de {id_origem} para {id_destino} nesta data.")
                 return {"erro": True, "msg": "Nenhuma viagem encontrada para esta data/rota."}

            lista = res[0] if (isinstance(res, list) and len(res) > 0 and isinstance(res[0], list)) else res
            disponiveis = lista 
            
            if not disponiveis: return {"erro": True, "msg": "Lista vazia."}
            
            try:
                disponiveis.sort(key=lambda x: float(x.get('price', 9999)))
                return {"erro": False, "dados": disponiveis[0]}
            except:
                 return {"erro": True, "msg": "Erro ao ler dados da passagem."}

        else:
            return {"erro": True, "msg": f"Erro API ({r.status_code}): {r.text[:100]}"}
            
    except Exception as e:
        return {"erro": True, "msg": f"Erro Conexão: {str(e)}"}

def calcular_dias(ida, volta):
    if not ida or not volta: return 1
    delta = (volta - ida).days
    return delta if delta > 0 else 1

# =========================================================
# 4. FRONTEND
# =========================================================

with st.sidebar:
    try:
        st.image("LOGO MSE.png", width=160)
    except:
        st.markdown("### MSE TRAVEL")
    st.markdown("---")
    menu = st.radio("Navegação", ["Cotação Geral", "Rodoviário", "Veículo", "Hospedagem", "🕵️ Descobrir IDs"])

st.title(f"📊 {menu}")

# --- NOVA TELA: DESCOBRIDOR DE IDs ---
if menu == "🕵️ Descobrir IDs":
    st.markdown("### 🔎 Encontre o Código da Cidade (ROD_XXX)")
    st.info("Digite o nome da cidade para ver o ID Numérico correto.")
    
    termo_cidade = st.text_input("Digite o nome da cidade:", placeholder="Ex: Londrina")
    
    if st.button("BUSCAR ID"):
        if len(termo_cidade) < 3:
            st.warning("Digite pelo menos 3 letras.")
        else:
            with st.spinner("Consultando API..."):
                resultado = buscar_id_cidade(termo_cidade)
                
            if isinstance(resultado, list):
                if len(resultado) > 0:
                    st.success(f"Encontramos {len(resultado)} cidades:")
                    for c in resultado:
                        # --- AQUI ESTAVA O ERRO, AGORA CORRIGIDO ---
                        # Mostramos o ID numérico, formatado como ROD_XXX
                        id_oficial = c.get('id')
                        nome_oficial = c.get('name')
                        codigo_final = f"ROD_{id_oficial}"
                        
                        st.markdown(f"**{nome_oficial}**")
                        st.code(f'"{nome_oficial.lower()}": "{codigo_final}"', language="python")
                else:
                    st.error("Nenhuma cidade encontrada com esse nome.")
            else:
                st.error(f"Erro na busca: {resultado.get('msg')}")

# --- TELAS NORMAIS ---
else:
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
            km_dist = get_km_google(origem, destino)
            if km_dist == 0: st.warning("⚠️ Distância não calculada automaticamente.")
            
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
                            <div class="info-text"><b>Viação:</b> {v.get('company', {}).get('name', 'N/A')}</div>
                            <div class="info-text"><b>Horário:</b> {v.get('departure', {}).get('time', '00:00')[:5]} ➝ {v.get('arrival', {}).get('time', '00:00')[:5]}</div>
                            <div class="price-big">R$ {float(v.get('price', 0)):.2f}</div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        est = km_dist * 0.50
                        msg_erro = api_res['msg']
                        st.markdown(f"""
                        <div class="result-card" style="border-left: 5px solid gray;">
                            <div class="card-title">🚌 Estimativa KM</div>
                            <div class="info-text" style="color:red;">{msg_erro}</div>
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

            # VEÍCULO
            if menu in ["Veículo", "Cotação Geral"]:
                with (c3 if menu == "Cotação Geral" else st.container()):
                    dias = calcular_dias(data_ida, data_volta)
                    is_auto = "EA" in (grupo_carro or "")
                    diaria = 203.44 if is_auto else 151.92
                    consumo = 9 if is_auto else 13
                    comb = ((km_dist * 2) / consumo) * 5.80
                    total = (diaria * dias) + comb
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="card-title" style="color:#2980B9;">🚗 Carro + Comb.</div>
                        <div class="info-text"><b>Distância:</b> {km_dist:.1f} km</div>
                        <div class="info-text"><b>Locação:</b> R$ {(diaria*dias):.2f}</div>
                        <div class="info-text"><b>Combustível:</b> R$ {comb:.2f}</div>
                        <div class="price-big">R$ {total:.2f}</div>
                    </div>""", unsafe_allow_html=True)

st.markdown("### 📌 Próximos Passos")
ca, cb, cc = st.columns(3)
with ca: st.link_button("🚌 Solicitar Passagem", "https://portalmse.com.br/index.php", use_container_width=True)
with cb: st.link_button("🚗 Solicitar Veículo", "https://docs.google.com/forms/d/e/1FAIpQLSc-ImW1hPShhR0dUT2z77rRN0PJtPw93Pz6EBMkybPJW9r8eg/viewform", use_container_width=True)
with cc: st.link_button("🏨 Solicitar Hotel", "https://docs.google.com/forms/d/e/1FAIpQLSc7K3xq-fa_HswlyLel5pKILUVMM5kzhHbNRPDlSGFke6aJ4A/viewform", use_container_width=True)
with cc: st.link_button("🏨 Solicitar Hotel", "https://docs.google.com/forms/d/e/1FAIpQLSc7K3xq-fa_Hsw1yLel5pKILUVMM5kzhHbNRPDISGFke6aJ4A/viewform", use_container_width=True)










