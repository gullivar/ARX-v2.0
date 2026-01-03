
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EXTERNAL_HOST = "106.254.248.154"
PORT = 17311

def test_connection():
    url = f"http://{EXTERNAL_HOST}:{PORT}/api/version"
    print(f"Testing connectivity to: {url}")
    
    try:
        response = requests.get(url, timeout=10.0)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            print("✅ Connection Successful!")
            return True
        else:
            print("❌ Connection Failed with non-200 status.")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Connection Timed Out (10s).")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
    return False

def test_generate():
    url = f"http://{EXTERNAL_HOST}:{PORT}/api/generate"
    print(f"\nTesting generation to: {url}")
    
    payload = {
        "model": "llama3:latest",
        "prompt": "Say hello",
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30.0)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response Snippet: {response.text[:100]}")
            print("✅ Generation Test Initialized (Model is reachable)")
        else:
            print(f"❌ Generation Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Generation Error: {e}")

if __name__ == "__main__":
    if test_connection():
        test_generate()
