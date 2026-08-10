#!/bin/bash
set -euo pipefail

ip="$1"

clear
echo -e "[+] Escaneando portas...\n"

nmap_output=$(nmap -sV --open "$ip" 2>/dev/null)

ftp_aberto=$(echo "$nmap_output" | grep "21/tcp" | grep "open" || true)
http_aberto=$(echo "$nmap_output" | grep "80/tcp" | grep "open" || true)

# ── FTP ──────────────────────────────────────────────
if [ -n "$ftp_aberto" ]; then
    echo -e "[+] Porta FTP (21) encontrada!\n"
    read -p "[?] Tentar logar como anônimo? (s/n): " confirmar

    if [[ "$confirmar" == "s" || "$confirmar" == "S" ]]; then
        echo -e "[+] Iniciando processo...\n"
        ftp "anonymous@$ip"
    else
        echo -e "[-] Pulando etapa...\n"
    fi    
else
    echo -e "[-] Porta FTP (21) fechada ou filtrada.\n"
fi

# ── HTTP / Gobuster ───────────────────────────────────
gobuster_output=""
if [ -n "$http_aberto" ]; then
    echo -e "[+] Porta HTTP (80) encontrada!\n"
    read -p "[?] Deseja procurar os diretorios com gobuster? (s/n): " confirmacao

    if [[ "$confirmacao" == "s" || "$confirmacao" == "S" ]]; then
        gobuster_output=$(gobuster dir -u "http://$ip" \
            -w /usr/share/seclists/Discovery/Web-Content/common.txt \
            -t 50 \
            -x php,txt,html \
            --no-error 2>/dev/null || echo -e "[-] Gobuster não encontrou resultados.\n")
    else
        echo -e "[-] Pulando etapa...\n"
    fi    
else
    echo -e "[-] Porta HTTP (80) fechada ou filtrada. Pulando gobuster.\n"
fi

# ── Resultado geral ───────────────────────────────────

resultado_portas=$(echo "$nmap_output" | grep "open" 2>/dev/null || true)
resultado_diretorios=$(echo "$gobuster_output" | grep "Status" 2>/dev/null || true)

clear
echo -e "=== RELATÓRIO FINAL ===\n"

if [ -n "$resultado_portas" ]; then
    echo -e "Portas abertas:\n$resultado_portas\n"
else
    echo -e "Portas abertas:\nNenhuma encontrada.\n"
fi

if [ -n "$resultado_diretorios" ]; then
    echo -e "Diretórios existentes:\n$resultado_diretorios\n"
fi

if [ -z "$ftp_aberto" ] && [ -z "$http_aberto" ]; then
    echo -e "[!] Nenhuma porta relevante encontrada no alvo.\n"
fi

# ── Confirmação ───────────────────────────────────────
echo -e "\n--------------------------------------------"
echo -e "[1] Voltar ao menu"
echo -e "--------------------------------------------"
read -p ">> " opcao

if [ "$opcao" = "1" ]; then
    exit 0
fi