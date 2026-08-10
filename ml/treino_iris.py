"""
Exercício didático de comparação de algoritmos de classificação usando o
dataset clássico Iris. NÃO faz parte do fluxo principal (main.py) — isso
aqui é só um script de estudo/comparação de algoritmos do scikit-learn,
sem relação com o classificador de sites usado no recon.

Precisa de internet (baixa o dataset da UCI). Rode direto:
    python ml/treino_iris.py
"""

import pandas
from sklearn import model_selection
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC

URL = 'http://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data'
ATRIBUTOS = ["sepal_length", "sepal_width", "petal_length", "petal_width", "class"]


def carregar_dataset():
    dataset = pandas.read_csv(URL, names=ATRIBUTOS)
    dataset.columns = ATRIBUTOS
    return dataset


def main():
    dataset = carregar_dataset()

    array = dataset.values
    X = array[:, 0:4]
    Y = array[:, 4]
    seed = 7

    X_train, X_validation, Y_train, Y_validation = model_selection.train_test_split(
        X, Y, test_size=0.20, random_state=seed
    )

    modelos = [
        ('LR', LogisticRegression(solver='liblinear', multi_class='ovr')),
        ('LDA', LinearDiscriminantAnalysis()),
        ('KNN', KNeighborsClassifier()),
        ('CART', DecisionTreeClassifier()),
        ('NB', GaussianNB()),
        ('SVM', SVC(gamma='auto')),
    ]

    print("Comparação de algoritmos (10-fold cross-validation):\n")
    for nome, modelo in modelos:
        kfold = model_selection.KFold(n_splits=10, random_state=seed, shuffle=True)
        resultados = model_selection.cross_val_score(
            modelo, X_train, Y_train, cv=kfold, scoring='accuracy'
        )
        print(f"{nome}: {resultados.mean():.4f} ({resultados.std():.4f})")

    # Avaliação final com KNN no conjunto de validação
    knn = KNeighborsClassifier()
    knn.fit(X_train, Y_train)
    predicoes = knn.predict(X_validation)

    print("\nAcurácia KNN:", accuracy_score(Y_validation, predicoes))
    print("Matriz de Confusão:\n", confusion_matrix(Y_validation, predicoes))
    print("Relatório de Classificação:\n", classification_report(Y_validation, predicoes))


if __name__ == "__main__":
    main()
