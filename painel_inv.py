import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Prevenção | BI Executive", page_icon="📊")

## --- ESTILIZAÇÃO CSS ---
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
    margin-bottom: 25px !important;
    box-shadow: 0 4px 20px rgba(0, 210, 255, 0.3);
    position: relative;
    z-index: 99;
}
.header-title { color: white !important; font-size: 26px !important; font-weight: 800 !important; margin:0; }

.card-kpi {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 15px; text-align: center;
    border-bottom: 4px solid #00d2ff;
    margin-top: 0px; 
}
.label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }
.value-kpi { color: #f0f6fc; font-size: 22px !important; font-weight: 900 !important; margin: 5px 0; letter-spacing: -1px; }
.sub-kpi { color: #00d2ff; font-size: 11px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def limpar_valor(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "nan"]: return 0.0
    val = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    val = re.sub(r'[^0-9\.\-]', '', val)
    try: return float(val)
    except: return 0.0

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
    df_raw['tipo_clean'] = df_raw['tipo'].fillna('').astype(str).str.upper().str.strip()
    df_raw['divisional'] = df_raw['cd'].apply(mapear_divisional)
    df_raw['semestre_clean'] = df_raw['semestre'].fillna('Sem Semestre').astype(str).str.strip()
    
    # 1. MAPEAMENTO DAS COLUNAS
    c_perda_total = next((c for c in df_raw.columns if 'total_custo_inv' in c), None)
    c_falta_vol = next((c for c in df_raw.columns if 'falta_vol' in c), None)
    c_transp = next((c for c in df_raw.columns if 'custo_inv_transporte' in c), None)
    
    c_fat = next((c for c in df_raw.columns if 'faturamento' in c), None)
    c_sac = next((c for c in df_raw.columns if 'sac' in c), None)
    c_1c = next((c for c in df_raw.columns if '1__ciclo' in c), None)

    # 2. LIMPEZA DOS VALORES
    df_raw['v_perda_consol'] = df_raw[c_perda_total].apply(limpar_valor) if c_perda_total else 0.0
    df_raw['v_falta'] = df_raw[c_falta_vol].apply(limpar_valor) if c_falta_vol else 0.0
    df_raw['v_transp'] = df_raw[c_transp].apply(limpar_valor) if c_transp else 0.0
    df_raw['v_sac'] = df_raw[c_sac].apply(limpar_valor) if c_sac else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0 
    
    df_raw['is_fin'] = df_raw['v_perda_consol'] != 0

    with st.sidebar:
        st.header("⚙️ Gerenciamento")
        if st.button("🔄 Atualizar Dados"): st.cache_data.clear(); st.rerun()
        s_sel = st.multiselect("Filtrar Semestre", options=sorted(df_raw['semestre_clean'].unique()))
        t_sel = st.multiselect("Filtrar por Tipo", options=sorted(df_raw['tipo_clean'].unique()))
        d_sel = st.multiselect("Filtrar Gerente", options=sorted([x for x in df_raw['divisional'].unique() if x != "Indefinido"]))

    df_filt = df_raw.copy()
    if s_sel: df_filt = df_filt[df_filt['semestre_clean'].isin(s_sel)]
    if t_sel: df_filt = df_filt[df_filt['tipo_clean'].isin(t_sel)]
    if d_sel: df_filt = df_filt[df_filt['divisional'].isin(d_sel)]

    # --- UI PRINCIPAL ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO INV PREVENÇAO DE PERDAS 2026</p></div>', unsafe_allow_html=True)

    # 3. NOVOS CÁLCULOS DOS TOTAIS
    perda_total = df_filt['v_perda_consol'].sum() 
    vfal = df_filt['v_falta'].sum()
    vtransp = df_filt['v_transp'].sum()
    vsac = df_filt['v_sac'].sum()
    vfat_total = df_filt['v_fat'].sum()
    
    perc_falta = (vfal / perda_total * 100) if perda_total != 0 else 0
    perc_transp = (vtransp / perda_total * 100) if perda_total != 0 else 0
    perc_sac = (vsac / perda_total * 100) if perda_total != 0 else 0
    
    perc_geral_perdas = (perda_total / vfat_total * 100) if vfat_total != 0 else 0
    perc_geral_str = f"{perc_geral_perdas:.3f}".replace('.', ',') + "%"
    
    # CONTAGEM ÚNICA DE FILIAIS
    total_uds = df_filt['cd'].nunique()
    fechadas = df_filt[df_filt['is_fin']]['cd'].nunique()

    # --- LÓGICA DE COMPARAÇÃO 2025 ---
    dados_2025 = pd.DataFrame([
        {'tipo': 'CD', 'semestre': '1º semestre', 'valor': 9415271},
        {'tipo': 'CD', 'semestre': '2º semestre', 'valor': 5379088},
        {'tipo': 'CROSS', 'semestre': '1º semestre', 'valor': 2183},
        {'tipo': 'CROSS', 'semestre': '2º semestre', 'valor': 1633},
        {'tipo': 'DQS', 'semestre': '1º semestre', 'valor': 269835},
        {'tipo': 'DQS', 'semestre': '2º semestre', 'valor': -268613},
        {'tipo': 'LV', 'semestre': '1º semestre', 'valor': 619830},
        {'tipo': 'LV', 'semestre': '2º semestre', 'valor': 2509390}
    ])
    tipos_presentes = df_filt['tipo_clean'].unique()
    if 'semestre_clean' in df_filt.columns:
        semestres_presentes = df_filt['semestre_clean'].str.lower().str.strip().unique()
        dados_2025['semestre_clean'] = dados_2025['semestre'].str.lower().str.strip()
        df_2025_filt = dados_2025[(dados_2025['tipo'].isin(tipos_presentes)) & (dados_2025['semestre_clean'].isin(semestres_presentes))]
    else:
        df_2025_filt = dados_2025[dados_2025['tipo'].isin(tipos_presentes)]

    perda_2025_abs = df_2025_filt['valor'].sum()
    perda_total_abs = abs(perda_total)
    var_perc = ((perda_total_abs - perda_2025_abs) / abs(perda_2025_abs)) * 100 if perda_2025_abs != 0 else 0

    if var_perc < 0:
        texto_var = f'<span style="color:#3fb950; font-weight:bold;">▼ {abs(var_perc):.1f}% (Redução)</span> vs 2025'
    elif var_perc > 0:
        texto_var = f'<span style="color:#ff4b4b; font-weight:bold;">▲ {var_perc:.1f}% (Aumento)</span> vs 2025'
    else:
        texto_var = "Igual a 2025"

    # --- EXIBIÇÃO DOS CARDS ---
    # 1. Damos um pouco mais de peso visual para a c7 (de 1.6 para 1.8)
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1, 1, 1.8])
    estilo_card = "height: 160px; padding: 10px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-sizing: border-box;"

    with c1: 
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi">Perda Consol.</div><div class="value-kpi">R$ {perda_total:,.0f}</div><div class="sub-kpi">{texto_var}</div></div></div>', unsafe_allow_html=True)
    with c2: 
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi">Falta Volume</div><div class="value-kpi">R$ {vfal:,.0f}</div><div class="sub-kpi">{abs(perc_falta):.1f}% da Perda</div></div></div>', unsafe_allow_html=True)
    with c3: 
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi">Transporte</div><div class="value-kpi">R$ {vtransp:,.0f}</div><div class="sub-kpi">{abs(perc_transp):.1f}% da Perda</div></div></div>', unsafe_allow_html=True)
    with c4: 
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi">SAC</div><div class="value-kpi">R$ {vsac:,.0f}</div><div class="sub-kpi">{abs(perc_sac):.1f}% da Perda</div></div></div>', unsafe_allow_html=True)
    with c5: 
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi">% Geral Perdas</div><div class="value-kpi">{perc_geral_str}</div><div class="sub-kpi">Sobre Fat.</div></div></div>', unsafe_allow_html=True)
    with c6: 
        perc_fin = (fechadas / total_uds * 100) if total_uds > 0 else 0
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi">Total Filiais Únicas</div><div class="value-kpi">{total_uds}</div><div class="sub-kpi">{perc_fin:.1f}% Fin.</div></div></div>', unsafe_allow_html=True)
    
    with c7: 
        df_validos = df_filt[df_filt['tipo_clean'].str.strip() != ''].copy()
        
        # Agrupa por Semestre e Tipo
        resumo_tipos = df_validos.groupby(['semestre_clean', 'tipo_clean']).agg(
            Tot=('cd', 'nunique'),
            Inv=('cd', 'count'),
            Fim=('cd', lambda x: df_validos.loc[x.index][df_validos.loc[x.index]['is_fin']]['cd'].nunique())
        ).reset_index()
        
        resumo_tipos['Pen'] = resumo_tipos['Tot'] - resumo_tipos['Fim']
        
        linhas_html = ""
        for _, row in resumo_tipos.iterrows():
            sem_label = row['semestre_clean'].replace('semestre', 'Sem.').replace('º', 'º')
            linhas_html += f"<tr><td style='text-align:left; color:#8b949e; padding:1px 1px; white-space:nowrap;'>{sem_label} | {row['tipo_clean']}</td><td style='color:#f0f6fc; text-align:center;'>{row['Tot']}</td><td style='color:#00d2ff; font-weight:bold; text-align:center;'>{row['Inv']}</td><td style='color:#3fb950; text-align:center;'>{row['Fim']}</td><td style='color:#ff4b4b; text-align:center;'>{row['Pen']}</td></tr>"
            
        tabela_html = f"<div style='max-height: 110px; overflow-y: auto; overflow-x: hidden; width: 100%;'><table style='width:100%; table-layout: fixed; font-size:8.5px; border-top:1px solid #30363d; margin-top:2px;'><colgroup><col style='width: 44%;'><col style='width: 14%;'><col style='width: 14%;'><col style='width: 14%;'><col style='width: 14%;'></colgroup><thead><tr style='color:#8b949e;'><th style='text-align:left; padding:1px 1px;'>Sem | Tipo</th><th>Tot</th><th style='color:#00d2ff;'>Inv</th><th>Fim</th><th>Pen</th></tr></thead><tbody>{linhas_html}</tbody></table></div>"
        
        st.markdown(f'<div class="card-kpi" style="{estilo_card}"><div style="width: 100%;"><div class="label-kpi" style="margin-bottom:2px;">Status / Semestre</div>{tabela_html}</div></div>', unsafe_allow_html=True)

    # --- GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1, 1.1])
    with g1:
        st.subheader("📊 Resultado Consolidado")
        df_plot = df_filt.groupby('tipo_clean')['v_perda_consol'].sum().reset_index()
        fig_b = px.bar(df_plot, x='tipo_clean', y=df_plot['v_perda_consol'].abs(), text='v_perda_consol', color='tipo_clean', 
                       color_discrete_map={'CD':'#3a7bd5','LV':'#7000ff','DQS':'#00f2ff'})
        fig_b.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b.update_layout(template="plotly_dark", height=380, showlegend=False, yaxis_visible=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_b, use_container_width=True)

    with g2:
        st.subheader("🏢 Status de Saúde (Apenas 1º Ciclo)")
        df_tree = df_filt[df_filt['v_1c'] != 0].copy()
        df_tree['cd_lbl'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        fig_t = px.treemap(df_tree, path=['tipo_clean', 'cd_lbl'], values=df_tree['v_1c'].abs(), color='tipo_clean', 
                           color_discrete_map={'CD':'#0040ff','LV':'#aa00ff','DQS':'#00d2ff'})
        fig_t.update_traces(textinfo="label+value", texttemplate="<b>%{label}</b><br>R$ %{value:,.0f}")
        fig_t.update_layout(template="plotly_dark", height=380, margin=dict(t=20, b=10, l=0, r=0))
        st.plotly_chart(fig_t, use_container_width=True)

    # --- BASE (TABELA + PIZZA) ---
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2 = st.columns([3, 1.2])
    with b1:
        st.subheader("📋 Detalhamento")
        df_tab = df_filt.copy()
        df_tab['%'] = (df_tab['v_perda_consol'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd_t'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd_t', 'local', 'v_perda_consol', '%', 'v_falta', 'v_transp', 'v_sac', 'is_fin']]
        st.dataframe(
            df_ex.style.apply(lambda r: ['background-color: #451a1a' if r['v_perda_consol'] < 0 else 'background-color: #1a4523']*len(r), axis=1),
            column_config={
                "v_perda_consol": st.column_config.NumberColumn("$RESULTADO", format="R$ %.2f"), 
                "v_falta": st.column_config.NumberColumn("FALTA VOL.", format="R$ %.0f"),
                "v_transp": st.column_config.NumberColumn("TRANSPORTE", format="R$ %.0f"),
                "v_sac": st.column_config.NumberColumn("SAC", format="R$ %.0f"),
                "%": st.column_config.NumberColumn("%PERDAS", format="%.3f%%")
            },
            use_container_width=True, hide_index=True
        )
    with b2:
        st.subheader("📍 Perda / Gerente")
        df_pi = df_filt[df_filt['divisional'] != "Indefinido"]
        fig_pi = px.pie(df_pi, values=df_pi['v_perda_consol'].abs(), names='divisional', hole=0.7, color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"])
        fig_pi.update_layout(template="plotly_dark", height=450, margin=dict(t=50, b=50, l=0, r=0), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_pi, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Erro crítico: {e}")