import streamlit as st
import sqlite3
import pandas as pd
import os

# Configura a página para ocupar a tela toda
st.set_page_config(page_title="Dashboard Redash", page_icon="📊", layout="wide")

st.title("📊 Painel de Dados Consolidados")
st.markdown("Lendo diretamente do banco de dados SQLite local.")

# --- O SEGREDO DO SÊNIOR: CACHE ---
@st.cache_data
def carregar_dados_do_banco():
    # 1. Descobre a pasta EXATA onde este script está salvo
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Monta o caminho completo até o banco de dados
    db_path = os.path.join(diretorio_atual, "consolidador_local.db")
    
    # 3. Conecta no seu banco de dados local
    conn = sqlite3.connect(db_path)
    
    # Lê a tabela inteira e joga para um DataFrame do Pandas
    query = "SELECT * FROM dados_redash"
    df = pd.read_sql_query(query, conn)
    
    # Fecha a conexão
    conn.close()
    return df

# Executa a função de carga com tratamento de erro
try:
    with st.spinner("Carregando base de dados, aguarde..."):
        df = carregar_dados_do_banco()
    
    st.success(f"✅ Banco carregado com sucesso! Total: {len(df):,} linhas.".replace(',', '.'))

    # --- CRIANDO UM FILTRO INTERATIVO ---
    st.subheader("Filtros")
    
    # Verifica se a coluna que criamos existe para criar um filtro
    if 'ORIGEM_CONSOLIDADA' in df.columns:
        origens = df['ORIGEM_CONSOLIDADA'].unique()
        origem_selecionada = st.selectbox("Selecione a Origem (Usuário Redash):", ["Todas"] + list(origens))
        
        # Aplica o filtro
        if origem_selecionada != "Todas":
            df_mostrar = df[df['ORIGEM_CONSOLIDADA'] == origem_selecionada]
        else:
            df_mostrar = df
    else:
        df_mostrar = df

    # --- EXIBINDO OS DADOS ---
    st.subheader("Visualização dos Dados")
    
    # O st.dataframe renderiza a tabela de forma super rápida e interativa
    st.dataframe(df_mostrar, use_container_width=True)

    # Exemplo extra: Um botão para baixar o que está na tela em CSV
    csv = df_mostrar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar dados filtrados em CSV",
        data=csv,
        file_name='extracao_redash.csv',
        mime='text/csv',
    )

except sqlite3.OperationalError as e:
    st.error(f"❌ Erro: Não foi possível ler a tabela. Verifique se o consolidador já salvou os dados. Detalhes: {e}")
except Exception as e:
    st.error(f"❌ Ocorreu um erro inesperado: {e}")