import streamlit as st
import pandas as pd
import requests
from babel.numbers import format_currency


st.set_page_config(page_title='Dash Vendas de Parceiros', layout='wide')

st.markdown("""
    <style>
        .stMultiSelect [data-baseweb="tag"] {
            background-color: #8A4CCC !important;
            color: white !important;
            border-radius: 8px;
        }
        
        div[data-baseweb="select"]:focus-within > div {
            border: 1px solid #8A4CCC !important;
        }
    </style>
""", unsafe_allow_html=True)

def bloco_categoria(nome, valor, perc):
            return f"""
                <div style="margin-top: 15px;">
                    <p style='font-size: 14px; font-weight: bold; margin-bottom: -2px;'>{nome}</p>
                    <p style='font-size: 16px; margin-bottom: -2px;'>{format_currency(valor, 'BRL', locale='pt_BR')}</p>
                    <p style='font-size: 12px; margin-bottom: 2px; color: #D6C2E9;'> <span style='font-size: 5px;'>🟣</span> {perc:.2f}%</p>
                </div>
            """


def colorir_percentual_texto(val):
    try:
        if isinstance(val, str) and "%" in val:
            val_num = float(val.replace("%", "").replace(",", "."))
            cor = "red"
            if val_num >= 100:
                cor = "green"
            elif 95 <= val_num < 100:
                cor = "orange"
            return f'color: {cor};'
    except:
        pass
    return ''

st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center;'>📊 Dashboard de Contas</h1>", unsafe_allow_html=True)


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

data = get_data()

st.session_state['dados'] = data

if not data.empty:
    data['conta'] = data['conta'].astype(str)
    categorias_principais = ['Venda própria', 'Laçador', 'Tche', 'Prime']
    categorias_secundarias = ['Bebidas', 'Souvenir', 'Cozinha', 'Extras']
    todas_categorias = categorias_principais + categorias_secundarias

    empresas = ['Todos'] + sorted(data['Empresa'].unique().tolist())
    anos = ['Todos'] + sorted(data['Ano'].unique().tolist())
    meses_dict = {i: mes for i, mes in enumerate(['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'], 1)}
    data['Mes_Extenso'] = data['Mes'].map(meses_dict)
    meses = ['Todos'] + list(meses_dict.values())
    dias = ['Todos'] + sorted(data['Dia'].unique().tolist())

    empresa_filtro = st.sidebar.multiselect("Empresa", empresas, default=['Todos'])
    ano_filtro = st.sidebar.multiselect("Ano", anos, default=['Todos'])
    mes_filtro = st.sidebar.multiselect("Mês", meses, default=['Todos'])
    dia_filtro = st.sidebar.multiselect("Dia", dias, default=['Todos'])

    if 'Todos' not in empresa_filtro:
        data = data[data['Empresa'].isin(empresa_filtro)]
    if 'Todos' not in ano_filtro:
        data = data[data['Ano'].isin(ano_filtro)]
    if 'Todos' not in mes_filtro:
        data = data[data['Mes_Extenso'].isin(mes_filtro)]
    if 'Todos' not in dia_filtro:
        data = data[data['Dia'].isin(dia_filtro)]

    total_geral = data[data['Categoria'].isin(todas_categorias)][['TotalLiq', 'servico']].sum().sum()

    st.markdown(f"""
        <div style="background-color: #D6C2E9; padding: 15px; border-radius: 10px; text-align: center;">
            <h4 style="color: #5D3A7A; margin-bottom: -5px;">Total Geral Vouchers + Contas
            <h3 style="color: #5D3A7A;">💰 {format_currency(total_geral, 'BRL', locale='pt_BR')}</h3></h4>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    colunas = st.columns(4)

for i, categoria_principal in enumerate(categorias_principais):
    contas_relacionadas = data[data['conta'].isin(data[data['Categoria'] == categoria_principal]['conta'].unique())]
    valor_liquido_principal = contas_relacionadas['TotalLiq'].sum()
    valor_servico_principal = contas_relacionadas['servico'].sum()
    valor_principal = valor_liquido_principal + valor_servico_principal
    perc_valor_principal = (valor_principal / total_geral * 100) if total_geral > 0 else 0

    # Filtrar apenas as contas que têm a categoria principal para o cálculo do ticket médio
    contas_categoria_principal = data[data['Categoria'] == categoria_principal]
    valor_categoria_principal = contas_categoria_principal['TotalLiq'].sum()
    qtd_categoria_principal = contas_categoria_principal['QTD'].sum()
    ticket_medio = valor_principal / qtd_categoria_principal if qtd_categoria_principal > 0 else 0

    perc_categoria_principal = (valor_categoria_principal / valor_principal * 100) if valor_principal > 0 else 0
    servico_total = contas_relacionadas['servico'].sum()
    perc_servico = (servico_total / valor_liquido_principal * 100) if valor_principal > 0 else 0

    subcategorias = contas_relacionadas[contas_relacionadas['Categoria'].isin(categorias_secundarias)]
    subcategorias_agrupadas = subcategorias.groupby('Categoria')['TotalLiq'].sum().to_dict()

    with colunas[i]:
        st.subheader(f"**{categoria_principal}**")

        # Exibir Ticket Médio acima do valor principal
        st.markdown(f"<p style='font-size: 16px; margin-bottom: -5px;'>🪙 <b>Ticket Médio:</b> {format_currency(ticket_medio, 'BRL', locale='pt_BR')}</p>", unsafe_allow_html=True)

        st.markdown(f"<h4 style='color: #A67DB8; margin-bottom: -5px;'>{format_currency(valor_principal, 'BRL', locale='pt_BR')}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 12px; margin-top: -5px;'><span style='font-size: 5px;'>🟣</span> {perc_valor_principal:.2f}%</p>", unsafe_allow_html=True)
        
        # Rodízio
        st.markdown(bloco_categoria("Rodízio", valor_categoria_principal, perc_categoria_principal), unsafe_allow_html=True)

        # Serviço
        st.markdown(bloco_categoria("Serviço", servico_total, perc_servico), unsafe_allow_html=True)

        # Subcategorias
        for subcategoria, valor in subcategorias_agrupadas.items():
            percentual_categoria = (valor / valor_principal * 100) if valor_principal > 0 else 0
            st.markdown(bloco_categoria(subcategoria, valor, percentual_categoria), unsafe_allow_html=True)

                
#######################################   REALIZADO POR DIA (PAX)  ##################################################################

st.divider()

def highlight_totals(val):
    return 'color: #8A4CCC; font-weight: bold;' if val != '-' else ''

def format_milhar(val):
    try:
        if pd.isna(val) or val == 0:
            return "-"
        return "{:,.0f}".format(int(val)).replace(",", ".")
    except (ValueError, TypeError):
        return "-"

def format_moeda(val):
    try:
        if pd.isna(val) or val == 0:
            return "-"
        return format_currency(val, 'BRL', locale='pt_BR')
    except (ValueError, TypeError):
        return "-"

@st.cache_data
def load_metas():
    metas = pd.read_excel('./Metas_Ajustadas_Sem_Domingos_Gatzz.xlsx', sheet_name="Sheet1")
    metas['Meta_Diária'] = pd.to_numeric(metas['Meta_Diária'], errors='coerce').fillna(0)
    return metas

# Carregar os dados de metas
metas_diarias = load_metas()

if 'Todos' not in empresa_filtro:
    metas_diarias = metas_diarias[metas_diarias['Empresa'].isin(empresa_filtro)]
if 'Todos' not in ano_filtro:
    metas_diarias = metas_diarias[metas_diarias['Ano'].isin(ano_filtro)]
if 'Todos' not in mes_filtro:
    metas_diarias = metas_diarias[metas_diarias['Mês'].isin(mes_filtro)]
if 'Todos' not in dia_filtro:
    metas_diarias = metas_diarias[metas_diarias['Dia'].isin(dia_filtro)]

data_filtrado = data[data['Categoria'].isin(categorias_principais)]

tabela_realizado = data_filtrado.pivot_table(
        index=['Categoria'], 
        columns='Dia', 
        values='QTD', 
        aggfunc='sum',
        margins=True,
        margins_name='Total'
    ).fillna(0)

if not tabela_realizado.empty:
    # Adicionar linha e coluna de total
    colunas_numericas = tabela_realizado.select_dtypes(include='number').columns
    tabela_realizado[colunas_numericas] = tabela_realizado[colunas_numericas].map(format_milhar)

    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 30px;'>📊 Realizado por dia (Pax)</h1>", unsafe_allow_html=True)


    st.dataframe(
        tabela_realizado.style.map(
            highlight_totals,
            subset=pd.IndexSlice[['Total'], :]
        ).map(
            highlight_totals,
            subset=pd.IndexSlice[:, ['Total']]
        )
    )
else:
    st.warning("Nenhum dado disponível para exibir.")

####################################   REALIZADO POR DIA (VALOR LÍQUIDO)  ############################################################

st.divider()

tabela_realizado_valor = data_filtrado.pivot_table(
    index=['Categoria'], 
    columns='Dia', 
    values='TotalLiq',
    aggfunc='sum',
    margins=True,
    margins_name='Total'
).fillna(0)

if not tabela_realizado_valor.empty:
    # Aplicando formatação de milhar
    colunas_numericas_valor = tabela_realizado_valor.select_dtypes(include='number').columns
    tabela_realizado_valor[colunas_numericas_valor] = tabela_realizado_valor[colunas_numericas_valor].map(format_moeda)

    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 30px;'>📊 Realizado por dia (Valor Líquido)</h1>", unsafe_allow_html=True)


    st.dataframe(
        tabela_realizado_valor.style.map(
            highlight_totals,
            subset=pd.IndexSlice[['Total'], :]
        ).map(
            highlight_totals,
            subset=pd.IndexSlice[:, ['Total']]
        )
    )
else:
    st.warning("Nenhum dado disponível para exibir.")

############################### METAS DIARIAS X QUANTIDADE REALIZADA #####################################################

st.divider()

# Filtrar apenas categorias principais
metas_diarias = metas_diarias[metas_diarias['Categoria'].isin(categorias_principais)]

# Tabela de Metas (Quantidade)
tabela_metas_diarias_qtd = metas_diarias.pivot_table(
    index=['Categoria'], 
    columns='Dia', 
    values='Meta_Diária',
    aggfunc='sum'
).fillna(0)

# Tabela de Realizado (Quantidade)
tabela_realizado_qtd = data_filtrado.pivot_table(
    index=['Categoria'], 
    columns='Dia', 
    values='QTD', 
    aggfunc='sum'
).fillna(0)


dias_comuns = sorted(set(tabela_metas_diarias_qtd.columns) | set(tabela_realizado_qtd.columns))
tabela_metas_diarias_qtd = tabela_metas_diarias_qtd.reindex(columns=dias_comuns, fill_value=0)
tabela_realizado_qtd = tabela_realizado_qtd.reindex(columns=dias_comuns, fill_value=0)

# Calcular Porcentagem de Alcance
tabela_percentual_alcance = tabela_realizado_qtd / tabela_metas_diarias_qtd * 100
tabela_percentual_alcance = tabela_percentual_alcance.fillna(0)

# Montar DataFrame Final lado a lado
tabela_comparativa = pd.DataFrame()

for dia in dias_comuns:
    tabela_comparativa[(dia, 'Meta')] = tabela_metas_diarias_qtd[dia]
    tabela_comparativa[(dia, 'Realizado')] = tabela_realizado_qtd[dia]
    tabela_comparativa[(dia, '%')] = tabela_percentual_alcance[dia]

# Formatar os valores
def format_milhar_sem_zero(val):
    try:
        if pd.isna(val) or val == 0:
            return "-"
        return "{:,.0f}".format(int(val)).replace(",", ".")
    except (ValueError, TypeError):
        return "-"

def format_percentual(val):
    try:
        if pd.isna(val):
            return "-"
        return f"{round(val)}%"
    except (ValueError, TypeError):
        return "-"

# Aplicar formatação por tipo de coluna
for dia in dias_comuns:
    tabela_comparativa[(dia, 'Meta')] = tabela_comparativa[(dia, 'Meta')].apply(format_milhar_sem_zero)
    tabela_comparativa[(dia, 'Realizado')] = tabela_comparativa[(dia, 'Realizado')].apply(format_milhar_sem_zero)
    tabela_comparativa[(dia, '%')] = tabela_comparativa[(dia, '%')].apply(format_percentual)

if not tabela_comparativa.empty:
    # Melhorar exibição do cabeçalho
    tabela_comparativa.columns = pd.MultiIndex.from_tuples(
        [(f"Dia {dia}", nome) for dia, nome in tabela_comparativa.columns]
    )

    # Exibir Tabela Final
    st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 20px;'>📊 Metas Diárias x Realizado</h1>", unsafe_allow_html=True)

    # Identificar colunas de % Alcance
    subset_percentual = [(f"Dia {dia}", '%') for dia in dias_comuns]

    st.dataframe(
        tabela_comparativa.style.map(
            colorir_percentual_texto,
            subset=pd.IndexSlice[:, subset_percentual]
        )
    )
else:
    st.warning("Nenhum dado disponível para exibir.")

