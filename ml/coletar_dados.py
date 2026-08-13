"""
CSV de entrada esperado (por padrão ml/data/urls_para_coletar.csv),
colunas 'url' e 'categoria':

    url,categoria
    http://192.168.1.10,Página Padrão do Servidor
    http://192.168.1.20/admin,Painel de Login/Admin

Uso:
    python -m ml.coletar_dados
    python -m ml.coletar_dados --arquivo outras_urls.csv --workers 20
"""

import os
import csv
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from ml.classificador_site import adicionar_exemplo
from ml.leitor import obte_codigo_fonte

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PADRAO = os.path.join(BASE_DIR, 'data', 'urls_para_coletar.csv')


def carregar_urls(caminho):
    """Lê o CSV de entrada e retorna lista de tuplas (url, categoria)."""
    pares = []
    with open(caminho, newline='', encoding='utf-8') as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            url = (linha.get('url') or '').strip()
            categoria = (linha.get('categoria') or '').strip()
            if url and categoria:
                pares.append((url, categoria))
    return pares


def _coletar_um(par):
    url, categoria = par
    html = obte_codigo_fonte(url)
    if html:
        adicionar_exemplo(html, categoria)
        return (url, categoria, True)
    return (url, categoria, False)


def coletar_em_lote(caminho_csv, max_workers=10):
    """Baixa e adiciona ao dataset todas as URLs do CSV, em paralelo."""
    pares = carregar_urls(caminho_csv)
    if not pares:
        print(f"[-] Nenhuma URL válida encontrada em {caminho_csv}.")
        print("    Formato esperado: colunas 'url' e 'categoria'.")
        return

    print(f"[+] {len(pares)} URL(s) para coletar, até {max_workers} em paralelo...\n")

    sucesso, falha = 0, 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(_coletar_um, par): par for par in pares}
        for futuro in as_completed(futuros):
            url, categoria, ok = futuro.result()
            if ok:
                sucesso += 1
                print(f"    [+] {url} -> '{categoria}' adicionado.")
            else:
                falha += 1
                print(f"    [-] {url} -> falhou ao baixar.")

    print(f"\n[+] Concluído: {sucesso}/{len(pares)} adicionados ({falha} falharam).")
    print("[i] Rode o classificador normalmente — o modelo é re-treinado")
    print("    sozinho na próxima chamada, porque o CSV de treino mudou de data.")


def main():
    parser = argparse.ArgumentParser(description="Coleta em lote de exemplos de treino.")
    parser.add_argument('--arquivo', default=CSV_PADRAO, help="CSV com colunas url,categoria")
    parser.add_argument('--workers', type=int, default=10,
                         help="Downloads simultâneos (padrão: 10 — evite exagerar contra um único alvo)")
    args = parser.parse_args()

    if not os.path.exists(args.arquivo):
        print(f"[-] Arquivo não encontrado: {args.arquivo}")
        print("    Crie um CSV com colunas 'url,categoria' nesse caminho,")
        print("    ou aponte outro com --arquivo.")
        return

    coletar_em_lote(args.arquivo, max_workers=args.workers)


if __name__ == "__main__":
    main()