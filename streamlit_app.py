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

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    [data-testid="stSidebar"] { background-color: #f4f4f4; border-right: 1px solid #ddd; }
    h1, h2, h3 { color: #8B0000; }
    .stButton>button { background-color: #8B0000; color: white; border-radius: 8px; font-weight: bold; width: 100%; padding: 10px; }
    .result-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #8B0000; margin-bottom: 20px; }
    .price-big { font-size: 1.8em; font-weight: 800; color: #2E7D32; }
    .info-text { color: #666; font-size: 0.9em; margin-bottom: 5px; }
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

# URL Oficial de Produção
QP_URL = "https://queropassagem.com.br/ws_v4"
AFFILIATE = "MSE" 

# --- LISTA DE CIDADES (Atualizada com o ID que você descobriu) ---
DE_PARA_QP = {
    # São Paulo (Capital) - Geralmente Tietê (ROD_1) recebe ônibus do PR
    "sao paulo": "ROD_1", "são paulo": "ROD_1", "sp": "ROD_1",
    "barra funda": "ROD_1", # Redirecionando Barra Funda para Tietê por enquanto (evitar erro do RS)
    
    "rio de janeiro": "ROD_55", "rio": "ROD_55", "rj": "ROD_55",
    "curitiba": "ROD_3", "belo horizonte": "ROD_7", "bh": "ROD_7",
    "florianopolis": "ROD_6", "brasilia": "ROD_2",
    "campinas": "ROD_13", "santos": "ROD_10", "maringa": "ROD_16", "foz do iguacu": "ROD_17",
    
    # --- CORREÇÃO CONFIRMADA ---
    # Terminal Rodoviário de Londrina (José Garcia Villar)
    "londrina": "ROD_837" 
}

TABELA_HOSPEDAGEM = { 
    "SP": 350, "RJ": 305, "PR": 250, "SC": 300, "MG": 310, "RS": 280, 
    "BA": 210, "DF": 260, "GO": 230, "PE": 170, "CE": 350 
}

# =========================================================
# 3. INTEGRAÇÕES
# =========================================================

def get_auth_headers():
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

def buscar_id_cidade_avancado(termo):
    """Busca avançada para encontrar IDs de Rodoviárias (substops)"""
    endpoint = f"{QP_URL}/stops"
    try:
        r = requests.get(endpoint, headers=get_auth_headers())
        if r.status_code == 200:
            tudo = r.json()
            resultados = []
            for item in tudo:
                nome_item = item.get('name', '').lower()
                if termo.lower() in nome_item:
                    substops = item.get('substops', [])
                    if substops:
                        for sub in substops:
                            resultados.append({
                                "tipo": "RODOVIÁRIA (Use este!)",
                                "nome": sub.get('name'),
                                "id": sub.get('id'),
                                "url": sub.get('url')
                            })
                    else:
                        resultados.append({
                            "tipo": "Parada Simples",
                            "nome": item.get('name'),
                            "id": item.get('id'),
                            "url": item.get('url')
                        })
            return resultados
        else:
            return {"erro": True, "msg": f"Erro Status {r.status_code}"}
    except Exception as e:
        return {"erro": True, "msg": str(e)}

def get_km_google(origem, destino):
    if not MAPS_KEY: return 0
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    try:
        orig_fmt = origem.strip() + (", Brasil" if "Brasil" not in origem else "")
        dest_fmt = destino.strip() + (", Brasil" if "Brasil" not in destino else "")
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
    
    # Se não achar na lista simples, tenta buscar dinamicamente (fallback)
    if not id_origem:
        # Lógica simples de fallback: se não está no dicionário, avisa para usar a ferramenta
        return {"erro": True, "msg": f"Cidade '{origem}' não mapeada. Use a aba 'Descobrir IDs'."}
    if not id_destino:
        return {"erro": True, "msg": f"Cidade '{destino}' não mapeada. Use a aba 'Descobrir IDs'."}

    endpoint = f"{QP_URL}/new/search"
    
    body = {
        "from": id_origem, 
        "to": id_destino, 
        "travelDate": data_iso, 
        "affiliateCode": AFFILIATE
    }

    try:
        r = requests.post(endpoint, json=body, headers=get_auth_headers())
        
        if r.status_code == 200:
            res = r.json()
            if not res: return {"erro": True, "msg": "Nenhuma viagem encontrada (Lista Vazia)."}
            
            lista = res[0] if (isinstance(res, list) and len(res) > 0 and isinstance(res[0], list)) else res
            
            disponiveis = [v for v in lista if v.get('availableSeats', 0) > 0]
            if not disponiveis: return {"erro": True, "msg": "Sem assentos disponíveis nesta data."}
            
            # Tratamento de preço (Objeto ou Float)
            def get_price_value(item):
                p = item.get('price')
                if isinstance(p, dict):
                    return float(p.get('price', 9999))
                return float(p or 9999)

            disponiveis.sort(key=get_price_value)
            return {"erro": False, "dados": disponiveis[0]}
        
        else:
            return {"erro": True, "msg": f"Erro API ({r.status_code}): {r.text[:200]}"}
            
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

# --- ABA DE DESCOBERTA ---
if menu == "🕵️ Descobrir IDs":
    st.markdown("### 🔎 Descobridor de Rodoviárias")
    st.info("Digite o nome da cidade para encontrar a RODOVIÁRIA (ID ROD_) correta.")
    
    termo = st.text_input("Nome da Cidade:", placeholder="Ex: Londrina")
    
    if st.button("BUSCAR ID") and len(termo) >= 3:
        with st.spinner("Varrendo rodoviárias..."):
            res = buscar_id_cidade_avancado(termo)
            if isinstance(res, list) and res:
                st.success(f"{len(res)} locais encontrados:")
                for c in res:
                    cor = "green" if "RODOVIÁRIA" in c['tipo'] else "black"
                    icone = "✅" if "RODOVIÁRIA" in c['tipo'] else "📍"
                    st.markdown(f"**:{cor}[{icone} {c['tipo']}]**")
                    st.write(f"{c['nome']}")
                    st.code(f'"{c["nome"].lower()}": "{c["id"]}"', language="python")
                    st.markdown("---")
            else:
                st.warning("Nada encontrado.")

# --- ABAS DE COTAÇÃO ---
else:
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            origem = st.text_input("Cidade de Origem", placeholder="Ex: Londrina")
            data_ida = st.date_input("Data de Ida", date.today())
        with col2:
            destino = st.text_input("Cidade de Destino", placeholder="Ex: Sao Paulo")
            data_volta = st.date_input("Data de Volta", date.today() + timedelta(days=1)) if menu != "Rodoviário" else None

    grupo_carro = None
    if menu in ["Veículo", "Cotação Geral"]:
        grupo_carro = st.selectbox("Categoria do Veículo", ["B - Econômico (Manual)", "EA - Executivo (Automático)"])

    if st.button("CALCULAR COTAÇÃO 🚀"):
        if not origem or not destino:
            st.error("Preencha Origem e Destino.")
        else:
            km_dist = get_km_google(origem, destino)
            
            # Chama API
            api_res = buscar_passagem_api(origem, destino, str(data_ida))

            c1, c2, c3 = st.columns(3)
            
            # RODOVIÁRIO
            with c1:
                if menu in ["Rodoviário", "Cotação Geral"]:
                    if not api_res['erro']:
                        v = api_res['dados']
                        
                        comp = v.get('company', {}).get('name', 'Viação')
                        saida = v.get('departure', {}).get('time', '00:00')[:5]
                        chegada = v.get('arrival', {}).get('time', '00:00')[:5]
                        
                        p_raw = v.get('price')
                        preco = float(p_raw.get('price')) if isinstance(p_raw, dict) else float(p_raw or 0)
                        
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="card-title" style="color:#E67E22;">🚌 Melhor Tarifa</div>
                            <div class="info-text"><b>Viação:</b> {comp}</div>
                            <div class="info-text"><b>Horário:</b> {saida} ➝ {chegada}</div>
                            <div class="price-big">R$ {preco:.2f}</div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        est = km_dist * 0.50
                        st.markdown(f"""
                        <div class="result-card" style="border-left: 5px solid gray;">
                            <div class="card-title">🚌 Estimativa KM</div>
                            <div class="info-text" style="color:red;">{api_res['msg']}</div>
                            <div class="price-big" style="color:#666;">R$ {est:.2f}</div>
                        </div>""", unsafe_allow_html=True)
            
            # HOTEL
            with c2:
                if menu in ["Hospedagem", "Cotação Geral"]:
                     dias = calcular_dias(data_ida, data_volta) + 1
                     uf = next((uf for uf in TABELA_HOSPEDAGEM if uf in destino.upper()), "BR")
                     total = TABELA_HOSPEDAGEM.get(uf, 300) * dias
                     st.markdown(f"""
                     <div class="result-card">
                        <div class="card-title" style="color:#27AE60;">🏨 Hotel ({uf})</div>
                        <div class="info-text"><b>Dias:</b> {dias}</div>
                        <div class="price-big">R$ {total:.2f}</div>
                     </div>""", unsafe_allow_html=True)
            
            # CARRO
            with c3:
                if menu in ["Veículo", "Cotação Geral"]:
                     dias_carro = calcular_dias(data_ida, data_volta)
                     is_auto = "EA" in (grupo_carro or "")
                     diaria = 203.44 if is_auto else 151.92
                     consumo = 9 if is_auto else 13
                     comb = ((km_dist * 2) / consumo) * 5.80
                     total_carro = (diaria * dias_carro) + comb
                     
                     st.markdown(f"""
                     <div class="result-card">
                        <div class="card-title" style="color:#2980B9;">🚗 Carro + Comb.</div>
                        <div class="info-text"><b>Distância:</b> {km_dist:.1f} km</div>
                        <div class="info-text"><b>Locação:</b> R$ {(diaria*dias_carro):.2f}</div>
                        <div class="price-big">R$ {total_carro:.2f}</div>
                     </div>""", unsafe_allow_html=True)
