import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha)
# ==========================================
st.set_page_config(layout="wide", page_title="Dashboard Risco Logística", page_icon="🚛")

# ==========================================
# 2. CARREGAMENTO DE DADOS (FORA DO FRAGMENTO)
# ==========================================
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dSYbGC3dFW2TP01ICfWY55P9OiurB0ngLsmrqM5kSYg/export?format=csv&gid=629990986"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df.columns = df.columns.str.strip().str.replace('\n', ' ').str.replace('  ', ' ')
        
        cols_num = ['DVG EM em Milhares', 'REC. TEC. em Milhares', 'GRAU DE RISCO GERAL', 'MALHA EM QNT']
        for col in cols_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['DATA'] = pd.to_datetime(df['DATA'], dayfirst=True).dt.date
        return df
    except Exception as e:
        return pd.DataFrame()

df_raw = load_data()

# ==========================================
# 3. SIDEBAR E FILTROS (NÍVEL GLOBAL)
# ==========================================
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    
    if st.button('🔄 Forçar Atualização'):
        st.cache_data.clear()
        st.rerun()
    
    st.write(f"Última leitura: {datetime.now().strftime('%H:%M:%S')}")
    st.divider()

    if not df_raw.empty:
        st.subheader("Filtros de Exibição")
        datas_disp = sorted(df_raw['DATA'].unique(), reverse=True)
        sel_date = st.selectbox("Selecione a Data", options=datas_disp)
        
        tipos_disp = sorted(df_raw['TIPO'].unique()) if 'TIPO' in df_raw.columns else []
        sel_tipos = st.multiselect("Tipo de Unidade", options=tipos_disp, default=tipos_disp)
        
        cds_disp = sorted(df_raw[df_raw['TIPO'].isin(sel_tipos)]['CD'].unique())
        sel_cds = st.multiselect("Filiais (CDs)", options=cds_disp, default=cds_disp)
    else:
        st.error("Erro ao carregar dados. Verifique a planilha.")
        st.stop()

# ==========================================
# 4. CONTEÚDO VISUAL (DENTRO DO FRAGMENTO)
# ==========================================
@st.fragment(run_every=600)
def render_visuals(df_full, data_escolhida, cds_escolhidos):
    # Lógica de comparação de datas
    datas_todas = sorted(df_full['DATA'].unique(), reverse=True)
    idx = datas_todas.index(data_escolhida)
    data_anterior = datas_todas[idx + 1] if idx + 1 < len(datas_todas) else data_escolhida

    # Filtragem Final
    df_at = df_full[(df_full['DATA'] == data_escolhida) & (df_full['CD'].isin(cds_escolhidos))].copy()
    df_ps = df_full[(df_full['DATA'] == data_anterior) & (df_full['CD'].isin(cds_escolhidos))].copy()

    # --- Header Customizado ---
    st.markdown("""
        <style>
        .stMetric { background-color: #111827; border-radius: 10px; padding: 15px; border: 1px solid #374151; }
        .header-bar { 
            background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%); 
            padding: 15px; border-radius: 8px; color: white; margin-bottom: 25px;
            text-align: center; font-weight: bold; font-size: 22px;
        }
        </style>
        <div class="header-bar">INDICADOR DE RISCO LOGÍSTICA</div>
    """, unsafe_allow_html=True)

    # --- KPIs ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("DVG Atual", f"R$ {df_at['DVG EM em Milhares'].sum()/1000:,.1f}k")
    with c2:
        dif = df_at['DVG EM em Milhares'].sum() - df_ps['DVG EM em Milhares'].sum()
        st.metric("DIF (vs Anterior)", f"{dif/1000:+.1f}k", delta=f"{dif/1000:,.1f}k", delta_color="inverse")
    with c3: st.metric("Qtd Malha", f"{int(df_at['MALHA EM QNT'].sum()):,}")
    with c4: st.metric("Risco Médio", f"{df_at['GRAU DE RISCO GERAL'].mean():.2f}")

    # --- Gráfico de Pareto ---
    st.subheader("Concentração de DVG por Unidade")
    df_p = df_at[df_at['DVG EM em Milhares'] > 0].sort_values('DVG EM em Milhares', ascending=False)
    if not df_p.empty:
        fig = go.Figure(go.Bar(x=df_p['CD'], y=df_p['DVG EM em Milhares'], marker_color='#3B82F6'))
        fig.update_layout(height=350, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    # --- Tabela Detalhada ---
    st.subheader("📋 Detalhamento Operacional")
    df_tab = df_at[['CD', 'CIDADE', 'REC. TEC. em Milhares', 'MALHA EM QNT', 'DVG EM em Milhares', 'GRAU DE RISCO GERAL']].copy()

    def style_performance(styler):
        styler.format({'DVG EM em Milhares': 'R$ {:,.1f}k', 'GRAU DE RISCO GERAL': '{:.2f}'})
        styler.background_gradient(cmap='RdYlGn_r', subset=['DVG EM em Milhares'])
        styler.background_gradient(cmap='YlOrRd', subset=['GRAU DE RISCO GERAL'], vmin=0, vmax=3)
        return styler

    st.dataframe(style_performance(df_tab.style), use_container_width=True, hide_index=True)

# ==========================================
# 5. EXECUÇÃO
# ==========================================
render_visuals(df_raw, sel_date, sel_cds)