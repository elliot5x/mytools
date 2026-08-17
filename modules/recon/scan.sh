#!/bin/bash

set -uo pipefail

ip="${1:?Uso: scan.sh <ip>}"

VERDE='\033[92m'
AMARELO='\033[93m'
VERMELHO='\033[91m'
CIANO='\033[96m'
NEGRITO='\033[1m'
RESET='\033[0m'

echo -e "${NEGRITO}${CIANO}[+] Escaneando portas em $ip...${RESET}\n"

nmap_output=$(nmap -sV -sC --open "$ip" 2>/dev/null) || nmap_output=""

portas_abertas=$(echo "$nmap_output" | awk '/^[0-9]+\/tcp/ && /open/')

if [ -n "$portas_abertas" ]; then
    echo -e "${NEGRITO}Portas abertas:${RESET}"
    while IFS= read -r linha; do
        [ -z "$linha" ] && continue
        porta=$(echo "$linha" | awk -F/ '{print $1}')
        resto=$(echo "$linha" | awk '{$1=$2=$3=""; print $0}' | sed -e 's/^[ \t]*//')
        echo -e "  ${VERDE}●${RESET} ${porta}\t${resto}"
    done <<< "$portas_abertas"
    echo ""
else
    echo -e "${VERMELHO}[-] Nenhuma porta aberta encontrada.${RESET}\n"
fi

ftp_aberto=$(echo "$nmap_output" | grep "21/tcp" | grep "open" || true)
ssh_aberto=$(echo "$nmap_output" | grep "22/tcp" | grep "open" || true)

# ── SSH ──────────────────────────────────────────────
if [ -n "$ssh_aberto" ]; then
    echo -e "${VERDE}[+] Porta SSH (22) encontrada!${RESET}\n"
fi

# ── FTP ──────────────────────────────────────────────
if [ -n "$ftp_aberto" ]; then
    echo -e "${VERDE}[+] Porta FTP (21) encontrada!${RESET}\n"
    read -p "$(echo -e "${AMARELO}[?] Tentar logar como anônimo? (s/n): ${RESET}")" confirmar

    if [[ "$confirmar" == "s" || "$confirmar" == "S" ]]; then
        echo -e "[+] Iniciando processo...\n"
        ftp "anonymous@$ip" || true
    else
        echo -e "[-] Pulando etapa...\n"
    fi
else
    echo -e "${VERMELHO}[-] Porta FTP (21) fechada ou filtrada.${RESET}\n"
fi

# ── HTTP / Gobuster Dinâmico ──────────────────────────
porta_alvo=""

portas_http=$(echo "$nmap_output" | awk '/open/ && /http/ {split($1, a, "/"); print a[1]}')

if [ -n "$portas_http" ]; then
    qtd_portas=$(echo "$portas_http" | wc -w)

    if [ "$qtd_portas" -gt 1 ]; then
        portas_linha=$(echo "$portas_http" | tr '\n' ' ')
        echo -e "\n${NEGRITO}[+] Múltiplos serviços web encontrados nas portas:${RESET} $portas_linha"

        while true; do
            read -p "$(echo -e "${AMARELO}[?] Qual porta você deseja usar para o Gobuster? ${RESET}")" porta_alvo
            if [[ ! "$porta_alvo" =~ ^[0-9]+$ ]]; then
                echo -e "${VERMELHO}[-] Entrada inválida: digite apenas o número da porta.${RESET}\n"
                continue
            fi
            if ! grep -qx "$porta_alvo" <<< "$portas_http"; then
                echo -e "${VERMELHO}[-] Porta $porta_alvo não está na lista encontrada pelo nmap. Tente novamente.${RESET}\n"
                continue
            fi
            break
        done
    else
        porta_alvo=$portas_http
        echo -e "\n${VERDE}[+] Serviço web detectado na porta:${RESET} $porta_alvo"
    fi

    read -p "$(echo -e "${AMARELO}[?] Deseja rodar o Gobuster na porta $porta_alvo? (s/n): ${RESET}")" confirma_gobuster

    if [[ "$confirma_gobuster" == "s" || "$confirma_gobuster" == "S" ]]; then
        echo -e "[+] Iniciando Gobuster em http://$ip:$porta_alvo...\n"
        gobuster dir -u "http://$ip:$porta_alvo" \
            -w /usr/share/wordlists/dirb/common.txt \
            -t 50 \
            -x php,txt,html \
            -b 400,404,403 \
            --no-error 2>/dev/null || true
    else
        echo -e "[-] Pulando etapa do Gobuster...\n"
    fi

    # ── Nuclei ─────────────────────────────────────────
    read -p "$(echo -e "${AMARELO}[?] Deseja disparar o Nuclei (scan ativo) na porta $porta_alvo? (s/n): ${RESET}")" confirma_nuclei

    if [[ "$confirma_nuclei" == "s" || "$confirma_nuclei" == "S" ]]; then
        echo -e "[+] Iniciando scan com Nuclei...\n"
        nuclei_output=$(nuclei -u "http://$ip:$porta_alvo" -jsonl -severity medium,high,critical 2>/dev/null) || true

        if [ -n "$nuclei_output" ]; then
            achou=0
            while IFS= read -r linha; do
                [ -z "$linha" ] && continue

                if ! echo "$linha" | jq -e . >/dev/null 2>&1; then
                    continue
                fi

                template_id=$(echo "$linha" | jq -r '."template-id" // empty')
                nome_vuln=$(echo "$linha" | jq -r '.info.name // "Vulnerabilidade Desconhecida"')
                cve=$(echo "$linha" | jq -r '(.info.classification["cve-id"] // []) | join(" ")')

                if [ -z "$template_id" ]; then
                    continue
                fi

                achou=1
                echo -e "  ${VERMELHO}⚠${RESET}  $nome_vuln ${AMARELO}$cve${RESET}"
            done <<< "$nuclei_output"

            if [ "$achou" -eq 0 ]; then
                echo -e "${VERMELHO}[-] O Nuclei retornou saída, mas nenhuma linha era um finding JSON válido.${RESET}\n"
            fi
        else
            echo -e "${VERMELHO}[-] Nenhum finding relevante retornado pelo Nuclei.${RESET}\n"
        fi
    else
        echo -e "[-] Scan do Nuclei cancelado pelo operador.\n"
    fi
else
    echo -e "${VERMELHO}[-] Nenhuma porta HTTP encontrada. Pulando Gobuster e Nuclei.${RESET}\n"
fi

exit 0