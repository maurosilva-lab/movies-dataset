import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (FUTURISTA)
# ==========================================
st.set_page_config(page_title="Centro de Comando | Estoque", page_icon="🛸", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        /* Tema Escuro / Cyberpunk */
        .main-header { font-size: 2.5rem; color: #00FFC4; font-weight: 800; text-align: center; margin-bottom: 0; text-transform: uppercase; letter-spacing: 2px;}
        .sub-header { font-size: 1.1rem; color: #8892B0; text-align: center; margin-bottom: 30px; }
        
        /* Cards Neon Futuristas */
        .kpi-card { background: linear-gradient(145deg, #0B132B, #1C2541); padding: 20px; border-radius: 12px; border-left: 5px solid #00FFC4; box-shadow: 0 4px 15px rgba(0, 255, 196, 0.15); color: white; transition: 0.3s;}
        .kpi-card:hover { transform: translateY(-5px); box-shadow: 0 6px 20px rgba(0, 255, 196, 0.3); border-left: 5px solid #00B4D8;}
        .kpi-title { margin:0; font-size: 14px; color: #8892B0; font-weight: 600; text-transform: uppercase;}
        .kpi-value { margin:0; font-size: 32px; color: #00FFC4; font-weight: bold; font-family: 'Courier New', monospace;}
        
        /* Botão de Download Moderno */
        .stDownloadButton>button { background: linear-gradient(90deg, #00FFC4 0%, #00B4D8 100%); color: #0B132B; border: none; padding: 15px 32px; font-size: 18px; border-radius: 8px; width: 100%; font-weight: 800; transition: 0.4s; text-transform: uppercase;}
        .stDownloadButton>button:hover { opacity: 0.8; transform: scale(1.02); color: #0B132B;}
        
        /* Estilo para tabelas de destaque */
        .target-table { border-collapse: collapse; width: 100%; background: #0B132B; color: #8892B0; border-radius: 10px; overflow: hidden; }
        .target-table th { background: #1C2541; color: #00FFC4; padding: 12px; text-align: left; text-transform: uppercase; font-size: 12px; }
        .target-table td { padding: 10px; border-bottom: 1px solid rgba(0, 255, 196, 0.1); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES DE CARREGAMENTO E TRATAMENTO
# ==========================================
SHEET_ID = "11-IwzWjgFVKynzDTkqpr4_Fbs4GclKhS7W0KTKms0q4" 

def tratar_moeda(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    val_str = str(val).replace('R$', '').replace(' ', '').replace('\xa0', '').strip()
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    try: return float(val_str)
    except: return 0.0

@st.cache_data(ttl=600)
def carregar_dados():
    url_resultados = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=BigQuery+Results"
    url_historico = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico"
    url_hist_valores = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico_Valores"
    
    try:
        df_res = pd.read_csv(url_resultados)
        df_hist = pd.read_csv(url_historico)
        df_val = pd.read_csv(url_hist_valores)
        
        df_res.columns = df_res.columns.str.strip()
        df_val.columns = df_val.columns.str.strip()
        
        # Tratamento financeiro
        cols_fin = ['VALOR_TOTAL_ESTOQUE_ATUALIZADO', 'QT_ESTOQUE', 'CUSTO_MEDIO', 'CUSTO_PGTO']
        for col in cols_fin:
            if col in df_res.columns:
                df_res[col] = df_res[col].apply(tratar_moeda)
        
        if 'VALOR_TOTAL_ESTOQUE' in df_val.columns:
            df_val['VALOR_TOTAL_ESTOQUE'] = df_val['VALOR_TOTAL_ESTOQUE'].apply(tratar_moeda)
            
        if 'DATA_HORA' in df_val.columns:
            df_val['DATA_HORA'] = pd.to_datetime(df_val['DATA_HORA'], dayfirst=True, errors='coerce')
        
        # Empresa como texto sem .0
        for df in [df_res, df_val]:
            if 'CD_EMPRESA' in df.columns:
                df['CD_EMPRESA'] = df['CD_EMPRESA'].astype(str).str.replace(r'\.0$', '', regex=True)
            
        if 'DATA_HORA_ATUALIZACAO' in df_hist.columns:
            df_hist['DATA_HORA_ATUALIZACAO'] = pd.to_datetime(df_hist['DATA_HORA_ATUALIZACAO'], errors='coerce')
            
        return df_res, df_hist, df_val
    except Exception as e:
        st.error(f"Erro na matriz de dados: {e}")
        return None, None, None

def formatar_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 3. INTERFACE DA APLICAÇÃO (UI)
# ==========================================
col_header, col_refresh = st.columns([0.85, 0.15])

with col_header:
    st.markdown('<p class="main-header">🛸 COMMAND CENTER | ESTOQUE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Monitoramento de Divergências e Estoque Não Vendável</p>', unsafe_allow_html=True)

with col_refresh:
    if st.button("🔄 ATUALIZAR"):
        st.cache_data.clear()
        st.rerun()

with st.spinner('Sincronizando com a Central...'):
    df_resultados, df_historico, df_hist_valores = carregar_dados()

if df_resultados is not None and not df_resultados.empty:
    
    tab1, tab2 = st.tabs(["📊 DASHBOARD VISÃO GLOBAL", "📥 EXTRAÇÃO DE DADOS"])
    
    with tab1:
        # ---- KPIs ----
        total_valor = df_resultados['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum()
        total_pecas = df_resultados['QT_ESTOQUE'].sum()
        qtd_cds = df_resultados['CD_EMPRESA'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown(f'<div class="kpi-card"><p class="kpi-title">Capital Imobilizado</p><p class="kpi-value">{formatar_brl(total_valor)}</p></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="kpi-card"><p class="kpi-title">Volume (Peças)</p><p class="kpi-value">{int(total_pecas):,}</p></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="kpi-card"><p class="kpi-title">Centros de Distribuição</p><p class="kpi-value">{qtd_cds} CDs</p></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="kpi-card"><p class="kpi-title">Status Sistema</p><p class="kpi-value">ONLINE</p></div>', unsafe_allow_html=True)
            
        st.write("---")
        
        # ---- GRÁFICOS ----
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("⚠️ Concentração por Área")
            df_area = df_resultados.groupby('DS_AREA_ARMAZ')['QT_ESTOQUE'].sum().reset_index().sort_values(by='QT_ESTOQUE', ascending=False).head(7)
            fig_area = px.pie(df_area, values='QT_ESTOQUE', names='DS_AREA_ARMAZ', hole=0.6, color_discrete_sequence=px.colors.sequential.Teal)
            fig_area.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", showlegend=False)
            st.plotly_chart(fig_area, use_container_width=True)
                
        with c2:
            st.subheader("🏢 Top 5 Filiais (R$)")
            df_cd = df_resultados.groupby('CD_EMPRESA')['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum().reset_index().sort_values(by='VALOR_TOTAL_ESTOQUE_ATUALIZADO', ascending=True).tail(5)
            fig_cd = px.bar(df_cd, x='VALOR_TOTAL_ESTOQUE_ATUALIZADO', y='CD_EMPRESA', orientation='h', color_continuous_scale="Tealgrn")
            fig_cd.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", coloraxis_showscale=False)
            st.plotly_chart(fig_cd, use_container_width=True)

        st.write("---")

        # ---- RADAR TEMPORAL ----
        st.subheader("📈 Radar Temporal: Evolução do Capital")
        if not df_hist_valores.empty:
            filiais = ["Todas as Filiais"] + sorted(df_hist_valores['CD_EMPRESA'].unique().tolist())
            selecionada = st.selectbox("Base de análise:", filiais)
            df_p = df_hist_valores.copy()
            if selecionada != "Todas as Filiais": df_p = df_p[df_p['CD_EMPRESA'] == selecionada]
            df_trend = df_p.groupby('DATA_HORA')['VALOR_TOTAL_ESTOQUE'].sum().reset_index()
            fig_evol = px.area(df_trend, x='DATA_HORA', y='VALOR_TOTAL_ESTOQUE', markers=True)
            fig_evol.update_traces(line_color='#00FFC4', fillcolor='rgba(0, 255, 196, 0.15)')
            fig_evol.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0")
            st.plotly_chart(fig_evol, use_container_width=True)

        st.write("---")

        # ---- NOVA SECÇÃO: TOP 10 SKUs ----
        st.subheader("🎯 Alvos Prioritários: Top 10 SKUs (Maior Impacto R$)")
        df_top_sku = df_resultados.groupby(['CD_PRODUTO_TRATADO', 'DS_PRODUTO', 'CD_EMPRESA'])['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum().reset_index()
        df_top_sku = df_top_sku.sort_values(by='VALOR_TOTAL_ESTOQUE_ATUALIZADO', ascending=False).head(10)
        
        # Formatação para exibição
        df_top_sku['VALOR_TOTAL_ESTOQUE_ATUALIZADO'] = df_top_sku['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].apply(formatar_brl)
        df_top_sku.columns = ['CÓDIGO SKU', 'DESCRIÇÃO DO PRODUTO', 'FILIAL', 'VALOR RETIDO']
        
        st.table(df_top_sku)

    with tab2:
        st.markdown('### 📥 Extração de Dados')
        st.dataframe(df_resultados.head(20), use_container_width=True)
        st.download_button(label="📥 DOWNLOAD BASE COMPLETA (.XLSX)", data=io.BytesIO().getvalue(), file_name="comando_estoque.xlsx")