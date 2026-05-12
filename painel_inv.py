import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Prevenção | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS (Layout Corrigido) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
    
    /* Aumentei o padding inferior da barra azul para os cards não cobrirem o texto */
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 2rem 1rem 5rem 1rem; 
        border-radius: 0 0 15px 15px; text-align: center;
        box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
        position: relative; z-index: 1;
    }
    .header-title { color: white !important; font-size: 28px !important; font-weight: 900 !important; margin:0; text-transform: uppercase; }

    /* Reduzi a margem negativa para um encaixe mais elegante */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 10px; text-align: center;
        border-bottom: 4px solid #00d2ff;
        margin-top: -60px; 
        height: 140px; display: flex; flex-direction: column; 
        justify-content: center; align-items: center; box-sizing: border-box;
        position: relative; z-index: 100;
    }
    .label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .value-kpi { color: #f0f6fc; font-size: 21px !important; font-weight: 900 !important; margin: 5px 0; letter-spacing: -1px; }
    .sub-kpi { color: #00d2ff; font-size: 11px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE LIMPEZA DE DADOS ---
def limpar_valor(v):
    if pd.isna(v): return 0.0
    val = str(v).upper().replace('R$', '').replace('\xa0', '').strip()
    if val in ["", "-", "NAN"]: return 0.0
    is_negative = '-' in val or '(' in val
    val = re.sub(r'[^0-9\.,]', '', val)
    if not val: return 0.0
    if '.' in val and ',' in val:
        val = val.replace('.', '').replace(',', '.')
    elif ',' in val:
        val = val.replace(',', '.')
    try:
        res = float(val)
        return -res if is_negative else res
    except: return 0.0

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # Identifica dinamicamente a coluna de Unidade ou CD (Garante que não dê erro de Index)
    col_unidade = next((c for c in df_raw.columns if c in ['cd', 'unidade']), df_raw.columns[0])
    
    # Mapeamento Dinâmico de Colunas de Valores
    c_total = next((c for c in df_raw.columns if 'total_custo_inv' in c), None)
    c_falta = next((c for c in df_raw.columns if 'falta_vol' in c), None)
    c_trans = next((c for c in df_raw.columns if 'transporte' in c), None)
    c_sac   = next((c for c in df_raw.columns if 'sac' in c), None)
    c_fat   = next((c for c in df_raw.columns if 'faturamento' in c), None)

    # Conversão de Valores
    df_raw['v_total'] = df_raw[c_total].apply(limpar_valor) if c_total else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_valor) if c_falta else 0.0
    df_raw['v_trans'] = df_raw[c_trans].apply(limpar_valor) if c_trans else 0.0
    df_raw['v_sac']   = df_raw[c_sac].apply(limpar_valor) if c_sac else 0.0
    df_raw['v_fat']   = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0

    # LÓGICA DO CONSOLIDADO: Total Custo + Falta Volume
    df_raw['v_consolidado'] = df_raw['v_total'] + df_raw['v_falta']

    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO INV PREVENÇÃO DE PERDAS 2026</p></div>', unsafe_allow_html=True)

    # Cálculos Globais
    total_cons = df_raw['v_consolidado'].sum()
    total_falta = df_raw['v_falta'].sum()
    total_trans = df_raw['v_trans'].sum()
    total_sac = df_raw['v_sac'].sum()
    total_fat = df_raw['v_fat'].sum()
    
    # --- 6 CARDS KPI ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {total_cons:,.0f}</div><div class="sub-kpi">Total + Falta</div></div>', unsafe_allow_html=True)
    
    with c2:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Falta Volume</div><div class="value-kpi">R$ {total_falta:,.0f}</div><div class="sub-kpi">Divergência Estoque</div></div>', unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="card-kpi" style="border-bottom: 4px solid #ffaa00;"><div class="label-kpi">Custo Transporte</div><div class="value-kpi">R$ {total_trans:,.0f}</div><div class="sub-kpi">Logística Inv.</div></div>', unsafe_allow_html=True)

    with c4:
        st.markdown(f'<div class="card-kpi" style="border-bottom: 4px solid #ff4b4b;"><div class="label-kpi">Custo SAC</div><div class="value-kpi">R$ {total_sac:,.0f}</div><div class="sub-kpi">Atendimento</div></div>', unsafe_allow_html=True)

    with c5:
        perc = (total_cons / total_fat * 100) if total_fat != 0 else 0
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Perda</div><div class="value-kpi">{perc:.3f}%</div><div class="sub-kpi">Sobre Fat.</div></div>', unsafe_allow_html=True)

    with c6:
        uds = len(df_raw[df_raw['v_total'] != 0])
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Unidades</div><div class="value-kpi">{uds}</div><div class="sub-kpi">Com Inventário</div></div>', unsafe_allow_html=True)

    # --- GRÁFICOS ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1])
    
    with g1:
        st.subheader("📊 Distribuição por Coluna")
        df_pizza = pd.DataFrame({
            'Categoria': ['Falta Volume', 'Transporte', 'SAC'],
            'Valor': [abs(total_falta), abs(total_trans), abs(total_sac)]
        })
        fig_pi = px.pie(df_pizza, values='Valor', names='Categoria', hole=0.6, 
                        color_discrete_sequence=['#00d2ff', '#ffaa00', '#ff4b4b'])
        fig_pi.update_layout(template="plotly_dark", height=400, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pi, use_container_width=True)

    with g2:
        st.subheader("📋 Detalhamento da Base")
        # Correção do erro vermelho: Usa col_unidade dinamicamente
        df_exib = df_raw[[col_unidade, 'v_total', 'v_falta', 'v_consolidado', 'v_trans', 'v_sac']].copy()
        
        st.dataframe(
            df_exib,
            column_config={
                col_unidade: "ID / UNIDADE",
                "v_total": st.column_config.NumberColumn("TOTAL CUSTO", format="R$ %.2f"),
                "v_falta": st.column_config.NumberColumn("FALTA VOL", format="R$ %.2f"),
                "v_consolidado": st.column_config.NumberColumn("CONSOLIDADO", format="R$ %.2f"),
                "v_trans": st.column_config.NumberColumn("TRANSPORTE", format="R$ %.2f"),
                "v_sac": st.column_config.NumberColumn("SAC", format="R$ %.2f"),
            },
            use_container_width=True, hide_index=True
        )

except Exception as e:
    st.error(f"⚠️ Erro ao processar dados: {e}")