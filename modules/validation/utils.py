import ipaddress
from sys import exit
from os import name
from time import sleep
from  subprocess import run

def cls():
    run(['cls'] if name == 'nt' else ['clear'])

def validar_ip(ip: str) -> str:

    """Valida e retorna o IP limpo. Lança ValueError se inválido."""
        
    ip = ip.strip()

    if not ip:
        raise ValueError("IP não pode ser vazio.")

    try:
        endereco = ipaddress.ip_address(ip)
    except ValueError:
        raise ValueError(f"'{ip}' não é um endereço IP válido.")

    if endereco.is_loopback:
        raise ValueError("IP de loopback não é um alvo válido.")
    if endereco.is_multicast:
        raise ValueError("IP de multicast não é um alvo válido.")

    return str(endereco)

def pedir_ip() -> str:

    """Loop de entrada: fica pedindo até receber um IP válido."""

    while True:
        cls()
        print("""\033[0;37;40m /░░░░    /█▀▀▀/    /░░░░    /░░░    /░ /░\033[0m
\033[0;37;40m│_▒ /▒   │ ▓▓▓     │ ▒__/   │_▒/▒   │ ▒▒ ▒\033[0m
\033[0;37;40m│ ▓▓▓/   │_▒_/     │ ▓      │ ▓ ▓   │ ▓│▓▓\033[0m
\033[0;37;40m│ █_/█   │ ░░░░    │ ████   │ ███   │ █│ █\033[0m
\033[0;37;40m│// //   │/___/    │/___/   │/__/   │//│//\033[0m\n""")
        print("----- Digite 'quit' para voltar ao menu.")
        raw = input("\n[+] Digite o IP do alvo: ")
        if raw.strip().lower() == 'quit':
            raise ValueError("[-] Voltando ao menu")
                
        try:
            ip = validar_ip(raw)
            print(f"[+] Alvo definido: {ip}")
            return ip
        except ValueError as e:
            print(f"[-] Inválido: {e}. Tente novamente.")
            sleep(1)
            cls()
        except KeyboardInterrupt:
            print("\n[-] Cancelado pelo usuário.")
            exit(0)