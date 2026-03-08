from app import app
from chatbot_engine import get_response
import logging

# Suppress other logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def test_matching():
    with open("test_results.log", "w", encoding="utf-8") as f:
        f.write("Starting Matching Logic Test...\n")
        with app.app_context():
            # Test cases that require flexible matching
            test_queries = [
                "schools in the university", # Should match "What schools and faculties..."
                "admission requirements",    # Should match "What are the admission requirements..."
                "contact info",              # Should match "How can I contact..."
                "random noise xyz"           # Should NOT match
            ]
            
            for query in test_queries:
                f.write(f"\nTesting query: '{query}'\n")
                intents_list = [] 
                ratio = 0.0
                
                try:
                    response = get_response(intents_list, user_query_text=query, ratio=ratio)
                    
                    if "(Source: https://www.mnu.ac.ke" in response:
                        f.write(f"MATCHED: query '{query}' -> Found source citation.\n")
                    else:
                        if "random" in query:
                             f.write(f"CORRECT: query '{query}' -> No match found (fallback).\n")
                        else:
                             f.write(f"FAILED: query '{query}' -> No match found.\n")
                        
                except Exception as e:
                    f.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    test_matching()
