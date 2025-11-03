import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(
    page_title="Dashboard de Métricas de Mídia (Teste)",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📊 Análise de Métricas de Marketing Digital")
st.markdown("Este dashboard utiliza dados de teste para calcular e gerar insights sobre CPM, CPC, CPL, CTR e CAC.")


# Função para carregar e processar os dados
@st.cache_data
def carregar_e_processar_dados(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo)

    # Garantir que as colunas numéricas estão no formato correto
    colunas_numericas = ['Investimento', 'Impressoes', 'Cliques', 'Leads', 'Novos_Clientes', 'Outros_Custos']
    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 2. CÁLCULO DAS MÉTRICAS

    # CTR (Taxa de Cliques): (Cliques / Impressoes) * 100
    df['CTR'] = (df['Cliques'] / df['Impressoes']) * 100
    df['CTR'] = df['CTR'].apply(lambda x: x if x <= 100 else 0)  # Previne valores > 100%

    # CPC (Custo por Clique): Investimento / Cliques
    df['CPC'] = df['Investimento'] / df['Cliques']

    # CPM (Custo por Mil Impressões): (Investimento / Impressoes) * 1000
    df['CPM'] = (df['Investimento'] / df['Impressoes']) * 1000

    # CPL (Custo por Lead): Investimento / Leads
    df['CPL'] = df['Investimento'] / df['Leads']

    # CAC (Custo de Aquisição de Cliente): (Investimento + Outros_Custos) / Novos_Clientes
    # O CAC aqui é diário. Para um CAC geral, somamos o total.
    df['Custo_Total_Diario'] = df['Investimento'] + df['Outros_Custos']
    df['CAC_Diario'] = df['Custo_Total_Diario'] / df['Novos_Clientes']

    # Tratar valores infinitos ou muito altos (ex: divisão por zero ou muito próximo)
    df = df.replace([float('inf'), -float('inf')], pd.NA).fillna(0)

    return df


# Carregar os dados
df_metricas = carregar_e_processar_dados('dados_metricas_teste.csv')

# --- SIDEBAR (Filtros) ---
st.sidebar.header("Opções de Filtro")

# Seleção de Plataforma
plataforma_selecionada = st.sidebar.multiselect(
    "Filtrar por Plataforma:",
    options=df_metricas['Plataforma'].unique(),
    default=df_metricas['Plataforma'].unique()
)

# Seleção de Campanha
campanha_selecionada = st.sidebar.multiselect(
    "Filtrar por Campanha:",
    options=df_metricas[df_metricas['Plataforma'].isin(plataforma_selecionada)]['Campanha'].unique(),
    default=df_metricas[df_metricas['Plataforma'].isin(plataforma_selecionada)]['Campanha'].unique()
)

# Aplicar Filtros
df_filtrado = df_metricas[
    (df_metricas['Plataforma'].isin(plataforma_selecionada)) &
    (df_metricas['Campanha'].isin(campanha_selecionada))
    ]

# --- PAINEL DE KPIs GERAIS ---
st.header("Métricas Chave (KPIs)")

if not df_filtrado.empty:
    # Agregação para o período total
    total_investimento = df_filtrado['Investimento'].sum()
    total_clientes = df_filtrado['Novos_Clientes'].sum()
    total_leads = df_filtrado['Leads'].sum()

    # KPIs Calculados
    cpc_medio = df_filtrado['CPC'].mean()
    ctr_medio = df_filtrado['CTR'].mean()
    cpl_medio = total_investimento / total_leads if total_leads > 0 else 0

    # CAC Geral (incluindo outros custos)
    cac_geral = df_filtrado['Custo_Total_Diario'].sum() / total_clientes if total_clientes > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("CPC Médio", f"R$ {cpc_medio:.2f}")
    col2.metric("CTR Médio", f"{ctr_medio:.2f}%")
    col3.metric("CPL Médio", f"R$ {cpl_medio:.2f}")
    col4.metric("CAC Geral", f"R$ {cac_geral:.2f}")

    # --- ANÁLISE DETALHADA ---
    st.header("Análise de Campanhas e Insights")

    # Tabela de Campanhas (Agrupamento)
    df_campanhas = df_filtrado.groupby(['Plataforma', 'Campanha']).agg(
        Investimento=('Investimento', 'sum'),
        Leads=('Leads', 'sum'),
        Clientes=('Novos_Clientes', 'sum'),
        CPL_Campanha=('CPL', 'mean'),
        CTR_Campanha=('CTR', 'mean')
    ).reset_index()

    df_campanhas = df_campanhas.rename(columns={
        'CPL_Campanha': 'CPL Médio',
        'CTR_Campanha': 'CTR Médio (%)'
    })

    st.subheader("Performance por Campanha")
    st.dataframe(df_campanhas.style.format({
        'Investimento': 'R$ {:,.2f}',
        'CPL Médio': 'R$ {:.2f}',
        'CTR Médio (%)': '{:.2f}',
    }), use_container_width=True)

    # --- GERAÇÃO DE INSIGHTS AUTOMÁTICOS ---
    st.subheader("💡 Insights Rápidos")

    # Insight 1: CPL Alto
    cpl_limite_alerta = 50.00
    campanhas_cpl_alto = df_campanhas[df_campanhas['CPL Médio'] > cpl_limite_alerta]

    if not campanhas_cpl_alto.empty:
        lista_campanhas = ", ".join(campanhas_cpl_alto['Campanha'].tolist())
        st.error(
            f"⚠️ **Alerta de Custo:** As campanhas **{lista_campanhas}** apresentam CPL médio acima de R$ {cpl_limite_alerta:.2f}. Revise a Landing Page ou o público-alvo.")
    else:
        st.success("✅ **CPL:** Nenhuma campanha está com CPL alarmante no momento.")

    # Insight 2: CTR baixo para Investimento
    if total_investimento > 0 and ctr_medio < 1.0:
        st.warning(
            f"⬇️ **Atenção ao CTR:** O CTR médio geral de {ctr_medio:.2f}% está abaixo do ideal (1.0%). Se o objetivo é tráfego, os criativos podem precisar de melhoria.")

    # --- VISUALIZAÇÃO GRÁFICA ---
    st.header("Visualização da Distribuição")

    col_vis1, col_vis2 = st.columns(2)

    with col_vis1:
        st.subheader("Investimento x Leads (por Campanha)")
        fig_leads = px.scatter(
            df_campanhas,
            x="Investimento",
            y="Leads",
            size="Leads",
            color="Plataforma",
            hover_name="Campanha",
            title="Investimento e Resultado em Leads"
        )
        st.plotly_chart(fig_leads, use_container_width=True)

    with col_vis2:
        st.subheader("Comparativo de Custos (CPC vs CPL)")
        df_custos = df_campanhas.melt(id_vars=['Campanha', 'Plataforma'],
                                      value_vars=['CPL Médio', 'CPL Médio', 'CPL Médio'], var_name='Métrica',
                                      value_name='Valor')
        fig_custos = px.bar(
            df_campanhas.sort_values(by='CPL Médio'),
            x="Campanha",
            y=["CPL Médio"],
            color="Plataforma",
            title="Custo Médio por Lead (CPL)"
        )
        st.plotly_chart(fig_custos, use_container_width=True)

else:
    st.info("Nenhum dado encontrado para os filtros selecionados.")