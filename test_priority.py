from app import app
from chatbot_engine import get_response
import logging

# Suppress other logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

def test_priority():
    with open("test_priority.log", "w", encoding="utf-8") as f:
        f.write("Starting Priority Test...\n")
        with app.app_context():
            
            # Case 1: "contact info"
            # Previous behavior: "You can contact at: NUMBER" (Intent 'number')
            # Expected behavior: QA Pair Match (Source citation)
            query1 = "contact info"
            f.write(f"\nTesting Query 1: '{query1}'\n")
            try:
                res1 = get_response([], user_query_text=query1, ratio=1.0) # ratio=1.0 mimics high confidence intent
                if "(Source: https://www.mnu.ac.ke" in res1:
                    f.write("PASS: 'contact info' returned Scraped Data.\n")
                else:
                    f.write(f"FAIL: 'contact info' returned: {res1}\n")
            except Exception as e:
                f.write(f"ERROR: {e}\n")

            # Case 2: "Check my fee balance"
            # Expected behavior: Functional Response "Please visit the student portal..."
            # This intent is 'fee_inquiry'
            query2 = "Check my fee balance"
            f.write(f"\nTesting Query 2: '{query2}'\n")
            try:
                # We need to simulate the intent classification for this to trigger the high-priority check
                # In real app, predict_class does this. Here we manually pass it.
                intents_list = [{'intent': 'fee_inquiry', 'probability': '0.95'}] 
                res2 = get_response(intents_list, user_query_text=query2, ratio=1.0)
                
                if "Please visit the student portal" in res2:
                    f.write("PASS: 'fee balance' returned Functional Response.\n")
                else:
                    f.write(f"FAIL: 'fee balance' returned: {res2}\n")
            except Exception as e:
                f.write(f"ERROR: {e}\n")
                
            # Case 3: "Hello"
            # Expected behavior: Greeting match (Standard Intent)
            query3 = "Hello"
            f.write(f"\nTesting Query 3: '{query3}'\n")
            try:
                intents_list = [{'intent': 'greeting', 'probability': '0.99'}]
                res3 = get_response(intents_list, user_query_text=query3, ratio=1.0)
                
                # Should NOT be a QA match
                if "(Source:" in res3:
                    f.write(f"FAIL: 'Hello' returned Scraped Data: {res3}\n")
                else:
                    f.write(f"PASS: 'Hello' returned Standard Response: {res3}\n")
            except Exception as e:
                f.write(f"ERROR: {e}\n")

if __name__ == "__main__":
    test_priority()
