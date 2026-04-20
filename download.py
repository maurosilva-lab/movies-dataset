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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES DE CARREGAMENTO E TRATAMENTO
# ==========================================
SHEET_ID = "11-IwzWjgFVKynzDTkqpr4_Fbs4GclKhS7W0KTKms0q4" 

def tratar_moeda(val):
    """ Função blindada para limpar formatos financeiros (R$, pontos e vírgulas) """
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    
    val_str = str(val).replace('R$', '').replace(' ', '').replace('\xa0', '').strip()
    
    # Se tem ponto de milhar e vírgula decimal (ex: 3.675.201,65)
    if '.' in val_str and ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    # Se tem só vírgula decimal (ex: 348090,23)
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try:
        return float(val_str)
    except:
        return 0.0

@st.cache_data(ttl=600)
def carregar_dados():
    url_resultados = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=BigQuery+Results"
    url_historico = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico"
    url_hist_valores = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico_Valores"
    
    try:
        # Lê bruto, sem forçar decimais, para o nosso tratador fazer o trabalho limpo
        df_res = pd.read_csv(url_resultados)
        df_hist = pd.read_csv(url_historico)
        df_val = pd.read_csv(url_hist_valores)
        
        # Strip em nomes de colunas por segurança
        df_res.columns = df_res.columns.str.strip()
        df_hist.columns = df_hist.columns.str.strip()
        df_val.columns = df_val.columns.str.strip()
        
        # Tratamento: Aba Results
        cols_financeiras = ['VALOR_TOTAL_ESTOQUE_ATUALIZADO', 'QT_ESTOQUE', 'CUSTO_MEDIO', 'CUSTO_PGTO']
        for col in cols_financeiras:
            if col in df_res.columns:
                df_res[col] = df_res[col].apply(tratar_moeda)
                
        # Tratamento: Aba Historico_Valores (Nova)
        if 'VALOR_TOTAL_ESTOQUE' in df_val.columns:
            df_val['VALOR_TOTAL_ESTOQUE'] = df_val['VALOR_TOTAL_ESTOQUE'].apply(tratar_moeda)
            
        if 'DATA_HORA' in df_val.columns:
            # dayfirst=True garante que o Pandas entenda dia/mês/ano corretamente
            df_val['DATA_HORA'] = pd.to_datetime(df_val['DATA_HORA'], dayfirst=True, errors='coerce')
            
        # Forçar a empresa a ser tratada como Texto, removendo ".0" do final
        if 'CD_EMPRESA' in df_val.columns:
            df_val['CD_EMPRESA'] = df_val['CD_EMPRESA'].astype(str).str.replace(r'\.0$', '', regex=True)
        if 'CD_EMPRESA' in df_res.columns:
            df_res['CD_EMPRESA'] = df_res['CD_EMPRESA'].astype(str).str.replace(r'\.0$', '', regex=True)
            
        if 'DATA_HORA_ATUALIZACAO' in df_hist.columns:
            df_hist['DATA_HORA_ATUALIZACAO'] = pd.to_datetime(df_hist['DATA_HORA_ATUALIZACAO'], errors='coerce')
            df_hist = df_hist.sort_values('DATA_HORA_ATUALIZACAO')
            
        return df_res, df_hist, df_val
    except Exception as e:
        st.error(f"Erro na matriz de dados: {e}")
        return None, None, None

def limpar_dados_para_excel(df):
    df_clean = df.copy()
    palavras_chave = ['ID', 'CD_', 'EAN', 'SKU', 'ITEM', 'PEDIDO', 'LOTE', 'BLOCO', 'APTO', 'SALA', 'EMPRESA', 'DIGIT']
    for col in df_clean.columns:
        if any(palavra in col.upper() for palavra in palavras_chave):
            df_clean[col] = df_clean[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    return df_clean

def converter_para_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Base Consolidada')
    return output.getvalue()

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

with st.spinner('Sincronizando com o BigQuery via Satélite...'):
    df_resultados, df_historico, df_hist_valores = carregar_dados()

if df_resultados is not None and not df_resultados.empty:
    
    # Organização em Abas
    tab1, tab2 = st.tabs(["📊 DASHBOARD VISÃO GLOBAL", "📥 EXTRAÇÃO DE DADOS"])
    
    with tab1:
        # ---- CÁLCULO DOS KPIs ----
        total_valor = df_resultados['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum()
        total_pecas = df_resultados['QT_ESTOQUE'].sum()
        qtd_cds = df_resultados['CD_EMPRESA'].nunique() if 'CD_EMPRESA' in df_resultados.columns else 0
        qtd_areas = df_resultados['DS_AREA_ARMAZ'].nunique() if 'DS_AREA_ARMAZ' in df_resultados.columns else 0
        
        # Formatando valores para o padrão brasileiro
        valor_formatado = f"R$ {total_valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pecas_formatado = f"{int(total_pecas):,}".replace(",", ".")
        
        # ---- LINHA 1: CARDS FUTURISTAS ----
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Capital Imobilizado</p><p class="kpi-value">{valor_formatado}</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Volume (Peças)</p><p class="kpi-value">{pecas_formatado}</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Centros de Distribuição</p><p class="kpi-value">{qtd_cds} CDs</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="kpi-card"><p class="kpi-title">Áreas Críticas</p><p class="kpi-value">{qtd_areas} Setores</p></div>', unsafe_allow_html=True)
            
        st.write("---")
        
        # ---- LINHA 2: GRÁFICOS DE ROSCA E BARRAS ----
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("⚠️ Concentração por Área de Armazém")
            if 'DS_AREA_ARMAZ' in df_resultados.columns:
                df_area = df_resultados.groupby('DS_AREA_ARMAZ')['QT_ESTOQUE'].sum().reset_index().sort_values(by='QT_ESTOQUE', ascending=False).head(7)
                fig_area = px.pie(df_area, values='QT_ESTOQUE', names='DS_AREA_ARMAZ', hole=0.6, 
                                  color_discrete_sequence=px.colors.sequential.Teal)
                fig_area.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", showlegend=False)
                fig_area.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_area, use_container_width=True)
                
        with c2:
            st.subheader("🏢 Top 5 Filiais por Valor Retido (R$)")
            if 'CD_EMPRESA' in df_resultados.columns:
                df_cd = df_resultados.groupby('CD_EMPRESA')['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum().reset_index().sort_values(by='VALOR_TOTAL_ESTOQUE_ATUALIZADO', ascending=True).tail(5)
                df_cd['CD_EMPRESA'] = "Filial " + df_cd['CD_EMPRESA']
                fig_cd = px.bar(df_cd, x='VALOR_TOTAL_ESTOQUE_ATUALIZADO', y='CD_EMPRESA', orientation='h',
                                text_auto='.2s', color='VALOR_TOTAL_ESTOQUE_ATUALIZADO', color_continuous_scale="Tealgrn")
                fig_cd.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", coloraxis_showscale=False)
                fig_cd.update_xaxes(title="", showgrid=False)
                fig_cd.update_yaxes(title="")
                st.plotly_chart(fig_cd, use_container_width=True)

        st.write("---")

        # ---- LINHA 3: GRÁFICO DE EVOLUÇÃO NEON ----
        st.subheader("📈 Radar Temporal: Evolução do Capital Retido")
        st.caption("*(Nota: Uma linha evolutiva surgirá assim que o robô realizar as próximas coletas de histórico)*")
        
        if df_hist_valores is not None and not df_hist_valores.empty:
            
            # Filtro Interativo
            filiais_disponiveis = ["Todas as Filiais"] + sorted(df_hist_valores['CD_EMPRESA'].dropna().unique().tolist())
            filial_selecionada = st.selectbox("Selecione a base de análise:", filiais_disponiveis)
            
            # Filtragem do DataFrame
            df_plot = df_hist_valores.copy()
            if filial_selecionada != "Todas as Filiais":
                df_plot = df_plot[df_plot['CD_EMPRESA'] == filial_selecionada]
            
            # Agrupar por data (caso existam múltiplos setores na mesma hora/data)
            df_trend = df_plot.groupby('DATA_HORA')['VALOR_TOTAL_ESTOQUE'].sum().reset_index().sort_values('DATA_HORA')
            
            # Gráfico de Área Cyberpunk
            fig_evol = px.area(df_trend, x='DATA_HORA', y='VALOR_TOTAL_ESTOQUE', markers=True)
            fig_evol.update_traces(
                line_color='#00FFC4', 
                line_width=3,
                fillcolor='rgba(0, 255, 196, 0.15)',
                marker=dict(size=8, color='#00B4D8', symbol='diamond')
            )
            fig_evol.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", 
                paper_bgcolor="rgba(0,0,0,0)", 
                font_color="#8892B0",
                xaxis_title="",
                yaxis_title="Valor Acumulado (R$)",
                hovermode="x unified",
                xaxis=dict(showgrid=True, gridcolor='rgba(136, 146, 176, 0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(136, 146, 176, 0.1)')
            )
            st.plotly_chart(fig_evol, use_container_width=True)
        else:
            st.info("Aguardando acumulação de dados no histórico para traçar a evolução...")

    with tab2:
        st.markdown('### 📡 Status da Transmissão')
        
        # Exibe o último registro da aba histórico
        if df_historico is not None and not df_historico.empty:
            ultimo_registro = df_historico.iloc[-1]
            data_obs = ultimo_registro['DATA_HORA_ATUALIZACAO']
            st.info(f"**Última Atualização:** {data_obs} | **Status:** {ultimo_registro['STATUS']} | **Linhas Processadas:** {ultimo_registro['QTD_LINHAS']}")
        
        with st.expander("👀 Visualizar matriz bruta dos dados (Top 10)"):
            st.dataframe(df_resultados.head(10), use_container_width=True)
            
        st.write("---")
        
        # Preparação para Download
        df_tratado = limpar_dados_para_excel(df_resultados)
        arquivo_excel = converter_para_excel(df_tratado)
        
        st.download_button(
            label="📥 INICIAR DOWNLOAD DA BASE TRATADA (.XLSX)",
            data=arquivo_excel,
            file_name="estoque_comando_tratado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )