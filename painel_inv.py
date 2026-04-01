import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS DEFINITIVA (NEON v5 - Unidades e Targets) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 1.5rem; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
    }
    .header-title { color: white !important; font-size: 28px !important; font-weight: 800 !important; margin:0; }

    /* Cards KPI */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 15px; text-align: center;
        min-height: 130px; border-bottom: 3px solid #00d2ff;
    }
    .label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; }
    .value-kpi { color: #f0f6fc; font-size: 24px; font-weight: 800; margin: 5px 0; }
    .sub-kpi { color: #00d2ff; font-size: 12px; font-weight: 500; }

    /* Barra de Progresso Estilo "Target" (Inspirado no print) */
    .target-container {
        background: #21262d; border-radius: 4px; height: 30px; 
        position: relative; overflow: hidden; margin: 10px 0;
        display: flex; align-items: center; justify-content: center;
    }
    .target-fill {
        background: #00d2ff; height: 100%; position: absolute; left: 0;
        box-shadow: 0 0 10px #00d2ff; z-index: 1;
    }
    .target-text { color: white; font-weight: bold; z-index: 2; font-size: 14px; }
    .target-line {
        position: absolute; height: 100%; width: 2px; 
        background: #00f2ff; z-index: 3; box-shadow: 0 0 8px #00f2ff;
    }
    .target-label { font-size: 10px; color: #8b949e; margin-top: -5px; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

@st.cache_data(ttl=300)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1iaHnigQGOH5w4xFlZXN0cXYSZlLqPuHE1Pdsgy0XSdI/export?format=csv&gid=1358149674"
    df = pd.read_csv(url).dropna(how='all')
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c).strip().lower()) for c in df.columns]
    return df

try:
    df_raw = load_data().copy()
    
    # Sidebar e Tratamento (Simplificado)
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)
    c_fal = next((c for c in df_raw.columns if 'falta_vol' in c), None)
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor)
    df_raw['v_falta'] = df_raw[c_fal].apply(limpar_valor)
    df_raw['is_fin'] = df_raw['v_1c'] != 0 # Consideramos fechado se tiver valor no 1C

    df_filt = df_raw.copy() # (Adicionar lógica de filtros multiselect aqui se desejar)

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # 1. LINHA DE KPIS FINANCEIROS
    k1, k2, k3 = st.columns(3)
    p1c = df_filt['v_1c'].sum()
    vfal = df_filt['v_falta'].sum()
    perda_total = p1c + vfal
    perc_falta = (vfal / perda_total * 100) if perda_total != 0 else 0

    with k1: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_total:,.0f}</div><div class="sub-kpi">1C + Falta Vol</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Volume Falta</div><div class="value-kpi">R$ {vfal:,.0f}</div><div class="sub-kpi">{abs(perc_falta):.1f}% do Total de Perdas</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="card-kpi"><div class="label-kpi">Média por Unidade</div><div class="value-kpi">R$ {perda_total/len(df_filt):,.0f}</div><div class="sub-kpi">Base: {len(df_filt)} Unidades</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. LINHA DE UNIDADES (TOTAL, FECHADO, PENDENTE) - ESTILO PRINT
    u1, u2, u3 = st.columns(3)
    total_uds = len(df_filt)
    fechadas = df_filt['is_fin'].sum()
    pendentes = total_uds - fechadas
    target_pos = 70 # Exemplo: Linha de meta em 70%

    with u1:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Total Unidades</div><div class="value-kpi">{total_uds}</div><div class="sub-kpi">Cadastradas no Sistema</div></div>', unsafe_allow_html=True)
    
    with u2: # Card "Finalizadas" com barra e target
        perc_f = (fechadas/total_uds*100) if total_uds > 0 else 0
        st.markdown(f'''
            <div class="card-kpi">
                <div class="label-kpi">Finalizadas</div>
                <div class="target-container">
                    <div class="target-fill" style="width: {perc_f}%;"></div>
                    <div class="target-line" style="left: {target_pos}%;"></div>
                    <div class="target-text">{fechadas}</div>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="target-label">0</span>
                    <span class="target-label">today's target</span>
                    <span class="target-label">{total_uds}</span>
                </div>
            </div>
        ''', unsafe_allow_html=True)

    with u3: # Card "Pendentes"
        perc_p = (pendentes/total_uds*100) if total_uds > 0 else 0
        st.markdown(f'''
            <div class="card-kpi">
                <div class="label-kpi">Pendentes</div>
                <div class="target-container" style="background: #2a1b1b;">
                    <div class="target-fill" style="width: {perc_p}%; background: #ff4b4b; box-shadow: 0 0 10px #ff4b4b;"></div>
                    <div class="target-line" style="left: {target_pos}%; background: #ff4b4b;"></div>
                    <div class="target-text">{pendentes}</div>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span class="target-label">0</span>
                    <span class="target-label">today's target</span>
                    <span class="target-label">{total_uds}</span>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
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