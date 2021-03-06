# coding=utf-8
from string import punctuation
from string import digits
from unicodedata import normalize
from unicodedata import combining
from os import listdir
from numpy import array
from numpy import asarray
from numpy import zeros
from collections import Counter
from nltk.corpus import stopwords
from nltk import tokenize
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Embedding
from keras import optimizers
from keras.layers.convolutional import Conv1D
from keras.layers.convolutional import MaxPooling1D
import re

vocabulary_path = 'Dataset/VocabularioPronto1.txt'


stop_words = set(stopwords.words('portuguese') + list(punctuation) + list(digits))


def load_letter_text(filename):
    filtered_words_letter = []

    with open(filename, 'r', encoding='latin-1') as fileDataset:
        textfile = fileDataset.read()
        tokens = tokenize.word_tokenize(textfile)
        # print(tokens)
        trick = ''

        for w in tokens:
            nfkd = normalize('NFKD', w)
            filtered = u"".join([c for c in nfkd if not combining(c)])
            filtered_word = re.sub('[^a-zA-Z0-9 \\\]', '', filtered)
            filtered_words_letter.append(filtered_word.lower())

        words = [word for word in filtered_words_letter if not word in stop_words]
        # print(words)

        # Gambiarra para Remover espaços vazios que "VIERAM DO ALEM" na lista de palavras filtradas
        for w in words:
            trick += w.lower() + " "

        filtered_words_letter = tokenize.word_tokenize(trick)

    return filtered_words_letter


def load_vocabulary_doc(filename):
    vocabulary_list = []
    with open(filename, 'r', encoding='latin-1') as fileVocabulary:
        textfile = fileVocabulary.read()
        vocabulary = tokenize.word_tokenize(textfile)

        vocabulary_list = [word for word in vocabulary if not word in stop_words]

    return vocabulary_list


def upgrade_vocabulary(filtered_words_letter, path_vocabulary_file):
    cont_equal_vocab = 0

    with open(path_vocabulary_file, 'a') as file:

        for target in filtered_words_letter:
            # Filtar novas palavras para o Vocabulario
            vocabulary_list = load_vocabulary_doc(path_vocabulary_file)

            for vocab in vocabulary_list:
                # print('Palavras Comparadas: ', target + ' : ' + vocab)
                if target.strip() == vocab.strip():
                    break
                cont_equal_vocab += 1

            if cont_equal_vocab == len(vocabulary_list):
                # print('Nova palavra no Vocabulario:' + target)
                # file.write(target.lower() + "\n")
                file.write(target + '\n')

            cont_equal_vocab = 0


# Atualiza o vocabulario a medida que aumenta a leitura no dataset
def upgrade_vocabulary(vocabulary_existent, tokens):
    with open(vocabulary_existent, 'r', encoding='latin-1') as file:
        vocab = file.read()
        vocabulary_tokens = tokenize.word_tokenize(vocab)
        cont_equal_word = 0
        words_filtered = []

        for word_document in tokens:
            for word_vocabulary in vocabulary_tokens:
                if word_vocabulary.lower() == word_document.lower():
                    break
                else:
                    cont_equal_word += 1

            if cont_equal_word == len(vocabulary_tokens):
                words_filtered.append(word_document)
            cont_equal_word = 0

    with open(vocabulary_existent, 'a', encoding='latin-1') as file:
        for word in words_filtered:
            file.write(word.lower() + '\n')


# Carrega todos os documentos em um diretorio
def process_letter(directory, vocab, is_trian):
    documents = list()
    # Percorre todos os documentos dentro de um diretorio
    for inside_file in listdir(directory):
        # Pula qualquer comentario no nosso dataset
        if is_trian and inside_file.startswith('0'):
            print("Lendo Arquivo.....", inside_file)
            path = directory + '/' + inside_file
            letter_tokens = load_letter_text(path)
            documents.append(letter_tokens)


        if not is_trian and inside_file.startswith('test'):
            print("Lendo Arquivo para Test.....", inside_file)
            path = directory + '/' + inside_file
            letter_tokens = load_letter_text(path)
            documents.append(letter_tokens)


    return documents


# Carrega um "embutido" tipo como um diretorio (E uma camada de incorporaçao que mapeia indices das palavras)
def embedding(filename):
    # Carrega o "embutido" na momoria e pula a primeira linha
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()
    # Cria um mapa de palavras para um vetor
    embedding = dict()
    for line in lines:
        parts = line.split()
        embedding[parts[0]] = asarray(parts[1:], dtype='float32')
    return embedding


# Peguei da internet, ainda estou estudado o que faz
def get_weight_matrix(embedding, vocab):
    vocab_size = len(vocab) + 1
    weight_matrix = zeros((vocab_size, 100))
    for word, i in vocab.items():
        vector = embedding.get(word)
        if vector is not None:
            weight_matrix[i] = vector
    return weight_matrix


'''vocabulary_list = Counter()
process_docs('Dataset/Banco de Dados Positivos/', vocabulary_list, True)
print(len(vocabulary_list))
print(vocabulary_list.most_common(10))
print(getVocabulary(vocabulary_path)[:20])
'''

# Carrega o vocaculario
vocab_filename = vocabulary_path  # Vocabulario feito por Edivaldo
vocab = load_vocabulary_doc(vocabulary_path)
vocab = set(vocab)

# Carrega todas as avaliaçoes de treinamento
letter_positive = process_letter('Dataset/Banco de Dados Positivos', vocab, True)
letter_negative = process_letter('Dataset/Banco de Dados Negativos', vocab, True)
train = letter_positive + letter_negative

tokenizer = Tokenizer()
tokenizer.fit_on_texts(train)

encoded_letters = tokenizer.texts_to_sequences(train)
# Conjunto de Treinameto e seu comprimento!
length = max([len(s) for s in train])
X_train = pad_sequences(encoded_letters, maxlen=length, padding='post')
# Definiçao de rotulos de treinamento
Y_train = array([0 for _ in range(36)] + [1 for _ in range(36)])

# Carrega a base dos testes
letter_positive = process_letter('Dataset/Banco de Dados Positivos', vocab, False)
letter_negative = process_letter('Dataset/Banco de Dados Negativos', vocab, False)
test_learning = letter_positive + letter_negative

encoded_letters = tokenizer.texts_to_sequences(test_learning)

X_test = pad_sequences(encoded_letters, maxlen=length, padding='post')
Y_test = array([0 for _ in range(100)] + [1 for _ in range(100)])

# Definir o tamanho do vocabulario
size = len(tokenizer.word_index) + 1

gross_embedding = embedding('Dataset/glove.txt')
embeddin_arrays = get_weight_matrix(gross_embedding, tokenizer.word_index)
embedding_layer = Embedding(size, 100, weights=[embeddin_arrays], input_length=length, trainable=False)

# Obter um otmizador / Exemplo baseado em https://keras.io/optmizers
optimizer = optimizers.Adam(lr=0.01, beta_1=0.9, beta_2=-.999, epsilon=None, decay=0.0, amsgrad=False)

# Definiçao do Modelo da CNN
model = Sequential()
model.add(embedding_layer)
model.add(Conv1D(filters=128, kernel_size=5, activation='relu'))
model.add(MaxPooling1D(pool_size=2))
model.add(Flatten())
model.add(Dense(10, activation='relu'))
# Camada de saida, a qual a ativaçao sigmoid gera um valor entre 0 e 1
model.add(Dense(1, activation='sigmoid'))
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train, Y_train, epochs=5, verbose=2)
print(model.summary())

loss, accuracy = model.evaluate()
print('Taxa de Perda: ', loss)
print('Taxa de Acuracia: ', accuracy * 100)
