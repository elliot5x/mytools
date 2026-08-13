#!/bin/bash

set -uo pipefail 

ip="${1:?Uso: scan.sh <ip> [arquivo_resultado.csv]}"
resultado_arquivo="${2:-$(mktemp --suffix=.csv)}"

clear
echo -e "[+] Escaneando portas em $ip...\n"

nmap_output=$(nmap -sV -sC --open "$ip" 2>/dev/null) || nmap_output=""

ftp_aberto=$(echo "$nmap_output" | grep "21/tcp" | grep "open" || true)
http_aberto=$(echo "$nmap_output" | awk '/open/ && /http/' || true)
ssh_aberto=$(echo "$nmap_output" | grep "22/tcp" | grep "open" || true)

ftp_testado="nao"

# ── SSH ──────────────────────────────────────────────
if [ -n "$ssh_aberto" ]; then
    echo -e "[+] Porta SSH (22) encontrada!\n"
fi

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

# ── HTTP / Gobuster Dinâmico ──────────────────────────
gobuster_output=""
porta_alvo=""
nuclei_ia=""

portas_http=$(echo "$nmap_output" | awk '/open/ && /http/ {split($1, a, "/"); print a[1]}')

if [ -n "$portas_http" ]; then
    qtd_portas=$(echo "$portas_http" | wc -w)

    if [ "$qtd_portas" -gt 1 ]; then
        portas_linha=$(echo "$portas_http" | tr '\n' ' ')
        echo -e "\n[+] Múltiplos serviços web encontrados nas portas: $portas_linha"

        while true; do
            read -p "[?] Qual porta você deseja usar para o Gobuster? " porta_alvo
            if [[ ! "$porta_alvo" =~ ^[0-9]+$ ]]; then
                echo -e "[-] Entrada inválida: digite apenas o número da porta.\n"
                continue
            fi
            if ! grep -qx "$porta_alvo" <<< "$portas_http"; then
                echo -e "[-] Porta $porta_alvo não está na lista encontrada pelo nmap. Tente novamente.\n"
                continue
            fi
            break
        done
    else
        porta_alvo=$portas_http
        echo -e "\n[+] Serviço web detectado na porta: $porta_alvo"
    fi

    read -p "[?] Deseja rodar o Gobuster na porta $porta_alvo? (s/n): " confirma_gobuster

    if [[ "$confirma_gobuster" == "s" || "$confirma_gobuster" == "S" ]]; then
        echo -e "[+] Iniciando Gobuster em http://$ip:$porta_alvo...\n"
        gobuster_output=$(gobuster dir -u "http://$ip:$porta_alvo" \
            -w /usr/share/wordlists/dirb/common.txt \
            -t 50 \
            -x php,txt,html \
            -b 400,404,403 \
            --no-error 2>/dev/null) || true
    else
        echo -e "[-] Pulando etapa do Gobuster...\n"
    fi

    # ── Nuclei ─────────────────────────────────────────
    read -p "[?] Deseja disparar o Nuclei (scan ativo) na porta $porta_alvo? (s/n): " confirma_nuclei

    if [[ "$confirma_nuclei" == "s" || "$confirma_nuclei" == "S" ]]; then
        echo -e "[+] Iniciando scan com Nuclei...\n"
        nuclei_output=$(nuclei -u "http://$ip:$porta_alvo" -jsonl -severity medium,high,critical 2>/dev/null) || true

        if [ -n "$nuclei_output" ]; then
            while IFS= read -r linha; do
                [ -z "$linha" ] && continue
                template_id=$(echo "$linha" | jq -r '."template-id" // empty')
                nome_vuln=$(echo "$linha" | jq -r '.info.name // "Vulnerabilidade Desconhecida"')
                cve=$(echo "$linha" | jq -r '(.info.classification["cve-id"] // []) | join(" ")')
                echo -e "[!] Encontrado: $nome_vuln | $cve"
                nuclei_ia="${nuclei_ia} NUCLEI_${template_id} ${cve}"
            done <<< "$nuclei_output"
        else
            echo -e "[-] Nenhum finding relevante retornado pelo Nuclei.\n"
        fi
    else
        echo -e "[-] Scan do Nuclei cancelado pelo operador.\n"
    fi
else
    echo -e "[-] Nenhuma porta HTTP encontrada. Pulando Gobuster e Nuclei.\n"
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
    http_status="nao"; [ -n "$portas_http" ] && http_status="sim"

    echo "ftp_aberto|${ip}|${ftp_status}"
    echo "ftp_testado|${ip}|${ftp_testado}"
    echo "http_aberto|${ip}|${http_status}"
    [ -n "$porta_alvo" ] && echo "http_alvo|${ip}|${porta_alvo}"
    [ -n "$nuclei_ia" ] && echo "nuclei|${ip}|$(echo "$nuclei_ia" | sed 's/|/-/g' | xargs)"

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