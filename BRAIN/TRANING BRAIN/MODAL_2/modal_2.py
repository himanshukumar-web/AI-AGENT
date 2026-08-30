"""
JARVIS AI — ML Model 2 (Multinomial Naive Bayes Intent Classifier)
Trains on intents in qna.json with fallback responses.
"""

import json
import random
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB


def load_and_train():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
    data_path = os.path.join(project_root, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.json')

    if not os.path.exists(data_path):
        return None, None, None

    try:
        with open(data_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading qna.json: {e}")
        return None, None, None

    training_data = []
    for intent in data.get('intents', []):
        if 'patterns' in intent and 'tag' in intent:
            for pattern in intent['patterns']:
                training_data.append((pattern, intent['tag']))

    if not training_data:
        return None, None, data

    X, y = zip(*training_data)
    vectorizer = CountVectorizer()
    X_vec = vectorizer.fit_transform(X)

    classifier = MultinomialNB()
    classifier.fit(X_vec, y)

    return vectorizer, classifier, data


# Cache trained model
vectorizer, classifier, data = None, None, None


def get_response(user_input):
    """Predict intent and return appropriate random response."""
    global vectorizer, classifier, data
    if not user_input or not str(user_input).strip():
        return None

    if vectorizer is None:
        vectorizer, classifier, data = load_and_train()
        if vectorizer is None:
            return None

    try:
        user_input_vectorized = vectorizer.transform([str(user_input)])
        predicted_intent = classifier.predict(user_input_vectorized)[0]

        for intent in data.get('intents', []):
            if intent.get('tag') == predicted_intent:
                responses = intent.get('responses', [])
                if responses:
                    return random.choice(responses)
        return None
    except Exception as e:
        return None


if __name__ == "__main__":
    print("Modal 2 response for 'hello':", get_response("hello"))
