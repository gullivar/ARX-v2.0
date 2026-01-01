import sys
import os
import asyncio
from app.services.llm_service import llm_service

# Add backend to path
sys.path.append(os.getcwd())

def test_llm():
    print("Testing LLM Connection...")
    base_url = llm_service.get_base_url()
    print(f"Resolved Base URL: {base_url}")
    
    print("Testing Analysis...")
    try:
        result = llm_service.analyze_content(
            title="Test Page",
            content="This is a test content about a suspected phishing site for Bank of America containing login forms."
        )
        print("Analysis Result:", result)
    except Exception as e:
        print(f"Analysis Failed: {e}")

if __name__ == "__main__":
    test_llm()
