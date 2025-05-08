# test_openrouter.py

from openai import OpenAI
import os
from dotenv import load_dotenv

# Load your API key from environment or .env
load_dotenv()
api_key = os.getenv("LLM_API_KEY")  # Make sure .env has LLM_API_KEY=your_key_here

# Initialize the client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

def run_ollama(prompt):
    """Uses OpenRouter to get a response from a hosted LLM model."""
    try:
        completion = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error during OpenRouter call: {str(e)}"

# DEMO USAGE
if __name__ == "__main__":
    demo_prompt = "What is insurance? context: "
    print("Sending prompt to OpenRouter...")
    response = run_ollama(demo_prompt)
    print("\nResponse from OpenRouter:\n")
    print(response)
