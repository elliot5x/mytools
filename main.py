from sys import exit
from time import sleep
import os
import subprocess
from rich.console import Console
from modules.validation.utils import (
    cls,
    exibir_menu_principal,
    exibir_banner_recon,
    pedir_ip,
)

console = Console()


def executar_scan(ip: str) -> bool:
    caminho = os.path.abspath('./modules/recon/scan.sh')

    if not os.path.exists(caminho):
        console.print(f"\n[bold red][-] Erro:[/bold red] Script não encontrado em {caminho}")
        return False

    exibir_banner_recon()

    try:
        subprocess.run(["bash", caminho, ip], check=True)
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"\n[bold red][-] Falha na execução. Código:[/bold red] {e.returncode}")
        return False
    except KeyboardInterrupt:
        console.print("\n[bold yellow][-] Execução interrompida pelo usuário.[/bold yellow]")
        return False


def main():
    while True:
        opcao = exibir_menu_principal()

        if opcao == "1":
            ip = pedir_ip()
            if ip and executar_scan(ip):
                console.input("\n[dim]Pressione Enter para voltar ao menu...[/dim]")

        elif opcao == "2":
            cls()
            console.print("[bold magenta]Saindo... Até logo![/bold magenta]")
            break

        else:
            console.print("\n[bold red]Opção inválida![/bold red]")
            sleep(1)


if __name__ == "__main__":
    main()