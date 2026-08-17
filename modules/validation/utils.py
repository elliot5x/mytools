import ipaddress
from sys import exit
from time import sleep
from rich.console import Console
from rich.panel import Panel

console = Console()

BANNER_MAIN = """[0;94;44m [0;34;40m▄[0;97;40m [0;94;44m▒▒▓▓█[0;37;40m [0;94;44m░[0;97;40m [0;94;44m▒▓▓[0;94;40m█[0;37;40m [0;97;40m [0;34;40m█[0;94;44m░▒▒▓█[0;37;40m [0;94;44m░[0;34;40m▀[0;94;44m▒▓▓[0;94;40m█[0;37;40m [0;94;44m░[0;34;40m▀[0;94;44m▒▓▓[0;94;40m█[0;37;40m [0;94;44m░[0;37;40m      [0;94;44m░[0;34;40m▀[0;94;44m▒▓▓█[0m
[0;94;44m  ░░▒▒▓▓[0;37;40m [0;94;44m [0;97;40m [0;94;44m▒▒▓▓[0;37;40m [0;97;40m  [0;94;44m ░▒▒[0;37;40m  [0;94;44m [0;97;40m [0;94;44m▒▒▓[0;94;40m█[0;37;40m [0;94;44m [0;97;40m [0;94;44m▒▒▓[0;94;40m█[0;37;40m [0;94;44m [0;37;40m      [0;94;44m [0;34;40m [0;94;44m▒▒▓▓[0m
[0;94;44m [0;97;40m [0;34;40m▀ [0;94;44m░▒▒▓[0;37;40m [0;34;40m█▄[0;94;44m░▒▒▓[0;37;40m [0;97;40m  [0;94;44m  ░▒[0;37;40m  [0;94;44m [0;97;40m [0;94;44m░▒▒▓[0;37;40m [0;94;44m [0;97;40m [0;94;44m░▒▒▓[0;37;40m [0;94;44m [0;37;40m      [0;94;44m [0;34;40m▄▄▄▄▄[0m
[0;94;44m [0;97;40m [0;34;40m  [0;94;44m░░▒▒[0;37;40m [0;97;40m [0;94;44m [0;34;40m█[0;94;44m░▒[0;37;40m  [0;97;40m  [0;94;44m   ░[0;37;40m  [0;94;44m [0;97;40m [0;94;44m ░▒▒[0;37;40m [0;94;44m [0;97;40m [0;94;44m ░▒▒[0;37;40m [0;94;44m [0;97;40m [0;94;44m ░▒▓[0;37;40m [0;97;40m  [0;94;44m ░▒▒[0m
[0;94;44m [0;97;40m [0;34;40m  [0;94;44m ░░▒[0;37;40m [0;97;40m [0;94;44m   ░[0;37;40m  [0;97;40m  [0;94;44m    [0;37;40m  [0;94;44m [0;97;40m [0;94;44m  ░▒[0;37;40m [0;94;44m [0;97;40m [0;94;44m  ░▒[0;37;40m [0;94;44m [0;34;40m [0;94;44m  ░▒[0;37;40m [0;94;44m [0;97;40m [0;94;44m  ░▒[0m
[0;94;44m [0;97;40m [0;34;40m [0;97;40m [0;94;44m  ░░[0;37;40m [0;97;40m [0;94;44m    [0;37;40m  [0;97;40m  [0;94;44m    [0;37;40m  [0;94;44m [0;34;40m▄[0;94;44m   [0;34;40m█[0;37;40m [0;94;44m [0;34;40m▄[0;94;44m   [0;34;40m█[0;37;40m [0;94;44m [0;34;40m▄[0;94;44m   ░[0;37;40m [0;94;44m [0;34;40m▄[0;94;44m   ░[0m"""

RECON_BANNER = """[0;37;40m                                                      [0m
[0;97;40m [0;34;40m████████▄[0;37;40m [0;34;40m▐█████████▌▐█████████▌[0;97;40m [0;34;40m█████████▐█████████▌[0m
[0;34;40m▐███████▌██▐███████▐██▐███████▌██▐███████▌█▐███████▐██[0m
[0;34;40m▐███████▌██▐███████▐██▐███████▌██▐███████▌█▐███████▐██[0m
[0;34;40m▐███████▌█▌▐███████▄▄[0;37;40m [0;34;40m▐███████▌██▐███████▌█▐███████▐██[0m
[0;34;40m▐█████████[0;37;40m [0;34;40m▐███████▀▀[0;37;40m [0;34;40m▐███████▌[0;37;40m  [0;34;40m▐███████▌█▐███████▐██[0m
[0;34;40m▐███████▌█▌▐███████▐██▐███████▌██▐███████▌█▐███████▐██[0m
[0;34;40m▐███████▌██▐██████████▐██████████▐█████████▐███████▐██[0m\n\n"""


def cls():
    console.clear()


def exibir_menu_principal() -> str:
    cls()
    print(BANNER_MAIN)
    console.print(Panel("[bold cyan]FERRAMENTAS ÚTEIS - BY: MARQUES[/bold cyan]", expand=False))
    console.print("\n[1] Reconhecimento\n[2] Sair\n")
    return console.input("[bold yellow]>> [/bold yellow]").strip()


def exibir_banner_recon():
    cls()
    print(RECON_BANNER)


def validar_ip(ip: str) -> str:
    ip = ip.strip()
    if not ip:
        raise ValueError("IP não pode ser vazio.")

    endereco = ipaddress.ip_address(ip)

    if endereco.is_loopback:
        raise ValueError("IP de loopback não é um alvo válido.")
    if endereco.is_multicast:
        raise ValueError("IP de multicast não é um alvo válido.")

    return str(endereco)


def pedir_ip() -> str | None:
    while True:
        cls()
        console.print(Panel("[bold green]MÓDULO DE RECONHECIMENTO[/bold green]\n[dim]Digite 'quit' para voltar ao menu[/dim]", expand=False))
        
        try:
            raw = console.input("\n[bold cyan][+][/bold cyan] Digite o IP do alvo: ").strip()
            
            if raw.lower() == 'quit':
                return None

            ip = validar_ip(raw)
            console.print(f"[bold green][+] Alvo definido:[/bold green] {ip}")
            sleep(0.6)
            return ip

        except ValueError as e:
            console.print(f"\n[bold red][-] Erro:[/bold red] {e}")
            sleep(1.2)
        except KeyboardInterrupt:
            console.print("\n\n[bold red][-] Cancelado pelo usuário.[/bold red]")
            exit(0)