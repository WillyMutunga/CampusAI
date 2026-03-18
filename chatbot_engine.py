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
        # Pre-warm the NLTK lemmatizer so the first user request doesn't hang for 15 seconds
        try:
            predict_class("wake up")
            print("Chatbot model pre-warmed successfully.", flush=True)
        except Exception as inner_e:
            print(f"Pre-warm skipped or failed: {inner_e}", flush=True)
    except Exception as e:
        print(f"Error loading chatbot model: {e}", flush=True)

# Initial load
load_chatbot_model()

# Global Cache
model_data = {"intents": []}
qa_cache = []

def init_qa_cache():
    """Load QAPairs and compile regex tokens once during startup."""
    global qa_cache, model_data
    import re
    # Load model.json instead of intents.json
    try:
        import json
        with open('model.json', 'r') as f:
            model_data = json.load(f)
            # Ensure it's in the standard format
            if 'intents' not in model_data:
                model_data = {'intents': model_data}
    except Exception as e:
        print(f"Error loading model.json: {e}")

    try:
        from app import app
        from models import QAPair
        with app.app_context():
            all_qa = QAPair.query.all()
            qa_cache.clear()
            for qa in all_qa:
                # Pre-tokenize the database questions
                question_tokens = set(re.findall(r'\w+', qa.question.lower()))
                qa_cache.append({
                    'id': qa.id,
                    'question': qa.question,
                    'answer': qa.answer,
                    'source_url': qa.source_url,
                    'tokens': question_tokens
                })
            print(f"Loaded {len(qa_cache)} QAPairs into cache.", flush=True)
    except Exception as e:
        print(f"Warning: Could not load QAPairs into cache: {e}", flush=True)

# Call this later from app.py
# init_qa_cache()


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
    global qa_cache, model_data
    
    model_tag = intents_list[0]['intent'] if intents_list else 'unknown'
    model_prob = float(intents_list[0]['probability']) if intents_list else 0.0
    
    response = ""
    source = "local"
    tag = model_tag
    
    import random
    import re

    # PRIORITY 1: Functional Intents
    if model_tag == 'fee_inquiry' and model_prob > 0.8:
        response = "Please visit the student portal to verify your up-to-date fee balance."
        return response
    elif model_tag == 'fee_structure' and model_prob > 0.8:
        response = "You can download the latest fee structure here: <a href='/static/uploads/fee_structure.pdf' target='_blank'>Download Fee Structure</a>."
        return response

    # Calculate QA Match Score using cache
    print(f"Checking cached QAPairs for: {user_query_text}", flush=True)
    qa_response = None
    best_qa_match = None
    highest_qa_score = 0.0
    
    try:
        query_tokens = set(re.findall(r'\w+', user_query_text.lower()))
        stop_words = {'what', 'where', 'how', 'the', 'is', 'are', 'in', 'at', 'to', 'a', 'an', 'of', 'tell', 'me', 'about'}
        query_tokens_filtered = query_tokens - stop_words
        if not query_tokens_filtered:
            query_tokens_filtered = query_tokens

        for qa in qa_cache:
            common = query_tokens_filtered & qa['tokens']
            if not query_tokens_filtered: continue
            
            score = len(common) / len(query_tokens_filtered)
            if user_query_text.lower() in qa['question'].lower():
                score += 0.5
            
            if score > highest_qa_score:
                highest_qa_score = score
                best_qa_match = qa
                
        print(f"Best QA Match Score: {highest_qa_score}", flush=True)
    except Exception as e:
        print(f"QA Pair Lookup Error: {e}")

    # Set threshold
    qa_threshold = 0.35 if len(query_tokens) >= 3 else 0.8
    model_threshold = 0.65

    print(f"Model Score ({model_tag}): {model_prob:.2f} | QA Score: {highest_qa_score:.2f}")

    # Comparison Logic
    use_qa = best_qa_match and highest_qa_score >= qa_threshold
    use_model = model_prob >= model_threshold

    if use_qa and use_model:
        # Compare scores to give the best answer
        if highest_qa_score > model_prob:
            response = f"{best_qa_match['answer']}\n\n(Source: {best_qa_match['source_url']})"
            source = "knowledge_base"
            tag = "qa_pair_match"
        else:
            use_qa = False # Fall back to model handling below
    elif use_qa:
         response = f"{best_qa_match['answer']}\n\n(Source: {best_qa_match['source_url']})"
         source = "knowledge_base"
         tag = "qa_pair_match"

    if not response and use_model:
        # Standard Knowledge from Model JSON
        for i in model_data['intents']:
            # Handle both formats since model.json has intent and text
            t = i.get('intent') or i.get('tag')
            if t == model_tag:
                # Use Responses array from Model JSON
                if i.get('responses'):
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
            confidence=max(model_prob, highest_qa_score),
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
