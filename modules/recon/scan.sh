#!/bin/bash
# Uso: scan.sh <ip> [arquivo_resultado_csv]
#
# Faz o reconhecimento (nmap + FTP anônimo opcional + gobuster opcional) e,
# ao final, grava um CSV simples (delimitador "|") em arquivo_resultado_csv
# com o formato:
#
#   tipo|chave|valor
#   porta|80|http:Apache httpd 2.4.41
#   ftp_aberto|<ip>|sim
#   http_aberto|<ip>|nao
#   diretorio|/admin|301
#
# Esse CSV é o que o main.py lê depois para montar o relatório final e
# decidir se manda o conteúdo do site para o classificador de Machine
# Learning. Se nenhum arquivo for passado, um temporário é criado e o
# caminho dele é impresso no final (útil para rodar o script sozinho).

set -uo pipefail 

ip="${1:?Uso: scan.sh <ip> [arquivo_resultado.csv]}"
resultado_arquivo="${2:-$(mktemp --suffix=.csv)}"

clear
echo -e "[+] Escaneando portas em $ip...\n"

nmap_output=$(nmap -sV -sC --open "$ip" 2>/dev/null) || nmap_output=""

ftp_aberto=$(echo "$nmap_output" | grep "21/tcp" | grep "open" || true)
http_aberto=$(echo "$nmap_output" | grep "80/tcp" | grep "open" || true)

ftp_testado="nao"

# ── FTP ──────────────────────────────────────────────
if [ -n "$ftp_aberto" ]; then
    echo -e "[+] Porta FTP (21) encontrada!\n"
    read -p "[?] Tentar logar como anônimo? (s/n): " confirmar

    if [[ "$confirmar" == "s" || "$confirmar" == "S" ]]; then
        echo -e "[+] Iniciando processo...\n"
        ftp_testado="sim"
        ftp "anonymous@$ip" || true
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
            --no-error 2>/dev/null) || true
    else
        echo -e "[-] Pulando etapa...\n"
    fi
else
    echo -e "[-] Porta HTTP (80) fechada ou filtrada. Pulando gobuster.\n"
fi

# ── Monta o CSV de resultado ──────────────────────────
resultado_portas=$(echo "$nmap_output" | grep "open" 2>/dev/null || true)
resultado_diretorios=$(echo "$gobuster_output" | grep "Status" 2>/dev/null || true)

{
    if [ -n "$resultado_portas" ]; then
        while IFS= read -r linha; do
            [ -z "$linha" ] && continue
            porta=$(echo "$linha" | awk '{print $1}')
            servico=$(echo "$linha" | awk '{print $3}')
            info=$(echo "$linha" | cut -d' ' -f4- | sed 's/|/-/g')
            echo "porta|${porta}|${servico}:${info}"
        done <<< "$resultado_portas"
    fi

    ftp_status="nao"; [ -n "$ftp_aberto" ] && ftp_status="sim"
    http_status="nao"; [ -n "$http_aberto" ] && http_status="sim"

    echo "ftp_aberto|${ip}|${ftp_status}"
    echo "ftp_testado|${ip}|${ftp_testado}"
    echo "http_aberto|${ip}|${http_status}"

    if [ -n "$resultado_diretorios" ]; then
        while IFS= read -r linha; do
            [ -z "$linha" ] && continue
            caminho=$(echo "$linha" | awk '{print $1}' | sed 's/|/-/g')
            status=$(echo "$linha" | grep -oE 'Status: [0-9]+' | grep -oE '[0-9]+')
            echo "diretorio|${caminho}|${status}"
        done <<< "$resultado_diretorios"
    fi
} > "$resultado_arquivo"

echo -e "\n[+] Resultado estruturado salvo em: $resultado_arquivo\n"

exit 0
