
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_keys = os.getenv("GOOGLE_API_KEYS", "").split(",")
if not api_keys: exit("No keys")

genai.configure(api_key=api_keys[0])

try:
    print(f"Testing Gemini 1.5 Flash with key {api_keys[0][:5]}...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    resp = model.generate_content("Hello, are you working?")
    print(f"Success! Response: {resp.text}")
except Exception as e:
    print(f"1.5 Flash Failed: {e}")

try:
    print(f"Testing Gemini 2.0 Flash Exp with key {api_keys[0][:5]}...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    resp = model.generate_content("Hello, are you working?")
    print(f"Success! Response: {resp.text}")
except Exception as e:
    print(f"2.0 Flash Exp Failed: {e}")
