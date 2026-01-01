import sys
import os
import asyncio
import logging

# Setup Path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic v2 Compatibility Patch ---
import pydantic
try:
    from pydantic_settings import BaseSettings
    if not hasattr(pydantic, 'BaseSettings'):
        pydantic.BaseSettings = BaseSettings
except ImportError:
    pass
# ---------------------------------------

from app.services.vector_service import vector_service

def test_similarity():
    query = "fake login page for bank credentials"
    print(f"\n--- Testing Vector Similarity Search for: '{query}' ---")
    
    try:
        results = vector_service.search_similar(query, limit=3)
        
        if not results:
            print("❌ No results found. Vector DB might be empty or malformed.")
            return

        print(f"✅ Found {len(results)} matches. The KB IS ready for similarity analysis.")
        for i, res in enumerate(results):
            # res is usually a dict or object depending on implementation. 
            # In v2 vector_service, search_similar returns list of dicts: {'fqdn':..., 'score':..., 'category':...}
            print(f"\n   Rank {i+1}:")
            print(f"     FQDN: {res.get('fqdn')}")
            print(f"     Score (Distance): {res.get('score', 'N/A')}")
            print(f"     Category: {res.get('category')}")
            
    except Exception as e:
        print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    test_similarity()
