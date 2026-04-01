import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS DEFINITIVA (NEON v4) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    
    /* Header Custom */
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 1.5rem; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
    }
    .header-title { color: white !important; font-size: 28px !important; font-weight: 800 !important; margin:0; }

    /* Estilo dos Cards KPI Neon */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; text-align: center;
        min-height: 150px; border-bottom: 3px solid #00d2ff;
        transition: transform 0.3s;
    }
    .card-kpi:hover { transform: translateY(-5px); border-color: #00f2ff; }
    
    .label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .value-kpi { color: #f0f6fc; font-size: 26px; font-weight: 800; margin: 8px 0; }
    .sub-kpi { color: #00d2ff; font-size: 13px; font-weight: 500; }

    /* Progress Bar (Card Evolução) */
    .p-bar-bg { background-color: #30363d; border-radius: 5px; height: 8px; width: 100%; margin-top: 15px; }
    .p-bar-fill { 
        background: linear-gradient(90deg, #00d2ff, #00f2ff); 
        height: 8px; border-radius: 5px; box-shadow: 0 0 10px #00d2ff; 
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE SUPORTE ---
def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan", "DIV/0"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

def mapear_divisional(cd):
    if pd.isna(cd) or str(cd).strip() in ["", "nan", "0"]: return "Indefinido"
    try:
        n_cd = int(re.sub(r'\D', '', str(cd).split('.')[0]))
    except: return "Indefinido"
    if n_cd in [590, 300, 50]: return 'Renato Nesello'
    elif n_cd in [2650, 994, 991, 1100, 1500, 1800, 1250]: return 'Antônio Paiva'
    elif n_cd in [350, 5200, 2900, 94, 490, 550, 2500, 1440]: return 'Christian'
    elif n_cd in [204, 2489, 97, 549, 2599, 1116, 1889, 389, 1879, 299, 1899, 2989, 5589, 1450, 49, 2999, 2099, 985, 93, 5289, 5299, 2649, 893, 5599, 1869, 1390]: return 'Mileide'
    return 'Outros'

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Filtros")
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
        t_sel = st.multiselect("Tipo de Processo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Gerente Divisional", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    # Mapeamento Dinâmico de Colunas
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor)
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor)
    df_raw['v_falta'] = df_raw[c_fal].apply(limpar_valor)
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # Métricas para os Cards
    p1c = df_filt['v_1c'].sum()
    v_falta_total = df_filt['v_falta'].sum()
    faturamento = df_filt['v_fat'].sum()
    perda_consolidada = p1c + v_falta_total
    
    perc_global = (abs(perda_consolidada) / faturamento * 100) if faturamento > 0 else 0
    perc_falta_sobre_perda = (v_falta_total / perda_consolidada * 100) if perda_consolidada != 0 else 0
    evolucao = (df_filt['is_fin'].sum() / len(df_filt) * 100) if len(df_filt) > 0 else 0

    # Renderização dos Cards (KPIs Superior)
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_consolidada:,.0f}</div><div class="sub-kpi">Financeiro + Mercadoria</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Perda Global</div><div class="value-kpi">{perc_global:.3f}%</div><div class="sub-kpi">Sobre Faturamento</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Volume Falta</div><div class="value-kpi">R$ {v_falta_total:,.0f}</div><div class="sub-kpi">{abs(perc_falta_sobre_perda):.1f}% do Total de Perdas</div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Evolução / Conclusão</div><div class="value-kpi">{evolucao:.1f}%</div><div class="p-bar-bg"><div class="p-bar-fill" style="width:{evolucao}%"></div></div></div>', unsafe_allow_html=True)

    # --- SEÇÃO DO MEIO: GRÁFICOS (BARRAS ACUMULADO + TREEMAP) ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.1])

    with g1:
        st.subheader("📊 Resultado Consolidado por Processo")
        df_proc = df_filt.copy()
        df_proc['res_total'] = df_proc['v_1c'] + df_proc['v_falta']
        df_plot = df_proc.groupby('tipo_clean')['res_total'].sum().reset_index()
        df_plot['v_abs'] = df_plot['res_total'].abs() # Para a barra crescer para cima
        
        fig_b = px.bar(df_plot, x='tipo_clean', y='v_abs', text='res_total', color='tipo_clean',
                       color_discrete_map={'CD': '#3a7bd5', 'LV': '#7000ff', 'DQS': '#00f2ff'})
        fig_b.update_traces(width=0.5, texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=400, margin=dict(t=40, b=0, l=0, r=0), 
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, yaxis_visible=False)
        st.plotly_chart(fig_b, use_container_width=True)

    with g2:
        st.subheader("🏢 Status de Saúde (Tipo > CD)")
        df_tree = df_filt.copy()
        df_tree['res_total'] = df_tree['v_1c'] + df_tree['v_falta']
        df_tree = df_tree[df_tree['res_total'] != 0].copy()
        df_tree['cd_label'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_label'], values=df_tree['res_total'].abs(), 
                           color='tipo_clean', color_discrete_map={'CD': '#0040ff', 'LV': '#aa00ff', 'DQS': '#00d2ff'})
        fig_t.update_traces(textinfo="label+value", texttemplate="<span style='font-size:18px'><b>%{label}</b></span><br>R$ %{value:,.0f}")
        fig_t.update_layout(template="plotly_dark", height=400, margin=dict(t=20, b=10, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_t, use_container_width=True)

    # --- SEÇÃO FINAL: TABELA E PIZZA (BASE LADO A LADO) ---
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2 = st.columns([3, 1.2])

    with t1:
        st.subheader("📋 Detalhamento Operacional")
        df_tab = df_filt.copy()
        df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '%', 'v_falta', 'is_fin']]

        def styler(row):
            bg = 'background-color: #451a1a;' if row['v_1c'] < 0 else 'background-color: #1a4523;'
            return [bg] * len(row)

        st.dataframe(df_ex.style.apply(styler, axis=1), column_config={
            "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
            "%": st.column_config.NumberColumn("%", format="%.4f%%"),
            "v_falta": st.column_config.NumberColumn("Falta", format="R$ %.0f"),
            "is_fin": "Fim"
        }, use_container_width=True, hide_index=True, height="content")

    with t2:
        st.subheader("📍 Perda / Gerência")
        df_p = df_filt[df_filt['divisional'] != "Indefinido"]
        fig_p = px.pie(df_p, values=df_p['v_1c'].abs(), names='divisional', hole=0.7, 
                       color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"])
        fig_p.update_layout(template="plotly_dark", height=500, margin=dict(t=50, b=50, l=0, r=0), 
                            paper_bgcolor='rgba(0,0,0,0)', showlegend=True,
                            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_p, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Erro ao processar BI: {e}")