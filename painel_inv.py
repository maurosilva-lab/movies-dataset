import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS EXECUTIVO ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1.5rem !important; margin-top: -30px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; }
    
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 15px; border-radius: 8px; text-align: center;
        margin-bottom: 20px; border-bottom: 4px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 26px !important; font-weight: 800 !important; margin: 0; }
    
    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 20px; text-align: center; border-top: 4px solid #00d2ff;
    }
    .value-kpi { color: white; font-size: 24px; font-weight: 900; margin: 5px 0; }
    .label-kpi { color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE LIMPEZA À PROVA DE ERROS ---
def limpar_valor(v):
    try:
        if pd.isna(v) or str(v).strip() in ["", "-", "nan", "#DIV/0!", "None"]: 
            return 0.0
        s = str(v).replace('R$', '').replace('%', '').replace(' ', '')
        # Trata formato brasileiro (1.000,00) vs americano (1,000.00)
        if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
        elif ',' in s: s = s.replace(',', '.')
        s = re.sub(r'[^0-9\.\-]', '', s)
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    return pd.read_csv(url).dropna(how='all')

try:
    df_raw = load_data().copy()
    
    # --- MAPEAMENTO INTELIGENTE DE COLUNAS ---
    # Buscamos as colunas por palavras-chave para evitar erro de renomeação
    def encontrar_coluna(termos):
        for col in df_raw.columns:
            if any(t.lower() in str(col).lower() for t in termos):
                return col
        return df_raw.columns[0] # Fallback para a primeira coluna

    c_1c = encontrar_coluna(['1', 'ciclo'])
    c_falta = encontrar_coluna(['falta', 'vol'])
    c_fat = encontrar_coluna(['faturamento', 'fat'])
    c_tipo = encontrar_coluna(['tipo'])
    c_cd = encontrar_coluna(['cd'])
    c_gerente = encontrar_coluna(['divisional', 'gerente', 'regional'])

    # --- PROCESSAMENTO SEGURO ---
    # Convertemos tudo para os tipos corretos IMEDIATAMENTE
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor)
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_valor)
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor)
    df_raw['total_perda'] = df_raw['v_1c'] + df_raw['v_falta']
    
    # Strings para filtros (sempre string, nunca float)
    df_raw['f_tipo'] = df_raw[c_tipo].fillna("OUTROS").astype(str).str.upper()
    df_raw['f_cd'] = df_raw[c_cd].fillna("N/A").astype(str).str.replace(".0", "", regex=False)
    df_raw['f_gerente'] = df_raw[c_gerente].fillna("N/A").astype(str).str.upper()

    # --- SIDEBAR (FILTROS) ---
    with st.sidebar:
        st.header("⚙️ Painel de Controle")
        if st.button("🔄 Sincronizar Google Sheets"):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        sel_tipo = st.multiselect("Filtrar Tipo:", options=sorted(df_raw['f_tipo'].unique()))
        sel_cd = st.multiselect("Filtrar CD:", options=sorted(df_raw['f_cd'].unique()))
        sel_ger = st.multiselect("Filtrar Gerente:", options=sorted(df_raw['f_gerente'].unique()))

    # Filtros
    df_filt = df_raw.copy()
    if sel_tipo: df_filt = df_filt[df_filt['f_tipo'].isin(sel_tipo)]
    if sel_cd: df_filt = df_filt[df_filt['f_cd'].isin(sel_cd)]
    if sel_ger: df_filt = df_filt[df_filt['f_gerente'].isin(sel_ger)]

    # --- DASHBOARD ---
    st.markdown('<div class="header-box"><p class="header-title">📊 DASHBOARD ESTRATÉGICO MAGALOG 2026</p></div>', unsafe_allow_html=True)
    
    # KPIs
    perda_total = df_filt['total_perda'].sum()
    fat_total = df_filt['v_fat'].sum()
    perc = (abs(perda_total) / fat_total * 100) if fat_total > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Total</p><p class="value-kpi">R$ {perda_total:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {df_filt["v_1c"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {df_filt["v_falta"].sum():,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">% Perda s/ Fat</p><p class="value-kpi">{perc:.3f}%</p></div>', unsafe_allow_html=True)

    # Gráficos Restaurados
    st.write("---")
    g1, g2 = st.columns(2)
    with g1:
        # Gráfico por Tipo de Unidade (CD/LV/DQS)
        df_g1 = df_filt.groupby('f_tipo')['total_perda'].sum().reset_index()
        fig1 = px.bar(df_g1, x='f_tipo', y='total_perda', title="Perdas por Processo", color='f_tipo', template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)
    
    with g2:
        # Perdas Acumuladas por Gerente
        df_g2 = df_filt.groupby('f_gerente')['total_perda'].sum().reset_index().sort_values('total_perda')
        fig2 = px.bar(df_g2, y='f_gerente', x='total_perda', orientation='h', title="Perdas por Gerente", template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

    # Tabela com Estilo de Cores Seguro
    st.markdown("### 📋 Detalhamento Operacional")
    
    def aplicar_cor(val):
        try:
            num = float(val)
            if num < 0: return 'color: #ff4b4b'
            if num > 0: return 'color: #00ffcc'
            return ''
        except: return ''

    # Selecionamos apenas o necessário para a tabela
    df_tab = df_filt[['f_tipo', 'f_cd', 'v_1c', 'v_falta', 'f_gerente']].copy()
    df_tab.columns = ['Tipo', 'CD', '1º Ciclo', 'Falta Vol', 'Responsável']
    
    st.dataframe(
        df_tab.style.applymap(aplicar_cor, subset=['1º Ciclo', 'Falta Vol'])
        .format({'1º Ciclo': 'R$ {:,.2f}', 'Falta Vol': 'R$ {:,.2f}'}),
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"Erro Crítico: {e}")
    st.info("Verifique se a Planilha do Google está acessível e possui as colunas necessárias.")