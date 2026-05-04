import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"Testing Key: {api_key[:10]}... (last 4: {api_key[-4:]})")
try:
    genai.configure(api_key=api_key, transport='rest')
    
    print("\nAvailable models for this key:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            
    print("\nTrying to connect to gemini-1.5-flash...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say 'Connection Successful'")
    print("-" * 30)
    print("SUCCESS!")
    print(f"Gemini says: {response.text}")
    print("-" * 30)
except Exception as e:
    print("-" * 30)
    print("FAILED TO CONNECT")
    print(f"Error Message: {str(e)}")
    print("-" * 30)
