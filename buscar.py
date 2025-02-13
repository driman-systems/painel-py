import requests
import pandas as pd

# URL do endpoint
url = "http://192.168.10.11:5005/contas"

# Fazendo a requisição
response = requests.get(url)

# Verifica se a requisição foi bem-sucedida
if response.status_code == 200:
    dados = response.json()

    # Converte para DataFrame
    df = pd.DataFrame(dados)

    # Filtrando apenas o ano de 2024 (ajuste conforme necessário)
    df_2024 = df[df["Ano"] == 2024]

    # Somando os valores líquidos por categoria
    totais = df_2024.groupby("Categoria")["TotalLiq"].sum()

    # Soma total geral
    total_geral = df_2024["TotalLiq"].sum()

    # Exibindo os resultados
    print("\n📊 **Totais por Categoria:**")
    print(totais)
    print(f"\n💰 **Total Geral:** R$ {total_geral:,.2f}")

else:
    print("❌ Erro ao acessar a API:", response.status_code)
