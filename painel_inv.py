import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. CONFIGURAÇÃO DA PÁGINA (ESTILO DASHBOARD PRO)
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS AVANÇADO (ESTILO NEON / FIGMA) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    .block-container { padding-top: 1rem !important; max-width: 95%; }
    
    /* TÍTULO COM GRADIENTE */
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.2);
    }
    .header-title { color: white; font-size: 28px; font-weight: 800; letter-spacing: 2px; margin:0; }

    /* CARDS ESTILO NEON */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 15px; padding: 20px; text-align: center;
        transition: transform 0.3s;
    }
    .card-kpi:hover { transform: translateY(-5px); border-color: #58a6ff; }
    .label-kpi { color: #8b949e; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .value-kpi { color: #f0f6fc; font-size: 26px; font-weight: 800; }
    .sub-kpi { color: #58a6ff; font-size: 13px; margin-top: 5px; font-weight: 500; }
    
    /* BARRA DE PROGRESSO CUSTOM */
    .progress-bg { background-color: #30363d; border-radius: 10px; height: 8px; width: 100%; margin-top: 15px; }
    .progress-fill { 
        background: linear-gradient(90deg, #58a6ff 0%, #00f2ff 100%); 
        height: 8px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 242, 255, 0.5); 
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LIMPEZA ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() in ["", "-", "nan", "DIV/0"]: return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    v = re.sub(r'[^0-9\.\-]', '', v)
    try: return float(v)
    except: return 0.0

def mapear_divisional(cd_bruto):
    # Alterado: se for nulo, retorna string vazia em vez de None
    if pd.isna(cd_bruto) or str(cd_bruto).strip() in ["", "nan", "None", "0", "0.0"]: 
        return "Indefinido" 
    
    try:
        s_cd = str(cd_bruto).split('.')[0]
        cd = int(re.sub(r'\D', '', s_cd))
    except: 
        return "Indefinido" # Alterado de None para string
    
    if cd in [590, 300, 50]: return 'Renato Nesello'
    elif cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
    elif cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    
    return 'Outros'

@st.cache_data(ttl=300)
def load_data():
    SHEET_ID = "1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI"
    GID_MAIN = "1358149674"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID_MAIN}"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    for col in ['tipo', 'semestre', 'cd', 'local']:
        if col in df.columns: df[col] = df[col].astype(str).replace('nan', '')
    return df

try:
    df_raw = load_data().copy()

    # DADOS FIXOS 2024
    df_2024 = pd.DataFrame([
        {"tipo_clean": "CD", "semestre": "1º semestre", "v_24": -9415271},
        {"tipo_clean": "CD", "semestre": "2º semestre", "v_24": -5379088},
        {"tipo_clean": "CROSS", "semestre": "1º semestre", "v_24": -2183},
        {"tipo_clean": "CROSS", "semestre": "2º semestre", "v_24": -1633},
        {"tipo_clean": "DQS", "semestre": "1º semestre", "v_24": -269835},
        {"tipo_clean": "DQS", "semestre": "2º semestre", "v_24": 268613},
        {"tipo_clean": "LV", "semestre": "1º semestre", "v_24": -619830},
        {"tipo_clean": "LV", "semestre": "2º semestre", "v_24": -2509390},
    ])

    # SIDEBAR
    with st.sidebar:
        st.header("⚙️ Filtros")
        if st.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()
        df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional).astype(str)
        tipos_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        divs_sel = st.multiselect("Divisional", options=sorted([x for x in df_raw['divisional'].unique() if x not in ['None','nan']]))

    # PROCESSAMENTO
    def get_col(s): return next((c for c in df_raw.columns if s in c), None)
    c_fat, c_1c, c_fal = get_col('faturam'), get_col('1__ciclo'), get_col('falta_vol')
    
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor)
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor)
    df_raw['v_fal'] = df_raw[c_fal].apply(limpar_valor)
    df_raw['is_fin'] = df_raw['v_1c'] != 0
    
    df_filt = df_raw.copy()
    if tipos_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(tipos_sel)]
    if divs_sel: df_filt = df_filt[df_filt['divisional'].isin(divs_sel)]

    # --- TÍTULO ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # --- CARDS KPI (ESTILO FIGMA) ---
    p1c = df_filt['v_1c'].sum(); vfal = df_filt['v_fal'].sum(); fat = df_filt['v_fat'].sum()
    consolidada = p1c + vfal
    p_global = (abs(consolidada)/fat*100) if fat > 0 else 0
    perc_fin = (df_filt['is_fin'].sum()/len(df_filt)*100) if len(df_filt)>0 else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {consolidada:,.0f}</div><div class="sub-kpi">1C + Falta Vol</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Perda Global</div><div class="value-kpi">{p_global:.3f}%</div><div class="sub-kpi">Sobre Faturamento</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Falta Vol</div><div class="value-kpi">{int(vfal):,}</div><div class="sub-kpi">Itens Pendentes</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'''<div class="card-kpi"><div class="label-kpi">Conclusão</div><div class="value-kpi">{perc_fin:.1f}%</div>
        <div class="progress-bg"><div class="progress-fill" style="width: {perc_fin}%"></div></div></div>''', unsafe_allow_html=True)

    # --- COMPARATIVO YoY ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📊 Ver Comparativo Ano Anterior (YoY)", expanded=False):
        res_at = df_filt.groupby(['tipo_clean', 'semestre'])['v_1c'].sum().reset_index()
        df_c = pd.merge(res_at, df_2024, on=['tipo_clean', 'semestre'], how='left').fillna(0)
        df_c['Dif'] = df_c['v_1c'] - df_c['v_24']
        st.table(df_c.style.format({'v_1c': 'R$ {:,.2f}', 'v_24': 'R$ {:,.2f}', 'Dif': 'R$ {:,.2f}'}))

    # --- GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1])
    
    with g1:
        st.subheader("📍 Perda por Gerência")
        df_pie = df_filt[~df_filt['divisional'].isin(['None','nan',''])]
        fig_p = px.pie(df_pie, values=df_pie['v_1c'].abs(), names='divisional', hole=0.7, color_discrete_sequence=px.colors.sequential.Cyan_r)
        fig_p.update_layout(template="plotly_dark", height=350, showlegend=True, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_p, use_container_width=True)

    with g2:
        st.subheader("🏢 Saúde por CD")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        fig_t = px.treemap(df_tree, path=['divisional', 'cd'], values=df_tree['v_1c'].abs(), color='v_1c', color_continuous_scale='RdBu_r')
        fig_t.update_layout(template="plotly_dark", height=350, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_t, use_container_width=True)

    # --- TABELA FINAL ---
    st.subheader("📋 Detalhamento Operacional")
    df_tab = df_filt.copy()
    df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
    df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '%', 'v_fal', 'is_fin']]

    def styler(row):
        color = '#641e1e' if row['v_1c'] < 0 else '#1e4620'
        text = '#ff9999' if row['v_1c'] < 0 else '#99ff99'
        return [f'background-color: {color}; color: {text}; font-weight: bold' if c in ['v_1c', '%', 'v_fal'] else '' for c in row.index]

    st.dataframe(df_ex.style.apply(styler, axis=1), column_config={
        "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
        "%": st.column_config.NumberColumn("%", format="%.3f%%"),
        "v_fal": st.column_config.NumberColumn("Falta", format="%.0f"),
        "is_fin": st.column_config.CheckboxColumn("Fim")
    }, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro: {e}")