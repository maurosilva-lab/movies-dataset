import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | Business Intelligence", page_icon="📊")

# --- ESTILIZAÇÃO CSS (FOCO NA BARRA DE EVOLUÇÃO) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0b0e14; }
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }

    /* Estilo dos Cards */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .metric-label { color: #8b949e; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .metric-value { color: #f0f6fc; font-size: 24px; font-weight: 700; }
    
    /* Barra de Progresso dentro do Card */
    .progress-container {
        background-color: #30363d;
        border-radius: 10px;
        height: 8px;
        width: 100%;
        margin-top: 15px;
    }
    .progress-bar {
        background: linear-gradient(90deg, #58a6ff 0%, #00f2ff 100%);
        height: 8px;
        border-radius: 10px;
        transition: width 0.5s ease-in-out;
    }
    .perc-text { color: #58a6ff; font-size: 12px; font-weight: 600; margin-top: 5px; }

    .header-container { padding: 1rem 0; margin-bottom: 2rem; border-bottom: 1px solid #30363d; text-align: center; }
    .main-title { color: #f0f6fc; font-size: 26px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() in ["", "-", "nan"] or "DIV/0" in str(valor): return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    v = re.sub(r'[^0-9\.\-]', '', v)
    try: return float(v)
    except: return 0.0

def mapear_divisional(cd_bruto):
    try: cd = int(float(str(cd_bruto).replace(',', '.')))
    except: return 'Outros'
    if cd in [590, 300, 50]: return 'Renato Nesello'
    elif cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif cd in [350, 5200, 2900, 94, 490, 550, 2500]: return 'Christian'
    elif cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    else: return 'Outros'

# 2. CARREGAMENTO
SHEET_ID = "1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI"
GID_MAIN = "1358149674"

@st.cache_data
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MAIN}"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data()
    
    # Processamento
    for col_txt in ['semestre', 'tipo', 'cd', 'local']:
        if col_txt in df_raw.columns: df_raw[col_txt] = df_raw[col_txt].astype(str).str.strip()

    cols_num = ["1__ciclo", "2__ciclo", "3__ciclo", "faturamento__lojas___site_", "falta_vol"]
    for col in cols_num:
        df_raw[col + "_num"] = df_raw[col].apply(limpar_valor) if col in df_raw.columns else 0.0

    df_raw['is_finalizado'] = (df_raw["1__ciclo_num"] != 0) | (df_raw["2__ciclo_num"] != 0) | (df_raw["3__ciclo_num"] != 0)
    df_raw['perc_perda_unidade'] = (df_raw["1__ciclo_num"].abs() / df_raw["faturamento__lojas___site__num"]) * 100
    df_raw['perc_perda_unidade'] = df_raw['perc_perda_unidade'].fillna(0.0).replace([float('inf')], 0.0)
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    df_raw['tipo_clean'] = df_raw['tipo'].str.upper()

    st.markdown('<div class="header-container"><span class="main-title">BI FECHAMENTO MAGALOG 2026</span></div>', unsafe_allow_html=True)

    # --- FILTROS (SIDEBAR) ---
    with st.sidebar:
        st.header("Filtros")
        tipos_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        divs_sel = st.multiselect("Divisional", options=sorted(df_raw['divisional'].unique()))
        semestre_sel = st.multiselect("Semestre", options=sorted(df_raw['semestre'].unique()))

    df_filt = df_raw.copy()
    if tipos_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(tipos_sel)]
    if divs_sel: df_filt = df_filt[df_filt['divisional'].isin(divs_sel)]
    if semestre_sel: df_filt = df_filt[df_filt['semestre'].isin(semestre_sel)]

    # --- CÁLCULOS ---
    total_un = len(df_filt)
    finalizados = df_filt['is_finalizado'].sum()
    perc_conclusao = (finalizados / total_un * 100) if total_un > 0 else 0
    perda_total = df_filt["1__ciclo_num"].sum()
    falta_vol = df_filt["falta_vol_num"].sum()
    fat_total = df_filt["faturamento__lojas___site__num"].sum()
    perc_global = (abs(perda_total) / fat_total * 100) if fat_total > 0 else 0.0

    # --- CARDS COM BARRA DE EVOLUÇÃO ---
    def card_com_progresso(label, value, percent, sub_text):
        return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="perc-text">{sub_text} ({percent:.1f}%)</div>
            <div class="progress-container">
                <div class="progress-bar" style="width: {percent}%"></div>
            </div>
        </div>
        """

    def card_simples(label, value, sub):
        return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="perc-text" style="color: #8b949e;">{sub}</div>
        </div>
        """

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5]) # Damos mais espaço para o card com barra
    c1.markdown(card_simples("1º Ciclo Total", f"R$ {perda_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), "Perda Financeira"), unsafe_allow_html=True)
    c2.markdown(card_simples("Falta Vol.", f"{falta_vol:,.0f}".replace('.', ','), "Itens Faltantes"), unsafe_allow_html=True)
    c3.markdown(card_simples("% Perda Global", f"{perc_global:.3f}%", "Sobre Faturamento"), unsafe_allow_html=True)
    c4.markdown(card_com_progresso("Status de Evolução", f"{int(finalizados)} / {total_un}", perc_conclusao, "Finalizadas"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICOS E TABELA ---
    col_g1, col_g2 = st.columns([1, 1.2])
    with col_g1:
        st.subheader("Perda por Divisional")
        fig = px.pie(df_filt, values=df_filt["1__ciclo_num"].abs(), names='divisional', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(template="plotly_dark", height=350, margin=dict(t=20, b=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        st.subheader("Treemap de Saúde")
        df_tree = df_filt[df_filt["1__ciclo_num"] != 0].copy()
        if not df_tree.empty:
            df_tree['abs_val'] = df_tree["1__ciclo_num"].abs()
            fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd'], values='abs_val', color='1__ciclo_num', color_continuous_scale='RdBu_r')
            fig_t.update_layout(template="plotly_dark", height=350, margin=dict(t=30, b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_t, use_container_width=True)

    st.subheader("Detalhamento Geral")
    st.dataframe(
        df_filt[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', '1__ciclo_num', 'perc_perda_unidade', 'is_finalizado']],
        column_config={
            "1__ciclo_num": st.column_config.NumberColumn("Resultado 1C", format="R$ %.2f"),
            "perc_perda_unidade": st.column_config.NumberColumn("% Perda", format="%.3f%%"),
            "is_finalizado": st.column_config.CheckboxColumn("Finalizado?")
        },
        use_container_width=True, hide_index=True
    )

except Exception as e:
    st.error(f"⚠️ Erro: {e}")