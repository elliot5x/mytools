# My Tools

## É uma ferramente que facilita o Recon em CTFs

Foi desenvolvida para realizar o padrão de recon sem que você precise se preocupar com as ferramentas e comandos, podendo focar em outras explorações.

Ela funciona de forma simples, você basicamente passa apenas o IP do alvo e a ferramenta faz o resto, rodando nmap, gobuster, curl, testando portas como FTP.

## Requisito

Você precisa de ferramentas como nmap, gobuster e o curl para que tudo funcione de forma limpa, os scripts rodam elas por trás dos panos.

## Instalação

- Clone esse repositório com: ```git clone https://github.com/elliot5x/mytools```
- Abra a pasta e de permissão para o script: ```cd mytools && chmod +x /modules/scan.sh```
- Instale as ferramentas se for necessário: ```sudo apt install nmap -y```, ```sudo apt install gobuster -y```

- Logo após é só rodar com: ```python main.py```