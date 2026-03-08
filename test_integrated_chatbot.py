from app import app, db
from chatbot_engine import predict_class, get_response
from models import UserQuery

def test_chatbot():
    with app.app_context():
        # 1. Test a known query (should be local)
        print("\n--- Testing Local Query (Greeting) ---")
        msg_local = "Hi"
        ints_local, ratio_local = predict_class(msg_local)
        res_local = get_response(ints_local, user_query_text=msg_local, student_id="TEST_USER", ratio=ratio_local)
        print(f"Query: {msg_local}")
        print(f"Response: {res_local}")
        
        # 2. Test an unknown query (should be OpenAI)
        print("\n--- Testing OpenAI Fallback ---")
        msg_openai = "What are the core values of a good university citizen?"
        ints_openai, ratio_openai = predict_class(msg_openai)
        res_openai = get_response(ints_openai, user_query_text=msg_openai, student_id="TEST_USER", ratio=ratio_openai)
        print(f"Query: {msg_openai}")
        print(f"Response: {res_openai}")
        
        # 3. Verify Database Logging
        print("\n--- Verifying DB Logging ---")
        queries = UserQuery.query.order_by(UserQuery.created_at.desc()).limit(2).all()
        for q in queries:
            print(f"Logged Query: {q.query_text} | Source: {q.source} | Confidence: {q.confidence}")

if __name__ == "__main__":
    test_chatbot()
