import google.generativeai as genai
import os

# Set your API key here
GEMINI_API_KEY = "AIzaSyB9AdNLDRzLkeG5qqF7QjvhciHtiGOVd6A"

# Configure the SDK
genai.configure(api_key=GEMINI_API_KEY)

def get_gemini_response(query):
    """
    Fetches a response from Google's Gemini Pro model for general campus questions.
    """
    try:
        print(f"Querying Gemini for: {query}")
        
        # Initialize the model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # System instructions
        system_instruction = (
            "You are a helpful assistant for a university campus. "
            "Answer student questions professionally and concisely. "
            "If you don't know something specific about this campus, provide general helpful advice."
        )
        
        # Generate content
        response = model.generate_content(
            f"{system_instruction}\n\nUser Question: {query}",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=300,
                temperature=0.7,
            )
        )
        
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "I apologize, but I'm having trouble connecting to my external intelligence engine right now."

if __name__ == "__main__":
    # Test
    test_query = "What are the common challenges for first-year students?"
    print(get_gemini_response(test_query))
