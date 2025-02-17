import streamlit as st
import pandas as pd
import requests
from babel.numbers import format_currency

st.set_page_config(page_title='Dash Vendas de Parceiros', layout='wide')
st.markdown("<h1 style='color: #5D3A7A; font-size: 26px;'>📊 Dashboard de Contas</h1>", unsafe_allow_html=True)

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
    categorias_secundarias = ['Bebidas', 'Souvenir', 'Cozinha', 'Outros']

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

    total_geral = data['TotalLiq'].sum()
    total_servico_geral = data['servico'].sum()
    perc_servico_geral = (total_servico_geral / total_geral * 100) if total_geral > 0 else 0

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"""
            <div style="background-color: #D6C2E9; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #5D3A7A; margin-bottom: -5px;">Total Geral</h4>
                <h3 style="color: #5D3A7A;">💰 {format_currency(total_geral, 'BRL', locale='pt_BR')}</h3>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background-color: #E8D6F0; padding: 15px; border-radius: 10px; text-align: center;">
                <h7 style="color: #5D3A7A;">Serviço Total</h7>
                <h6 style="color: #5D3A7A; text-align: center; margin-top: 7px">{format_currency(total_servico_geral, 'BRL', locale='pt_BR')}</h6>
                <h5 style="color: #A67DB8;">🔹 {perc_servico_geral:.2f}%</h5>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()

    colunas = st.columns(4)

    for i, categoria_principal in enumerate(categorias_principais):
        contas_relacionadas = data[data['conta'].isin(data[data['Categoria'] == categoria_principal]['conta'].unique())]
        valor_principal = contas_relacionadas['TotalLiq'].sum()
        perc_valor_principal = (valor_principal / total_geral * 100) if total_geral > 0 else 0
        valor_categoria_principal = data[data['Categoria'] == categoria_principal]['TotalLiq'].sum()
        perc_categoria_principal = (valor_categoria_principal / valor_principal * 100) if valor_principal > 0 else 0
        servico_total = contas_relacionadas['servico'].sum()
        perc_servico = (servico_total / valor_principal * 100) if valor_principal > 0 else 0

        subcategorias = contas_relacionadas[contas_relacionadas['Categoria'].isin(categorias_secundarias)]
        subcategorias_agrupadas = subcategorias.groupby('Categoria')['TotalLiq'].sum().to_dict()

        with colunas[i]:
            st.subheader(f"**{categoria_principal}**")
            st.markdown(f"<h4 style='color: #A67DB8;'>{format_currency(valor_principal, 'BRL', locale='pt_BR')}</h4>", unsafe_allow_html=True)
            st.write(f"🔹 {perc_valor_principal:.2f}% do Total Geral")
            st.write(f"Rodízio: {format_currency(valor_categoria_principal, 'BRL', locale='pt_BR')} ({perc_categoria_principal:.2f}%)")
            st.write(f"Serviço: {format_currency(servico_total, 'BRL', locale='pt_BR')} ({perc_servico:.2f}%)")

            for subcategoria, valor in subcategorias_agrupadas.items():
                percentual_categoria = (valor / valor_principal * 100) if valor_principal > 0 else 0
                st.write(f"{subcategoria}: {format_currency(valor, 'BRL', locale='pt_BR')} ({percentual_categoria:.2f}%)")
