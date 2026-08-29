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
        print(f"Data file not found: {data_path}")
        return None, None, None

    # Load the JSON data
    with open(data_path) as file:
        data = json.load(file)

    # Extract training data
    training_data = []
    for intent in data.get('intents', []):
        if 'patterns' in intent:
            for pattern in intent['patterns']:
                training_data.append((pattern, intent['tag']))
        else:
            print(f"Warning: 'patterns' key is missing in intent: {intent}")

    # Check if training_data is empty
    if not training_data:
        print("Error: No training data found.")
        return None, None, data
    else:
        # Prepare features and labels
        X, y = zip(*training_data)

        # Convert text data to numerical format
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform(X)

        # Train a naive Bayes classifier
        classifier = MultinomialNB()
        classifier.fit(X, y)
        
        return vectorizer, classifier, data

# Initialize on import if needed, or lazy load
vectorizer, classifier, data = None, None, None

def get_response(user_input):
    global vectorizer, classifier, data
    if not vectorizer:
        vectorizer, classifier, data = load_and_train()
        if not vectorizer:
            return "I am not trained yet."

    # Convert user input to numerical format
    user_input_vectorized = vectorizer.transform([user_input])

    # Predict the intent
    predicted_intent = classifier.predict(user_input_vectorized)[0]

    # Get a random response for the predicted intent
    for intent in data.get('intents', []):
        if intent.get('tag') == predicted_intent:
            responses = intent.get('responses', [])
            if responses:
                return random.choice(responses)
            else:
                return "I'm sorry, I don't have a response for that."
    return "I didn't understand that."
