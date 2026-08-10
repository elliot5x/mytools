# Recon + ML

Ferramenta de reconhecimento (nmap + FTP anônimo + gobuster) que, ao final,
usa um classificador de Machine Learning para dizer que **tipo de site**
foi encontrado — em vez de só mostrar os echos crus das ferramentas.

## Estrutura do projeto

```
.
├── main.py                      # menu principal, orquestra tudo
├── requirements.txt
├── modules/
│   ├── validation/
│   │   ├── __init__.py
│   │   └── utils.py             # validação de IP, pedir_ip(), cls()
│   └── recon/
│       └── scan.sh              # nmap + FTP anônimo + gobuster
└── ml/
    ├── __init__.py
    ├── leitor.py                 # baixa o HTML de uma URL
    ├── classificador_site.py     # treina/carrega o modelo e classifica
    ├── coletar_dados.py          # script p/ AMPLIAR o dataset com sites reais
    ├── treino_iris.py            # exercício didático separado (não usado no fluxo principal)
    └── data/
        ├── sites_treino.csv      # dataset de treino (rotulado)
        └── modelo.pkl            # cache do modelo treinado (gerado automaticamente)
```

## Como funciona o fluxo

1. `main.py` pede o IP e chama `modules/recon/scan.sh <ip> <arquivo_temp>`.
2. `scan.sh` continua interativo (pergunta se quer tentar FTP anônimo, se
   quer rodar gobuster), mas agora, além dos echos na tela, grava um
   **CSV estruturado** (delimitador `|`, sem cabeçalho) no arquivo temporário
   passado como segundo argumento. Formato:

   ```
   porta|80|http:Apache httpd 2.4.41
   ftp_aberto|<ip>|nao
   http_aberto|<ip>|sim
   diretorio|/admin|301
   ```

3. `main.py` lê esse CSV (`carregar_resultado`), e se a porta 80 estiver
   aberta, baixa o HTML com `ml/leitor.py` e manda para
   `ml/classificador_site.classificar_url()`.
4. O **relatório final impresso ao usuário é a classificação da ML**
   ("Loja Virtual", "Portal de Notícias", etc., com nível de confiança),
   junto com o resumo de portas/diretórios — não mais uma lista solta de
   echos das ferramentas.

Usei CSV (em vez de JSON) para a saída do `scan.sh` justamente pela sugestão
de vocês: é trivial de gerar em bash puro (sem depender de `jq`), e o
`csv.reader` do Python lê isso sem sobrar lixo em memória depois.

## Rodando

```bash
pip install -r requirements.txt
python main.py
```

Na primeira vez que classificar uma URL, o modelo é treinado a partir de
`ml/data/sites_treino.csv` e cacheado em `ml/data/modelo.pkl`. Nas
próximas vezes, só re-treina se o CSV de treino for mais novo que o cache
(ou seja, se você adicionar exemplos novos).

## Sobre o dataset de treino — isso é o ponto mais importante

O `ml/data/sites_treino.csv` que já vem no projeto tem **20 exemplos
sintéticos** (escritos à mão, não são HTML real de sites) cobrindo 5
categorias pensadas para recon/pentest, não para e-commerce genérico:

- **Página Padrão do Servidor** — Apache/nginx/IIS "recém-instalado"
- **Painel de Login/Admin** — telas de autenticação, phpMyAdmin, roteadores
- **CMS Conhecido** — WordPress, Joomla, Drupal
- **Aplicação Web Customizada** — sistemas internos, dashboards, SPAs
- **Listagem de Diretório** — "Index of /", diretórios expostos

Isso só serve pra o pipeline funcionar de primeira. **Não é suficiente
para um modelo confiável.**

### Opção 1 — coletar manualmente com o `coletar_dados.py`

Edite a lista `URLS_TREINO` em `ml/coletar_dados.py` com pares
`(url, categoria)` de sites reais que você já sabe classificar, e rode:

```bash
python -m ml.coletar_dados
```

Isso baixa o HTML de cada URL e acrescenta uma linha em
`sites_treino.csv`. Tente manter uma quantidade parecida de exemplos por
categoria (uns 15-20 cada, pelo menos), senão o modelo tende a "chutar"
sempre a categoria com mais exemplos.

### Opção 2 — usar seus próprios laboratórios de teste

Como as categorias agora são voltadas a recon/pentest, datasets públicos
genéricos de classificação de site (loja, notícia, etc.) não servem mais
de base. A fonte mais natural aqui é rodar `coletar_dados.py` contra VMs
de laboratório que você já usa/conhece — é exatamente o tipo de alvo que
aparece nos seus scans reais:

- **Metasploitable2/3** — boas fontes de "Página Padrão do Servidor"
- **DVWA / bWAPP** — "Painel de Login/Admin" e "Aplicação Web Customizada"
- Uma instalação limpa de **WordPress/Joomla/Drupal** — "CMS Conhecido"
- Qualquer Apache/nginx servindo uma pasta sem `index.html` — "Listagem
  de Diretório"

Isso tende a te dar exemplos muito mais parecidos com o que você
realmente encontra nos scans do que um dataset genérico de e-commerce.

## Observação sobre o uso

`scan.sh` faz varredura de portas, tenta FTP anônimo e enumera diretórios
com gobuster — use apenas em alvos que você tem autorização para testar.