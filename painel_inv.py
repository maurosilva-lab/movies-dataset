import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS EXECUTIVO (Garante visibilidade dos filtros) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1.5rem !important; margin-top: -30px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    
    /* Estilização da Sidebar para garantir que apareça */
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #313d4f; }
    
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 12px; border-radius: 5px; text-align: center;
        margin-bottom: 20px; border-bottom: 3px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; }
    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 15px; text-align: center; border-top: 3px solid #00d2ff; min-height: 100px;
    }
    .value-kpi { color: white; font-size: 20px; font-weight: 900; margin: 0; }
    .label-kpi { color: #8b949e; font-size: 11px; text-transform: uppercase; }
    </style>
""", unsafe_allow_html=True)

def limpar_universal(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan", "#DIV/0!", "None"]: return 0.0
    s = str(v).replace('R$', '').replace('%', '').replace(' ', '')
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    return df

try:
    df_raw = load_data().copy()
    
    # Identificação de Colunas (Usando nomes exatos ou parciais comuns)
    c_1c = next((c for c in df_raw.columns if '1' in str(c) and 'Ciclo' in str(c)), "1º Ciclo")
    c_falta = next((c for c in df_raw.columns if 'Falta' in str(c)), "Falta Vol")
    c_fat = next((c for c in df_raw.columns if 'Fat' in str(c)), "Faturamento")
    
    # Colunas de Filtro
    col_tipo = next((c for c in df_raw.columns if 'Tipo' in str(c)), "Tipo")
    col_cd = next((c for c in df_raw.columns if 'CD' in str(c)), "CD")
    col_div = next((c for c in df_raw.columns if 'Divisional' in str(c) or 'Gerente' in str(c)), "Divisional")

    # Tratamento de dados - Converte para String antes de aplicar filtros para evitar erro de float/str
    df_raw['f_tipo'] = df_raw[col_tipo].fillna("N/A").astype(str).str.upper()
    df_raw['f_cd'] = df_raw[col_cd].fillna("N/A").astype(str).str.replace(".0", "", regex=False)
    df_raw['f_gerente'] = df_raw[col_div].fillna("N/A").astype(str).str.upper()

    # Conversão Numérica Blindada
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_universal).astype(float)
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_universal).astype(float)
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_universal).astype(float)
    df_raw['total_perda'] = df_raw['v_1c'] + df_raw['v_falta']

    # --- FILTROS (FORA DA LÓGICA DE CÁLCULO PARA NÃO SUMIREM) ---
    with st.sidebar:
        st.markdown("### 📊 Filtros Magalog")
        
        if st.button("🔄 Sincronizar Agora"):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        
        sel_tipo = st.multiselect("Selecione o Tipo:", options=sorted(df_raw['f_tipo'].unique()))
        sel_cd = st.multiselect("Selecione o CD:", options=sorted(df_raw['f_cd'].unique()))
        sel_ger = st.multiselect("Selecione o Gerente:", options=sorted(df_raw['f_gerente'].unique()))

    # Aplicação dos Filtros
    df_filt = df_raw.copy()
    if sel_tipo: df_filt = df_filt[df_filt['f_tipo'].isin(sel_tipo)]
    if sel_cd: df_filt = df_filt[df_filt['f_cd'].isin(sel_cd)]
    if sel_ger: df_filt = df_filt[df_filt['f_gerente'].isin(sel_ger)]

    # --- CONTEÚDO DO DASHBOARD ---
    st.markdown('<div class="header-box"><p class="header-title">DASHBOARD EXECUTIVO MAGALOG 2026</p></div>', unsafe_allow_html=True)
    
    # KPIs
    perda_total = df_filt['total_perda'].sum()
    fat_total = df_filt['v_fat'].sum()
    perc = (abs(perda_total) / fat_total * 100) if fat_total > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Total</p><p class="value-kpi">R$ {perda_total:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {df_filt["v_1c"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {df_filt["v_falta"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">% Perda s/ Fat</p><p class="value-kpi">{perc:.3f}%</p></div>', unsafe_allow_html=True)

    # Gráficos
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        fig_proc = px.bar(df_filt.groupby('f_tipo')['total_perda'].sum().reset_index(), x='f_tipo', y='total_perda', title="Perdas por Processo", color='f_tipo', template="plotly_dark")
        st.plotly_chart(fig_proc, use_container_width=True)
    with c2:
        fig_ger = px.bar(df_filt.groupby('f_gerente')['total_perda'].sum().reset_index().sort_values('total_perda'), y='f_gerente', x='total_perda', orientation='h', title="Perdas por Gerente", template="plotly_dark")
        st.plotly_chart(fig_ger, use_container_width=True)

    # Tabela com Estilo Blindado (Corrige o erro de float vs str)
    st.markdown("### 📋 Detalhamento")
    
    def safe_style(val):
        try:
            num = float(val)
            if num < 0: return 'color: #ff4b4b'
            if num > 0: return 'color: #00ffcc'
            return ''
        except: return ''

    df_tab = df_filt[['f_tipo', 'f_cd', 'v_1c', 'v_falta', 'f_gerente']].copy()
    
    st.dataframe(
        df_tab.style.applymap(safe_style, subset=['v_1c', 'v_falta'])
        .format({'v_1c': 'R$ {:,.2f}', 'v_falta': 'R$ {:,.2f}'}),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.sidebar.error(f"Erro nos dados: {e}")
    st.error("Erro Crítico detectado. Verifique os logs ou clique em Sincronizar.")