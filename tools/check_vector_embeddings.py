import chromadb
from chromadb.utils import embedding_functions
import logging
import time

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
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
        
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
        vector = sample['embeddings'][0]
        dim = len(vector)
        doc_preview = sample['documents'][0][:100]
        
        print(f"   ID (FQDN): {fqdn}")
        print(f"   Document Preview: {doc_preview}...")
        print(f"   Vector Dimension: {dim} (Standard for all-MiniLM-L6-v2 implies 384)")
        
        if dim > 0:
            print("✅ Vector Embedding exists and is valid.")
        else:
            print("❌ Vector Embedding is MISSING or EMPTY.")

        # 3. Similarity Search Test
        test_query = "online casino gambling betting"
        print(f"\n[Testing Similarity Search for query: '{test_query}']")
        
        start_time = time.time()
        results = collection.query(
            query_texts=[test_query],
            n_results=3
        )
        duration = time.time() - start_time
        
        print(f"   Search Time: {duration:.4f}s")
        if results['ids']:
            for i, result_id in enumerate(results['ids'][0]):
                dist = results['distances'][0][i]
                meta = results['metadatas'][0][i]
                print(f"   Rank {i+1}: {result_id} (Distance: {dist:.4f}) - Category: {meta.get('category')}")
            print("✅ Similarity Analysis is WORKING.")
        else:
            print("❌ Search returned no results.")

    except Exception as e:
        print(f"❌ Error during check: {e}")

if __name__ == "__main__":
    check_embeddings()
