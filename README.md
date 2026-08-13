# Recon + ML

Ferramenta de automação de recon (nmap, FTP e gobuster) que utiliza um classificador de Machine Learning para identificar a categoria da aplicação web encontrada (ex: Painel de Login, CMS, Página Padrão) em vez de apenas exibir logs brutos.

## Estrutura do Projeto

.
├── main.py                      # Script principal e orquestrador
├── requirements.txt             # Dependências Python
├── modules/
│   ├── validation/
│   │   └── utils.py             # Validação de IP e utilitários de terminal
│   └── recon/
│       └── scan.sh              # Script Bash (nmap + FTP + gobuster)
└── ml/
    ├── leitor.py                 # Extração do HTML alvo
    ├── classificador_site.py     # Treinamento e inferência do modelo
    ├── coletar_dados.py          # Script para expandir o dataset
    └── data/
        ├── sites_treino.csv      # Dataset rotulado
        └── modelo.pkl            # Cache do modelo treinado

## Como Funciona

1. Varredura: O main.py executa o scan.sh para mapear portas, testar FTP anônimo e enumerar diretórios via gobuster.
2. Estruturação: Os resultados da varredura são exportados em um CSV temporário delimitado por |.
3. Classificação via ML: Se a porta web estiver aberta, o HTML da página é capturado e enviado ao classificador.
4. Relatório: O terminal exibe a categoria identificada (ex: "CMS Conhecido", "Painel de Login") com a porcentagem de confiança, além do resumo de portas e diretórios.

## Instalação e Uso

pip install -r requirements.txt
python main.py

*O modelo é treinado automaticamente na primeira execução a partir de ml/data/sites_treino.csv e salvo em cache (ml/data/modelo.pkl). Ele só é re-treinado se o CSV for modificado.*

## Dataset e Treinamento

O arquivo sites_treino.csv inicial conta com dados básicos para validação do pipeline. As categorias cobertas são:

- Página Padrão do Servidor (Apache, nginx, IIS)
- Painel de Login/Admin (Telas de autenticação, phpMyAdmin)
- CMS Conhecido (WordPress, Joomla, Drupal)
- Aplicação Web Customizada (Dashboards, SPAs)
- Listagem de Diretório (Index of /)

### Expandindo o Dataset

Para melhorar a precisão do modelo em cenários reais:

1. Coleta Direta: Adicione as URLs e suas respectivas categorias no array URLS_TREINO dentro de ml/coletar_dados.py e execute:
   python -m ml.coletar_dados
2. Laboratórios Controlados: Aponte a coleta para aplicações de teste conhecidas (como Metasploitable, DVWA ou instalações locais de CMS) para gerar amostras realistas.

## Aviso Legal

Ferramenta desenvolvida exclusivamente para fins educacionais e testes autorizados. Não execute escaneamentos em alvos sem autorização prévia.