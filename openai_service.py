import openai
import os

# Set your API key here or use environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_openai_response(query):
    """
    Fetches a response from OpenAI's GPT model for general campus questions.
    """
    try:
        print(f"Querying OpenAI for: {query}")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # or gpt-4
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a university campus. Answer student questions professionally and concisely. If you don't know something specific about this campus, provide general helpful advice."},
                {"role": "user", "content": query}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "I apologize, but I'm having trouble connecting to my external knowledge base right now."

if __name__ == "__main__":
    # Test
    test_query = "What are the common challenges for first-year students?"
    print(get_openai_response(test_query))
