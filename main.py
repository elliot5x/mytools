from sys import exit
from time import sleep
import os
import subprocess
import tempfile
import csv
from modules.validation.utils import pedir_ip, cls
from ml.classificador_site import classificar_url


BANNER = """[0;37;40m /░░░░░    /░  /░           /░░░    /░░░    /░░░    /░       /░░░[0m
[0;37;40m│ ▒ ▒ ▒   │//▒/▒/          │//▒/   │_▒/▒   │_▒/▒   │ ▒      │ ▒_/[0m
[0;37;40m│ ▓ ▓ ▓    │//▓/            │ ▓    │ ▓ ▓   │ ▓ ▓   │ ▓      │/_▓ [0m
[0;37;40m│ █ █ █     │ █             │ █    │ ███   │ ███   │ ███    /███ [0m
[0;37;40m│//////     │//             │//    │/__/   │/__/   │/__/   │/__/ [0m"""


def executar_scan(ip):
    """Roda o scan.sh e devolve os dados estruturados (dict), ou None se falhar."""
    caminho = os.path.abspath('./modules/recon/scan.sh')

    if not os.path.exists(caminho):
        print(f"\n[-] Erro: script não encontrado em {caminho}")
        return None

    resultado_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
            resultado_path = tmp.name

        subprocess.run(["bash", caminho, ip, resultado_path], check=True)
        return carregar_resultado(resultado_path)

    except subprocess.CalledProcessError as e:
        print(f"\n[-] O script falhou com código de retorno: {e.returncode}")
        return None
    except KeyboardInterrupt:
        print("\n[-] Execução interrompida pelo usuário.")
        return None
    finally:
        if resultado_path and os.path.exists(resultado_path):
            os.remove(resultado_path)


def carregar_resultado(caminho_csv):
    """Lê o CSV temporário (delimitador '|') gerado pelo scan.sh."""
    dados = {'portas': [], 'ftp_aberto': False, 'http_aberto': False, 'diretorios': []}

    if not os.path.exists(caminho_csv):
        return dados

    with open(caminho_csv, newline='', encoding='utf-8') as f:
        leitor = csv.reader(f, delimiter='|')
        for linha in leitor:
            if len(linha) != 3:
                continue
            tipo, chave, valor = linha
            if tipo == 'porta':
                dados['portas'].append({'porta': chave, 'servico': valor})
            elif tipo == 'http_aberto':
                dados['http_aberto'] = (valor == 'sim')
            elif tipo == 'ftp_aberto':
                dados['ftp_aberto'] = (valor == 'sim')
            elif tipo == 'diretorio':
                dados['diretorios'].append({'caminho': chave, 'status': valor})

    return dados


def gerar_relatorio(ip, dados):
    """Monta o relatório final: portas + diretórios encontrados + veredito da ML."""
    print("\n=== RELATÓRIO FINAL ===\n")

    if dados['portas']:
        print("Portas abertas:")
        for p in dados['portas']:
            print(f"  - {p['porta']} ({p['servico']})")
    else:
        print("Portas abertas: nenhuma encontrada.")

    if dados['diretorios']:
        print("\nDiretórios encontrados:")
        for d in dados['diretorios']:
            print(f"  - {d['caminho']} (status {d['status']})")

    # A resposta principal para o usuário é o veredito da ML, não os echos crus.
    if dados['http_aberto']:
        print("\n[+] Porta HTTP aberta — classificando o site com Machine Learning...")
        try:
            categoria, confianca = classificar_url(f"http://{ip}")
            if categoria:
                print(f"\n>>> Classificação do site: {categoria} (confiança: {confianca:.0%})")
            else:
                print("\n[-] Não foi possível baixar o site para classificar.")
        except Exception as e:
            print(f"\n[-] Erro ao classificar o site: {e}")
    else:
        print("\n[i] Porta HTTP fechada — nada para classificar com a ML.")


def menu():
    while True:
        try:
            cls()
            print(BANNER)
            print("------------ Ferramentas utéis By: Marques ------------\n\n")
            print("[1] Recon + ML\n[2] Sair\n")
            escolha = int(input(">> "))

            if escolha == 1:
                ip = pedir_ip()
                dados = executar_scan(ip)
                if dados is not None:
                    gerar_relatorio(ip, dados)
                    input("\nPressione Enter para voltar ao menu...")
            elif escolha == 2:
                exit()
            else:
                print("Erro, número inválido.")
                sleep(1)

        except ValueError as e:
            print(e)
            sleep(1)


if __name__ == "__main__":
    menu()
