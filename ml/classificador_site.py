"""
Classificador de sites por categoria, voltado pra recon/pentest (ex.:
"Página Padrão do Servidor", "Painel de Login/Admin", "CMS Conhecido",
"Aplicação Web Customizada", "Listagem de Diretório").

Usa um pipeline simples Bag-of-Words + Naive Bayes, treinado a partir de
ml/data/sites_treino.csv. O modelo treinado é cacheado em ml/data/modelo.pkl
e só é re-treinado quando o CSV de treino muda — assim cada scan não paga
o custo de re-treinar do zero.

Uso típico (chamado pelo main.py depois do scan.sh):

    from ml.classificador_site import classificar_url
    categoria, confianca = classificar_url("http://192.168.0.10")
"""

import os
import csv
import joblib
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ml.leitor import obte_codigo_fonte

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_CSV = os.path.join(BASE_DIR, 'data', 'sites_treino.csv')
MODELO_PKL = os.path.join(BASE_DIR, 'data', 'modelo.pkl')


def carregar_dataset(caminho=DADOS_CSV):
    textos, labels = [], []
    with open(caminho, newline='', encoding='utf-8') as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            if linha.get('html') and linha.get('categoria'):
                textos.append(linha['html'])
                labels.append(linha['categoria'])
    return textos, labels


def treinar_modelo(forcar=False):
    """Treina o pipeline, ou recarrega do cache se o dataset não mudou."""
    if not os.path.exists(DADOS_CSV):
        raise FileNotFoundError(
            f"Dataset de treino não encontrado em {DADOS_CSV}. "
            "Veja ml/coletar_dados.py para popular esse arquivo."
        )

    dataset_mtime = os.path.getmtime(DADOS_CSV)
    if not forcar and os.path.exists(MODELO_PKL):
        if os.path.getmtime(MODELO_PKL) >= dataset_mtime:
            return joblib.load(MODELO_PKL)

    textos, labels = carregar_dataset()
    if len(set(labels)) < 2:
        raise ValueError(
            "O dataset de treino precisa de pelo menos 2 categorias diferentes."
        )

    pipeline = Pipeline([
        ('vetorizador', CountVectorizer(max_features=5000)),
        ('classificador', MultinomialNB()),
    ])
    pipeline.fit(textos, labels)

    os.makedirs(os.path.dirname(MODELO_PKL), exist_ok=True)
    joblib.dump(pipeline, MODELO_PKL)
    return pipeline


def classificar_html(html):
    """Classifica um HTML já baixado. Retorna (categoria, confianca)."""
    modelo = treinar_modelo()
    probs = modelo.predict_proba([html])[0]
    idx = probs.argmax()
    return modelo.classes_[idx], float(probs[idx])


def classificar_url(url):
    """Baixa o HTML da URL e classifica. Retorna (None, 0.0) se não conseguir baixar."""
    codigo_fonte = obte_codigo_fonte(url)
    if not codigo_fonte:
        return None, 0.0
    return classificar_html(codigo_fonte)


def adicionar_exemplo(html, categoria, caminho=DADOS_CSV):
    """Acrescenta um novo exemplo rotulado ao dataset de treino."""
    # Sanitiza o texto para manter o padrão de linha única do CSV
    html_limpo = html.replace('\n', ' ').replace('\r', ' ').strip()
    
    novo_arquivo = not os.path.exists(caminho)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, 'a', newline='', encoding='utf-8') as f:
        escritor = csv.writer(f)
        if novo_arquivo:
            escritor.writerow(['html', 'categoria'])
        # Grava a versão sem quebras de linha
        escritor.writerow([html_limpo, categoria])