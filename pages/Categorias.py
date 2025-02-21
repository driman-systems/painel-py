import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# ------------------------------------------------------------------------------
# Configurações iniciais e estilo
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title='Dashboard Vendas Por Categorias',
    layout='wide'
)

paleta_roxos = ["#D6C2E9", "#CAB0EA", "#8A4CCC", "#5D3A7A", "#4A306D"]

def formata_brasil(x):
    # Se x não for numérico, apenas retorna como string
    if pd.isnull(x):
        return "0"
    # Garante inteiro (ou arredonda)
    val_int = int(round(x))
    # Formata com vírgula como separador de milhar e depois troca "," por "."
    return f"{val_int:,}".replace(",", ".")

# CSS para deixar o visual coerente com a primeira página
st.markdown("""
    <style>
        /* Ajuste de tags MultiSelect (lilás) */
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #8A4CCC !important;
            color: white !important;
            border-radius: 8px;
        }

        div[data-baseweb="select"]:focus-within > div {
            border: 1px solid #8A4CCC !important;
        }

        /* Centraliza alguns textos de cabeçalho, se necessário */
        h1, h2, h3, h4 {
            color: #5D3A7A;
            text-align: center;
            font-family: "Arial, sans-serif";
        }

        /* Formatação especial para caixas de destaque (cards) */
        .info-card {
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Título principal
# ------------------------------------------------------------------------------
st.markdown("<h1 style='font-size: 32px; color: #5D3A7A'>📊 Dashboard Vendas por Categoria</h1>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Função para buscar dados da API com cache
# ------------------------------------------------------------------------------
if "dados" not in st.session_state:
    @st.cache_data
    def get_data():
        url = "http://192.168.10.11:5005/contas"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return pd.DataFrame(data)
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Erro ao buscar os dados: {e}")
            return pd.DataFrame()

# ------------------------------------------------------------------------------
# Carregar os dados (usa sessão ou função)
# ------------------------------------------------------------------------------
if "dados" in st.session_state:
    data = st.session_state['dados']
else:
    data = get_data()

# ------------------------------------------------------------------------------
# Se dados estiverem disponíveis, processa
# ------------------------------------------------------------------------------
if not data.empty:
    # Conversão de colunas para evitar erros
    data['conta'] = data['conta'].astype(str)
    data['Ano'] = data['Ano'].astype(str)
    data['Mes'] = data['Mes'].astype(int)
    data['Dia'] = data['Dia'].astype(str)
    data['TotalLiq'] = data['TotalLiq'].astype(float)

    # Mapeamento de número do mês para nome
    meses_nomes = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    data["Mes_Nome"] = data["Mes"].map(meses_nomes)

    # Ano e mês atuais (para usar como default)
    ano_atual = str(datetime.now().year)
    mes_atual = meses_nomes[datetime.now().month]

    # Opções para filtros (com "Todos" incluído)
    opcoes_empresa = ["Todos"] + sorted(data["Empresa"].unique())
    opcoes_ano = ["Todos"] + sorted(data["Ano"].unique())
    opcoes_mes = ["Todos"] + list(meses_nomes.values())  # Usa todos os nomes de mês
    opcoes_categoria = ["Todos"] + sorted(data["Categoria"].unique())

    # ------------------------------------------------------------------------------
    # SIDEBAR - Filtros
    # ------------------------------------------------------------------------------
    empresas_selecionadas = st.sidebar.multiselect(
        "Empresa", 
        options=opcoes_empresa, 
        default=["Todos"]
    )
    anos_selecionados = st.sidebar.multiselect(
        "Ano", 
        options=opcoes_ano, 
        default=[ano_atual]
    )
    meses_selecionados = st.sidebar.multiselect(
        "Mês", 
        options=opcoes_mes, 
        default=[mes_atual]
    )
    categorias_selecionadas = st.sidebar.multiselect(
        "Categoria", 
        options=opcoes_categoria, 
        default=["Todos"]
    )

    # ------------------------------------------------------------------------------
    # Aplicando filtros
    # ------------------------------------------------------------------------------
    df_filtrado = data.copy()
    
    df_filtrado["Dia"] = pd.to_numeric(df_filtrado["Dia"], errors="coerce")

    if "Todos" not in empresas_selecionadas:
        df_filtrado = df_filtrado[df_filtrado["Empresa"].isin(empresas_selecionadas)]

    if "Todos" not in anos_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Ano"].isin(anos_selecionados)]

    if "Todos" not in meses_selecionados:
        df_filtrado = df_filtrado[df_filtrado["Mes_Nome"].isin(meses_selecionados)]

    if "Todos" not in categorias_selecionadas:
        df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(categorias_selecionadas)]

    # ------------------------------------------------------------------------------
    # MÉTRICAS PRINCIPAIS
    # ------------------------------------------------------------------------------
    total_geral = df_filtrado["TotalLiq"].sum()
    total_servicos = df_filtrado["servico"].sum()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="info-card" style="background-color: #D6C2E9; color: #5D3A7A; text-align: 'center'">
            <h3>💰 Total Geral</h3>
            <h2>R$ {formata_brasil(total_geral)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="info-card" style="background-color: #D6C2E9; color: #5D3A7A">
            <h3>🛠️ Total de Serviços</h3>
            <h2>R$ {formata_brasil(total_servicos)}</h2>
        </div>
        """, unsafe_allow_html=True)

    # ------------------------------------------------------------------------------
    # TABELA DE RESUMO POR CATEGORIA
    # ------------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 30px;'>📋 Resumo por Categoria</h1>", unsafe_allow_html=True)

    df_categorias = df_filtrado.groupby("Categoria").agg(
        Quantidade=("QTD", "sum"),
        Total=("TotalLiq", "sum")
    ).reset_index()

    # Adicionar coluna de participação no total (%)
    if df_categorias["Total"].sum() > 0:
        df_categorias["% Part"] = (df_categorias["Total"] / df_categorias["Total"].sum()) * 100
    else:
        df_categorias["% Part"] = 0

    # Formatação de valores
    df_categorias["Total"] = df_categorias["Total"].apply(lambda x: f'R$ {x:,.2f}')
    df_categorias["% Part"] = df_categorias["% Part"].apply(lambda x: f'{x:.2f}%')

    # Linha de total
    total_sum = (
        df_categorias["Total"]
        .replace('[R$ ,]', '', regex=True)
        .astype(float)
        .sum()
    )

    total_row = pd.DataFrame({
        "Categoria": ["Total"],
        "Quantidade": [df_categorias["Quantidade"].sum()],
        "Total": [f'R$ {total_sum:,.2f}'],
        "% Part": ["100.00%"]
    })

    # Concatena o totalizador
    df_categorias = pd.concat([df_categorias, total_row], ignore_index=True)

    # Configuração AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_categorias)
    gb.configure_default_column(
        resizable=True,
        auto_size=True,
        wrap_text=True
    )
    gb.configure_grid_options(domLayout='autoHeight')
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()

    # Estilo para a linha final (Total)
    custom_css = {
        ".ag-row-last": {
            "fontWeight": "bold",
            "fontSize": "15px",
            "backgroundColor": "#E8E8E8 !important"
        }
    }

    AgGrid(
        df_categorias,
        gridOptions=gb.build(),
        theme="balham",
        height=400,
        fit_columns_on_grid_load=True,
        custom_css=custom_css
    )

    # ------------------------------------------------------------------------------
    # GRÁFICO DE BARRAS - FATURAMENTO POR CATEGORIA
    # ------------------------------------------------------------------------------
    st.markdown("---")
    # Converter "Total" para número antes de plotar
    df_categorias["Total_num"] = (
        df_categorias["Total"]
        .replace('[R$ ,]', '', regex=True)
        .astype(float)
    )

    fig = px.bar(
        df_categorias,
        x="Total_num",
        y="Categoria",
        orientation='h',
        text="Total",
        title="💰 Faturamento por Categoria",
        color="Total_num",
        color_continuous_scale=px.colors.sequential.Purples_r
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        title={
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=22, family="Arial, sans-serif", color="#5D3A7A")
        },
        yaxis_title="Categoria",
        xaxis_title="",
        showlegend=False,
        plot_bgcolor="white",
        xaxis=dict(showgrid=True),
        yaxis=dict(showgrid=False),
        font=dict(size=14)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------------------
    # TABELA DINÂMICA - QUANTIDADE POR DIA
    # ------------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 30px;'>📋 Quantidade por Dia e Categoria</h1>", unsafe_allow_html=True)

    df_pivot = df_filtrado.pivot_table(
        index="Categoria", 
        columns="Dia", 
        values="QTD", 
        aggfunc="sum",
        margins=True,
        margins_name='Total',
        fill_value=0
    )
    
    df_pivot_ft = df_pivot.style.format(
        subset=df_pivot.columns[1:],
        formatter=formata_brasil
    )

    st.dataframe(df_pivot_ft)

    # ------------------------------------------------------------------------------
    # TABELA DINÂMICA - TOTAL LÍQUIDO POR DIA
    # ------------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 30px;'>💰 Total Líquido por Dia e Categoria</h1>", unsafe_allow_html=True)

    df_pivot_total = df_filtrado.pivot_table(
        index="Categoria", 
        columns="Dia", 
        values="TotalLiq", 
        aggfunc="sum", 
        fill_value=0,
        margins=True,
        margins_name='Total'
    )
    
    df_pivot_total_ft = df_pivot_total.style.format(
        subset=df_pivot.columns[1:],
        formatter=formata_brasil
    )

    st.dataframe(df_pivot_total_ft)
    # ------------------------------------------------------------------------------
    # GRÁFICO DE LINHA - TENDÊNCIA DE FATURAMENTO POR DIA
    # ------------------------------------------------------------------------------
    st.markdown("---")
    
    df_trend = df_filtrado.pivot_table(
        index="Dia", 
        columns="Categoria", 
        values="TotalLiq", 
        aggfunc="sum", 
        fill_value=0
    ).reset_index()

    df_trend_long = df_trend.melt(
        id_vars=["Dia"], 
        var_name="Categoria", 
        value_name="Faturamento"
    )

    fig = px.line(
        df_trend_long,
        x="Dia",
        y="Faturamento",
        color="Categoria",
        markers=True,
        line_shape="spline",
        title="📈 Tendência de Vendas por Dia"
    )

    fig.update_layout(
        title={
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=22, family="Arial, sans-serif", color="#5D3A7A")
        },
        xaxis_title="Dia do Mês", 
        yaxis_title="Faturamento (R$)",
        plot_bgcolor="white",
        legend_title="Categoria",
        xaxis=dict(showgrid=True, gridcolor="lightgray"),
        yaxis=dict(showgrid=True, gridcolor="lightgray"),
        font=dict(size=14)
    )
    fig.update_traces(mode="lines+markers", line=dict(width=2, dash="dot"))
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------------------
    # GRÁFICO DE BARRAS AGRUPADAS - VENDAS POR DIA DA SEMANA
    # ------------------------------------------------------------------------------
    st.markdown("---")
    
    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 30px;'></h1>")

    # Converter "Data" para datetime
    df_filtrado["Data"] = pd.to_datetime(df_filtrado["Data"], errors="coerce")

    # Criar a coluna com os dias da semana
    df_filtrado["Dia_Semana"] = df_filtrado["Data"].dt.day_name()

    # Traduzir dias para português
    traducao_dias = {
        "Monday": "Segunda-feira",
        "Tuesday": "Terça-feira",
        "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira",
        "Friday": "Sexta-feira",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }
    df_filtrado["Dia_Semana"] = df_filtrado["Dia_Semana"].map(traducao_dias)

    # Ordenação correta
    dias_semana_ordenados = [
        "Segunda-feira", "Terça-feira", "Quarta-feira",
        "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"
    ]
    df_filtrado = df_filtrado[df_filtrado["Dia_Semana"].notna()]

    df_semana = df_filtrado.pivot_table(
        index="Dia_Semana",
        columns="Categoria",
        values="TotalLiq",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    # Força a ordem
    df_semana["Dia_Semana"] = pd.Categorical(
        df_semana["Dia_Semana"],
        categories=dias_semana_ordenados,
        ordered=True
    )
    df_semana = df_semana.sort_values("Dia_Semana")

    df_long = df_semana.melt(
        id_vars=["Dia_Semana"],
        var_name="Categoria",
        value_name="Faturamento"
    )

    fig = px.bar(
        df_long,
        x="Dia_Semana",
        y="Faturamento",
        color="Categoria",
        text_auto=True,
        barmode="group",
        title="📊 Vendas por Dia da Semana",
        color_continuous_scale=px.colors.sequential.Purples_r
    )
    fig.update_layout(
        title={
            "x": 0.5,
            "xanchor": "center",
            "font": dict(size=22, family="Arial, sans-serif", color="#5D3A7A")
        },
        xaxis_title="Dia da Semana",
        yaxis_title="Faturamento (R$)",
        plot_bgcolor="white",
        legend_title="Categoria",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True),
        font=dict(size=14)
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    # Caso o DataFrame esteja vazio ou se houve erro na requisição
    st.warning("Não foi possível carregar os dados ou não há dados disponíveis.")
