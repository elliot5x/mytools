from sys import exit
from time import sleep
import os
import subprocess
import tempfile
import csv
import json
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
    dados = {
        'portas': [], 
        'ftp_aberto': False, 
        'http_aberto': False, 
        'diretorios': [],
        'porta_alvo': '80'
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

    return dados

def executar_nuclei_focado(ip, porta):
    """Roda Nuclei em background usando a porta dinâmica, extrai as vulnerabilidades e retorna como texto."""
    comando_base = ["nuclei", "-u", f"http://{ip}:{porta}", "-jsonl"]
    templates = ["-severity", "medium,high,critical"]
    comando = comando_base + templates
    achados_ia = []
    
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        # Lê linha por linha do output oculto
        for linha in resultado.stdout.splitlines():
            if not linha.strip():
                continue
            try:
                dado = json.loads(linha)
                template_id = dado.get("template-id", "")
                info = dado.get("info", {})
                nome_vuln = info.get("name", "Vulnerabilidade Desconhecida")
                
                # Tenta extrair a CVE se existir
                cve = ""
                if "classification" in info and "cve-id" in info["classification"]:
                    cve = " ".join(info["classification"]["cve-id"])
                
                # Monta a string limpa para a IA aprender
                tag_ia = f"NUCLEI_{template_id} {cve}".strip()
                achados_ia.append(tag_ia)
                
                # Printa de forma limpa para visualização
                print(f"[!] Encontrado: {nome_vuln} | {cve}")
                
            except json.JSONDecodeError:
                continue

        if not achados_ia:
            print("[-] Nenhum finding relevante retornado pelo Nuclei.")
            
        return " ".join(achados_ia)
            
    except FileNotFoundError:
        print("\n[-] Erro: Nuclei não está instalado ou não está no PATH do sistema.")
        return ""


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

    # Pega a porta web correta (padrão 80 ou a dinâmica detectada pelo Bash)
    porta_web = dados.get('porta_alvo', '80')
    texto_nuclei = ""
    
    rodar_nuclei = input(f"\n[?] Deseja disparar o Nuclei (scan ativo) contra o alvo {ip}:{porta_web}? (s/n): ").strip().lower()
    if rodar_nuclei == 's':
        print(f"[+] Iniciando scan com Nuclei...")
        texto_nuclei = executar_nuclei_focado(ip, porta_web)
    else:
        print("[-] Scan do Nuclei cancelado pelo operador.")

    if dados['http_aberto']:
        print(f"\n[+] Porta HTTP ({porta_web}) aberta — cruzando HTML com dados de Recon...")
        try:
            html = obte_codigo_fonte(f"http://{ip}:{porta_web}") or ""
            
            # Ordenação para manter consistência no dataset
            texto_recon = ""
            for p in sorted(dados['portas'], key=lambda x: x['porta']):
                texto_recon += f" PORTA {p['porta']} SERVICO {p['servico']} "
            for d in sorted(dados['diretorios'], key=lambda x: x['caminho']):
                texto_recon += f" DIRETORIO {d['caminho']} STATUS {d['status']} "

            texto_final = f"{texto_recon} {html}"
            texto_final = texto_final.replace('\n', ' ').replace('\r', ' ')

            if texto_final.strip():
                # Classifica
                categoria, confianca = classificar_html(texto_final)
                print(f"\n>>> Classificação do alvo: {categoria} (confiança: {confianca * 100:.0f}%)")
                
                if confianca > 0.60:
                    # Concatena Nuclei + Recon para o treino
                    texto_retroalimentacao = f"{texto_final} {texto_nuclei}".strip()
                    
                    print(f"\n[?] A IA quer registrar este alvo definitivamente como '{categoria}'.")
                    print("Opções:\n")
                    print(" [1] Sim, a categoria está correta (Validar)")
                    print(" [2] Não, eu quero digitar a categoria correta (Ensinar nova classe)")
                    print(" [3] Descartar achado\n")
                    
                    escolha = input(">>: ").strip()
                    
                    if escolha == '1':
                        print("\n[+] Injetando dados validados na base de treino...\n")
                        adicionar_exemplo(texto_retroalimentacao, categoria)
                    elif escolha == '2':
                        nova_categoria = input("\n>> Digite a categoria correta: ").strip()
                        print(f"\n[+] Excelente! Injetando aprendizado como '{nova_categoria}'...\n")
                        adicionar_exemplo(texto_retroalimentacao, nova_categoria)
                    else:
                        print("[-] Achado descartado. O dataset não foi alterado.\n")
                        
                else:
                    print("[-] Confiança da IA muito baixa. Abortando scan automatizado e aprendizado.\n")
                    
            else:
                print("\n[-] Nenhum dado (HTML ou Recon) obtido para classificar.")
                
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