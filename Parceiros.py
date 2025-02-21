import streamlit as st
import pandas as pd
import requests
from babel.numbers import format_currency
from datetime import datetime

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

def formata_brasil(x):
    # Se x não for numérico, apenas retorna como string
    if pd.isnull(x):
        return "0"
    # Garante inteiro (ou arredonda)
    val_int = int(round(x))
    # Formata com vírgula como separador de milhar e depois troca "," por "."
    return f"{val_int:,}".replace(",", ".")

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
    ano_atual = datetime.now().year
    mes_atual_num = datetime.now().month
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
    mes_atual_str = meses_dict[mes_atual_num]
    mes_atual = [mes_atual_str] if mes_atual_str in meses else ['Todos']

    empresa_filtro = st.sidebar.multiselect("Empresa", empresas, default=['Todos'])
    ano_filtro = st.sidebar.multiselect("Ano", anos, default=[ano_atual])
    mes_filtro = st.sidebar.multiselect("Mês", meses, default=mes_atual)
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
            <h3 style="color: #5D3A7A; margin-bottom: -5px;">Total Geral Vouchers + Contas
            <h2 style="color: #5D3A7A;">💰 R$ {formata_brasil(total_geral)}</h2></h3>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    colunas = st.columns(4)

for i, categoria_principal in enumerate(categorias_principais):
    contas_relacionadas = data[data['conta'].isin(data[data['Categoria'] == categoria_principal]['conta'].unique())]
    valor_liquido_principal = contas_relacionadas['TotalLiq'].sum()
    servico_principal = contas_relacionadas['servico'].sum()
    valor_principal = valor_liquido_principal + servico_principal
    perc_valor_principal = (valor_principal / total_geral * 100) if total_geral > 0 else 0

    # Filtrar apenas as contas que têm a categoria principal para o cálculo do ticket médio
    contas_categoria_principal = data[data['Categoria'] == categoria_principal]
    valor_categoria_principal = contas_categoria_principal['TotalLiq'].sum()
    qtd_categoria_principal = contas_categoria_principal['QTD'].sum()
    ticket_medio = valor_principal / qtd_categoria_principal if qtd_categoria_principal > 0 else 0
    preco_medio = valor_categoria_principal / qtd_categoria_principal if qtd_categoria_principal > 0 else 0
    
    perc_categoria_principal = (valor_categoria_principal / valor_principal * 100) if valor_principal > 0 else 0
    perc_servico = (servico_principal / valor_liquido_principal * 100) if valor_principal > 0 else 0

    subcategorias = contas_relacionadas[contas_relacionadas['Categoria'].isin(categorias_secundarias)]
    subcategorias_agrupadas = subcategorias.groupby('Categoria')['TotalLiq'].sum().to_dict()

    with colunas[i]:
        st.subheader(f"**{categoria_principal}**")

        # Exibir Ticket Médio acima do valor principal
        st.markdown(f"<p style='font-size: 14px; margin-bottom: -5px;'>🪙<b>Ticket Médio:</b> {format_currency(ticket_medio, 'BRL', locale='pt_BR')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 14px; margin-bottom: -5px;'>💷<b>Preço Médio:</b> {format_currency(preco_medio, 'BRL', locale='pt_BR')}</p>", unsafe_allow_html=True)

        st.markdown(f"<h4 style='color: #A67DB8; margin-bottom: -5px;'>{formata_brasil(valor_principal)}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 12px; margin-top: -5px;'><span style='font-size: 5px;'>🟣</span> {perc_valor_principal:.2f}%</p>", unsafe_allow_html=True)
        
        # Rodízio
        st.markdown(bloco_categoria("Rodízio", valor_categoria_principal, perc_categoria_principal), unsafe_allow_html=True)

        # Serviço
        st.markdown(bloco_categoria("Serviço", servico_principal, perc_servico), unsafe_allow_html=True)

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

tabela_realizado.columns = tabela_realizado.columns.map(str)

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

tabela_realizado_valor.columns = tabela_realizado_valor.columns.map(str)

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

# Filtrar apenas categorias principais
metas_diarias = metas_diarias[metas_diarias['Categoria'].isin(categorias_principais)]
data_filtrado = data_filtrado[data_filtrado['Categoria'].isin(categorias_principais)]

# Função para agrupar dias por blocos
def agrupar_dias(dia):
    if 1 <= dia <= 8:
        return '1 a 8'
    elif 9 <= dia <= 15:
        return '9 a 15'
    elif 16 <= dia <= 23:
        return '16 a 23'
    elif 24 <= dia <= 31:
        return '24 a 31'
    return 'Outro'

metas_diarias['Bloco_Dias'] = metas_diarias['Dia'].apply(agrupar_dias)
data_filtrado['Bloco_Dias'] = data_filtrado['Dia'].apply(agrupar_dias)

# Tabela de Metas (Quantidade)
tabela_metas_diarias_qtd = metas_diarias.pivot_table(
    index=['Categoria'], 
    columns='Bloco_Dias', 
    values='Meta_Diária',
    aggfunc='sum'
).fillna(0)

tabela_metas_diarias_qtd.columns = tabela_metas_diarias_qtd.columns.map(str)

# Tabela de Realizado (Quantidade)
tabela_realizado_qtd = data_filtrado.pivot_table(
    index=['Categoria'], 
    columns='Bloco_Dias', 
    values='QTD', 
    aggfunc='sum'
).fillna(0)

# Garantir que os blocos estejam na ordem correta
dias_comuns = ['1 a 8', '9 a 15', '16 a 23', '24 a 31']
tabela_metas_diarias_qtd = tabela_metas_diarias_qtd.reindex(columns=dias_comuns, fill_value=0)
tabela_realizado_qtd = tabela_realizado_qtd.reindex(columns=dias_comuns, fill_value=0)

# Calcular Porcentagem de Alcance
tabela_percentual_alcance = tabela_realizado_qtd / tabela_metas_diarias_qtd * 100
tabela_percentual_alcance = tabela_percentual_alcance.fillna(0)

# Montar DataFrame Final lado a lado
tabela_comparativa = pd.DataFrame()

for bloco in dias_comuns:
    tabela_comparativa[(bloco, 'Meta')] = tabela_metas_diarias_qtd[bloco]
    tabela_comparativa[(bloco, 'Rzdo')] = tabela_realizado_qtd[bloco]
    tabela_comparativa[(bloco, '%')] = tabela_percentual_alcance[bloco]

# Adicionar coluna de totalizador mensal
tabela_comparativa[('Total', 'Meta')] = tabela_metas_diarias_qtd.sum(axis=1)
tabela_comparativa[('Total', 'Rzdo')] = tabela_realizado_qtd.sum(axis=1)
tabela_comparativa[('Total', '%')] = (tabela_comparativa[('Total', 'Rzdo')] / tabela_comparativa[('Total', 'Meta')] * 100).fillna(0)

# Aplicar formatação por tipo de coluna
for bloco in dias_comuns + ['Total']:
    tabela_comparativa[(bloco, 'Meta')] = tabela_comparativa[(bloco, 'Meta')].apply(format_milhar_sem_zero)
    tabela_comparativa[(bloco, 'Rzdo')] = tabela_comparativa[(bloco, 'Rzdo')].apply(format_milhar_sem_zero)
    tabela_comparativa[(bloco, '%')] = tabela_comparativa[(bloco, '%')].apply(format_percentual)

# Melhorar exibição do cabeçalho
tabela_comparativa.columns = pd.MultiIndex.from_tuples(
    [(f"{bloco}", nome) for bloco, nome in tabela_comparativa.columns]
)

# Exibir Tabela Final
st.markdown("<h1 style='color: #5D3A7A; font-size: 32px; text-align: center; margin-top: 20px;'>💷 Metas Diárias x Realizado</h1>", unsafe_allow_html=True)

# Identificar colunas de % Alcance
subset_percentual = [(f"{bloco}", '%') for bloco in dias_comuns + ['Total']]

st.dataframe(
    tabela_comparativa.style.map(
        colorir_percentual_texto,
        subset=pd.IndexSlice[:, subset_percentual]
    )
)
