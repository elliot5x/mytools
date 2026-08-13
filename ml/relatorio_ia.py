import re
import textwrap

from ml.conhecimento import BaseConhecimento

# Limite mínimo de similaridade pra um trecho da base de conhecimento entrar
# no relatório. Testado na prática: abaixo disso os resultados tendem a ser
# "genéricos" (ex.: casar por causa de listas de porta/protocolo comuns a
# quase qualquer texto técnico) em vez de realmente relevantes pro achado.
SIMILARIDADE_MINIMA_RELATORIO = 0.12

# Pontos de atenção genéricos por categoria. Ajuste/expanda essa lista
# conforme o seu classificador aprender categorias novas — é só isso que
# vai crescer, o resto do código não precisa mudar.
PONTOS_DE_ATENCAO = {
    "Painel de Login/Admin": [
        "Existe alguma política de rate limiting / bloqueio por tentativas visível?",
        "Credenciais padrão do fabricante já foram trocadas?",
        "O painel precisa mesmo estar exposto assim, ou deveria estar atrás de VPN/allowlist de IP?",
    ],
    "CMS Conhecido": [
        "Qual a versão exata do CMS e dos plugins/temas visíveis?",
        "Essa versão consta em algum CVE público conhecido (checar NVD/base de conhecimento)?",
        "Há arquivos de config/backup expostos por engano (.env, wp-config.php.bak etc.)?",
    ],
    "Listagem de Diretório": [
        "Listagem de diretório costuma vazar estrutura interna — algo sensível está acessível ali?",
        "Há backups, logs ou configs entre os arquivos listados?",
    ],
    "Página Padrão do Servidor": [
        "Pode ser serviço mal configurado/recém-instalado, ou honeypot — vale confirmar qual dos dois.",
        "Confirmar que não há vhost/aplicação real escondida atrás dessa página padrão.",
    ],
    "Aplicação Web Customizada": [
        "Sem assinatura conhecida — vale mapear manualmente endpoints e parâmetros antes de testar.",
        "Inputs refletidos na tela são indício de possíveis pontos de injeção a validar manualmente.",
    ],
}


def _pontos_padrao(categoria):
    return PONTOS_DE_ATENCAO.get(
        categoria,
        ["Categoria sem pontos de atenção pré-cadastrados — adicione em ml/relatorio_ia.py conforme for aprendendo."],
    )


def _diretorios_do_texto_recon(texto_recon):
    """Extrai só os trechos 'DIRETORIO ... STATUS ...' do texto_recon, descartando
    a lista de PORTA/SERVICO — nomes de diretório costumam ser bem mais
    distintivos pra busca (ex.: 'admin', 'squirrelmail') do que a lista de
    portas/protocolos, que se repete parecido em quase qualquer alvo e só
    "puxa" a busca pra trechos genéricos de rede na base de conhecimento."""
    return " ".join(re.findall(r'DIRETORIO\s+\S+\s+STATUS\s+\S+', texto_recon))


def gerar_analise(categoria, confianca, texto_recon="", nuclei_texto="", base=None):
    """Monta um bloco de texto com categoria, pontos de atenção e contexto da base de conhecimento."""
    base = base or BaseConhecimento()

    linhas = [f"Categoria: {categoria} (confiança: {confianca * 100:.0f}%)"]

    linhas.append("\nPontos de atenção comuns para essa categoria:\n")
    for ponto in _pontos_padrao(categoria):
        linhas.append(f"  - {ponto}")

    diretorios = _diretorios_do_texto_recon(texto_recon)
    query_busca = f"{categoria} {diretorios} {nuclei_texto}".strip()
    trechos = base.buscar(query_busca, top_k=3, similaridade_minima=SIMILARIDADE_MINIMA_RELATORIO)
    if trechos:
        linhas.append("\nContexto relevante da sua base de conhecimento:\n")
        for t in trechos:
            resumo = textwrap.shorten(t['texto'], width=280, placeholder="...")
            linhas.append(f"\n  [{t['fonte']} | similaridade {t['similaridade']:.2f}]\n")
            linhas.append(f"    {resumo}...")
    else:
        linhas.append(
            "\n(Nenhum material relevante na base de conhecimento local ainda — "
            "adicione arquivos em ml/data/conhecimento/ para enriquecer essa análise.)"
        )

    return "\n".join(linhas)