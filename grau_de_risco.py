import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha de Streamlit)
st.set_page_config(layout="wide", page_title="Dashboard Risco Logística", page_icon="🚛")

# 2. FUNÇÃO DE ATUALIZAÇÃO AUTOMÁTICA (Fragmento)
@st.fragment(run_every=600) # Atualiza a cada 10 minutos
def render_dashboard():
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dSYbGC3dFW2TP01ICfWY55P9OiurB0ngLsmrqM5kSYg/export?format=csv&gid=629990986"

    # Botão de atualização manual na barra lateral
    with st.sidebar:
        if st.button('🔄 Atualizar Dados Agora'):
            st.cache_data.clear()
            st.rerun()
        st.write(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")

    # CSS para Design Profissional
    st.markdown("""
        <style>
        .stMetric { background-color: #111827; border-radius: 10px; padding: 15px; border: 1px solid #374151; }
        [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
        .header-bar { 
            background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%); 
            padding: 10px 20px; border-radius: 8px; color: white; 
            margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;
        }
        </style>
        <div class="header-bar">
            <span style="font-weight: bold; font-size: 20px;">INDICADOR DE RISCO LOGÍSTICA</span>
            <span style="font-size: 14px; opacity: 0.8;">Data Analytics Unit | v4.0</span>
        </div>
        """, unsafe_allow_html=True)

    # Função de carregamento com cache curto (60 segundos)
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
            st.error(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()

    df_raw = load_data()

    if not df_raw.empty:
        # --- O RESTANTE DO SEU CÓDIGO DE GRÁFICOS E TABELAS VAI AQUI ---
        # (Filtros, KPIs, Pareto, Tabela...)
        st.write("Dados carregados com sucesso!") # Apenas exemplo
        
        # Exemplo da sua tabela com o estilo
        # st.dataframe(style_performance(df_table.style)...)
    else:
        st.info("💡 Carregando dados da planilha...")

# 3. EXECUÇÃO DO DASHBOARD
render_dashboard()