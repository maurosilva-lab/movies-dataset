import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Magalog | BI Executive", page_icon="📊")

# --- ESTILIZAÇÃO CSS ATUALIZADA (EXECUTIVE NEON v3) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #0d1117; }
    .block-container { padding-top: 2rem !important; max-width: 95%; }
    
    /* TÍTULO COM GRADIENTE */
    .header-box {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0, 210, 255, 0.2);
    }
    .header-title { color: white; font-size: 28px; font-weight: 800; letter-spacing: 2px; margin:0; }

    /* CARDS ESTILO NEON */
    .card-kpi {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 15px; padding: 25px; text-align: center;
        transition: transform 0.3s;
        min-height: 160px;
    }
    .card-kpi:hover { transform: translateY(-5px); border-color: #00d2ff; }
    
    /* TEXTOS DENTRO DOS CARDS */
    .label-kpi { color: #8b949e; font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 10px; }
    .value-kpi { color: #f0f6fc; font-size: 28px; font-weight: 800; }
    .sub-kpi { color: #00d2ff; font-size: 14px; margin-top: 8px; font-weight: 500; }
    
    /* BARRA DE PROGRESSO CUSTOM (PARA O CARD EVOLUÇÃO) */
    .progress-bg { background-color: #30363d; border-radius: 10px; height: 10px; width: 100%; margin-top: 20px; }
    .progress-fill { 
        background: linear-gradient(90deg, #00d2ff 0%, #00f2ff 100%); 
        height: 10px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 242, 255, 0.5); 
    }
    </style>
""", unsafe_allow_html=True)

# ... (Mantenha as funções limpar_valor, mapear_divisional e load_data iguaizinhas) ...

# ... (Início do bloco try, carregamento de dados e sidebar permanecem iguais) ...

    # 3. Processamento Numérico
    def get_col(name_snippet):
        match = [c for c in df_raw.columns if name_snippet in c]
        return match[0] if match else None

    c_fat = get_col('faturamento')
    c_1c = get_col('1__ciclo')
    c_falta = get_col('falta_vol') # Esta é a coluna de Volume de Falta

    df_raw['v_1c'] = df_raw[c_1c].apply(limpar_valor) if c_1c else 0.0
    df_raw['v_fat'] = df_raw[c_fat].apply(limpar_valor) if c_fat else 0.0
    df_raw['v_falta'] = df_raw[c_falta].apply(limpar_valor) if c_falta else 0.0 # Valor em R$ da falta
    df_raw['is_finalizado'] = df_raw['v_1c'] != 0

    # Aplicação de Filtros (continua igual)
    # ...

    # --- UI PRINCIPAL - REVISADA ---
    st.markdown('<div class="header-box"><p class="header-title">BI FECHAMENTO MAGALOG 2026</p></div>', unsafe_allow_html=True)

    # Cálculos KPIs
    perda_1c = df_filt['v_1c'].sum()
    falta_vol = df_filt['v_falta'].sum()
    fat_total = df_filt['v_fat'].sum()
    
    # 1. Perda Consolidada (Base para o cálculo de porcentagem)
    perda_consolidada = perda_1c + falta_vol
    
    # 2. % Perda Global sobre faturamento
    perc_global = (abs(perda_consolidada) / fat_total * 100) if fat_total > 0 else 0.0
    
    # 3. NOVO CÁLCULO: Porcentagem do Volume de Falta sobre a Perda Consolidada TOTAL
    if perda_consolidada != 0:
        perc_falta_sobre_total = (falta_vol / perda_consolidada * 100)
    else:
        perc_falta_sobre_total = 0.0
        
    # 4. Evolução / Conclusão
    total_un = len(df_filt)
    finalizados = df_filt['is_finalizado'].sum()
    perc_conclusao = (finalizados / total_un * 100) if total_un > 0 else 0

    # Renderização dos Cards KPIs revisados
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Perda Consolidada</div><div class="value-kpi">R$ {perda_consolidada:,.0f}</div><div class="sub-kpi">1C + Falta Vol (Financeiro)</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">% Perda Global</div><div class="value-kpi">{perc_global:.3f}%</div><div class="sub-kpi">Sobre Faturamento</div></div>', unsafe_allow_html=True)
    with k3:
        # ALTERAÇÃO SOLICITADA: Mostra a porcentagem sobre o total de perdas, remove "itens pendentes"
        st.markdown(f'<div class="card-kpi"><div class="label-kpi">Volume Falta</div><div class="value-kpi">R$ {falta_vol:,.0f}</div><div class="sub-kpi">{perc_falta_sobre_total:.1f}% da Perda Total</div></div>', unsafe_allow_html=True)
    with k4:
        # ALTERAÇÃO SOLICITADA: Barra de progresso neon inspirada no print
        st.markdown(f'''<div class="card-kpi"><div class="label-kpi">Evolução / Conclusão</div><div class="value-kpi">{perc_conclusao:.1f}%</div>
        <div class="progress-bg"><div class="progress-fill" style="width: {perc_conclusao}%"></div></div></div>''', unsafe_allow_html=True)

# ... (Mantenha a seção do comparativo YoY e os gráficos iguaizinhas) ...

# --- SEÇÃO 1: GRÁFICOS DO MEIO (RESULTADO CONSOLIDADO + TREEMAP) ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_esquerda, col_direita = st.columns([1, 1.1])

    with col_esquerda:
        st.subheader("📊 Resultado Consolidado por Processo")
        
        # Criamos uma cópia para o cálculo e identificamos o nome da coluna de falta
        df_proc_plot = df_filt.copy()
        col_f_nome = 'v_fal' if 'v_fal' in df_proc_plot.columns else 'v_falta'
        
        # SOMA: 1º Ciclo + Falta Vol
        df_proc_plot['v_consolidada_tipo'] = df_proc_plot['v_1c'] + df_proc_plot[col_f_nome]
        
        # Agrupamento por Tipo (CD, LV, DQS)
        df_proc = df_proc_plot.groupby('tipo_clean')['v_consolidada_tipo'].sum().reset_index()
        
        # Valor absoluto para a barra crescer para cima (Estética)
        df_proc['v_abs'] = df_proc['v_consolidada_tipo'].abs()
        
        fig_b = px.bar(
            df_proc, 
            x='tipo_clean', 
            y='v_abs', 
            color='tipo_clean',
            text='v_consolidada_tipo', # Exibe o valor real negativo no rótulo
            color_discrete_map={
                'CD': '#3a7bd5',   
                'LV': '#7000ff',   
                'DQS': '#00f2ff'   
            }
        )
        
        fig_b.update_traces(
            width=0.5,
            texttemplate='R$ %{text:,.0f}', 
            textposition='outside',
            marker_line_width=0
        )
        
        fig_b.update_layout(
            template="plotly_dark", 
            height=400, 
            margin=dict(t=40, b=0, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            xaxis_title="",
            yaxis_visible=False 
        )
        st.plotly_chart(fig_b, use_container_width=True)

    with col_direita:
        st.subheader("🏢 Status de Saúde (Tipo > CD)")
        
        df_tree = df_filt.copy()
        col_f_tree = 'v_fal' if 'v_fal' in df_tree.columns else 'v_falta'
        df_tree['v_consolidada_tree'] = df_tree['v_1c'] + df_tree[col_f_tree]
        
        # Filtra apenas registros com movimentação
        df_tree = df_tree[df_tree['v_consolidada_tree'] != 0].copy()
        df_tree['cd_label'] = df_tree['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # HIERARQUIA: Tipo (CD/LV/DQS) -> Código da Unidade
        fig_t = px.treemap(
            df_tree, 
            path=['tipo_clean', 'cd_label'],
            values=df_tree['v_consolidada_tree'].abs(), 
            color='tipo_clean',
            color_discrete_map={
                'CD': '#0040ff', 
                'LV': '#aa00ff', 
                'DQS': '#00d2ff'
            }
        )
        
        fig_t.update_traces(
            textinfo="label+value",
            texttemplate="<span style='font-size:18px'><b>%{label}</b></span><br>R$ %{value:,.0f}",
            marker_line_width=2,
            marker_line_color="#0d1117"
        )
        
        fig_t.update_layout(
            template="plotly_dark", 
            height=400, 
            margin=dict(t=20, b=10, l=0, r=0),
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_t, use_container_width=True)

    # --- SEÇÃO 2: BASE (TABELA SEM CORTE + PIZZA) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_tab_base, col_pie_base = st.columns([3, 1.2])

    with col_tab_base:
        st.subheader("📋 Detalhamento Operacional")
        df_tab = df_filt.copy()
        col_f_tab = 'v_fal' if 'v_fal' in df_tab.columns else 'v_falta'
        
        df_tab['v_fat'] = pd.to_numeric(df_tab['v_fat'], errors='coerce').fillna(0)
        df_tab['%'] = (df_tab['v_1c'] / df_tab['v_fat'] * 100).fillna(0)
        df_tab['cd'] = df_tab['cd'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        df_ex = df_tab[['semestre', 'tipo_clean', 'divisional', 'cd', 'local', 'v_1c', '%', col_f_tab, 'is_fin']]

        def styler(row):
            bg = 'background-color: #451a1a;' if row['v_1c'] < 0 else 'background-color: #1a4523;'
            return [bg] * len(row)

        st.dataframe(
            df_ex.style.apply(styler, axis=1), 
            column_config={
                "v_1c": st.column_config.NumberColumn("Resultado", format="R$ %.2f"),
                "%": st.column_config.NumberColumn("%", format="%.4f%%"),
                col_f_tab: st.column_config.NumberColumn("Falta", format="%.0f"),
                "is_fin": "Fim"
            }, 
            use_container_width=True, 
            hide_index=True,
            height="content" # <--- O segredo está aqui: mudei de None para "content"
        )# Automático para não cortar


    with col_pie_base:
        st.subheader("📍 Perda / Gerência")
        df_p = df_filt[df_filt['divisional'] != "Indefinido"]
        
        fig_p = px.pie(
            df_p, values=df_p['v_1c'].abs(), names='divisional', hole=0.7, 
            color_discrete_sequence=["#00d2ff", "#008cff", "#0040ff", "#3a7bd5"]
        )
        fig_p.update_layout(
            template="plotly_dark", height=500, 
            margin=dict(t=50, b=50, l=0, r=0), 
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_p, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Erro ao renderizar: {e}")