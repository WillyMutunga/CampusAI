import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle
import numpy as np
import random
import sys

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

def download_nltk_resources():
    """Download necessary NLTK data."""
    nltk_packages = ['punkt', 'wordnet', 'omw-1.4', 'punkt_tab']
    for package in nltk_packages:
        print(f"Checking {package}...")
        try:
            nltk.data.find(f'tokenizers/{package}')
        except LookupError:
            try:
                nltk.data.find(f'corpora/{package}')
            except LookupError:
                print(f"Downloading {package}...")
                nltk.download(package, quiet=True)
        except Exception as e:
            print(f"Error processing {package}: {e}")
            print(f"Attempting to force download {package}...")
            nltk.download(package, quiet=True, force=True)

def preprocess_data(intents_file='intents.json', output_file='data.pickle'):
    """
    Load intents, preprocess data, and create training arrays.
    """
    print(f"Loading data from {intents_file}...")
    try:
        with open(intents_file, 'r') as file:
            intents = json.load(file)
    except FileNotFoundError:
        print(f"Error: File {intents_file} not found.")
        return

    words = []
    classes = []
    documents = []
    ignore_words = ['?', '!', '.', ',']

    print("Tokenizing and analyzing patterns...")
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            # Tokenize each word
            w = nltk.word_tokenize(pattern)
            words.extend(w)
            # Add to documents in corpus
            documents.append((w, intent['tag']))
            # Add to classes list
            if intent['tag'] not in classes:
                classes.append(intent['tag'])

    # Lemmatize, lower each word and remove duplicates
    print("Lemmatizing and cleaning...")
    words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
    words = sorted(list(set(words)))

    # Sort classes
    classes = sorted(list(set(classes)))

    print(f"Found {len(documents)} documents (patterns)")
    print(f"Found {len(classes)} classes (intents)")
    print(f"Found {len(words)} unique lemmatized words")

    # Create training data
    training = []
    output_empty = [0] * len(classes)

    print("Creating training data (Bag of Words)...")
    for doc in documents:
        # Initialize bag of words
        bag = []
        pattern_words = doc[0]
        # Lemmatize pattern words
        pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]

        # Create bag of words array with 1, if word found in current pattern
        for w in words:
            bag.append(1) if w in pattern_words else bag.append(0)

        # Output is a '0' for each tag and '1' for current tag (for each pattern)
        output_row = list(output_empty)
        output_row[classes.index(doc[1])] = 1

        training.append([bag, output_row])

    # Shuffle features and turn into np.array
    random.shuffle(training)
    training = np.array(training, dtype=object)

    # Create train and test lists. X - patterns, Y - intents
    train_x = list(training[:, 0])
    train_y = list(training[:, 1])

    print("Training data created")
    print(f"train_x shape: {len(train_x)} samples, {len(train_x[0])} features")
    print(f"train_y shape: {len(train_y)} samples, {len(train_y[0])} output classes")

    # Save all structures
    data = {
        'words': words,
        'classes': classes,
        'train_x': np.array(train_x),
        'train_y': np.array(train_y)
    }

    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"Data successfully saved to {output_file}")

if __name__ == "__main__":
    download_nltk_resources()
    preprocess_data()
