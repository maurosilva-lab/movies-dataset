import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Prevenção | BI Executive", page_icon="📊")

## --- ESTILIZAÇÃO CSS EXECUTIVA ---
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0b0e14 !important; }
.main { padding: 0rem !important; }

.block-container {
    padding-top: 1.8rem !important; 
    padding-bottom: 1rem !important;
}

/* Header principal com degradê elegante */
.header-box {
    background: linear-gradient(135deg, #0e1726 0%, #0052d4 50%, #4364f7 100%) !important;
    padding: 1.2rem;
    border-radius: 12px;
    text-align: center;
    margin-bottom: 20px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 82, 212, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.header-title { color: #ffffff !important; font-size: 24px !important; font-weight: 800 !important; margin:0; letter-spacing: 0.5px; }

/* Cards KPIs */
.card-kpi {
    background: #151c28;
    border: 1px solid #1f293d;
    border-radius: 10px;
    padding: 12px 10px;
    text-align: center;
    height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    transition: transform 0.2s ease;
}
.card-kpi:hover { border-color: #00d2ff; }

.label-kpi { color: #8b949e; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; }
.value-kpi { color: #f0f6fc; font-size: 20px !important; font-weight: 800 !important; margin: 2px 0; }
.sub-kpi { color: #00d2ff; font-size: 11px; font-weight: 500; }

/* Painel da Tabela de Status Executivo */
.status-container {
    background: #151c28;
    border: 1px solid #1f293d;
    border-radius: 10px;
    padding: 12px 15px;
    height: 100%;
    min-height: 290px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.status-title {
    color: #f0f6fc;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
    border-bottom: 1px solid #1f293d;
    padding-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Custom Table CSS */
.exec-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.exec-table th { color: #8b949e; text-align: center; padding: 6px 4px; font-weight: 600; border-bottom: 1px solid #2a364f; }
.exec-table th:first-child { text-align: left; }
.exec-table td { padding: 6px 4px; text-align: center; border-bottom: 1px solid #1c2638; color: #d0d7de; }
.exec-table td:first-child { text-align: left; font-weight: 600; color: #f0f6fc; }

.badge-inv { background: rgba(0, 210, 255, 0.15); color: #00d2ff; padding: 2px 6px; border-radius: 4px; font-weight: 700; }
.badge-fim { color: #3fb950; font-weight: 700; }
.badge-pen { color: #ff4b4b; font-weight: 700; }
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
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO INV PREVENÇÃO DE PERDAS 2026</p></div>', unsafe_allow_html=True)

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
    
    total_uds = df_filt['cd'].nunique()
    fechadas = df_filt[df_filt['is_fin']]['cd'].nunique()

    # COMPARAÇÃO 2025
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
        texto_var = f'<span style="color:#3fb950; font-weight:bold;">▼ {abs(var_perc):.1f}%</span> vs 2025'
    elif var_perc > 0:
        texto_var = f'<span style="color:#ff4b4b; font-weight:bold;">▲ {var_perc:.1f}%</span> vs 2025'
    else:
        texto_var = "Igual a 2025"

    # --- NOVO LAYOUT EXECUTIVO DO TOPO ---
    col_kpis, col_status = st.columns([3.2, 1.8])

    with col_kpis:
        # Linha 1 de KPIs (3 colunas)
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consol.</div><div class="value-kpi">R$ {perda_total:,.0f}</div><div class="sub-kpi">{texto_var}</div></div>', unsafe_allow_html=True)
        with k2:
            st.markdown(f'<div class="card-kpi"><div class="label-kpi">Falta Volume</div><div class="value-kpi">R$ {vfal:,.0f}</div><div class="sub-kpi">{abs(perc_falta):.1f}% da Perda</div></div>', unsafe_allow_html=True)
        with k3:
            st.markdown(f'<div class="card-kpi"><div class="label-kpi">Transporte</div><div class="value-kpi">R$ {vtransp:,.0f}</div><div class="sub-kpi">{abs(perc_transp):.1f}% da Perda</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

        # Linha 2 de KPIs (3 colunas)
        k4, k5, k6 = st.columns(3)
        with k4:
            st.markdown(f'<div class="card-kpi"><div class="label-kpi">SAC</div><div class="value-kpi">R$ {vsac:,.0f}</div><div class="sub-kpi">{abs(perc_sac):.1f}% da Perda</div></div>', unsafe_allow_html=True)
        with k5:
            st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Geral Perdas</div><div class="value-kpi">{perc_geral_str}</div><div class="sub-kpi">Sobre Faturamento</div></div>', unsafe_allow_html=True)
        with k6:
            perc_fin = (fechadas / total_uds * 100) if total_uds > 0 else 0
            st.markdown(f'<div class="card-kpi"><div class="label-kpi">Filiais Únicas</div><div class="value-kpi">{total_uds}</div><div class="sub-kpi">{perc_fin:.1f}% Finalizados</div></div>', unsafe_allow_html=True)

    with col_status:
        # Tabela Executiva de Status ao Lado dos KPIs
        df_validos = df_filt[df_filt['tipo_clean'].str.strip() != ''].copy()
        
        # Agrupamento correto:
        # Tot = Total de filiais unicas
        # Inv = Quantidade de inventarios FECHADOS/REALIZADOS (is_fin == True)
        # Fim = Filiais unicas com inventario finalizado
        resumo_tipos = df_validos.groupby(['semestre_clean', 'tipo_clean']).agg(
            Tot=('cd', 'nunique'),
            Inv=('cd', lambda x: df_validos.loc[x.index][df_validos.loc[x.index]['is_fin']]['cd'].count()),
            Fim=('cd', lambda x: df_validos.loc[x.index][df_validos.loc[x.index]['is_fin']]['cd'].nunique())
        ).reset_index()
        
        resumo_tipos['Pen'] = resumo_tipos['Tot'] - resumo_tipos['Fim']
        
        linhas_html = ""
        for _, row in resumo_tipos.iterrows():
            sem_label = row['semestre_clean'].replace('semestre', 'Sem.').replace('º', 'º')
            linhas_html += f"<tr><td>{sem_label} | {row['tipo_clean']}</td><td>{row['Tot']}</td><td><span class='badge-inv'>{row['Inv']}</span></td><td><span class='badge-fim'>{row['Fim']}</span></td><td><span class='badge-pen'>{row['Pen']}</span></td></tr>"
            
        tabela_status = f"""<div class="status-container"><div class="status-title"><span>📋 Status dos Inventários</span><span style="font-size:10px; color:#8b949e; font-weight:normal;">Visão por Semestre</span></div><div style="max-height: 220px; overflow-y: auto;"><table class="exec-table"><thead><tr><th>Semestre / Tipo</th><th>Filiais</th><th>Qtd Inv</th><th>Fim</th><th>Pen</th></tr></thead><tbody>{linhas_html}</tbody></table></div></div>"""
        
        st.markdown(tabela_status, unsafe_allow_html=True)
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