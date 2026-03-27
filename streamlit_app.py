import altair as alt
import pandas as pd
import streamlit as st
from typing import List
from datetime import datetime, timedelta

# --- VARIÁVEIS DE CONFIGURAÇÃO CRÍTICAS ---
GOOGLE_SHEET_ID = "1xzUgn5hv63ZX6IkVeoAweOPP1JWmPM9BDiZ2GWqrtRI" 

# GIDs DAS ABAS
GID_PRINCIPAL = "1339063720"     # Estoque, Custo Extra e HISTÓRICO DIÁRIO
GID_MOVIMENTACAO = "999352715"   # Movimentação (Apenas para barras de entrada/saída se necessário)

# --- CONFIGURAÇÃO DAS COLUNAS ---

# 1. Estoque Atual (Colunas A, B, C -> Indices 0, 1, 2)
ESTOQUE_INDICES = range(0, 3) 
ESTOQUE_COLS = ["CD_EMPRESA", "DS_AREA_ARMAZ", "VALOR_ESTOQUE_AGREGADO"]

# 2. Histórico Diário Acumulado (Colunas G, H, I, J -> Indices 6, 7, 8, 9)
# G=Data, H=Empresa, I=Area, J=Valor Total
HISTORICO_INDICES = range(6, 10)
HISTORICO_COLS = ["DATA_ATUALIZACAO", "CD_EMPRESA", "DS_AREA_ARMAZ", "VALOR_TOTAL_DIA"]

# 3. Custo Extra (Colunas L, M, N -> Indices 11, 12, 13)
CUSTO_EXTRA_INDICES = range(11, 14) 
CUSTO_EXTRA_COLS = ["CD_EMPRESA", "VALOR_EXTRA_AGREGADO", "QT_ESTOQUE_AGREGADA"] 

# 4. Movimentação (Para barras de fluxo)
MOVIMENTACAO_INDICES = range(0, 6)
MOVIMENTACAO_COLS = [
    "DATA_ATUALIZACAO", "CD_EMPRESA", "DS_AREA_ARMAZ", 
    "VALOR_SALDO_TOTAL", "VALOR_MOVIMENTO", "STATUS_MOVIMENTO"
]

# ----------------------------------------
# FUNÇÕES DE FORMATAÇÃO E CARGA
# ----------------------------------------

def formatar_monetario_padrao(numero: float) -> str:
    """Formata para KPI monetário (ex: R$ 1,5 M ou R$ 79.076,00)."""
    if pd.isna(numero) or numero == 0: return "R$ 0,00"
    abs_numero = abs(numero)
    
    if abs_numero >= 1e9: 
        return f'R$ {numero / 1e9:,.2f} B'.replace('.', 'X').replace(',', '.').replace('X', ',')
    elif abs_numero >= 1e6: 
        return f'R$ {numero / 1e6:,.2f} M'.replace('.', 'X').replace(',', '.').replace('X', ',')
    elif abs_numero >= 1e3: 
        return f'R$ {numero / 1e3:,.2f} K'.replace('.', 'X').replace(',', '.').replace('X', ',')
    else: 
        return f'R$ {numero:,.2f}'.replace('.', 'X').replace(',', '.').replace('X', ',')


def formatar_quantidade_kpi(numero: float) -> str:
    if pd.isna(numero) or numero == 0: return "0"
    abs_numero = abs(numero)
    if abs_numero >= 1e6:
        if abs_numero >= 1e9: return f'{numero/1e9:.1f} bi'.replace('.', ',')
        else: return f'{numero/1e6:.1f} mi'.replace('.', ',')
    else: 
        return f'{int(numero):,}'.replace(',', '.') 

def formatar_visual_tabela(val):
    if pd.isna(val) or val == 0: return "-"
    abs_val = abs(val)
    if abs_val >= 1e9: return f'{val/1e9:.1f} bi'.replace('.', ',')
    if abs_val >= 1e6: return f'{val/1e6:.1f} mi'.replace('.', ',')
    elif abs_val >= 1e3: return f'{val/1e3:.1f} mil'.replace('.', ',')
    else: return f'{val:.0f}'.replace('.', ',')

@st.cache_data(ttl=3600) 
def load_data_by_gid(gid: str, target_columns: List[str], column_indices: range) -> pd.DataFrame:
    url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        # Seleciona colunas pelo índice para evitar erro de nome
        df_selected = df.iloc[:, column_indices] 
        if len(df_selected.columns) == len(target_columns):
            df_selected.columns = target_columns
            return df_selected
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

def limpar_coluna_monetaria(series):
    """Remove R$, pontos de milhar e converte virgula decimal para ponto."""
    return pd.to_numeric(
        series.astype(str)
        .str.replace(r'^[R$\s]+', '', regex=True)  
        .str.replace(r'[R$\s]', '', regex=True)    
        .str.replace('.', '', regex=False)        
        .str.replace(',', '.', regex=False),      
        errors='coerce'
    )

def clear_cache_and_rerun():
    load_data_by_gid.clear() 
    st.rerun()


# --- INÍCIO DA PÁGINA ---
st.set_page_config(page_title="Dashboard Estoque Não Vendável", page_icon="📊", layout="wide")
st.title("📊 Dashboard de Estoque Não Vendável (Full-filmet)") 

if st.button("🔄 **Atualizar Dados Imediatamente**", type="primary"):
    clear_cache_and_rerun()
    
st.markdown("---")

# --- FILTROS PADRÃO DE EMPRESA ---
FILTROS_PADRAO_EMPRESA = ['1300', '1590', '1350', '11500', '12900', '1996', '15350', '1991','15200']

# ==============================================================================
# CARREGAMENTO DE DADOS
# ==============================================================================
# 1. Resumo Atual (Aba Principal)
df_resumo_full = load_data_by_gid(GID_PRINCIPAL, ESTOQUE_COLS, ESTOQUE_INDICES)
# 2. Histórico Diário (Aba Principal - Colunas G a J)
df_historico_diario = load_data_by_gid(GID_PRINCIPAL, HISTORICO_COLS, HISTORICO_INDICES)
# 3. Custo Extra (Aba Principal)
df_custo_extra = load_data_by_gid(GID_PRINCIPAL, CUSTO_EXTRA_COLS, CUSTO_EXTRA_INDICES) 
# 4. Movimentação (Entrada/Saida)
df_movimentacao = load_data_by_gid(GID_MOVIMENTACAO, MOVIMENTACAO_COLS, MOVIMENTACAO_INDICES)

if df_resumo_full.empty:
    st.error("Erro ao carregar dados principais. Verifique o ID da planilha.")
    st.stop()

# ==============================================================================
# PRÉ-PROCESSAMENTO
# ==============================================================================
# A. Resumo Atual
df_resumo_full["VALOR_ESTOQUE_AGREGADO"] = limpar_coluna_monetaria(df_resumo_full["VALOR_ESTOQUE_AGREGADO"])
df_resumo_full["CD_EMPRESA"] = df_resumo_full["CD_EMPRESA"].astype(str).str.replace(r'\.0$', '', regex=True)
df_resumo_full["DS_AREA_ARMAZ"] = df_resumo_full["DS_AREA_ARMAZ"].astype(str)

# B. Histórico Diário (G a J)
if not df_historico_diario.empty:
    df_historico_diario["VALOR_TOTAL_DIA"] = limpar_coluna_monetaria(df_historico_diario["VALOR_TOTAL_DIA"])
    df_historico_diario["DATA_ATUALIZACAO"] = pd.to_datetime(df_historico_diario["DATA_ATUALIZACAO"], dayfirst=True, errors='coerce').dt.normalize()
    df_historico_diario["CD_EMPRESA"] = df_historico_diario["CD_EMPRESA"].astype(str).str.replace(r'\.0$', '', regex=True)
    df_historico_diario.dropna(subset=["DATA_ATUALIZACAO", "VALOR_TOTAL_DIA"], inplace=True)

# C. Movimentação (Para barras)
if not df_movimentacao.empty:
    df_movimentacao["VALOR_MOVIMENTO"] = limpar_coluna_monetaria(df_movimentacao["VALOR_MOVIMENTO"])
    df_movimentacao["DATA_ATUALIZACAO"] = pd.to_datetime(df_movimentacao["DATA_ATUALIZACAO"], dayfirst=True, errors='coerce').dt.normalize()
    df_movimentacao.dropna(subset=["DATA_ATUALIZACAO", "VALOR_MOVIMENTO"], inplace=True)
    
    df_movimentacao["TIPO_MOVIMENTO"] = "OUTROS"
    df_movimentacao.loc[df_movimentacao["VALOR_MOVIMENTO"] > 0, "TIPO_MOVIMENTO"] = "ENTRADA"
    df_movimentacao.loc[df_movimentacao["VALOR_MOVIMENTO"] < 0, "TIPO_MOVIMENTO"] = "SAIDA"

# D. Custo Extra
if not df_custo_extra.empty:
    df_custo_extra["VALOR_EXTRA_AGREGADO"] = limpar_coluna_monetaria(df_custo_extra["VALOR_EXTRA_AGREGADO"])
    df_custo_extra["QT_ESTOQUE_AGREGADA"] = pd.to_numeric(df_custo_extra["QT_ESTOQUE_AGREGADA"], errors='coerce').fillna(0).astype(float) 
    df_custo_extra["CD_EMPRESA"] = df_custo_extra["CD_EMPRESA"].astype(str).str.replace(r'\.0$', '', regex=True)


# Definição de datas limite baseada no Histórico Diário (que é a fonte principal da curva agora)
if not df_historico_diario.empty:
    max_date_mov = df_historico_diario["DATA_ATUALIZACAO"].max()
    min_date_mov = df_historico_diario["DATA_ATUALIZACAO"].min()
else:
    # Fallback se histórico vazio
    max_date_mov = datetime.now()
    min_date_mov = datetime.now() - timedelta(days=30)
    

# ---------------------------------------------------------
## ⚙️ SEÇÃO 1: FILTROS GLOBAIS
# ---------------------------------------------------------
st.header("⚙️ Filtros Globais")
c_multiselect, c_areas, c_datas = st.columns([1.5, 1.5, 2])

# Filtro 1: CD_EMPRESA 
empresas_disp = df_resumo_full["CD_EMPRESA"].unique()
empresas_disp_sorted = sorted(empresas_disp)
with c_multiselect:
    sel_empresa_area = st.multiselect(
        "CD'S (Análise de Área/KPIs)", 
        empresas_disp_sorted, 
        default=[e for e in FILTROS_PADRAO_EMPRESA if e in empresas_disp_sorted]
    )

# Filtro 2: ÁREAS 
areas_disp = df_resumo_full["DS_AREA_ARMAZ"].unique()
with c_areas:
    sel_areas_estoque = st.multiselect("Áreas (Visão Geral Estoque)", areas_disp, default=list(areas_disp))

# Filtro 3: INTERVALO DE DATAS 
with c_datas:
    st.markdown("Intervalo de Análise (Gráfico)")
    default_start_date = max_date_mov.date() - timedelta(days=15)
    
    data_inicio = st.date_input("Data de Início", value=default_start_date, min_value=min_date_mov.date(), max_value=max_date_mov.date())
    data_fim = st.date_input("Data de Fim", value=max_date_mov.date(), min_value=min_date_mov.date(), max_value=max_date_mov.date())
st.markdown("---")


# --- CÁLCULOS GLOBAIS (FLUXO E EXTRA) ---
if not df_movimentacao.empty:
    df_fluxo_chart = df_movimentacao[
        (df_movimentacao["TIPO_MOVIMENTO"].isin(["ENTRADA", "SAIDA"])) &
        (df_movimentacao["DATA_ATUALIZACAO"] >= pd.to_datetime(data_inicio)) &
        (df_movimentacao["DATA_ATUALIZACAO"] <= pd.to_datetime(data_fim))
    ].copy()
    
    if sel_empresa_area:
        df_fluxo_chart = df_fluxo_chart[df_fluxo_chart["CD_EMPRESA"].isin(sel_empresa_area)]

    total_entrada_chart = df_fluxo_chart["VALOR_MOVIMENTO"][df_fluxo_chart["TIPO_MOVIMENTO"] == "ENTRADA"].sum()
    total_saida_chart = df_fluxo_chart["VALOR_MOVIMENTO"][df_fluxo_chart["TIPO_MOVIMENTO"] == "SAIDA"].abs().sum() 
    saldo_periodo_chart = total_entrada_chart - total_saida_chart
else:
    total_entrada_chart = 0
    total_saida_chart = 0
    saldo_periodo_chart = 0

# Totais Custo Extra
df_custo_extra_filtrado = pd.DataFrame() 
total_custo_extra_filtrado = 0
total_quantidade_acumulada_filtrada = 0

if not df_custo_extra.empty:
    if sel_empresa_area:
        df_custo_extra_filtrado = df_custo_extra[df_custo_extra["CD_EMPRESA"].isin(sel_empresa_area)]
    else:
        df_custo_extra_filtrado = df_custo_extra.copy()

    total_custo_extra_filtrado = df_custo_extra_filtrado["VALOR_EXTRA_AGREGADO"].sum()
    total_quantidade_acumulada_filtrada = df_custo_extra_filtrado["QT_ESTOQUE_AGREGADA"].sum()


# ---------------------------------------------------------
## 💰 SEÇÃO 2: Análise de Estoque, Acumulado
# ---------------------------------------------------------
st.header("Análise de Estoque Não Vendável e Custo")

# 1. CÁLCULO E FILTRAGEM DO ESTOQUE
if sel_empresa_area:
    df_filtrado_area = df_resumo_full[df_resumo_full["CD_EMPRESA"].isin(sel_empresa_area)].copy()
else:
    df_filtrado_area = df_resumo_full.copy()

# Total Estoque Atual (KPI)
total_estoque_acumulado_filtrado = df_filtrado_area["VALOR_ESTOQUE_AGREGADO"].sum()

# KPI Custo Médio
custo_unitario = 0
if total_quantidade_acumulada_filtrada > 0:
    custo_unitario = total_custo_extra_filtrado / total_quantidade_acumulada_filtrada


# 2. EXIBIÇÃO DOS KPIS
col_total_est_val, col_total_qt_extra, col_custo_unit, col_fluxo_periodo = st.columns([1, 1, 1, 1]) 

with col_total_est_val:
    st.metric(f"Valor Total em Estoque NV", formatar_monetario_padrao(total_estoque_acumulado_filtrado))
    st.caption("Total Atual (Base Resumo)")

with col_total_qt_extra:
    st.metric(f"Quantidade Total em Estoque NV", formatar_quantidade_kpi(total_quantidade_acumulada_filtrada))
    st.caption("Itens em Custo Extra (Qtd)")

with col_custo_unit:
    st.metric(f"Custo Extra Médio p/ Unid.", formatar_monetario_padrao(custo_unitario))
    st.caption("Total Custo Extra / Total Qtd.")

with col_fluxo_periodo:
    st.metric(f"Saldo Período (R$)", 
              formatar_monetario_padrao(saldo_periodo_chart), 
              delta=formatar_monetario_padrao(total_entrada_chart), 
              delta_color="inverse") 
    st.caption(f"Movimentação {data_inicio.strftime('%d/%m')} a {data_fim.strftime('%d/%m')}")

st.markdown("### 1. Detalhamento de Concentração por Área")


# 3. TABELA DE ACUMULADO POR ÁREA
df_acumulado = df_filtrado_area.groupby("DS_AREA_ARMAZ")["VALOR_ESTOQUE_AGREGADO"].sum().reset_index()
df_acumulado.rename(columns={"VALOR_ESTOQUE_AGREGADO": "VALOR_ACUMULADO_R$", "DS_AREA_ARMAZ": "ÁREA DE ARMAZENAGEM"}, inplace=True)
df_acumulado = df_acumulado.sort_values(by="VALOR_ACUMULADO_R$", ascending=False)
df_acumulado = df_acumulado[df_acumulado["VALOR_ACUMULADO_R$"] != 0]

# Cálculo da Participação (%)
total_acumulado_filtro = df_acumulado["VALOR_ACUMULADO_R$"].sum()
if total_acumulado_filtro > 0:
    df_acumulado["PARTICIPAÇÃO (%)"] = (df_acumulado["VALOR_ACUMULADO_R$"] / total_acumulado_filtro)
else:
    df_acumulado["PARTICIPAÇÃO (%)"] = 0

col_table_final = st.columns(1)[0] 
with col_table_final:
    if not df_acumulado.empty:
        styler = (
            df_acumulado.style
            .background_gradient(subset=["VALOR_ACUMULADO_R$"], cmap='Reds') 
            .format({
                "VALOR_ACUMULADO_R$": formatar_visual_tabela,
                "PARTICIPAÇÃO (%)": "{:.1%}"
            }) 
            .hide(axis="index")
        )
        styler.set_table_styles([
            {'selector': 'th:nth-child(2), th:nth-child(3)', 'props': [('text-align', 'center')]},
            {'selector': 'td:nth-child(2), td:nth-child(3)', 'props': [('text-align', 'center')]}
        ])
        st.dataframe(styler, use_container_width=True, height=350)
    else:
        st.info("Selecione empresas no filtro global para esta análise.")
        
st.markdown("---") 

# --- MATRIZ DE CONCENTRAÇÃO ---
st.header("### 2. Matriz de Concentração de Problemas (Empresa x Área x Ineficiência)")

df_matriz = pd.merge(df_filtrado_area, df_custo_extra_filtrado[['CD_EMPRESA', 'QT_ESTOQUE_AGREGADA', 'VALOR_EXTRA_AGREGADO']], on='CD_EMPRESA', how='left').fillna(0)
df_matriz_final = df_matriz.groupby(['CD_EMPRESA', 'DS_AREA_ARMAZ']).agg(ValorNV=('VALOR_ESTOQUE_AGREGADO', 'sum'), QtdNV=('QT_ESTOQUE_AGREGADA', 'sum'), CustoExtra=('VALOR_EXTRA_AGREGADO', 'sum')).reset_index()

df_matriz_final.rename(columns={'ValorNV': 'Valor NV', 'QtdNV': 'Qtd. Total NV', 'CustoExtra': 'Custo Extra Total'}, inplace=True)
df_matriz_final['Custo Médio p/ Unidade'] = (df_matriz_final['Custo Extra Total'] / df_matriz_final['Qtd. Total NV']).fillna(0)

df_matriz_final = df_matriz_final[(df_matriz_final['Valor NV'] != 0) | (df_matriz_final['Custo Extra Total'] != 0)].sort_values(by=['Valor NV', 'Custo Médio p/ Unidade'], ascending=[False, False])

if not df_matriz_final.empty:
    quantile_valor = df_matriz_final['Valor NV'].quantile(0.75) if df_matriz_final['Valor NV'].max() > 0 else 0
    quantile_custo = df_matriz_final['Custo Médio p/ Unidade'].quantile(0.75) if df_matriz_final['Custo Médio p/ Unidade'].max() > 0 else 0
    
    styler_matriz = (
        df_matriz_final.style
        .format({
            "Valor NV": formatar_monetario_padrao,
            "Qtd. Total NV": lambda x: f'{int(x):,}'.replace(',', '.') if x > 0 else '-',
            "Custo Extra Total": formatar_monetario_padrao,
            "Custo Médio p/ Unidade": formatar_monetario_padrao
        })
        .background_gradient(subset=["Valor NV"], cmap='Reds', vmin=quantile_valor)
        .background_gradient(subset=["Custo Médio p/ Unidade"], cmap='Oranges', vmin=quantile_custo)
        .hide(axis="index")
    )
    st.dataframe(styler_matriz, use_container_width=True, height=500)
    st.caption("**Guia:** Vermelho/Laranja = Prioridade Crítica (Valor NV Alto ou Ineficiência Alta).")
else:
    st.info("Sem dados de estoque para Matriz.")

st.markdown("---")

# ---------------------------------------------------------
## 📈 SEÇÃO 3: Evolução Diária (DADOS DA ABA PRINCIPAL G-J)
# ---------------------------------------------------------

st.header("Evolução Diária de Fluxo do Estoque Não Vendável")

# 1. Preparar dados históricos da coluna G a J
if not df_historico_diario.empty:
    
    # Filtrar Histórico pelas Empresas selecionadas
    df_hist_filtrado = df_historico_diario.copy()
    if sel_empresa_area:
        df_hist_filtrado = df_hist_filtrado[df_hist_filtrado["CD_EMPRESA"].isin(sel_empresa_area)]
        
    # Filtrar Histórico pelas Datas selecionadas
    df_hist_filtrado = df_hist_filtrado[
        (df_hist_filtrado["DATA_ATUALIZACAO"] >= pd.to_datetime(data_inicio)) &
        (df_hist_filtrado["DATA_ATUALIZACAO"] <= pd.to_datetime(data_fim))
    ]
    
    # Agrupar por data (soma das empresas no dia)
    df_linha_final = df_hist_filtrado.groupby("DATA_ATUALIZACAO")["VALOR_TOTAL_DIA"].sum().reset_index()

    st.markdown(f"**Evolução e Fluxo - {data_inicio.strftime('%d/%m')} a {data_fim.strftime('%d/%m')}**")
    
    # GRÁFICO 1: BARRAS DE FLUXO (Mantido se houver dados de movimentação, pois ajuda a ver a variação)
    if not df_fluxo_chart.empty:
        df_grafico_barras = df_fluxo_chart.groupby(["DATA_ATUALIZACAO", "TIPO_MOVIMENTO"])["VALOR_MOVIMENTO"].sum().reset_index()
        barras = alt.Chart(df_grafico_barras).mark_bar().encode(
            x=alt.X('DATA_ATUALIZACAO:T', title="Data", axis=alt.Axis(format="%d/%m", labelAngle=-45)), 
            y=alt.Y('VALOR_MOVIMENTO:Q', title="Fluxo Diário (R$)", axis=alt.Axis(format='s')), 
            color=alt.Color('TIPO_MOVIMENTO:N', legend=alt.Legend(title="Tipo"),
                            scale=alt.Scale(domain=['ENTRADA', 'SAIDA'], range=['#dc3545', '#28a745'])), 
            tooltip=[alt.Tooltip('DATA_ATUALIZACAO', title='Data', format='%d/%m'), alt.Tooltip('VALOR_MOVIMENTO', title='Valor', format=',.2f')]
        ).properties(height=200)
        st.altair_chart(barras, use_container_width=True)

    # GRÁFICO 2: LINHA DE ACUMULADO (Baseado em colunas G-J)
    st.markdown("#### 🌊 Tendência do Acumulado Geral (Histórico Real)")
    
    if not df_linha_final.empty:
        base_line = alt.Chart(df_linha_final).encode(
            x=alt.X('DATA_ATUALIZACAO:T', title="Data", axis=alt.Axis(format="%d/%m", labelAngle=-45))
        )

        area_acumulado = base_line.mark_area(opacity=0.3, color='#dc3545').encode(
            y=alt.Y('VALOR_TOTAL_DIA:Q', title='Saldo Total (R$)', axis=alt.Axis(format='s'), scale=alt.Scale(zero=False))
        )
        
        line_acumulado = base_line.mark_line(color='#dc3545', size=3).encode(
            y=alt.Y('VALOR_TOTAL_DIA:Q')
        )
        
        points_acumulado = base_line.mark_point(filled=True, size=70, color='#dc3545').encode(
            y=alt.Y('VALOR_TOTAL_DIA:Q'),
            tooltip=[
                alt.Tooltip('DATA_ATUALIZACAO', title='Data', format='%d/%m/%Y'),
                alt.Tooltip('VALOR_TOTAL_DIA', title='Saldo Histórico', format=',.2f')
            ]
        )

        st.altair_chart((area_acumulado + line_acumulado + points_acumulado).interactive(), use_container_width=True)
    else:
        st.info("Sem dados históricos (Colunas G-J) para o período e empresas selecionados.")
            
else:
    st.info("Não foi possível carregar os dados históricos da aba principal (Colunas G-J). Verifique a planilha.")

st.markdown("---")

# ---------------------------------------------------------
## 📊 SEÇÃO 4: Visão Geral de Estoque
# ---------------------------------------------------------
st.header("Visão Geral de Estoque Não Vendável (Valores por Área e Empresa)")

if sel_empresa_area: mask_empresa = df_resumo_full["CD_EMPRESA"].isin(sel_empresa_area)
else: mask_empresa = df_resumo_full["CD_EMPRESA"].isin([]) 
    
df_filt = df_resumo_full[(df_resumo_full["DS_AREA_ARMAZ"].isin(sel_areas_estoque)) & (mask_empresa)]

if not df_filt.empty:
    df_pivot = df_filt.pivot_table(index="CD_EMPRESA", columns="DS_AREA_ARMAZ", values="VALOR_ESTOQUE_AGREGADO", aggfunc="sum", fill_value=0)
    df_pivot.columns = df_pivot.columns.astype(str)
    df_pivot["TOTAL GERAL"] = df_pivot.sum(axis=1)
    styler = df_pivot.style.format(formatar_visual_tabela) 
    styler.set_properties(**{'text-align': 'center'}, subset=pd.IndexSlice[:, df_pivot.columns.tolist()])
    st.dataframe(styler, use_container_width=True)
else:
    st.info("Sem dados de estoque nos filtros globais selecionados.")

st.markdown("---")

# ---------------------------------------------------------
## 📦 SEÇÃO 5: Detalhe de Custo Extra
# ---------------------------------------------------------
st.header("📦 Detalhamento de Custo e Quantidade Extra por Empresa")

if not df_custo_extra.empty:
    df_custo_agregado = df_custo_extra.groupby("CD_EMPRESA").agg(TOTAL_CUSTO=('VALOR_EXTRA_AGREGADO', 'sum'), TOTAL_QUANTIDADE=('QT_ESTOQUE_AGREGADA', 'sum')).reset_index()
    df_custo_agregado = df_custo_agregado[(df_custo_agregado["TOTAL_CUSTO"] != 0) | (df_custo_agregado["TOTAL_QUANTIDADE"] != 0)]

    if not df_custo_agregado.empty:
        styler_custo = (
            df_custo_agregado.style
            .format({"TOTAL_CUSTO": formatar_visual_tabela, "TOTAL_QUANTIDADE": lambda x: f'{int(x):,}'.replace(',', '.') })
            .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}, {'selector': 'td', 'props': [('text-align', 'center')]}])
            .hide(axis="index")
        )
        st.dataframe(styler_custo, use_container_width=True)
    else:
        st.info("Não há dados de Custo Extra para exibir.")
st.markdown("---")