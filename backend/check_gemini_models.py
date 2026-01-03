
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_keys = os.getenv("GOOGLE_API_KEYS", "").split(",")
key = api_keys[0] if api_keys else os.getenv("GOOGLE_API_KEY")

print(f"Using Key: {key[:5]}...")
genai.configure(api_key=key)

try:
    print("Listing models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
