from sys import exit
from time import sleep
import os
import subprocess
from modules.validation.utils import pedir_ip, cls


def executar_script(nome_script, ip):
    caminho = os.path.abspath(f'./modules/{nome_script}')
    
    if not os.path.exists(caminho):
        print(f"\n[-] Erro: Script {nome_script} não encontrado em ./modules/")
        return

    try:
        subprocess.run(["bash", caminho, ip], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[-] O script falhou com código de retorno: {e.returncode}")
    except KeyboardInterrupt:
        print("\n[-] Execução interrompida pelo usuário.")

def menu():
    while True:
        try:
            cls()
            print("""[0;37;40m /░░░░░    /░  /░           /░░░    /░░░    /░░░    /░       /░░░[0m
[0;37;40m│ ▒ ▒ ▒   │//▒/▒/          │//▒/   │_▒/▒   │_▒/▒   │ ▒      │ ▒_/[0m
[0;37;40m│ ▓ ▓ ▓    │//▓/            │ ▓    │ ▓ ▓   │ ▓ ▓   │ ▓      │/_▓ [0m
[0;37;40m│ █ █ █     │ █             │ █    │ ███   │ ███   │ ███    /███ [0m
[0;37;40m│//////     │//             │//    │/__/   │/__/   │/__/   │/__/ [0m\n""")
            print("------------ Ferramentas utéis By: Marques ------------\n\n")
            print("[1] Reconhecimento\n[2] Sair\n")
            escolha = int(input(">> "))
            opcoes = {
                1: lambda: executar_script('scan.sh', pedir_ip()),
                2: exit
            }
            if escolha in opcoes:
                opcoes[escolha]()
            else:
                print("Erro, número inválido.")
                sleep(1)

        except ValueError as e:
            print(e)
            sleep(1)


menu()