import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model

lemmatizer = WordNetLemmatizer()

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bow(sentence, words, show_details=True):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                bag[i] = 1
                if show_details:
                    print(f"found in bag: {w}")
    return(np.array(bag))

def predict_class(sentence, model, words, classes):
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def verify_intents():
    print("Loading model and data...")
    try:
        model = load_model('campus_ai_model.h5')
        data = pickle.load(open('data.pickle', 'rb'))
        words = data['words']
        classes = data['classes']
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    test_queries = [
        "What is mental health", # From openai_fallback / General
        "Who is computer HOD",   # New intent
        "where is the canteen",  # New intent
        "tell me about placement", # New intent
        "Hi",                    # Old intent
    ]

    print("\nVerifying Intents:")
    print("-" * 30)
    for query in test_queries:
        print(f"Query: '{query}'")
        ints = predict_class(query, model, words, classes)
        if ints:
            print(f"Predicted Intent: {ints[0]['intent']} (Conf: {ints[0]['probability']})")
        else:
            print("Predicted Intent: None")
        print("-" * 30)

if __name__ == "__main__":
    verify_intents()
