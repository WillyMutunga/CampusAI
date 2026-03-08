from app import app
import json

client = app.test_client()

def test_autocomplete():
    print("Testing /autocomplete route...")
    # Test with a query that should match something in intents.json (e.g. 'fee')
    try:
        response = client.get('/autocomplete?query=fee')
        print(f"Status Code: {response.status_code}")
        data = response.get_json()
        print(f"Data: {data}")
        
        if response.status_code == 200 and isinstance(data, list):
            if len(data) > 0:
                print("Autocomplete Route: SUCCESS (Returned suggestions)")
            else:
                print("Autocomplete Route: WARNING (Returned empty list, check intents.json)")
        else:
            print("Autocomplete Route: FAILURE")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_autocomplete()
