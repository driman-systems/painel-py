import streamlit as st
import pandas as pd
import requests
from babel.numbers import format_currency

# Configuração inicial do Streamlit
st.set_page_config(page_title='Dashboard de Contas', layout='wide')
st.markdown("<h1 style='color: #5D3A7A;'>📊 Dashboard de Contas</h1>", unsafe_allow_html=True)

# Função para buscar dados da API com cache
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

# Carregar os dados
data = get_data()

if not data.empty:
    # Garantir que 'conta' seja string para evitar problemas de filtragem
    data['conta'] = data['conta'].astype(str)

    # Categorias principais e secundárias
    categorias_principais = ['Venda própria', 'Laçador', 'Tche', 'Prime']
    categorias_secundarias = ['Bebidas', 'Souvenir', 'Delivery', 'Cozinha', 'Outros']

    # 📌 Filtros com múltipla seleção
    with st.expander("🔍 **Filtros**", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        empresas = ['Todos'] + sorted(data['Empresa'].unique().tolist())
        anos = ['Todos'] + sorted(data['Ano'].unique().tolist())
        meses_dict = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                      7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
        data['Mes_Extenso'] = data['Mes'].map(meses_dict)
        meses = ['Todos'] + list(meses_dict.values())
        dias = ['Todos'] + sorted(data['Dia'].unique().tolist())

        empresa_filtro = col1.multiselect("Empresa", empresas, default=['Todos'])
        ano_filtro = col2.multiselect("Ano", anos, default=['Todos'])
        mes_filtro = col3.multiselect("Mês", meses, default=['Todos'])
        dia_filtro = col4.multiselect("Dia", dias, default=['Todos'])

    # Aplicando filtros
    if 'Todos' not in empresa_filtro:
        data = data[data['Empresa'].isin(empresa_filtro)]
    if 'Todos' not in ano_filtro:
        data = data[data['Ano'].isin(ano_filtro)]
    if 'Todos' not in mes_filtro:
        data = data[data['Mes_Extenso'].isin(mes_filtro)]
    if 'Todos' not in dia_filtro:
        data = data[data['Dia'].isin(dia_filtro)]

    st.markdown("<br>", unsafe_allow_html=True)

    # ✅ Correção do TOTAL GERAL: soma de **todas as contas**
    total_geral = data['TotalLiq'].sum()
    total_servico_geral = data['servico'].sum()
    perc_servico_geral = (total_servico_geral / total_geral * 100) if total_geral > 0 else 0

    # Criando a estrutura das 5 colunas (as 4 primeiras iguais, a última mais larga)
    colunas = st.columns([1, 1, 1, 1, 1.5])  # A última coluna é mais larga

    for i, categoria_principal in enumerate(categorias_principais):
        # 🔹 Selecionando todas as contas relacionadas à categoria principal
        contas_relacionadas = data[data['conta'].isin(data[data['Categoria'] == categoria_principal]['conta'].unique())]

        # ✅ Valor Principal: Soma das contas da categoria principal + vinculadas
        valor_principal = contas_relacionadas['TotalLiq'].sum()
        perc_valor_principal = (valor_principal / total_geral * 100) if total_geral > 0 else 0

        # ✅ Valor da Categoria Principal: Soma somente das contas da própria categoria
        valor_categoria_principal = data[data['Categoria'] == categoria_principal]['TotalLiq'].sum()
        perc_categoria_principal = (valor_categoria_principal / valor_principal * 100) if valor_principal > 0 else 0

        # ✅ Soma do Serviço: soma das contas da categoria principal + vinculadas
        servico_total = contas_relacionadas['servico'].sum()
        perc_servico = (servico_total / valor_principal * 100) if valor_principal > 0 else 0

        # 🔹 Pegando subcategorias **dentro da categoria principal**
        subcategorias = contas_relacionadas[contas_relacionadas['Categoria'].isin(categorias_secundarias)]
        subcategorias_agrupadas = subcategorias.groupby('Categoria')['TotalLiq'].sum().to_dict()

        with colunas[i]:
            st.subheader(f"**{categoria_principal}**")

            # ✅ **Deixando os valores mais juntos**
            st.markdown(f"""
                <div style="text-align: left;">
                    <h4 style="color: #A67DB8;">{format_currency(valor_principal, 'BRL', locale='pt_BR')}</h4>
                    <p style="font-size: 12px; margin-top: -10px;">🔹 {perc_valor_principal:.2f}% do Total Geral</p>
                </div>
            """, unsafe_allow_html=True)

            # ✅ **Organizando os blocos de informações**
            def bloco_info(titulo, valor, porcentagem):
                return f"""
                    <p style='font-size: 16px; margin-bottom: -5px;'>{titulo}</p>
                    <p style='font-size: 22px; margin-bottom: -5px;'>{format_currency(valor, 'BRL', locale='pt_BR')}</p>
                    <p style='font-size: 16px; margin-bottom: 10px;'>🔸 {porcentagem:.2f}%</p>
                """

            st.markdown(bloco_info("Rodízio", valor_categoria_principal, perc_categoria_principal), unsafe_allow_html=True)
            st.markdown(bloco_info("Total Serviço", servico_total, perc_servico), unsafe_allow_html=True)

            for subcategoria, valor in subcategorias_agrupadas.items():
                percentual_categoria = (valor / valor_principal * 100) if valor_principal > 0 else 0
                st.markdown(bloco_info(f"Total {subcategoria}", valor, percentual_categoria), unsafe_allow_html=True)

    # 🟣 Coluna 5: TOTAL GERAL (mais larga)
    with colunas[4]:
        st.markdown(f"""
            <div style="background-color: #D6C2E9; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #5D3A7A; margin-bottom: -5px;">Total Geral</h4>
                <h3 style="color: #5D3A7A;">💰 {format_currency(total_geral, 'BRL', locale='pt_BR')}</h3>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div style="background-color: #E8D6F0; padding: 10px; border-radius: 10px; text-align: center; margin-top: 10px;">
                <p style="color: #5D3A7A; font-size: 14px; margin-bottom: -5px;">Serviço Total</p>
                <h4 style="color: #5D3A7A;">{format_currency(total_servico_geral, 'BRL', locale='pt_BR')}</h4>
                <h3 style="color: #A67DB8;">🔹 {perc_servico_geral:.2f}%</h3>
            </div>
        """, unsafe_allow_html=True)
