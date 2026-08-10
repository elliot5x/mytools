"""
Script auxiliar para AMPLIAR o dataset de treino com sites reais.

O dataset que vem pronto (ml/data/sites_treino.csv) é sintético — serve só
para o pipeline funcionar de primeira. Para o classificador ficar
minimamente confiável, rode este script na sua máquina (com acesso à
internet) apontando para sites reais e categorizados manualmente por você.

Uso (rode a partir da pasta raiz do projeto, a mesma onde está main.py):
    1. Edite a lista URLS_TREINO abaixo, adicionando (url, categoria).
    2. python -m ml.coletar_dados
    3. O modelo é re-treinado automaticamente na próxima chamada de
       classificar_url(), pois o cache (modelo.pkl) fica mais velho que o
       CSV assim que você adiciona um exemplo novo.

Dica: procure manter as categorias com uma quantidade parecida de
exemplos entre si (ex.: ~15-20 por categoria), senão o modelo tende a
"chutar" sempre a categoria com mais exemplos.
"""

from ml.classificador_site import adicionar_exemplo
from ml.leitor import obte_codigo_fonte

# Adicione aqui pares (url, categoria) reais para expandir o dataset.
# Categorias sugeridas (pode criar outras, contanto que sejam consistentes
# com o que já está em ml/data/sites_treino.csv):
#   "Página Padrão do Servidor", "Painel de Login/Admin", "CMS Conhecido",
#   "Aplicação Web Customizada", "Listagem de Diretório"
URLS_TREINO = [
    # ("http://192.168.1.10", "Página Padrão do Servidor"),
    # ("http://192.168.1.20/admin", "Painel de Login/Admin"),
    # ("http://192.168.1.30", "CMS Conhecido"),
]


def main():
    if not URLS_TREINO:
        print("[-] Nenhuma URL configurada. Edite URLS_TREINO neste arquivo antes de rodar.")
        return

    adicionados = 0
    for url, categoria in URLS_TREINO:
        print(f"[+] Coletando {url} ({categoria})...")
        html = obte_codigo_fonte(url)
        if html:
            adicionar_exemplo(html, categoria)
            adicionados += 1
            print("    -> adicionado ao dataset.")
        else:
            print("    -> falhou ao baixar, pulando.")

    print(f"\n[+] Concluído: {adicionados}/{len(URLS_TREINO)} exemplos adicionados.")


if __name__ == "__main__":
    main()