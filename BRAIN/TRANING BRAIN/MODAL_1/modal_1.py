# import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# import nltk
# nltk.download('stopwords')
# import nltk
# nltk.download('punkt')
# Load your Q&A dataset from a text file
def load_dataset(file_path):
    if not os.path.exists(file_path):
        print(f"Dataset not found: {file_path}")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        qna_pairs = [line.strip().split(':') for line in lines if ':' in line]
        dataset = [{'question': q, 'answer': a} for q, a in qna_pairs]
    return dataset


# Preprocess the text
def preprocess_text(text):
    try:
        stop_words = set(stopwords.words('english'))
        ps = PorterStemmer()
        tokens = word_tokenize(text.lower())
        tokens = [ps.stem(token) for token in tokens if token.isalnum() and token not in stop_words]
        return ' '.join(tokens)
    except Exception as e:
        print(f"Error preprocessing text: {e}")
        return text

# Train the TF-IDF vectorizer
def train_tfidf_vectorizer(dataset):
    if not dataset:
        return None, None
    corpus = [preprocess_text(qa['question']) for qa in dataset]
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(corpus)
    return vectorizer, X

# Retrieve the most relevant answer
def get_answer(question, vectorizer, X, dataset):
    if not vectorizer or X is None:
        return "Brain not trained."
    question = preprocess_text(question)
    question_vec = vectorizer.transform([question])
    similarities = cosine_similarity(question_vec, X)
    best_match_index = similarities.argmax()
    return dataset[best_match_index]['answer']

# Main function
def mind(text):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    dataset_path = os.path.join(project_root, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.txt')
    
    dataset = load_dataset(dataset_path)
    vectorizer, X = train_tfidf_vectorizer(dataset)
    user_question = text
    answer = get_answer(user_question, vectorizer, X, dataset)
    print(answer)
