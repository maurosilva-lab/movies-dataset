import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Dashboard de Auditoria", layout="wide")

# 1. Link do Google Sheets (Exportação CSV)
SHEET_ID = "1BTHfdgcNq_oRlEC18j4LiwEX_u63mxGXLGskgbR8P1w"
GID = "783239189"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=600) # Atualiza o cache a cada 10 minutos
def load_data():
    try:
        df = pd.read_csv(URL)
        
        # --- Limpeza e Formatação ---
        # Certifique-se que os nomes das colunas aqui batem com o cabeçalho da sua planilha
        # Exemplo: df.columns = ['Data', 'Valor', 'Auditado', 'Peças']
        
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'])
            df = df.sort_values('Data')
        
        # Criando os acumulados
        df['Acumulado Valor'] = df['Valor'].cumsum()
        df['Acumulado Peças'] = df['Peças'].cumsum()
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# Título do App
st.title("📊 Painel de Controle: Auditoria e Produção")
st.markdown("---")

df = load_data()

if not df.empty:
    # --- KPIs em Destaque ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Valor", f"R$ {df['Valor'].sum():,.2f}")
    col2.metric("Total Peças", f"{int(df['Peças'].sum())} un")
    col3.metric("Total Auditado", f"R$ {df['Valor Auditado'].sum():,.2f}")

    # --- Primeira Linha de Gráficos ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Gráfico de Linha Diário (Valor)")
        fig1 = px.line(df, x='Data', y='Valor', markers=True, 
                       line_shape='spline', color_discrete_sequence=['#1f77b4'])
        st.plotly_chart(fig1, use_container_width=True)

    with row1_col2:
        st.subheader("Valor Auditado por Dia")
        fig2 = px.line(df, x='Data', y='Valor Auditado', markers=True,
                       color_discrete_sequence=['#d62728'])
        st.plotly_chart(fig2, use_container_width=True)

    # --- Segunda Linha (Acumulado) ---
    st.subheader("Progresso Acumulado (Valor vs Peças)")
    
    fig3 = go.Figure()
    # Adiciona linha de Valor Acumulado
    fig3.add_trace(go.Scatter(x=df['Data'], y=df['Acumulado Valor'], 
                             name='Acumulado Valor (R$)', line=dict(color='green', width=3)))
    
    # Adiciona linha de Peças Acumuladas com eixo Y secundário
    fig3.add_trace(go.Scatter(x=df['Data'], y=df['Acumulado Peças'], 
                             name='Acumulado Peças (Qtd)', line=dict(color='orange', width=3),
                             yaxis='y2'))

    fig3.update_layout(
        xaxis=dict(title='Data'),
        yaxis=dict(title='Valor Acumulado (R$)', titlefont=dict(color='green'), tickfont=dict(color='green')),
        yaxis2=dict(title='Peças Acumuladas', titlefont=dict(color='orange'), tickfont=dict(color='orange'),
                    overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig3, use_container_width=True)

    # --- Tabela de Dados Opcional ---
    with st.expander("Visualizar Dados Brutos"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("Aguardando dados da planilha...")

# Botão para forçar atualização
if st.button('🔄 Atualizar Dados'):
    st.cache_data.clear()
    st.rerun()