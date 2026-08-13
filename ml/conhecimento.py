"""
Base de conhecimento local para dar mais contexto às classificações do
classificador_site.py.

Uso:
    from ml.conhecimento import BaseConhecimento

    base = BaseConhecimento()
    trechos = base.buscar("painel de login WordPress credenciais padrão", top_k=3)
    for t in trechos:
        print(t['fonte'], t['similaridade'], t['texto'][:200])

Para reindexar manualmente depois de adicionar arquivos nem precisa —
a classe detecta sozinha (por data de modificação) quando os arquivos da
pasta mudaram e reindexa automaticamente na próxima instância.
"""

import os
import re
import glob
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_CONHECIMENTO = os.path.join(BASE_DIR, 'data', 'conhecimento')
INDICE_PKL = os.path.join(BASE_DIR, 'data', 'conhecimento_index.pkl')

TAMANHO_CHUNK = 800  # caracteres por trecho (~1 parágrafo grande)
SOBREPOSICAO = 100   # sobreposição entre trechos, pra não cortar ideia ao meio


def _extrair_texto_pdf(caminho):
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"[-] pypdf não instalado, pulando PDF: {caminho}")
        print("    Instale com: pip install pypdf")
        return ""
    try:
        leitor = PdfReader(caminho)
        return "\n".join((pagina.extract_text() or "") for pagina in leitor.pages)
    except Exception as e:
        print(f"[-] Erro lendo PDF {caminho}: {e}")
        return ""


def _ler_arquivo(caminho):
    if caminho.lower().endswith('.pdf'):
        return _extrair_texto_pdf(caminho)
    with open(caminho, encoding='utf-8', errors='ignore') as f:
        return f.read()


def _dividir_em_chunks(texto, tamanho=TAMANHO_CHUNK, sobreposicao=SOBREPOSICAO):
    texto = re.sub(r'\s+', ' ', texto).strip()
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        chunks.append(texto[inicio:fim])
        inicio = fim - sobreposicao
    return [c for c in chunks if len(c.strip()) > 50]


class BaseConhecimento:
    def __init__(self, pasta=PASTA_CONHECIMENTO, indice_pkl=INDICE_PKL):
        self.pasta = pasta
        self.indice_pkl = indice_pkl
        self.vetorizador = None
        self.matriz = None
        self.chunks = []  # lista de dicts: {texto, fonte}
        self._carregar_ou_indexar()

    def _arquivos_fonte(self):
        arquivos = []
        for padrao in ('*.txt', '*.md', '*.pdf'):
            arquivos.extend(glob.glob(os.path.join(self.pasta, '**', padrao), recursive=True))
        return sorted(arquivos)

    def _carregar_ou_indexar(self):
        os.makedirs(self.pasta, exist_ok=True)
        arquivos = self._arquivos_fonte()
        if not arquivos:
            return  # base vazia — buscar() simplesmente retorna []

        assinatura = sorted((a, os.path.getmtime(a)) for a in arquivos)
        if os.path.exists(self.indice_pkl):
            dados = joblib.load(self.indice_pkl)
            if dados.get('assinatura') == assinatura:
                self.vetorizador = dados['vetorizador']
                self.matriz = dados['matriz']
                self.chunks = dados['chunks']
                return

        self.reindexar()

    def reindexar(self):
        """Relê todos os arquivos da pasta e reconstrói o índice TF-IDF do zero."""
        arquivos = self._arquivos_fonte()
        self.chunks = []
        for caminho in arquivos:
            texto = _ler_arquivo(caminho)
            if not texto.strip():
                continue
            nome_fonte = os.path.relpath(caminho, self.pasta)
            for chunk in _dividir_em_chunks(texto):
                self.chunks.append({'texto': chunk, 'fonte': nome_fonte})

        if not self.chunks:
            self.vetorizador = None
            self.matriz = None
            print(f"[-] Nenhum conteúdo indexável encontrado em {self.pasta}")
            return

        self.vetorizador = TfidfVectorizer(max_features=20000)
        self.matriz = self.vetorizador.fit_transform([c['texto'] for c in self.chunks])

        assinatura = sorted((a, os.path.getmtime(a)) for a in arquivos)
        os.makedirs(os.path.dirname(self.indice_pkl), exist_ok=True)
        joblib.dump({
            'assinatura': assinatura,
            'vetorizador': self.vetorizador,
            'matriz': self.matriz,
            'chunks': self.chunks,
        }, self.indice_pkl)
        print(f"[+] Base de conhecimento indexada: {len(self.chunks)} trecho(s) de {len(arquivos)} arquivo(s).")

    def buscar(self, query, top_k=3, similaridade_minima=0.05):
        """Retorna os top_k trechos mais parecidos com a query (lista vazia se a base estiver vazia)."""
        if not self.vetorizador or not self.chunks:
            return []

        vetor_query = self.vetorizador.transform([query])
        similaridades = cosine_similarity(vetor_query, self.matriz)[0]
        indices = similaridades.argsort()[::-1][:top_k]

        resultados = []
        for i in indices:
            if similaridades[i] < similaridade_minima:
                continue
            resultados.append({
                'texto': self.chunks[i]['texto'],
                'fonte': self.chunks[i]['fonte'],
                'similaridade': float(similaridades[i]),
            })
        return resultados