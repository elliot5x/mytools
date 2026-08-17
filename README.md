# Mytools - CLI Automation & Recon

Automação em Python e Shell Script que criei para agilizar o fluxo inicial de reconhecimento de rede e enumeração de serviços em ambientes de laboratório e estudo.

A ideia do projeto é centralizar comandos repetitivos em uma interface de terminal direta e organizada, validando as entradas antes de rodar os scripts de varredura.

---

## 🛠️ Tecnologias e Dependências

### Dependências Python
- Python 3.10+ | Caso não tenha instalado, baixe ele aqui: https://www.python.org/downloads/
- `rich` (formatação de terminal, painéis e cores)

### Ferramentas de Sistema (CLI)
Para os módulos em Shell Script funcionarem corretamente, é necessário ter instaladas as ferramentas utilizadas nas rotinas:
- `nmap`
- `gobuster`
- `nuclei`
- `jq`
- `ftp`

Você pode rodar: ```sudo apt install nmap gobuster nuclei jq -y```

---

## 🚀 Instalação

1. Clone o repositório ou baixe os arquivos:
```bash
git clone https://github.com/elliot5x/Mytoos.git
cd Mytools
```

2. Crie e ative um ambiente virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```
Para desativar é só digitar: ```deactivate``` e o ambiente venv é fechado.

3. Instale as bibliotecas Python:
```bash
pip install -r requirements.txt
```

4. Garanta permissão de execução para os scripts shell:
```bash
chmod +x modules/recon/scan.sh
```

---

## 💻 Como Usar

Basta rodar o script principal:

```bash
python3 main.py
```

### Fluxo de Uso
1. Selecione a opção `[1] Reconhecimento` no menu.
2. Insira o endereço IP que deseja analisar.
3. O script valida se o IP informado é estruturalmente válido e dispara as rotinas interativas de verificação de portas e serviços configuradas no módulo.
4. Para sair da aplicação, escolha a opção `[2] Sair`.

---