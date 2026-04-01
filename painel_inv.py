import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- CSS (Estilo do Print com Ajuste de Cards) ---
st.markdown("""
    <style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0rem !important; margin-top: -45px !important; }
    [data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
    
    .header-box {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 10px; border-radius: 5px; text-align: center;
        margin-bottom: 20px; border-bottom: 3px solid #00d2ff;
    }
    .header-title { color: white !important; font-size: 24px !important; font-weight: 800 !important; letter-spacing: 2px; }

    .card-kpi {
        background: #1c222d; border: 1px solid #313d4f; border-radius: 10px;
        padding: 15px; text-align: center; border-top: 3px solid #00d2ff;
        min-height: 100px;
    }
    .value-kpi { color: white; font-size: 22px; font-weight: 900; margin: 0; }
    .label-kpi { color: #8b949e; font-size: 11px; text-transform: uppercase; margin-bottom: 5px; }
    .sub-value { color: #00d2ff; font-size: 13px; font-weight: 700; }
    </style>
""", unsafe_allow_html=True)

# --- ENGINE DE DADOS ---
@st.cache_data(ttl=60)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

try:
    df_raw = load_data().copy()
    
    # Mapeamento de colunas financeiras originais
    df_raw['v_1c'] = df_raw['1__ciclo'].apply(limpar_valor) if '1__ciclo' in df_raw.columns else 0.0
    df_raw['v_falta'] = df_raw['falta_vol'].apply(limpar_valor) if 'falta_vol' in df_raw.columns else 0.0
    df_raw['v_fat'] = df_raw['faturamento'].apply(limpar_valor) if 'faturamento' in df_raw.columns else 0.0
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper()
    df_raw['is_fin'] = df_raw['v_1c'] != 0

    # --- FILTROS SIDEBAR ---
    with st.sidebar:
        st.markdown("### 📊 Gerenciamento")
        if st.button("🔄 Atualizar Dados"):
            st.cache_data.clear()
            st.rerun()
        t_sel = st.multiselect("Tipo", options=sorted(df_raw['tipo_clean'].unique()))

    df_filt = df_raw.copy()
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]

    # --- TÍTULO ---
    st.markdown('<div class="header-box"><p class="header-title">PAINEL FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # --- KPIS REESTRUTURADOS ---
    v_1c = df_filt['v_1c'].sum()
    v_falta = df_filt['v_falta'].sum()
    v_perda_ano = v_1c + v_falta
    fat_total = df_filt['v_fat'].sum()
    health_perc = (abs(v_perda_ano) / fat_total * 100) if fat_total > 0 else 0.0
    
    total_un = len(df_filt)
    fechadas = df_filt['is_fin'].sum()
    pendentes = total_un - fechadas

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(f'<div class="card-kpi"><p class="label-kpi">1º Ciclo</p><p class="value-kpi">R$ {v_1c:,.0f}</p></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Falta Vol</p><p class="value-kpi">R$ {v_falta:,.0f}</p></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Perda Ano</p><p class="value-kpi">R$ {v_perda_ano:,.0f}</p></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="card-kpi"><p class="label-kpi">Health %</p><p class="value-kpi">{health_perc:.3f}%</p></div>', unsafe_allow_html=True)
    with k5: 
        # Card Unificado: Status das Unidades
        st.markdown(f'''<div class="card-kpi"><p class="label-kpi">Status Unidades</p><p class="value-kpi">{total_un}</p>
                    <p class="sub-value"><span style="color:#00d2ff">Fin: {fechadas}</span> | <span style="color:#ff4b4b">Pend: {pendentes}</span></p></div>''', unsafe_allow_html=True)

    # --- GRÁFICOS CENTRAIS ---
    g1, g2 = st.columns([1.2, 1])
    
    with g1:
        st.markdown("**Perdas vs. Estornos**")
        df_g = df_filt.groupby('tipo_clean')[['v_1c', 'v_falta']].sum().reset_index()
        df_g['total'] = df_g['v_1c'] + df_g['v_falta']
        
        # Correção do gráfico: valores negativos para baixo
        fig = px.bar(df_g, x='tipo_clean', y='total', color='tipo_clean', 
                     color_discrete_map={'CD':'#3a86ff','LV':'#8338ec','DQS':'#06d6a0'},
                     text_auto='.2s')
        
        fig.update_layout(template="plotly_dark", height=380, showlegend=False, 
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                          yaxis_title="R$ Total", xaxis_title="")
        # Inverte o eixo se quiser garantir, mas o Plotly já faz automático se o valor for negativo
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.markdown("**Status de Saúde Treemap**")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_lbl'], values=df_tree['v_1c'].abs(),
                           color='tipo_clean', color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # --- TABELA ---
    st.markdown("**Detalhamento Operacional**")
    df_tab = df_filt.copy()
    df_tab['cd_t'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
    df_show = df_tab[['tipo_clean', 'cd_t', 'local', 'v_1c', '%', 'v_falta', 'is_fin']].reset_index(drop=True)
    
    def style_rows(row):
        color = '#451a1a' if row['v_1c'] < 0 else '#1a4523'
        return [f'background-color: {color}'] * len(row)

    st.dataframe(df_show.style.apply(style_rows, axis=1), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro detectado: {e}")