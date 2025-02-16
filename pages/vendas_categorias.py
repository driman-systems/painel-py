import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# Configuração inicial do Streamlit
st.set_page_config(page_title='Dashboard Vendas Por Categorias', layout='wide')
st.markdown("<h1 style='color: #5D3A7A; text-align: center;'>📊 Dashboard Vendas Por Categoria</h1>", unsafe_allow_html=True)

# Função para buscar dados da API com cache
@st.cache_data
def get_data():
    url = "http://192.168.10.11:5005/contas"  # Substituir pela sua API real
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao buscar os dados: {e}")
        return pd.DataFrame()

# Carregar os dados
data = get_data()

if not data.empty:
    # Conversão de colunas para evitar erros
    data['conta'] = data['conta'].astype(str)
    data['Ano'] = data['Ano'].astype(str)
    data['Mes'] = data['Mes'].astype(int)  # Converter para número inteiro
    data['Dia'] = data['Dia'].astype(str)

    # Criar dicionário para mapear número do mês para nome
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    
    # Criar uma coluna com os nomes dos meses
    data["Mes_Nome"] = data["Mes"].map(meses_nomes)

    # Definir valores padrão (Ano e Mês atual)
    ano_atual = str(datetime.now().year)
    mes_atual = meses_nomes[datetime.now().month]

    # Criar opções dos filtros com "Todos" como primeiro item
    opcoes_empresa = ["Todos"] + list(data["Empresa"].unique())
    opcoes_ano = ["Todos"] + list(data["Ano"].unique())
    opcoes_mes = ["Todos"] + list(data["Mes_Nome"].unique())  # Agora usa os nomes dos meses
    opcoes_categoria = ["Todos"] + list(data["Categoria"].unique())

    # --- 🎯 Filtros Interativos ---
    with st.expander("🔍 **Filtros**", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        empresas_selecionadas = col1.multiselect("Empresa", options=opcoes_empresa, default=["Todos"])
        anos_selecionados = col2.multiselect("Ano", options=opcoes_ano, default=[ano_atual])
        meses_selecionados = col3.multiselect("Mês", options=opcoes_mes, default=[mes_atual])
        categorias_selecionadas = col4.multiselect("Categoria", options=opcoes_categoria, default=["Todos"])

    # --- 🔍 Aplicar Filtros nos Dados ---
    df_filtrado = data.copy()
    
    # Filtrar Empresa
    if "Todos" not in empresas_selecionadas:
        df_filtrado = df_filtrado[df_filtrado["Empresa"].isin(empresas_selecionadas)]
    
    # Filtrar Ano
    if "Todos" not in anos_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Ano"].isin(anos_selecionados)]
    
    # Filtrar Mês
    if "Todos" not in meses_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Mes_Nome"].isin(meses_selecionados)]
    
    # Filtrar Categoria
    if "Todos" not in categorias_selecionadas:
        df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(categorias_selecionadas)]

    # --- 🔢 Métricas Principais ---
    total_geral = df_filtrado["TotalLiq"].sum()
    total_servicos = df_filtrado["servico"].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style="background-color: #c7a2e6; padding: 20px; border-radius: 10px; text-align: center;">
            <h3 style="color: #4a306d;">💰 Total Geral</h3>
            <h1 style="color: #4a306d;">R$ {total_geral:,.2f}</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: #a3c4e6; padding: 20px; border-radius: 10px; text-align: center;">
            <h3 style="color: #2a406d;">🛠️ Total de Serviços</h3>
            <h1 style="color: #2a406d;">R$ {total_servicos:,.2f}</h1>
        </div>
        """, unsafe_allow_html=True)


    # --- 📋 Exibir dados filtrados ---
    #st.dataframe(df_filtrado)
    
# --- 📊 Criar tabela de resumo ---
df_categorias = df_filtrado.groupby("Categoria").agg(
    Quantidade=("QTD", "sum"),
    Total=("TotalLiq", "sum")
).reset_index()

# Adicionar coluna de participação no total (%)
df_categorias["% Part"] = (df_categorias["Total"] / df_categorias["Total"].sum()) * 100

# Formatar valores
df_categorias["Total"] = df_categorias["Total"].apply(lambda x: f'${x:,.0f}')
df_categorias["% Part"] = df_categorias["% Part"].apply(lambda x: f'{x:.2f}%')

# Criar totalizadores corretamente
total_sum = df_categorias["Total"].replace('[\$,]', '', regex=True).astype(float).sum()

total_row = pd.DataFrame({
    "Categoria": ["Total"],
    "Quantidade": [df_categorias["Quantidade"].sum()],
    "Total": [f'${total_sum:,.0f}'],
    "% Part": ["100.00%"]
})

# Concatenar totalizador ao dataframe original
df_categorias = pd.concat([df_categorias, total_row], ignore_index=True)

# Criar configuração interativa da tabela
gb = GridOptionsBuilder.from_dataframe(df_categorias)

# Permitir redimensionamento automático das colunas
gb.configure_default_column(
    resizable=True,
    auto_size=True,
    wrap_text=True
)

# Configurar estilos personalizados para o totalizador (negrito e maior)
custom_css = {
    ".ag-row-last": {
        "fontWeight": "bold",
        "fontSize": "16px",
        "backgroundColor": "#E8E8E8 !important"
    }
}

# Aplicar estilos às colunas
gb.configure_grid_options(domLayout='autoHeight')

# Adicionar paginação e barra lateral
gb.configure_pagination(paginationAutoPageSize=True)
gb.configure_side_bar()

st.markdown("<h3 style='text-align: center;'>📋 Resumo por Categoria</h3>", unsafe_allow_html=True)
AgGrid(df_categorias, gridOptions=gb.build(), theme="balham", height=400, fit_columns_on_grid_load=True, custom_css=custom_css)

import plotly.express as px

# Converter "Total" para número antes de plotar o gráfico
df_categorias["Total_num"] = df_categorias["Total"].replace('[\$,]', '', regex=True).astype(float)

# Criar gráfico de barras horizontais
fig = px.bar(df_categorias, 
             x="Total_num", 
             y="Categoria", 
             orientation='h', 
             text=df_categorias["Total"], 
             title="💰 Faturamento por Categoria",
             color="Total_num",
             color_continuous_scale="blues")

fig.update_traces(textposition="outside")

# Configurar layout do gráfico
fig.update_layout(
    title={
        "text": "💰 Faturamento por Categoria",
        "x": 0.5,  # Centraliza o título
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(size=30, family="Arial, sans-serif", color="black")  # Ajusta fonte
    },
    yaxis_title="Categoria", 
    xaxis_title="", 
    showlegend=False, 
    plot_bgcolor="white",
    xaxis=dict(showgrid=True, gridcolor="lightgray"),
    yaxis=dict(showgrid=False),
    font=dict(size=14)  # Ajusta fonte dos eixos
)

# Exibir gráfico
st.plotly_chart(fig, use_container_width=True)

# Criar tabela dinâmica com soma da quantidade por categoria e dia
df_pivot = df_filtrado.pivot_table(
    index="Categoria", 
    columns="Dia", 
    values="QTD", 
    aggfunc="sum", 
    fill_value=0
).reset_index()

# Adicionar coluna de total por categoria
df_pivot["Total"] = df_pivot.iloc[:, 1:].sum(axis=1)

# Adicionar linha de totalizador geral (soma das colunas)
total_row = pd.DataFrame(df_pivot.iloc[:, 1:].sum(axis=0)).T
total_row.insert(0, "Categoria", "Total")  # Nome da categoria na linha total

# Concatenar totalizador à tabela dinâmica
df_pivot = pd.concat([df_pivot, total_row], ignore_index=True)

# Criar configuração interativa da tabela
gb = GridOptionsBuilder.from_dataframe(df_pivot)

# Permitir redimensionamento automático das colunas
gb.configure_default_column(
    resizable=True,
    auto_size=True,
    wrap_text=True
)

# **Fixar a coluna "Categoria"**
gb.configure_column("Categoria", pinned="left")  # Mantém a coluna fixa ao rolar

# **Garantir que a última linha (total) fique visível**
gb.configure_grid_options(domLayout='normal')

# Ajustar estilos para destacar totalizadores
cell_style = {
    "styleConditions": [
        {
            "condition": 'params.value == "Total"',  # Linha de total
            "style": {"fontWeight": "bold", "fontSize": "16px", "backgroundColor": "#E8E8E8"}
        },
        {
            "condition": "rowIndex == df_pivot.index[-1]",  # Última linha (total)
            "style": {"fontWeight": "bold", "fontSize": "16px", "backgroundColor": "#E8E8E8"}
        },
        {
            "condition": f'colId == "Total"',  # Última coluna (total)
            "style": {"fontWeight": "bold", "fontSize": "16px", "backgroundColor": "#E8E8E8"}
        }
    ]
}

# Aplicar estilos às colunas e linhas de totalizadores
gb.configure_column("Categoria", cellStyle=cell_style)
gb.configure_column("Total", cellStyle=cell_style)

# Exibir tabela dinâmica com fixação da coluna de categoria
st.markdown("<h3 style='text-align: center;'>📋 Quantidade por Dia e Categoria</h3>", unsafe_allow_html=True)
AgGrid(df_pivot, gridOptions=gb.build(), theme="balham", height=400, fit_columns_on_grid_load=True)

# Criar tabela dinâmica com soma do Total Líquido por categoria e dia
df_pivot_total = df_filtrado.pivot_table(
    index="Categoria", 
    columns="Dia", 
    values="TotalLiq",  # Agora usamos "TotalLiq" ao invés de "QTD"
    aggfunc="sum", 
    fill_value=0
).reset_index()

# Adicionar coluna de total por categoria (removendo centavos)
df_pivot_total["Total"] = df_pivot_total.iloc[:, 1:].sum(axis=1).astype(int)

# Adicionar linha de totalizador geral (soma das colunas)
total_row = pd.DataFrame(df_pivot_total.iloc[:, 1:].sum(axis=0)).T
total_row.insert(0, "Categoria", "Total")  # Nome da categoria na linha total

# Concatenar totalizador à tabela dinâmica
df_pivot_total = pd.concat([df_pivot_total, total_row], ignore_index=True)

# **Remover centavos formatando valores monetários**
for col in df_pivot_total.columns[1:]:  # Ignora a coluna "Categoria"
    df_pivot_total[col] = df_pivot_total[col].apply(lambda x: f'R$ {int(x):,}'.replace(",", "."))

# Criar configuração interativa da tabela
gb = GridOptionsBuilder.from_dataframe(df_pivot_total)

# Permitir redimensionamento automático das colunas
gb.configure_default_column(
    resizable=True,
    auto_size=True,
    wrap_text=True
)

# **Fixar a coluna "Categoria"**
gb.configure_column("Categoria", pinned="left")  # Mantém a coluna fixa ao rolar

# **Garantir que a última linha (total) fique visível**
gb.configure_grid_options(domLayout='normal')

# Ajustar estilos para destacar totalizadores
cell_style = {
    "styleConditions": [
        {
            "condition": 'params.value == "Total"',  # Linha de total
            "style": {"fontWeight": "bold", "fontSize": "16px", "backgroundColor": "#E8E8E8"}
        },
        {
            "condition": "rowIndex == df_pivot_total.index[-1]",  # Última linha (total)
            "style": {"fontWeight": "bold", "fontSize": "16px", "backgroundColor": "#E8E8E8"}
        },
        {
            "condition": f'colId == "Total"',  # Última coluna (total)
            "style": {"fontWeight": "bold", "fontSize": "16px", "backgroundColor": "#E8E8E8"}
        }
    ]
}

# Aplicar estilos às colunas e linhas de totalizadores
gb.configure_column("Categoria", cellStyle=cell_style)
gb.configure_column("Total", cellStyle=cell_style)

# Exibir tabela dinâmica com fixação da coluna de categoria
st.markdown("<h3 style='text-align: center;'>💰 Total Líquido por Dia e Categoria</h3>", unsafe_allow_html=True)
AgGrid(df_pivot_total, gridOptions=gb.build(), theme="balham", height=400, fit_columns_on_grid_load=True)


import plotly.express as px

# Criar tabela dinâmica com soma do Total Líquido por categoria e dia
df_trend = df_filtrado.pivot_table(
    index="Dia", 
    columns="Categoria", 
    values="TotalLiq", 
    aggfunc="sum", 
    fill_value=0
).reset_index()

# Transformar o DataFrame para formato longo (long format) para o Plotly
df_trend_long = df_trend.melt(id_vars=["Dia"], var_name="Categoria", value_name="Faturamento")

# Criar gráfico de linha com tendência de vendas por dia
fig = px.line(df_trend_long, 
              x="Dia", 
              y="Faturamento", 
              color="Categoria", 
              markers=True, 
              line_shape="spline", 
              title="📈 Tendência de Vendas por Dia")

# Ajustar layout do gráfico
fig.update_layout(
    title={
        "x": 0.5,  # Centralizar título
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(size=20, family="Arial, sans-serif", color="black")
    },
    xaxis_title="Dia do Mês", 
    yaxis_title="Faturamento (R$)", 
    plot_bgcolor="white",
    legend_title="Categoria",
    xaxis=dict(showgrid=True, gridcolor="lightgray"),
    yaxis=dict(showgrid=True, gridcolor="lightgray"),
    font=dict(size=14)
)

# Ajustar formato dos valores e a linha tracejada para melhor visualização
fig.update_traces(mode="lines+markers", line=dict(width=2, dash="dot"))

# Exibir gráfico
st.plotly_chart(fig, use_container_width=True)

import plotly.express as px
import pandas as pd

# **Converter a coluna de Data para datetime**
df_filtrado["Data"] = pd.to_datetime(df_filtrado["Data"], errors="coerce")

# **Criar a coluna com os dias da semana corretamente**
df_filtrado["Dia_Semana"] = df_filtrado["Data"].dt.day_name()

# **Dicionário para traduzir os dias da semana**
traducao_dias = {
    "Monday": "Segunda-feira",
    "Tuesday": "Terça-feira",
    "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

# **Traduzir os dias para português**
df_filtrado["Dia_Semana"] = df_filtrado["Dia_Semana"].map(traducao_dias)

# **Ordenação correta dos dias da semana**
dias_semana_ordenados = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

# **Filtrar apenas linhas com dias válidos**
df_filtrado = df_filtrado[df_filtrado["Dia_Semana"].notna()]

# **Criar tabela dinâmica somando o faturamento por categoria e dia da semana**
df_semana = df_filtrado.pivot_table(
    index="Dia_Semana",
    columns="Categoria",
    values="TotalLiq",
    aggfunc="sum",
    fill_value=0
).reset_index()

# **Corrigir a ordenação dos dias**
df_semana["Dia_Semana"] = pd.Categorical(df_semana["Dia_Semana"], categories=dias_semana_ordenados, ordered=True)
df_semana = df_semana.sort_values("Dia_Semana")

# **Transformar o DataFrame para formato longo para o Plotly**
df_long = df_semana.melt(id_vars=["Dia_Semana"], var_name="Categoria", value_name="Faturamento")

# **Criar gráfico de barras agrupadas**
fig = px.bar(df_long,
             x="Dia_Semana",
             y="Faturamento",
             color="Categoria",
             text_auto=True,
             barmode="group",
             title="📊 Vendas por Dia da Semana")

# **Ajustar layout do gráfico**
fig.update_layout(
    title={
        "x": 0.5,  # Centraliza o título
        "xanchor": "center",
        "yanchor": "top",
        "font": dict(size=20, family="Arial, sans-serif", color="black")
    },
    xaxis_title="Dia da Semana",
    yaxis_title="Faturamento (R$)",
    plot_bgcolor="white",
    legend_title="Categoria",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="lightgray"),
    font=dict(size=14)
)

# **Exibir gráfico no Streamlit**
st.plotly_chart(fig, use_container_width=True)
