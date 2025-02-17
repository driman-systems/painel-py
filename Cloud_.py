import streamlit as st
import pandas as pd
import requests
from babel.numbers import format_currency
import os

# Configuração inicial do Streamlit
st.set_page_config(page_title='Dash Vendas de Parceiros', layout='wide')
st.markdown("<h1 style='color: #5D3A7A;'>📊 Dashboard de Contas</h1>", unsafe_allow_html=True)

# Definição de categorias (centralizada para evitar inconsistências)
CATEGORIAS_PRINCIPAIS = ['Venda própria', 'Laçador', 'Tche', 'Prime']
CATEGORIAS_SECUNDARIAS = ['Bebidas', 'Souvenir', 'Delivery', 'Cozinha', 'Outros']

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

# Função para carregar e tratar os dados de metas
@st.cache_data
def load_metas():
    try:
        file_path = "Metas_Ajustadas_Sem_Domingos_Gatzz.xlsx"
        if not os.path.exists(file_path):
            st.warning(f"Arquivo de metas não encontrado: {file_path}")
            return pd.DataFrame()
        
        metas = pd.read_excel(file_path, sheet_name="Sheet1")
        
        # Verificar se as colunas necessárias estão presentes
        colunas_necessarias = ['Empresa', 'Ano', 'Mês', 'Dia', 'Meta_Diária']
        if not all(col in metas.columns for col in colunas_necessarias):
            st.error(f"O arquivo de metas não contém as colunas necessárias: {colunas_necessarias}")
            return pd.DataFrame()
        
        # Converter colunas para o tipo correto
        metas['Meta_Diária'] = pd.to_numeric(metas['Meta_Diária'], errors='coerce').fillna(0)
        metas['Ano'] = metas['Ano'].astype(int)
        metas['Mês'] = metas['Mês'].astype(int)
        metas['Dia'] = metas['Dia'].astype(int)
        
        return metas
    except Exception as e:
        st.error(f"Erro ao carregar metas: {e}")
        return pd.DataFrame()
    
    
# Função para criar e aplicar filtros
def criar_e_aplicar_filtros(data):
    if data.empty:
        return data, [], [], [], []
    
    # Garantir que 'conta' seja string para evitar problemas de filtragem
    data['conta'] = data['conta'].astype(str)
    
    # Preparar opções de filtro
    empresas = ['Todos'] + sorted(data['Empresa'].unique().tolist())
    anos = ['Todos'] + sorted(data['Ano'].unique().tolist())
    meses_dict = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
                  7: 'Jullo', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
    data['Mes_Extenso'] = data['Mes'].map(meses_dict)
    meses = ['Todos'] + list(meses_dict.values())
    dias = ['Todos'] + sorted(data['Dia'].unique().tolist())

    # Interface de filtros no expander
    with st.expander("🔍 **Filtros**", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        empresa_filtro = col1.multiselect("Empresa", empresas, default=['Todos'])
        ano_filtro = col2.multiselect("Ano", anos, default=['Todos'])
        mes_filtro = col3.multiselect("Mês", meses, default=['Todos'])
        dia_filtro = col4.multiselect("Dia", dias, default=['Todos'])

    # Aplicar filtros
    filtered_data = data.copy()
    if 'Todos' not in empresa_filtro:
        filtered_data = filtered_data[filtered_data['Empresa'].isin(empresa_filtro)]
    if 'Todos' not in ano_filtro:
        filtered_data = filtered_data[filtered_data['Ano'].isin(ano_filtro)]
    if 'Todos' not in mes_filtro:
        filtered_data = filtered_data[filtered_data['Mes_Extenso'].isin(mes_filtro)]
    if 'Todos' not in dia_filtro:
        filtered_data = filtered_data[filtered_data['Dia'].isin(dia_filtro)]
    
    return filtered_data, empresa_filtro, ano_filtro, mes_filtro, dia_filtro

# Função para mostrar cartões de totais
def mostrar_cartoes_totais(data):
    if data.empty:
        return
    
    st.markdown("<hr>", unsafe_allow_html=True)
    col_total1, col_total2 = st.columns([1, 1])
    
    total_geral = data['TotalLiq'].sum()
    total_servico = data['servico'].sum()
    perc_servico = (total_servico / total_geral * 100) if total_geral > 0 else 0
    
    with col_total1:
        st.markdown(f"""
            <div style="background-color: #D6C2E9; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #5D3A7A; margin-bottom: -5px;">Total Geral</h4>
                <h3 style="color: #5D3A7A;">💰 {format_currency(total_geral, 'BRL', locale='pt_BR')}</h3>
            </div>
        """, unsafe_allow_html=True)

    with col_total2:
        st.markdown(f"""
            <div style="background-color: #E8D6F0; padding: 10px; border-radius: 10px; text-align: center; margin-top: 10px;">
                <p style="color: #5D3A7A; font-size: 14px; margin-bottom: -5px;">Serviço Total</p>
                <h4 style="color: #5D3A7A;">{format_currency(total_servico, 'BRL', locale='pt_BR')}</h4>
                <h3 style="color: #A67DB8;">🔹 {perc_servico:.2f}%</h3>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)

# Função para mostrar métricas por categoria principal
def mostrar_metricas_categorias(data):
    if data.empty:
        return
    
    # Preparar valores totais
    total_geral = data['TotalLiq'].sum()
    
    # Criar colunas para as categorias principais
    colunas = st.columns([1, 1, 1, 1])
    
    for i, categoria_principal in enumerate(CATEGORIAS_PRINCIPAIS):
        # Selecionar contas da categoria principal
        contas_principais = data[data['Categoria'] == categoria_principal]
        contas_ids = contas_principais['conta'].unique()
        
        # Selecionar todas as contas relacionadas à categoria principal
        contas_relacionadas = data[data['conta'].isin(contas_ids)]
        
        # Calcular valores
        valor_principal = contas_relacionadas['TotalLiq'].sum()
        valor_categoria_principal = contas_principais['TotalLiq'].sum()
        servico_total = contas_relacionadas['servico'].sum()
        
        # Calcular percentuais
        perc_valor_principal = (valor_principal / total_geral * 100) if total_geral > 0 else 0
        perc_categoria_principal = (valor_categoria_principal / valor_principal * 100) if valor_principal > 0 else 0
        perc_servico = (servico_total / valor_principal * 100) if valor_principal > 0 else 0
        
        # Subcategorias dentro da categoria principal
        subcategorias = contas_relacionadas[contas_relacionadas['Categoria'].isin(CATEGORIAS_SECUNDARIAS)]
        subcategorias_agrupadas = subcategorias.groupby('Categoria')['TotalLiq'].sum().to_dict()
        
        with colunas[i]:
            st.subheader(f"**{categoria_principal}**")
            
            # Valor principal
            st.markdown(f"""
                <div style="text-align: left;">
                    <h4 style="color: #A67DB8;">{format_currency(valor_principal, 'BRL', locale='pt_BR')}</h4>
                    <p style="font-size: 12px; margin-top: -10px;">🔹 {perc_valor_principal:.2f}% do Total Geral</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Função helper para blocos de informação
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

# Função para mostrar tabelas resumo
def mostrar_tabelas_resumo(data):
    if data.empty:
        return
    
    # Garantir que valores numéricos estejam corretos
    data['TotalLiq'] = pd.to_numeric(data['TotalLiq'], errors='coerce').fillna(0)
    data['QTD'] = pd.to_numeric(data['QTD'], errors='coerce').fillna(0)
    
    # Filtrar dados para categorias principais
    data_filtrado = data[data['Categoria'].isin(CATEGORIAS_PRINCIPAIS)]
    
    # Função para formatar moeda
    def format_currency_milhar(val):
        if val == 0:
            return "-"
        return format_currency(val, 'BRL', locale='pt_BR').replace("R$", "R$ ")
    
    # Função para formatar números
    def format_milhar(val):
        if val == 0:
            return "-"
        return "{:,}".format(int(val)).replace(",", ".")
    
    # Tabela de valores
    tabela_diaria = data_filtrado.pivot_table(
        index='Categoria', 
        columns='Dia', 
        values='TotalLiq', 
        aggfunc='sum', 
        margins=True, 
        margins_name='Total'
    ).fillna(0)
    
    st.write("### Resumo Diário de Contas")
    st.dataframe(
        tabela_diaria.loc[CATEGORIAS_PRINCIPAIS + ['Total']].style.format(format_currency_milhar)
        .set_table_styles([
            {'selector': 'th', 'props': [('font-size', '16px'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('font-size', '14px')]},
            {'selector': 'tr:last-child td', 'props': [('font-weight', 'bold'), ('font-size', '16px')]},
            {'selector': 'td:last-child', 'props': [('font-weight', 'bold'), ('font-size', '16px')]}
        ])
    )
    
    # Tabela de quantidades
    tabela_diaria_qtde = data_filtrado.pivot_table(
        index='Categoria', 
        columns='Dia', 
        values='QTD', 
        aggfunc='sum', 
        margins=True, 
        margins_name='Total'
    ).fillna(0)
    
    st.write("### Resumo Diário de Contas - Soma de Quantidades")
    st.dataframe(
        tabela_diaria_qtde.loc[CATEGORIAS_PRINCIPAIS + ['Total']].style.format(format_milhar)
        .set_table_styles([
            {'selector': 'th', 'props': [('font-size', '16px'), ('font-weight', 'bold')]},
            {'selector': 'td', 'props': [('font-size', '14px')]},
            {'selector': 'tr:last-child td', 'props': [('font-weight', 'bold'), ('font-size', '16px')]},
            {'selector': 'td:last-child', 'props': [('font-weight', 'bold'), ('font-size', '16px')]}
        ])
    )

# Função para mostrar comparativo de metas
def mostrar_comparativo_metas(data, metas_diarias):
    if data.empty or metas_diarias.empty:
        st.warning("Dados insuficientes para mostrar o comparativo de metas.")
        return
    
    # Filtrar dados para categorias principais
    data_filtrado = data[data['Categoria'].isin(CATEGORIAS_PRINCIPAIS)]
    data_filtrado['QTD'] = pd.to_numeric(data_filtrado['QTD'], errors='coerce').fillna(0)
    
    # Filtrar apenas os dias correspondentes entre realizado e meta
    dias_comuns = sorted(set(data_filtrado['Dia'].unique()) & set(metas_diarias['Dia'].unique()))
    
    if not dias_comuns:
        st.warning("Nenhum dia em comum encontrado entre as metas e os realizados.")
        return
    
    # Criar Tabela de Realizado por Dia
    tabela_realizado = data_filtrado.pivot_table(
        index=['Categoria'], 
        columns='Dia', 
        values='QTD', 
        aggfunc='sum', 
        margins=False
    ).fillna(0)
    
    # Criar Tabela de Metas por Dia
    tabela_metas = metas_diarias.pivot_table(
        index=['Categoria'], 
        columns='Dia', 
        values='Meta_Diária', 
        aggfunc='sum', 
        margins=False
    ).fillna(0)
    
    # Criar tabela comparativa
    tabela_comparativa = pd.DataFrame(index=tabela_realizado.index)
    for col in dias_comuns:
        try:
            tabela_comparativa[f"{col} - Meta"] = tabela_metas[col]
            tabela_comparativa[f"{col} - Realizado"] = tabela_realizado[col]
            tabela_comparativa[f"{col} - % Alcance"] = (tabela_realizado[col] / tabela_metas[col]) * 100
        except (KeyError, ZeroDivisionError):
            continue
    
    # Aplicar formatação condicional
    def highlight(val):
        if isinstance(val, (int, float)) and not pd.isna(val):
            if val >= 100:
                return 'background-color: lightgreen; color: black'
            elif 95 <= val < 100:
                return 'background-color: yellow; color: black'
            else:
                return 'background-color: red; color: white'
        return ''
    
    # Exibir a tabela comparativa
    st.write("### Comparativo Metas x Realizado")
    st.dataframe(
        tabela_comparativa.style.format("{:.0f}").applymap(
            highlight, subset=[col for col in tabela_comparativa.columns if '% Alcance' in col]
        )
    )

# Fluxo principal do aplicativo
def main():
    # Carregar dados
    data = get_data()
    if data.empty:
        st.error("Não foi possível carregar os dados. Verifique a conexão com a API.")
        return
    
    # Aplicar filtros
    data_filtrado, empresa_filtro, ano_filtro, mes_filtro, dia_filtro = criar_e_aplicar_filtros(data)
    
    # Mostrar cartões de totais
    mostrar_cartoes_totais(data_filtrado)
    
    # Mostrar métricas por categoria
    mostrar_metricas_categorias(data_filtrado)
    
    # Mostrar tabelas resumo
    mostrar_tabelas_resumo(data_filtrado)
    
       # Carregar e mostrar comparativo de metas
metas_diarias = load_metas()
# Aplicar os mesmos filtros às metas
if not metas_diarias.empty:
    # Aplicar filtro de empresa
    if 'Todos' not in empresa_filtro:
        metas_diarias = metas_diarias[metas_diarias['Empresa'].isin(empresa_filtro)]

    # Aplicar filtro de ano
    if 'Todos' not in ano_filtro:
        metas_diarias = metas_diarias[metas_diarias['Ano'].isin([int(a) for a in ano_filtro if a != 'Todos'])]

    # Aplicar filtro de mês
    if 'Todos' not in mes_filtro:
        meses_dict_rev = {v: k for k, v in {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
              7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}.items()}
        meses_num = [meses_dict_rev[m] for m in mes_filtro if m != 'Todos']
        if meses_num:
            metas_diarias = metas_diarias[metas_diarias['Mês'].isin(meses_num)]

    # Aplicar filtro de dia
    if 'Todos' not in dia_filtro:
        metas_diarias = metas_diarias[metas_diarias['Dia'].isin(dia_filtro)]

    # Verificar se há dados após aplicar os filtros
    if metas_diarias.empty:
        st.warning("Nenhuma meta encontrada para os filtros aplicados.")
    else:
        mostrar_comparativo_metas(data_filtrado, metas_diarias)
else:
    st.warning("Não foi possível carregar as metas. Verifique o arquivo de metas.")

# Finalização do código
if __name__ == "__main__":
    main()