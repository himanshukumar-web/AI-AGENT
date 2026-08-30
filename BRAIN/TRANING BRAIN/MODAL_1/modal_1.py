"""
JARVIS AI — ML Model 1 (TF-IDF & Cosine Similarity QA Engine)
Automatically downloads necessary NLTK corpora on startup.
"""

import os
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Ensure required NLTK resources are available
def _ensure_nltk_resources():
    for resource in ['punkt', 'punkt_tab', 'stopwords']:
        try:
            nltk.data.find(f'tokenizers/{resource}' if 'punkt' in resource else f'corpora/{resource}')
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass

_ensure_nltk_resources()


def load_dataset(file_path):
    """Load Q&A dataset from text file."""
    if not os.path.exists(file_path):
        return []

    dataset = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        for line in file:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                dataset.append({'question': parts[0].strip(), 'answer': parts[1].strip()})
    return dataset


def preprocess_text(text):
    """Tokenize, remove stopwords, and stem text."""
    if not text:
        return ""
    try:
        stop_words = set(stopwords.words('english'))
        ps = PorterStemmer()
        tokens = word_tokenize(text.lower())
        stemmed = [ps.stem(token) for token in tokens if token.isalnum() and token not in stop_words]
        return ' '.join(stemmed) if stemmed else text.lower()
    except Exception:
        return text.lower()


def train_tfidf_vectorizer(dataset):
    """Train TF-IDF vectorizer on dataset questions."""
    if not dataset:
        return None, None
    corpus = [preprocess_text(qa['question']) for qa in dataset]
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(corpus)
    return vectorizer, X


def get_answer(question, vectorizer, X, dataset, threshold=0.3):
    """Retrieve the most relevant answer via cosine similarity."""
    if not vectorizer or X is None or not dataset:
        return None
    processed_q = preprocess_text(question)
    if not processed_q:
        return None
    q_vec = vectorizer.transform([processed_q])
    similarities = cosine_similarity(q_vec, X)
    best_idx = similarities.argmax()
    best_score = similarities[0, best_idx]
    if best_score >= threshold:
        return dataset[best_idx]['answer']
    return None


# Global cached model
_vectorizer = None
_matrix = None
_dataset = None


def mind(text):
    """Execute TF-IDF QA engine."""
    global _vectorizer, _matrix, _dataset
    if _vectorizer is None or _matrix is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
        dataset_path = os.path.join(project_root, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.txt')
        _dataset = load_dataset(dataset_path)
        _vectorizer, _matrix = train_tfidf_vectorizer(_dataset)

    return get_answer(text, _vectorizer, _matrix, _dataset)


if __name__ == "__main__":
    print("Modal 1 response:", mind("who are you"))
