import sys
print("Initializing Chatbot Engine...", flush=True)

try:
    import numpy as np
    print("Imported numpy", flush=True)
    import pickle
    print("Imported pickle", flush=True)
    import nltk
    from nltk.stem import WordNetLemmatizer
    from tensorflow.keras.models import load_model
    print("Imported tensorflow", flush=True)
    print("Imported nltk", flush=True)
    from models import db, FeeStatement, Knowledge, UserQuery, QAPair # Import ORM models
    from gemini_service import get_gemini_response
except Exception as e:
    print(f"Import Error: {e}", flush=True)
    sys.exit(1)


lemmatizer = WordNetLemmatizer()
model = None
words = []
classes = []

def load_chatbot_model():
    global model, words, classes
    try:
        model = load_model('campus_ai_model.h5')
        data = pickle.load(open("data.pickle", "rb"))
        words = data['words']
        classes = data['classes']
        print("Chatbot model (re)loaded successfully.", flush=True)
    except Exception as e:
        print(f"Error loading chatbot model: {e}", flush=True)

# Initial load
load_chatbot_model()

# 1. Database Connection Logic
# 1. Database Connection Logic - REMOVED (Handled by Flask-SQLAlchemy)

# 2. Text Preprocessing
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence.lower())
    return [lemmatizer.lemmatize(word) for word in sentence_words]

def bow(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)
    recognized_count = 0
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s: 
                bag[i] = 1
                recognized_count += 1
    return np.array(bag), recognized_count

# 3. Predict Intent
def predict_class(sentence):
    cleaned = clean_up_sentence(sentence)
    total_words = len(cleaned)
    p, recognized_count = bow(sentence, words)
    
    # If no words are recognized at all, we should indicate low confidence
    if recognized_count == 0 or total_words == 0:
        return [], 0.0
        
    ratio = recognized_count / total_words
    
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Return results and the recognition ratio
    return [{"intent": classes[r[0]], "probability": str(r[1])} for r in results], ratio

# 4. Fetch Response (Database Logic via ORM)
def get_response(intents_list, user_query_text="", student_id=None, ratio=1.0):
    tag = intents_list[0]['intent'] if intents_list else 'unknown'
    probability = float(intents_list[0]['probability']) if intents_list else 0.0
    
    response = ""
    source = "local"
    
    # Load intents JSON for fallback responses (greeting, goodbye)
    import json
    import random
    try:
        with open('intents.json', 'r') as f:
            intents_data = json.load(f)
    except:
        intents_data = {"intents": []}

    # If confidence is low OR ratio of recognized words is low, fallback to Gemini
    # Use 0.5 as a reasonable threshold for recognizing the sentence context
    # PRIORITY 1: Functional Intents (Database Queries) - specific interactive features
    # These should take precedence if confidence is high, as they provide dynamic user-specific data.
    if tag == 'fee_inquiry' and probability > 0.8:
        response = "Please visit the student portal to verify your up-to-date fee balance."
        return response # Early return for specific function
    elif tag == 'fee_structure' and probability > 0.8:
        response = "You can download the latest fee structure here: <a href='/static/uploads/fee_structure.pdf' target='_blank'>Download Fee Structure</a>."
        return response

    # PRIORITY 2: Scraped Knowledge Base (QAPair)
    # Check this BEFORE generic intents (like 'number', 'greeting') to ensure we use specific scraped info.
    print(f"Checking QAPairs for: {user_query_text}", flush=True)
    qa_response = None
    try:
        # Flexible matching logic using Token Overlap
        all_qa = QAPair.query.all()
        best_match = None
        highest_score = 0.0
        
        query_tokens = set(nltk.word_tokenize(user_query_text.lower()))
        stop_words = {'what', 'where', 'how', 'the', 'is', 'are', 'in', 'at', 'to', 'a', 'an', 'of', 'tell', 'me', 'about'}
        query_tokens = query_tokens - stop_words
        
        if not query_tokens:
             query_tokens = set(nltk.word_tokenize(user_query_text.lower()))

        for qa in all_qa:
            question_tokens = set(nltk.word_tokenize(qa.question.lower()))
            common = query_tokens & question_tokens
            if not query_tokens: continue
            
            score = len(common) / len(query_tokens)
            if user_query_text.lower() in qa.question.lower():
                score += 0.5
            
            if score > highest_score:
                highest_score = score
                best_match = qa
        
        print(f"Best QA Match Score: {highest_score}", flush=True)
        
        # Use a reasonable threshold. 0.3 is enough to beat "generic" matches usually.
        # BUT for short queries, we need a much stricter threshold to avoid false positives (e.g. "hi" matching a long sentence)
        threshold = 0.35
        if len(query_tokens) < 3:
            threshold = 0.8 # strict for short queries
            
        if best_match and highest_score >= threshold: 
            qa_response = f"{best_match.answer}\n\n(Source: {best_match.source_url})"
            source = "knowledge_base"
            tag = "qa_pair_match"
            
    except Exception as e:
        print(f"QA Pair Lookup Error: {e}")

    if qa_response:
        response = qa_response
    
    # PRIORITY 3: Standard Intents (greeting, etc.) from Model/JSON
    # Only use if we didn't find a QA match
    elif probability > 0.7:
        if tag in ['greeting', 'goodbye']:
            # Try DB first, then JSON
            row = Knowledge.query.filter_by(intent_tag=tag).first()
            if row:
                response = row.content
            else:
                for i in intents_data['intents']:
                    if i['tag'] == tag:
                        response = random.choice(i['responses'])
                        break
        else:
            # Other general intents (including 'number', 'location', etc.)
            # If QAPair didn't catch it, we fallback to these static responses.
            row = Knowledge.query.filter_by(intent_tag=tag).first()
            if row:
                response = row.content
            else:
                for i in intents_data['intents']:
                    if i['tag'] == tag:
                        if i['responses']:
                            response = random.choice(i['responses'])
                        break
                        
    # PRIORITY 4: Gemini Fallback
    if not response:
        response = get_gemini_response(user_query_text)
        source = "gemini"
        tag = "gemini_fallback"
    
    # Log the query for learning
    try:
        new_query = UserQuery(
            student_id=student_id,
            query_text=user_query_text,
            response_text=response,
            intent_tag=tag,
            confidence=probability,
            source=source
        )
        db.session.add(new_query)
        db.session.commit()
        print(f"Logged query: {user_query_text[:30]}...")
    except Exception as e:
        print(f"Error logging query: {e}")
        db.session.rollback()

    return response

# Test it out
if __name__ == "__main__":
    print("CampusAI is online! Type 'quit' to stop.")
    while True:
        message = input("You: ")
        if message.lower() == 'quit': break
        ints, ratio = predict_class(message)
        res = get_response(ints, user_query_text=message, ratio=ratio)
        print(f"Bot: {res}")