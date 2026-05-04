import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key, transport='rest')

models_to_try = [
    'gemini-flash-latest',
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash-001',
    'gemini-2.5-flash',
    'gemini-pro-latest'
]

working_model = None

for model_name in models_to_try:
    print(f"Trying {model_name}...")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Say 'Test'")
        print(f"SUCCESS with {model_name}!")
        working_model = model_name
        break
    except Exception as e:
        print(f"Failed: {str(e)[:100]}...")

if working_model:
    print(f"\nWe should use: {working_model}")
else:
    print("\nAll models failed due to quota or access limits.")
