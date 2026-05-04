import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÃO E DESIGN DE ALTA PERFORMANCE
# ==========================================
st.set_page_config(page_title="Gestão de Auditoria | Financeiro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #0B0F1A; }
        .main-header { font-size: 1.8rem; color: #F8FAFC; font-weight: 800; padding-bottom: 2px; }
        .sub-header { color: #94A3B8; font-size: 0.95rem; margin-bottom: 25px; }
        
        .kpi-container { display: flex; gap: 15px; margin-bottom: 25px; }
        .kpi-card { 
            background: #161B22; border: 1px solid #30363D; padding: 20px; 
            border-radius: 8px; flex: 1; border-left: 4px solid #3B82F6;
        }
        .kpi-card.neg { border-left-color: #EF4444; }
        .kpi-card.pos { border-left-color: #10B981; }
        .kpi-card.warn { border-left-color: #F59E0B; }
        
        .kpi-title { margin:0; font-size: 0.75rem; color: #8B949E; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;}
        .kpi-value { margin:0; font-size: 1.8rem; color: #F0F6FC; font-weight: 700; padding-top: 5px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. TRATAMENTO FINANCEIRO BLINDADO
# ==========================================
SHEET_ID = "1MubIJ-ckdUQ8cQilZ6qEg2p2Ag40Fdk2vwfIsVUFkJY"

def converter_dinheiro(val):
    if pd.isna(val) or str(val).strip() == '': return 0.0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).replace('R$', '').replace('$', '').replace(' ', '').replace('\xa0', '').strip()
    if s.count(',') == 1 and s.count('.') >= 1:
        s = s.replace('.', '').replace(',', '.')
    elif s.count(',') == 1 and s.count('.') == 0:
        s = s.replace(',', '.')
    elif s.count('.') > 1 and s.count(',') == 0:
        s = s.replace('.', '')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=300)
def carregar_dados_auditoria():
    url_h = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Historico_Valores&headers=0"
    url_d = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=BigQuery+Results"
    url_s = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=SOBRA"
    url_r = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=RESUMO"
    
    try:
        df_h = pd.read_csv(url_h, header=None).iloc[:, 0:5]
        df_h.columns = ['DATA_HORA', 'BRANCH_ID', 'RUA', 'QTD_PECAS', 'VALOR_TOTAL_ESTOQUE']
        df_h['VALOR_TOTAL_ESTOQUE'] = df_h['VALOR_TOTAL_ESTOQUE'].apply(converter_dinheiro)
        df_h['DATA_HORA'] = pd.to_datetime(df_h['DATA_HORA'], dayfirst=True, errors='coerce')
        df_h['BRANCH_ID'] = df_h['BRANCH_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        df_d = pd.read_csv(url_d)
        df_d.columns = df_d.columns.str.strip().str.upper()
        if 'VALOR_TOTAL_ESTOQUE_ATUALIZADO' in df_d.columns:
            df_d['VALOR_TOTAL_ESTOQUE_ATUALIZADO'] = df_d['VALOR_TOTAL_ESTOQUE_ATUALIZADO'].apply(converter_dinheiro)
        if 'BALBOA_CMUP' in df_d.columns:
            df_d['BALBOA_CMUP'] = df_d['BALBOA_CMUP'].apply(converter_dinheiro)
        if 'BRANCH_ID' in df_d.columns:
            df_d['BRANCH_ID'] = df_d['BRANCH_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        df_s = pd.read_csv(url_s)
        df_s.columns = df_s.columns.str.strip().str.upper()
        if 'CUSTO_LIQUIDO' in df_s.columns:
            df_s['SOBRA_TOTAL'] = df_s['CUSTO_LIQUIDO'].apply(converter_dinheiro)
        if 'FILIAL' in df_s.columns:
            df_s['FILIAL'] = df_s['FILIAL'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

        df_r = pd.read_csv(url_r)
        df_r.columns = df_r.columns.str.strip().str.upper()
        col_filial = df_r.columns[0]
        df_r.rename(columns={col_filial: 'BRANCH_ID'}, inplace=True)
        df_r['BRANCH_ID'] = df_r['BRANCH_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        for col in df_r.columns:
            if any(x in col for x in ['BALBOA', 'SOBRA', 'LIQ', 'FATURAMENTO']):
                df_r[col] = df_r[col].apply(converter_dinheiro)

        return df_h, df_d, df_s, df_r
    except Exception as e: 
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None, None

def processar_auditoria(df_d_in, df_s_in):
    df_d_f = df_d_in.copy()
    df_s_f = df_s_in.copy()
    if df_d_f.empty: return pd.DataFrame()
    
    linha_col_bq = 'RESULTADO_LINHA' if 'RESULTADO_LINHA' in df_d_f.columns else 'MLPBI_LINHA'
    df_d_f[linha_col_bq] = df_d_f[linha_col_bq].fillna('NÃO CLASSIFICADO')
    col_vlr_bq = 'BALBOA_CMUP' if 'BALBOA_CMUP' in df_d_f.columns else 'VALOR_TOTAL_ESTOQUE_ATUALIZADO'
    
    df_b = df_d_f.groupby(['BRANCH_ID', linha_col_bq], dropna=False)[col_vlr_bq].sum().reset_index()
    df_b.rename(columns={'BRANCH_ID': 'CD', linha_col_bq: 'LINHA', col_vlr_bq: 'BRUTO'}, inplace=True)
    df_b['LINHA'] = df_b['LINHA'].astype(str).str.strip().str.upper()

    df_s_grp = pd.DataFrame(columns=['CD', 'LINHA', 'VLR_SOBRA'])
    if not df_s_f.empty and 'SOBRA_TOTAL' in df_s_f.columns:
        df_s_f['FILIAL'] = df_s_f['FILIAL'].fillna('0')
        linha_col_s = 'LINHA' if 'LINHA' in df_s_f.columns else 'RESULTADO_LINHA'
        df_s_f[linha_col_s] = df_s_f[linha_col_s].fillna('NÃO CLASSIFICADO')
        
        df_s_grp = df_s_f.groupby(['FILIAL', linha_col_s], dropna=False)['SOBRA_TOTAL'].sum().reset_index()
        df_s_grp.rename(columns={'FILIAL': 'CD', linha_col_s: 'LINHA', 'SOBRA_TOTAL': 'VLR_SOBRA'}, inplace=True)
        df_s_grp['CD'] = df_s_grp['CD'].astype(str).str.strip()
        df_s_grp['LINHA'] = df_s_grp['LINHA'].astype(str).str.strip().str.upper()

    df_m = pd.merge(df_b, df_s_grp, on=['CD', 'LINHA'], how='outer').fillna(0)
    df_m['LIQUIDO'] = df_m['VLR_SOBRA'] - df_m['BRUTO']
    return df_m

# ==========================================
# 4. CONSTRUÇÃO DA UI
# ==========================================
df_h, df_d, df_s, df_r = carregar_dados_auditoria()

if df_h is not None and df_r is not None:
    st.markdown('<div class="main-header">Centro de Comando <span>| Auditoria de Riscos</span></div>', unsafe_allow_html=True)
    
    unidades = ["Brasil (Consolidado)"] + sorted(df_d['BRANCH_ID'].unique().tolist())
    sel_unidade = st.selectbox("📍 Filtrar Unidade:", unidades)

    if sel_unidade != "Brasil (Consolidado)":
        df_h_f = df_h[df_h['BRANCH_ID'] == sel_unidade].copy()
        df_d_f = df_d[df_d['BRANCH_ID'] == sel_unidade].copy()
        df_s_f = df_s[df_s['FILIAL'] == sel_unidade].copy() if not df_s.empty else df_s.copy()
        df_r_f = df_r[df_r['BRANCH_ID'] == sel_unidade].copy() if not df_r.empty else df_r.copy()
    else:
        df_h_f, df_d_f, df_s_f, df_r_f = df_h.copy(), df_d.copy(), df_s.copy(), df_r.copy()

    col_bruto = next((c for c in df_r_f.columns if 'BALBOA' in c or 'BRUTO' in c), None)
    col_sobra = next((c for c in df_r_f.columns if 'SOBRA' in c), None)
    col_liq   = next((c for c in df_r_f.columns if 'LIQ' in c), None)

    v_bruto_risco = df_r_f[col_bruto].sum() if col_bruto else 0
    v_sobra_risco = df_r_f[col_sobra].sum() if col_sobra else 0
    v_liq_risco   = df_r_f[col_liq].sum() if col_liq else 0
    
    if 'UPDATED_AT' in df_d_f.columns:
        df_d_f['UPDATED_AT'] = pd.to_datetime(df_d_f['UPDATED_AT'], format='mixed', errors='coerce')
        hoje = pd.Timestamp.today().normalize()
        df_d_f['DIAS_PARADO'] = (hoje - df_d_f['UPDATED_AT'].dt.normalize()).dt.days
    else:
        df_d_f['DIAS_PARADO'] = 0  

    condicao_divergencia = df_d_f['RUA'].isin(['DVG', 'FIN'])
    condicao_cdk_risco = (df_d_f['RUA'] == 'CDK') & (df_d_f['DIAS_PARADO'] > 7)
    df_d_critico = df_d_f[condicao_divergencia | condicao_cdk_risco]
    
    fmt = lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    c_html = f"""
    <div class="kpi-container">
        <div class="kpi-card neg">
            <p class="kpi-title">🔴 Exposição Bruta (Visão Resumo)</p>
            <p class="kpi-value">{fmt(v_bruto_risco)}</p>
        </div>
        <div class="kpi-card pos">
            <p class="kpi-title">🟢 Provisão de Sobra</p>
            <p class="kpi-value">{fmt(v_sobra_risco)}</p>
        </div>
        <div class="kpi-card warn">
            <p class="kpi-title">⚖️ Impacto Líquido</p>
            <p class="kpi-value">{fmt(v_liq_risco)}</p>
        </div>
        <div class="kpi-card">
            <p class="kpi-title">📦 Peças Afetadas (Risco / Atraso)</p>
            <p class="kpi-value">{len(df_d_critico):,} un</p>
        </div>
    </div>
    """
    st.markdown(c_html, unsafe_allow_html=True)

    df_audit_total = processar_auditoria(df_d_f, df_s_f)
    layout_transp = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#94A3B8")

    tab1, tab2, tab3 = st.tabs(["📉 EVOLUÇÃO TEMPORAL", "🎯 IMPACTO DVG/FIN", "⚔️ TABELA DE AUDITORIA"])

    # ==========================================
    # TAB 1: EVOLUÇÃO + TABELA DE RUAS ISOLADA AQUI
    # ==========================================
    with tab1:
        st.write("#### Tendência Diária de Risco")
        df_evol = df_h_f.groupby([df_h_f['DATA_HORA'].dt.date, 'RUA'])['VALOR_TOTAL_ESTOQUE'].sum().reset_index()
        fig_evol = px.line(df_evol, x='DATA_HORA', y='VALOR_TOTAL_ESTOQUE', color='RUA', markers=True,
                           color_discrete_map={'DVG': '#EF4444', 'FIN': '#F59E0B', 'CTE': '#3B82F6', 'SNT': '#8B5CF6'})
        
        fig_evol.update_layout(**layout_transp, hovermode="x unified")
        fig_evol.update_xaxes(dtick="D1", tickformat="%d/%m", title="", showgrid=False)
        fig_evol.update_yaxes(title="Valor em Estoque (R$)", gridcolor="#1E293B")
        fig_evol.update_traces(line_shape='spline', marker=dict(size=8))
        st.plotly_chart(fig_evol, use_container_width=True)
        
        st.write("---")
        st.write("#### 📦 Posição Atual por Rua")
        
        df_d_f['RUA'] = df_d_f['RUA'].astype(str).str.strip().str.upper()
        col_vlr_rua = 'BALBOA_CMUP' if 'BALBOA_CMUP' in df_d_f.columns else 'VALOR_TOTAL_ESTOQUE_ATUALIZADO'
        df_rua = df_d_f.groupby('RUA').agg(QTD_PECAS=('RUA', 'count'), VALOR_TOTAL_ESTOQUE=(col_vlr_rua, 'sum')).reset_index()
        
        st.dataframe(
            df_rua.sort_values('VALOR_TOTAL_ESTOQUE', ascending=False),
            column_config={
                "RUA": "Status / Rua",
                "QTD_PECAS": st.column_config.NumberColumn("Qtd Peças", format="%d un"),
                "VALOR_TOTAL_ESTOQUE": st.column_config.NumberColumn("Custo Acumulado", format="R$ %.2f")
            },
            width="stretch", hide_index=True 
        )

   # ==========================================
    # TAB 2: GRÁFICO OTIMIZADO (SOMENTE DVG E FIN)
    # ==========================================
    with tab2:
        st.write("#### 🎯 Raio-X de Divergências Críticas (Apenas DVG e FIN)")
        
        # Filtro EXCLUSIVO para DVG e FIN nesta aba
        df_d_dvg_fin = df_d_f[df_d_f['RUA'].isin(['DVG', 'FIN'])]
        df_audit_tab2 = processar_auditoria(df_d_dvg_fin, df_s_f)
        
        if not df_audit_tab2.empty:
            # ---------------------------------------------------------
            # CORREÇÃO: Consolidar todas as filiais (CDs) por Categoria 
            # antes de desenhar o gráfico para evitar barras sobrepostas
            # ---------------------------------------------------------
            df_plot = df_audit_tab2.groupby('LINHA')[['BRUTO', 'VLR_SOBRA', 'LIQUIDO']].sum().reset_index()
            
            # Pega o Top 12 baseado no Custo Bruto
            df_plot = df_plot.sort_values('BRUTO', ascending=True).tail(12)
            
            # Formatador elegante
            fmt_k = lambda x: f"R$ {x/1000:,.1f}k".replace(",", "X").replace(".", ",").replace("X", ".") if abs(x) >= 1000 else f"R$ {x:,.0f}"
            
            fig_bar = go.Figure()
            
            # 1. Custo Bruto (Risco)
            fig_bar.add_trace(go.Bar(
                y=df_plot['LINHA'], x=df_plot['BRUTO'], 
                name='Risco Bruto (DVG/FIN)', orientation='h', 
                marker_color='#EF4444', 
                text=[fmt_k(v) for v in df_plot['BRUTO']],
                textposition='auto', # 'auto' resolve o esmagamento do texto
                textfont=dict(weight='bold')
            ))
            
            # 2. Sobra (Provisão)
            fig_bar.add_trace(go.Bar(
                y=df_plot['LINHA'], x=df_plot['VLR_SOBRA'], 
                name='Provisão Sistêmica', orientation='h', 
                marker_color='#10B981', 
                text=[fmt_k(v) for v in df_plot['VLR_SOBRA']],
                textposition='auto', 
                textfont=dict(weight='bold')
            ))
            
            # 3. Saldo Líquido
            fig_bar.add_trace(go.Bar(
                y=df_plot['LINHA'], x=df_plot['LIQUIDO'], 
                name='Saldo Líquido Real', orientation='h', 
                marker_color='#3B82F6', 
                text=[fmt_k(v) for v in df_plot['LIQUIDO']],
                textposition='auto', 
                textfont=dict(weight='bold')
            ))
            
            fig_bar.update_layout(
                **layout_transp, 
                barmode='group', 
                height=max(500, len(df_plot) * 60), # Altura dinâmica baseada na qtd de barras
                bargap=0.15,      # Barras mais gordinhas
                bargroupgap=0.02, # Barras do mesmo grupo coladinhas
                legend=dict(orientation="h", y=1.05, x=0.5, xanchor='center', font=dict(size=14, color="#F8FAFC")),
                xaxis=dict(showgrid=True, gridcolor='#1E293B', zeroline=True, zerolinecolor='#475569', title=""),
                yaxis=dict(showgrid=False, title="", tickfont=dict(size=11, color="#CBD5E1")),
                margin=dict(l=0, r=40, t=20, b=0)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # ==========================================
    # TAB 3: TABELA DE AUDITORIA COMPLETA
    # ==========================================
    with tab3:
        st.write("#### Detalhamento da Auditoria")
        st.dataframe(
            df_audit_total.sort_values('LIQUIDO').rename(columns={'CD':'CD','LINHA':'Categoria','BRUTO':'Custo Bruto Total','VLR_SOBRA':'Sobra Total','LIQUIDO':'Saldo Líquido'}),
            column_config={
                "Custo Bruto Total": st.column_config.NumberColumn(format="R$ %.2f"),
                "Sobra Total": st.column_config.NumberColumn(format="R$ %.2f"),
                "Saldo Líquido": st.column_config.NumberColumn(format="R$ %.2f")
            },
            width="stretch", hide_index=True 
        )

else:
    st.error("Aguardando comunicação com a base de dados.")