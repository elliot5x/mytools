import requests


def obte_codigo_fonte(url, timeout=8):
    """Baixa o código-fonte (HTML) de uma URL. Retorna None em caso de erro."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url, headers=headers, timeout=timeout)
        resposta.raise_for_status()

        return resposta.text

    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return None
