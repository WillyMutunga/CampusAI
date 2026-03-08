from chatbot_engine import get_response

# Mock intent list as if it came from predict_class
intents = [{'intent': 'canteen', 'probability': '0.99'}]
query = "where is the canteen"

print(f"Testing query: {query}")
response = get_response(intents, user_query_text=query)
print(f"Response: {response}")

if "canteen" in response.lower() or "cafetaria" in response.lower() or "food" in response.lower():
    print("SUCCESS: Response seems relevant.")
else:
    print("FAILURE: Response does not seem relevant.")
