import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira)
# ==========================================
st.set_page_config(layout="wide", page_title="Dashboard Risco Logística", page_icon="🚛")

# ==========================================
# 2. CONTROLES GLOBAIS E SIDEBAR
# ==========================================
# O botão de atualizar deve ficar FORA do fragmento para recarregar o app todo
with st.sidebar:
    st.header("⚙️ Controles de Dados")
    if st.button('🔄 Atualizar Dados Agora'):
        st.cache_data.clear()
        st.rerun()
    st.write(f"Última atualização: {datetime.now().strftime('%H:%M:%S')}")
    st.divider()

# ==========================================
# 3. FRAGMENTO DE CONTEÚDO (Auto-update)
# ==========================================
@st.fragment(run_every=600) # Atualiza automaticamente a cada 10 minutos (600s)
def render_dashboard_content():
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1dSYbGC3dFW2TP01ICfWY55P9OiurB0ngLsmrqM5kSYg/export?format=csv&gid=629990986"

    # --- CSS para Design ---
    st.markdown("""
        <style>
        .stMetric { background-color: #111827; border-radius: 10px; padding: 15px; border: 1px solid #374151; }
        [data-testid="stMetricValue"] { font-size: 24px !important; font-weight: bold; }
        .header-bar { 
            background: linear-gradient(90deg, #1E3A8A 0%, #1e40af 100%); 
            padding: 10px 20px; border-radius: 8px; color: white; 
            margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;
        }
        .gauge-card { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; height: 100%; }
        </style>
        <div class="header-bar">
            <span style="font-weight: bold; font-size: 20px;">INDICADOR DE RISCO LOGÍSTICA</span>
            <span style="font-size: 14px; opacity: 0.8;">Data Analytics Unit | v4.0</span>
        </div>
        """, unsafe_allow_html=True)

    # --- Carregamento e Tratamento ---
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
        col_cd, col_dvg, col_risco = 'CD', 'DVG EM em Milhares', 'GRAU DE RISCO GERAL'
        col_malha, col_rec_tec, col_tipo = 'MALHA EM QNT', 'REC. TEC. em Milhares', 'TIPO'

        # --- Filtros dentro do fragmento ---
        with st.sidebar:
            st.subheader("Filtros de Exibição")
            datas_disp = sorted(df_raw['DATA'].unique(), reverse=True)
            sel_date = st.selectbox("Data de Análise", options=datas_disp)
            
            idx_atual = datas_disp.index(sel_date)
            data_anterior = datas_disp[idx_atual + 1] if idx_atual + 1 < len(datas_disp) else sel_date

            tipos_disp = sorted(df_raw[col_tipo].unique()) if col_tipo in df_raw.columns else []
            sel_tipos = st.multiselect("Tipo de Unidade", options=tipos_disp, default=tipos_disp)
            
            cds_disp = sorted(df_raw[df_raw[col_tipo].isin(sel_tipos)][col_cd].unique())
            sel_cds = st.multiselect("Filiais (CDs)", options=cds_disp, default=cds_disp)

        df_atual = df_raw[(df_raw['DATA'] == sel_date) & (df_raw[col_cd].isin(sel_cds))].copy()
        df_passado = df_raw[(df_raw['DATA'] == data_anterior) & (df_raw[col_cd].isin(sel_cds))].copy()

        # --- Linha 1: KPIs ---
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.2])

        with c1:
            st.metric("DVG Atual (k)", f"R$ {df_atual[col_dvg].sum()/1000:,.1f}k")
        
        with c2:
            dvg_hoje = df_atual[col_dvg].sum()
            dvg_ontem = df_passado[col_dvg].sum()
            dif_valor = dvg_hoje - dvg_ontem
            st.metric("DIF (vs Anterior)", f"{dif_valor/1000:+.1f}k", delta=f"{dif_valor/1000:,.1f}k", delta_color="inverse")

        with c3:
            st.metric("Qtd Malha", f"{int(df_atual[col_malha].sum()):,}")

        with c4:
            st.metric("REC. TEC. (k)", f"R$ {df_atual[col_rec_tec].sum()/1000:,.1f}k")

        with c5:
            st.markdown('<div class="gauge-card">', unsafe_allow_html=True)
            risco_med = df_atual[col_risco].mean()
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number", value = risco_med,
                number = {'font': {'color': 'white', 'size': 30}, 'valueformat': '.2f'},
                title = {'text': "Risco Médio", 'font': {'color': '#94A3B8', 'size': 12}},
                gauge = {'axis': {'range': [0, 3]}, 'bar': {'color': "#3B82F6"},
                         'steps': [{'range': [0, 1], 'color': "green"}, {'range': [1, 2], 'color': "yellow"}, {'range': [2, 3], 'color': "red"}]}
            ))
            fig_gauge.update_layout(height=130, margin=dict(l=15, r=15, t=30, b=5), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Linha 2: Pareto ---
        st.subheader("Concentração DVG por CD")
        df_p = df_atual[df_atual[col_dvg] > 0].sort_values(col_dvg, ascending=False).reset_index(drop=True)
        if not df_p.empty:
            df_p['cum_perc'] = 100 * df_p[col_dvg].cumsum() / df_p[col_dvg].sum()
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=df_p[col_cd].astype(str), y=df_p[col_dvg], name="DVG", marker_color='#3B82F6',
                                   text=[f"R$ {v/1000:.1f}k" for v in df_p[col_dvg]], textposition='outside'))
            fig_p.add_trace(go.Scatter(x=df_p[col_cd].astype(str), y=df_p['cum_perc'], name="%", yaxis="y2", line=dict(color="#F87171", width=3)))
            fig_p.update_layout(height=380, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                yaxis2=dict(overlaying="y", side="right", range=[0, 110]), legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
            st.plotly_chart(fig_p, use_container_width=True)

        # --- Tabela Detalhada ---
        st.subheader("📋 Detalhamento Operacional")
        df_table = df_atual[[col_cd, 'CIDADE', col_rec_tec, col_malha, col_dvg, col_risco]].copy()

        def style_performance(styler):
            styler.format({col_dvg: 'R$ {:,.1f}k', col_risco: '{:.2f}', col_malha: '{:,}'})
            styler.background_gradient(cmap='RdYlGn_r', subset=[col_dvg])
            styler.background_gradient(cmap='YlOrRd', subset=[col_risco], vmin=0, vmax=3)
            
            def color_contrast(val):
                if isinstance(val, (int, float)) and val < 1.5: return 'color: black; font-weight: bold;'
                return 'color: white; font-weight: bold;'
            
            styler.map(color_contrast, subset=[col_risco])
            styler.set_properties(**{'text-align': 'center', 'border': '1px solid #262730'})
            return styler

        st.dataframe(style_performance(df_table.style), use_container_width=True, hide_index=True)

    else:
        st.info("💡 Aguardando conexão com a planilha...")

# ==========================================
# 4. EXECUÇÃO FINAL
# ==========================================
render_dashboard_content()