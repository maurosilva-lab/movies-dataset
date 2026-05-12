import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Prevenção | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS CORRIGIDA ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117 !important; }
    .main { padding: 0rem !important; }
    
    .block-container {
        padding-top: 2.5rem !important; 
        padding-bottom: 1rem !important;
    }
    
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        padding: 1rem; border-radius: 0 0 15px 15px; text-align: center;
        margin-bottom: 0px !important; 
        box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
        position: relative;
        z-index: 1; /* <-- Mantém a barra azul no fundo */
    }
    .header-title { color: white !important; font-size: 26px !important; font-weight: 800 !important; margin:0; }

    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 10px; text-align: center;
        border-bottom: 4px solid #00d2ff;
        margin-top: -105px; 
        height: 150px; display: flex; flex-direction: column; 
        justify-content: center; align-items: center; box-sizing: border-box;
        position: relative;
        z-index: 100; /* <-- FIX: Garante que os cards fiquem NA FRENTE da barra azul */
    }
    .label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
    .value-kpi { color: #f0f6fc; font-size: 22px !important; font-weight: 900 !important; margin: 5px 0; letter-spacing: -1px; }
    .sub-kpi { color: #00d2ff; font-size: 11px; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE LIMPEZA BLINDADA ---
def limpar_valor(v):
    if pd.isna(v): return 0.0
    if isinstance(v, (int, float)): return float(v)
    
    # Limpa espaços invisíveis e converte para string uppercase
    val = str(v).upper().replace('R$', '').replace('\xa0', '').strip()
    if val in ["", "-", "NAN"]: return 0.0
    
    # Verifica se é negativo (ex: "-R$ 100" ou "(100)")
    is_negative = '-' in val or ('(' in val and ')' in val)
    
    # Remove tudo que não for número, ponto ou vírgula
    val = re.sub(r'[^0-9\.,]', '', val)
    if not val: return 0.0
    
    # Trata formato BR (1.234,56 -> 1234.56)
    if '.' in val and ',' in val:
        if val.rfind(',') > val.rfind('.'): # Vírgula é o decimal
            val = val.replace('.', '').replace(',', '.')
        else: # Ponto é o decimal
            val = val.replace(',', '')
    elif ',' in val:
         val = val.replace(',', '.')
         
    try: 
        result = float(val)
        return -result if is_negative else result
    except: 
        return 0.0

def mapear_divisional(cd):
    if pd.isna(cd) or str(cd).strip() in ["", "nan", "0"]: return "Indefinido"
    try: n_cd = int(re.sub(r'\D', '', str(cd).split('.')[0]))
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
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip() if 'tipo' in df_raw.columns else 'INDEFINIDO'
    
    # Tratamento da coluna CD/Unidade
    col_cd = next((c for c in df_raw.columns if c in ['cd', 'unidade']), None)
    if col_cd:
        df_raw['cd'] = df_raw[col_cd]
        df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    else:
        df_raw['cd'] = '0'
        df_raw['divisional'] = 'Indefinido'
    
    # MAPEAMENTO ROBUSTO (Se a palavra chave existir na coluna, ele captura)
    c_total = next((c for c in df_raw.columns if 'total' in c and 'custo' in c), None)
    c_falta = next((c for c in df_raw.columns if 'falta' in c), None)
    c_liq   = next((c for c in df_raw.columns if 'liq' in c), None)
    c_trans = next((c for c in df_raw.columns if 'transp' in c), None)
    c_fat   = next((c for c in df_raw.columns if 'fat' in c), None)

    # Conversão 
    df_raw['v_total'] = df_raw[c_total].apply(limpar_valor) if c_total else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_valor) if c_falta else 0.0
    df_raw['v_liq']   = df_raw[c_liq].apply(limpar_valor) if c_liq else 0.0
    df_raw['v_trans'] = df_raw[c_trans].apply(limpar_valor) if c_trans else 0.0
    df_raw['v_fat']   = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    
    df_raw['is_fin'] = df_raw['v_total'] != 0

    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        
        s_sel = st.multiselect("Filtrar Semestre", options=sorted(df_raw['semestre'].dropna().unique())) if 'semestre' in df_raw.columns else []
        t_sel = st.multiselect("Filtrar por Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Filtrar Gerente", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    df_filt = df_raw.copy()
    if s_sel: df_filt = df_filt[df_filt['semestre'].isin(s_sel)]
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO INV PREVENÇAO DE PERDAS 2026</p></div>', unsafe_allow_html=True)

    # CÁLCULOS
    total_bruto = df_filt['v_total'].sum()
    total_falta = df_filt['v_falta'].sum()
    total_liq   = df_filt['v_liq'].sum()
    total_trans = df_filt['v_trans'].sum()
    total_fat   = df_filt['v_fat'].sum()
    
    perc_geral_perdas = (total_liq / total_fat * 100) if total_fat != 0 else 0
    total_uds = len(df_filt)
    fechadas = df_filt['is_fin'].sum()

    # --- COMPARAÇÃO COM 2025 ---
    dados_2025 = pd.DataFrame([
        {'tipo': 'CD', 'semestre': '1º semestre', 'valor': 9415271}, {'tipo': 'CD', 'semestre': '2º semestre', 'valor': 5379088},
        {'tipo': 'CROSS', 'semestre': '1º semestre', 'valor': 2183}, {'tipo': 'CROSS', 'semestre': '2º semestre', 'valor': 1633},
        {'tipo': 'DQS', 'semestre': '1º semestre', 'valor': 269835}, {'tipo': 'DQS', 'semestre': '2º semestre', 'valor': -268613},
        {'tipo': 'LV', 'semestre': '1º semestre', 'valor': 619830}, {'tipo': 'LV', 'semestre': '2º semestre', 'valor': 2509390}
    ])

    tipos_presentes = df_filt['tipo_clean'].unique()
    if 'semestre' in df_filt.columns:
        semestres_presentes = df_filt['semestre'].astype(str).str.lower().str.strip().unique()
        dados_2025['semestre_clean'] = dados_2025['semestre'].str.lower().str.strip()
        df_2025_filt = dados_2025[(dados_2025['tipo'].isin(tipos_presentes)) & (dados_2025['semestre_clean'].isin(semestres_presentes))]
    else:
        df_2025_filt = dados_2025[dados_2025['tipo'].isin(tipos_presentes)]

    perda_2025_abs = df_2025_filt['valor'].sum()
    var_perc = ((abs(total_liq) - perda_2025_abs) / abs(perda_2025_abs)) * 100 if perda_2025_abs != 0 else 0

    if var_perc < 0:
        texto_var = f'<span style="color:#3fb950; font-weight:bold;">▼ {abs(var_perc):.1f}% (Redução)</span> vs 2025'
    elif var_perc > 0:
        texto_var = f'<span style="color:#ff4b4b; font-weight:bold;">▲ {var_perc:.1f}% (Aumento)</span> vs 2025'
    else:
        texto_var = "Igual a 2025"

    # --- 6 CARDS KPI ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1: 
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Custo Inv Total</div><div class="value-kpi">R$ {total_bruto:,.0f}</div><div class="sub-kpi">Valor Bruto</div></div>', unsafe_allow_html=True)
    with c2: 
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Falta Volume</div><div class="value-kpi">R$ {total_falta:,.0f}</div><div class="sub-kpi">Divergência de Estoque</div></div>', unsafe_allow_html=True)
    with c3: 
        st.markdown(f'<div class="card-kpi" style="border-bottom: 4px solid #3fb950;"><div class="label-kpi">Inv. Líquido (Real)</div><div class="value-kpi">R$ {total_liq:,.0f}</div><div class="sub-kpi">{texto_var}</div></div>', unsafe_allow_html=True)
    with c4: 
        st.markdown(f'<div class="card-kpi" style="border-bottom: 4px solid #ffaa00;"><div class="label-kpi">Custo Transporte</div><div class="value-kpi">R$ {total_trans:,.0f}</div><div class="sub-kpi">Despesa Informativa</div></div>', unsafe_allow_html=True)
    with c5: 
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Perda Líquida</div><div class="value-kpi">{perc_geral_perdas:.3f}%</div><div class="sub-kpi">Sobre Faturamento</div></div>', unsafe_allow_html=True)
    with c6: 
        perc_finalizadas = (fechadas / total_uds * 100) if total_uds > 0 else 0
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Total Unidades</div><div class="value-kpi">{total_uds}</div><div class="sub-kpi">{perc_finalizadas:.1f}% Finalizadas</div></div>', unsafe_allow_html=True)

    # --- GRÁFICOS DO MEIO ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.1])
    
    with g1:
        st.subheader("📊 Resultado Líquido por Tipo")
        df_plot = df_filt.groupby('tipo_clean')['v_liq'].sum().reset_index()
        fig_b = px.bar(df_plot, x='tipo_clean', y=df_plot['v_liq'].abs(), text='v_liq', color='tipo_clean', 
                       color_discrete_map={'CD':'#3a7bd5','LV':'#7000ff','DQS':'#00f2ff'})
        fig_b.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=380, showlegend=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_b, use_container_width=True)

    with g2:
        st.subheader("🏢 Status de Saúde (Inv Líquido)")
        df_tree = df_filt[df_filt['v_liq'] != 0].copy()
        if not df_tree.empty:
            df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
            fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_lbl'], values=df_tree['v_liq'].abs(), color='tipo_clean', 
                               color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
            fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
            fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=20, b=10, l=0, r=0))
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("Nenhum dado com Resultado Líquido finalizado.")

    # --- BASE DETALHADA ---
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns([3, 1.2])
    
    with b1:
        st.subheader("📋 Detalhamento (Líquido = Total Custo - Falta Vol)")
        df_tab = df_filt.copy()
        df_tab['%_liq'] = (df_tab['v_liq'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd_t'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        cols_exibicao = ['tipo_clean', 'divisional', 'cd_t']
        if 'local' in df_tab.columns: cols_exibicao.append('local')
        cols_exibicao.extend(['v_total', 'v_falta', 'v_liq', 'v_trans', '%_liq', 'is_fin'])
        
        df_ex = df_tab[cols_exibicao]
        st.dataframe(
            df_ex.style.apply(lambda r: ['background-color: #451a1a' if r['v_liq'] < 0 else 'background-color: #1a4523']*len(r), axis=1),
            column_config={
                "tipo_clean": "TIPO", "divisional": "GERENTE", "cd_t": "UNIDADE", "local": "LOCAL",
                "v_total": st.column_config.NumberColumn("TOTAL CUSTO", format="R$ %.2f"),
                "v_falta": st.column_config.NumberColumn("FALTA VOL.", format="R$ %.2f"),
                "v_liq": st.column_config.NumberColumn("INV. LÍQUIDO", format="R$ %.2f"), 
                "v_trans": st.column_config.NumberColumn("TRANSPORTE", format="R$ %.2f"), 
                "%_liq": st.column_config.NumberColumn("% PERDA", format="%.3f%%"), 
                "is_fin": "FINALIZADA"
            },
            use_container_width=True, hide_index=True, height="content"
        )
        
    with b2:
        st.subheader("📍 Perda / Gerente")
        df_pi = df_filt[(df_filt['divisional'] != "Indefinido") & (df_filt['v_liq'] != 0)]
        if not df_pi.empty:
            fig_pi = px.pie(df_pi, values=df_pi['v_liq'].abs(), names='divisional', hole=0.7, color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"])
            fig_pi.update_layout(template="plotly_dark", height=450, margin=dict(t=50, b=50, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_pi, use_container_width=True)
        else:
            st.info("Sem dados suficientes para o gráfico.")

except Exception as e:
    st.error(f"⚠️ Erro crítico: {e}")