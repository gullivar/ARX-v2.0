import chromadb
# from chromadb.utils import embedding_functions # SKIP loading model for simple inspection
import logging
import time

# --- Pydantic v2 Compatibility Patch for ChromaDB ---
import pydantic
try:
    from pydantic_settings import BaseSettings
    if not hasattr(pydantic, 'BaseSettings'):
        pydantic.BaseSettings = BaseSettings
except ImportError:
    pass
# ----------------------------------------------------

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DB_PATH = "./backend/data/chroma_db"
COLLECTION_NAME = "threat_intel_kb"

def check_embeddings():
    print("--- [Vector DB Integrity Check] ---")
    try:
        # 1. Connect
        client = chromadb.PersistentClient(path=DB_PATH)
        # We access collection WITHOUT embedding function to inspect raw stored data rapidly
        collection = client.get_collection(name=COLLECTION_NAME)
        
        count = collection.count()
        print(f"✅ Total Items in Vector DB: {count}")
        
        if count == 0:
            print("❌ DB is empty.")
            return

        # 2. Inspect Single Item (Check Embedding Existence)
        print("\n[Inspecting Sample Item...]")
        # Fetch 1 item WITH embeddings
        sample = collection.get(limit=1, include=["embeddings", "documents", "metadatas"])
        
        if not sample['ids']:
            print("❌ No items found.")
            return
            
        fqdn = sample['ids'][0]
        
        # Check embeddings
        if sample['embeddings'] is None:
             print("❌ Embeddings field returned None (Expected list).")
             return

        vector = sample['embeddings'][0]
        dim = len(vector)
        doc_preview = sample['documents'][0][:100] if sample['documents'] else "No Text"
        
        print(f"   ID (FQDN): {fqdn}")
        print(f"   Document Preview: {doc_preview}...")
        print(f"   Vector Dimension: {dim} (Standard for all-MiniLM-L6-v2 implies 384)")
        
        if dim > 0:
            print("✅ Vector Embedding exists and is valid.")
        else:
            print("❌ Vector Embedding is MISSING or EMPTY.")

        print("\n[NOTE] Skipping similarity search test in this quick check to avoid loading heavy ML models.")
        print("To run full similarity test, verify 'embeddings' field above is populated.")

    except Exception as e:
        print(f"❌ Error during check: {e}")

if __name__ == "__main__":
    check_embeddings()
