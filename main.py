from sys import exit
from time import sleep
import os
import subprocess
import tempfile
import csv
from ml.classificador_site import classificar_html, adicionar_exemplo
from modules.validation.utils import pedir_ip, cls
from ml.leitor import obte_codigo_fonte


BANNER = """[0;37;40m /░░░░░    /░  /░           /░░░    /░░░    /░░░    /░       /░░░[0m
[0;37;40m│ ▒ ▒ ▒   │//▒/▒/          │//▒/   │_▒/▒   │_▒/▒   │ ▒      │ ▒_/[0m
[0;37;40m│ ▓ ▓ ▓    │//▓/            │ ▓    │ ▓ ▓   │ ▓ ▓   │ ▓      │/_▓ [0m
[0;37;40m│ █ █ █     │ █             │ █    │ ███   │ ███   │ ███    /███ [0m
[0;37;40m│//////     │//             │//    │/__/   │/__/   │/__/   │/__/ [0m"""


def executar_scan(ip):
    """Roda o scan.sh e devolve os dados estruturados (dict), ou None se falhar."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(base_dir, 'modules', 'recon', 'scan.sh')

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
    dados = {
        'portas': [], 
        'ftp_aberto': False, 
        'http_aberto': False, 
        'diretorios': [],
        'porta_alvo': '80',
        'nuclei_achados': ''
    }

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
            elif tipo == 'http_alvo':
                dados['porta_alvo'] = valor  # Captura a porta dinâmica (ex: 10000, 8080)
            elif tipo == 'diretorio':
                dados['diretorios'].append({'caminho': chave, 'status': valor})
            elif tipo == 'nuclei':
                dados['nuclei_achados'] = valor

    return dados

def gerar_relatorio(ip, dados):
    """Monta o relatório final: portas + diretórios encontrados + veredito da ML e gerencia o scan ativo."""
    cls()
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

    if dados.get('nuclei_achados'):
        print("\nAchados do Nuclei:")
        print(f"  {dados['nuclei_achados']}")

    if dados['http_aberto']:
        porta_web = dados.get('porta_alvo', '80')

        print("\n[+] Porta HTTP aberta — cruzando HTML com dados de Recon...")
        try:
            html = obte_codigo_fonte(f"http://{ip}:{porta_web}") or ""

            texto_recon = ""
            
            # Ordena as portas numéricamente para a string ser sempre igual
            for p in sorted(dados['portas'], key=lambda x: x['porta']):
                texto_recon += f" PORTA {p['porta']} SERVICO {p['servico']} "
            
            # Ordena os diretórios alfabeticamente
            for d in sorted(dados['diretorios'], key=lambda x: x['caminho']):
                texto_recon += f" DIRETORIO {d['caminho']} STATUS {d['status']} "

            # Achados do Nuclei (já extraídos pelo scan.sh) entram junto na string final
            texto_final = f"{texto_recon} {html} {dados.get('nuclei_achados', '')}"
            
            # --- PROTEÇÃO DO CSV ADICIONADA AQUI ---
            texto_final = texto_final.replace('\n', ' ').replace('\r', ' ').strip()
            # --------------------------------------

            if texto_final:
                categoria, confianca = classificar_html(texto_final)
                # Assumindo que confianca venha como decimal (ex: 0.65). Se vier como 65, remova o * 100.
                print(f"\n>>> Classificação do alvo: {categoria} (confiança: {confianca * 100:.0f}%)")
                
                if confianca > 0.60:
                    # TRAVA: Human-in-the-loop
                    print(f"\n[?] A IA quer registrar este alvo definitivamente como '{categoria}'.")
                    print("Opções:\n")
                    print(" [1] Sim, a categoria está correta (Validar)")
                    print(" [2] Não, eu quero digitar a categoria correta (Ensinar nova classe)")
                    print(" [3] Descartar achado\n")
                    
                    escolha = input(">>: ").strip()
                    
                    if escolha == '1':
                        print("\n[+] Injetando dados validados na base de treino...\n")
                        adicionar_exemplo(texto_final, categoria)
                    elif escolha == '2':
                        nova_categoria = input("\n>> Digite a categoria correta: ").strip()
                        print(f"\n[+] Excelente! Injetando aprendizado como '{nova_categoria}'...\n")
                        adicionar_exemplo(texto_final, nova_categoria)
                    else:
                        print("[-] Achado descartado. O dataset não foi alterado.\n")
                        
                else:
                    print("[-] Confiança da IA muito baixa. Abortando aprendizado.\n")
                    
            else:
                print("\n[-] Nenhum dado (HTML, Recon ou Nuclei) obtido para classificar.")
                
        except Exception as e:
            print(f"\n[-] Erro ao classificar o site: {e}")

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