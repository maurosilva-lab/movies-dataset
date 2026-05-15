import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E DESIGN (CYBERPUNK)
# ==========================================
st.set_page_config(page_title="Centro de Comando | Estoque", page_icon="🛸", layout="wide", initial_sidebar_state="expanded")

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
        
        /* Sidebar Dark */
        [data-testid="stSidebar"] { background-color: #0B132B; border-right: 1px solid #1C2541;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES DE TRATAMENTO
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
        df_hist.columns = df_hist.columns.str.strip()
        df_val.columns = df_val.columns.str.strip()
        
        for col in ['VALOR_TOTAL_ESTOQUE_ATUALIZADO', 'QT_ESTOQUE', 'CUSTO_MEDIO', 'CUSTO_PGTO']:
            if col in df_res.columns: df_res[col] = df_res[col].apply(tratar_moeda)
        
        if 'VALOR_TOTAL_ESTOQUE' in df_val.columns: df_val['VALOR_TOTAL_ESTOQUE'] = df_val['VALOR_TOTAL_ESTOQUE'].apply(tratar_moeda)
        if 'DATA_HORA' in df_val.columns:
            df_val['DATA_HORA'] = pd.to_datetime(df_val['DATA_HORA'], dayfirst=True, errors='coerce')
            df_val['DATA_APENAS'] = df_val['DATA_HORA'].dt.date
        
        for df in [df_res, df_val]:
            if 'CD_EMPRESA' in df.columns: df['CD_EMPRESA'] = df['CD_EMPRESA'].astype(str).str.replace(r'\.0$', '', regex=True)
            
        return df_res, df_hist, df_val
    except Exception as e:
        st.error(f"Erro na matriz de dados: {e}")
        return None, None, None

# ==========================================
# 3. CARGA E FILTROS (SIDEBAR)
# ==========================================
df_resultados_raw, df_historico, df_hist_valores_raw = carregar_dados()

if df_resultados_raw is not None:
    with st.sidebar:
        st.markdown('<h2 style="color: #00FFC4; text-align: center;">⚙️ FILTROS GLOBAIS</h2>', unsafe_allow_html=True)
        st.markdown("---")
        
        empresas_disp = sorted(df_resultados_raw['CD_EMPRESA'].unique())
        sel_empresas = st.multiselect("Selecione as Filiais:", empresas_disp, default=empresas_disp)
        
        areas_disp = sorted(df_resultados_raw['DS_AREA_ARMAZ'].unique())
        sel_areas = st.multiselect("Selecione as Áreas:", areas_disp, default=areas_disp)
        
        st.markdown("---")
        st.subheader("📅 Período do Radar")
        datas_disp = df_hist_valores_raw['DATA_APENAS'].dropna().unique()
        min_d, max_d = (min(datas_disp), max(datas_disp)) if len(datas_disp) > 0 else (None, None)
        sel_data = st.date_input("Intervalo Temporal:", value=(min_d, max_d), min_value=min_d, max_value=max_d)

    # Aplicação dos Filtros nos DataFrames
    df_res = df_resultados_raw[df_resultados_raw['CD_EMPRESA'].isin(sel_empresas) & df_resultados_raw['DS_AREA_ARMAZ'].isin(sel_areas)]
    
    df_val = df_hist_valores_raw[df_hist_valores_raw['CD_EMPRESA'].isin(sel_empresas) & df_hist_valores_raw['DS_AREA_ARMAZ'].isin(sel_areas)]
    if isinstance(sel_data, tuple) and len(sel_data) == 2:
        df_val = df_val[(df_val['DATA_APENAS'] >= sel_data[0]) & (df_val['DATA_APENAS'] <= sel_data[1])]

    # ==========================================
    # 4. DASHBOARD PRINCIPAL
    # ==========================================
    st.markdown('<p class="main-header">🛸 COMMAND CENTER | ESTOQUE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Monitoramento em Tempo Real via BigQuery</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 VISÃO ESTRATÉGICA", "📥 EXTRAÇÃO"])

    with tab1:
        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        v_total = df_res['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum()
        p_total = df_res['QT_ESTOQUE'].sum()
        c1.markdown(f'<div class="kpi-card"><p class="kpi-title">Capital Imobilizado</p><p class="kpi-value">R$ {v_total:,.2f}</p></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="kpi-card"><p class="kpi-title">Volume (Peças)</p><p class="kpi-value">{int(p_total):,}</p></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="kpi-card"><p class="kpi-title">Filiais Ativas</p><p class="kpi-value">{df_res["CD_EMPRESA"].nunique()}</p></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="kpi-card"><p class="kpi-title">Áreas Analisadas</p><p class="kpi-value">{df_res["DS_AREA_ARMAZ"].nunique()}</p></div>', unsafe_allow_html=True)

        st.write("---")
        
        # Gráficos de Distribuição
        g1, g2 = st.columns(2)
        with g1:
            fig_p = px.pie(df_res.groupby('DS_AREA_ARMAZ')['QT_ESTOQUE'].sum().reset_index(), values='QT_ESTOQUE', names='DS_AREA_ARMAZ', hole=0.6, title="Distribuição por Setor", color_discrete_sequence=px.colors.sequential.Teal)
            fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#8892B0", showlegend=False)
            st.plotly_chart(fig_p, use_container_width=True)
        
        with g2:
            # CORREÇÃO 1: Forçando o Eixo Y a ser Categórico criando uma nova coluna com a string 'Filial'
            df_b = df_res.groupby('CD_EMPRESA')['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum().reset_index().sort_values('VALOR_TOTAL_ESTOQUE_ATUALIZADO', ascending=True).tail(5)
            df_b['CD_EMPRESA_LBL'] = "Filial " + df_b['CD_EMPRESA']
            
            fig_b = px.bar(df_b, x='VALOR_TOTAL_ESTOQUE_ATUALIZADO', y='CD_EMPRESA_LBL', orientation='h', title="Top 5 Filiais Críticas", color='VALOR_TOTAL_ESTOQUE_ATUALIZADO', color_continuous_scale="GnBu", text_auto='.2s')
            fig_b.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)", 
                font_color="#8892B0", 
                coloraxis_showscale=False,
                yaxis_title="", # Esconde o nome do eixo para ficar limpo
                xaxis_title=""
            )
            st.plotly_chart(fig_b, use_container_width=True)

        st.write("---")

        # Tabela Acumulada
        st.subheader("📋 Detalhamento da Posição Atual")
        df_tab = df_res.groupby(['CD_EMPRESA', 'DS_AREA_ARMAZ'])['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].sum().reset_index().sort_values('VALOR_TOTAL_ESTOQUE_ATUALIZADO', ascending=False)
        st.dataframe(df_tab.style.format({'VALOR_TOTAL_ESTOQUE_ATUALIZADO': 'R$ {:,.2f}'.format}).background_gradient(cmap='GnBu'), use_container_width=True, hide_index=True)

        st.write("---")

       # GRÁFICO DE ONDAS (STREAMPGRAPH / SPLINE)
        st.subheader("📈 Radar Temporal: Evolução de Fluxo")
        if not df_val.empty:
            # Agrupa APENAS por data/hora para ter o volume total consolidado
            df_wave = df_val.groupby('DATA_HORA')['VALOR_TOTAL_ESTOQUE'].sum().reset_index()
            
            # Cria o gráfico de área com uma cor só (Neon)
            fig_wave = px.area(df_wave, x='DATA_HORA', y='VALOR_TOTAL_ESTOQUE')
            
            fig_wave.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#8892B0",
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title=""),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Acumulado Total (R$)"),
                margin=dict(l=0, r=0, t=20, b=0),
                showlegend=False
            )
            
            # Aplica o efeito spline (curvas suaves), cor neon da linha e preenchimento translúcido
            fig_wave.update_traces(
                line_shape='spline', 
                line=dict(color='#00FFC4', width=3), 
                fillcolor='rgba(0, 255, 196, 0.15)',
                opacity=1
            )
            
            st.plotly_chart(fig_wave, use_container_width=True)
        else:
            st.info("Aguardando telemetria de dados históricos...")

    with tab2:
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

        st.button("🔄 LIMPAR CACHE E RECARREGAR", on_click=lambda: st.cache_data.clear())
        st.dataframe(df_res, use_container_width=True)
        
        st.write("---")
        
        df_tratado = limpar_dados_para_excel(df_res) # Alterado para baixar apenas o filtrado (df_res) em vez do raw
        arquivo_excel = converter_para_excel(df_tratado)
        
        st.download_button(
            label="📥 INICIAR DOWNLOAD DA BASE TRATADA (.XLSX)",
            data=arquivo_excel,
            file_name="estoque_comando_tratado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )